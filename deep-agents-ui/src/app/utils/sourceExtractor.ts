import type { Source, ToolCall } from "../types/types";

/**
 * 校验对象是否为有效的来源数据
 */
function isValidSource(obj: unknown): obj is { url: string; title: string; type?: string } {
  return (
    typeof obj === "object" &&
    obj !== null &&
    typeof (obj as Record<string, unknown>).url === "string" &&
    typeof (obj as Record<string, unknown>).title === "string"
  );
}

/**
 * 创建 Source 对象，确保 type 字段类型安全
 */
function createSource(
  index: number,
  data: { url: string; title: string; type?: string }
): Source {
  return {
    index,
    title: data.title,
    url: data.url,
    type: data.type === "page" || data.type === "attachment" ? data.type : undefined,
  };
}

/**
 * 从工具调用结果中提取来源
 * 支持 confluence_get_page 和 confluence_search 两种工具
 */
export function extractSourcesFromToolCalls(toolCalls: ToolCall[]): Source[] {
  const sources: Source[] = [];
  const seenUrls = new Set<string>();
  let index = 1;

  for (const toolCall of toolCalls) {
    if (!toolCall.result) continue;

    try {
      // 处理 confluence_get_page 结果
      if (toolCall.name === "confluence_get_page") {
        const result = JSON.parse(toolCall.result);
        const metadata = result?.metadata;
        if (isValidSource(metadata) && !seenUrls.has(metadata.url)) {
          seenUrls.add(metadata.url);
          sources.push(createSource(index++, metadata));
        }
      }

      // 处理 confluence_search 结果（数组格式）
      if (toolCall.name === "confluence_search") {
        const results = JSON.parse(toolCall.result);
        if (Array.isArray(results)) {
          for (const item of results) {
            if (isValidSource(item) && !seenUrls.has(item.url)) {
              seenUrls.add(item.url);
              sources.push(createSource(index++, item));
            }
          }
        }
      }
    } catch {
      // JSON 解析失败，跳过
    }
  }

  return sources;
}
