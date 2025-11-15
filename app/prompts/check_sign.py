CHECK_IMAGE_SIGN_PROMPT = """\
检查表格扫描件中的签名位置和质量状态。

<position_detection>
识别所有可能的签名位置：
1. 明确标识：含"签名/签字/姓名"字样，或人员角色（申请人/审核人/负责人/质检员等）
2. 视觉特征：横线区域(_____)、空白方框、日期栏旁、表格底部审批栏
3. 语义暗示：确认/同意/批准等字样后的空白，职务后空白（如"经理:___"）
4. 结构暗示：表格最后几行、多人签名重复结构、对称审批流程栏

注意：
- 只检测人员签名位置，不要将表格内容、检查项目、评分项等误判为签名位置
- 标准审批表通常有3-5个签名位置（如质检员、技术负责人、施工负责人、监理工程师）
</position_detection>

<status_codes>
missing: 完全空白，无任何痕迹（最严重）
faint: 笔迹极淡，颜色很浅，需仔细辨认才能看到（严重质量问题）
blurry: 模糊失焦，边缘不清
illegible: 极度潦草，无法辨认
partial: 不完整，被遮挡或裁切
stained: 有污渍、水渍覆盖
smudged: 墨迹晕染、印油不清
ok: 清晰正常，无明显问题
na: 标注了N/A、/、无等（豁免）
</status_codes>

<critical_rules>
1. **缺漏判定**：签名位置完全空白、只有下划线/框线、或仅有极微弱痕迹时判定为missing
2. **笔迹过淡判定**：若笔迹颜色极浅、对比度很低、几乎看不清楚，判定为faint（不是ok）
3. **宁缺毋滥原则**：有疑问时应标记为问题状态，不要轻易判定为ok
4. **优先级**：missing > faint > partial > blurry > other > ok
</critical_rules>

<output_format>
输出JSON（无Markdown代码块）：
{
  "位置名称": {
    "status": "状态代码",
    "description": "问题说明（非ok/na必填）"
  }
}

示例：
{
  "专职质量检查员": {"status": "missing", "description": "完全空白"},
  "技术负责人": {"status": "faint", "description": "笔迹极淡，颜色很浅"},
  "施工负责人": {"status": "ok"},
  "监理工程师": {"status": "blurry", "description": "失焦模糊"}
}

无签名位置则返回: {}
</output_format>
"""
