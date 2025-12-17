"use client";

import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import styles from "./MarkdownContent.module.scss";
import type { Source } from "../../types/types";

interface MarkdownContentProps {
  content: string;
  sources?: Source[];
  className?: string;
  /** 是否显示参考来源列表（只在最终报告显示） */
  showSourcesList?: boolean;
}

/**
 * 从 Markdown 内容中解析参考来源
 * 支持格式:
 * - 1. **《标题》** - URL
 * - [1] [标题](url)
 * - | [1] | 标题 | [链接](url) |
 */
function extractSourcesFromContent(content: string): Source[] {
  const sources: Source[] = [];
  let match;

  // 模式 1: 数字. **《标题》** - URL (Perplexica 常见格式)
  const pattern1 = /(\d+)\.\s*\*?\*?[《\[]([^》\]]+)[》\]]\*?\*?\s*-\s*(https?:\/\/[^\s\n]+)/g;
  while ((match = pattern1.exec(content)) !== null) {
    const index = parseInt(match[1], 10);
    if (!sources.find((s) => s.index === index)) {
      sources.push({
        index,
        title: match[2].trim(),
        url: match[3].trim(),
      });
    }
  }

  // 模式 2: [n] [标题](url)
  const pattern2 = /\[(\d+)\]\s*\[([^\]]+)\]\(([^)]+)\)/g;
  while ((match = pattern2.exec(content)) !== null) {
    const index = parseInt(match[1], 10);
    if (!sources.find((s) => s.index === index)) {
      sources.push({
        index,
        title: match[2],
        url: match[3],
      });
    }
  }

  // 模式 3: | [n] | 标题 | [链接](url) | 或 | [n] | 标题 | url |
  const pattern3 =
    /\|\s*\[?(\d+)\]?\s*\|\s*([^|]+)\s*\|\s*(?:\[([^\]]*)\]\()?([^)|]+)\)?/g;
  while ((match = pattern3.exec(content)) !== null) {
    const index = parseInt(match[1], 10);
    if (!sources.find((s) => s.index === index)) {
      sources.push({
        index,
        title: match[2].trim(),
        url: match[4].trim().replace(/\)?\s*\|?$/, ""),
      });
    }
  }

  // 模式 4: - [标题](url) 列表格式，按顺序编号
  if (sources.length === 0) {
    const pattern4 = /-\s*\[([^\]]+)\]\(([^)]+)\)/g;
    let idx = 1;
    while ((match = pattern4.exec(content)) !== null) {
      sources.push({
        index: idx++,
        title: match[1],
        url: match[2],
      });
    }
  }

  return sources;
}

/**
 * 将 [1] 或 [1][2] 格式的引文转换为可点击的 HTML 链接
 */
function processCitations(content: string, sources: Source[]): string {
  if (sources.length === 0) {
    return content;
  }

  // 匹配 [数字] 但排除 Markdown 链接格式 [text](url) 和参考来源部分
  // 使用负向前瞻排除 [数字] 后面紧跟 ] 或 ( 的情况
  const citationRegex = /\[(\d+)\](?!\(|[^\]]*\]\()/g;

  return content.replace(citationRegex, (match, numStr: string) => {
    const index = parseInt(numStr, 10);
    const source = sources.find((s) => s.index === index);

    if (source?.url) {
      // 生成 Perplexica 风格的引文 HTML
      return `<a href="${source.url}" target="_blank" rel="noopener noreferrer" class="citation" title="${source.title}">${index}</a>`;
    }

    return match;
  });
}

/**
 * 从内容中提取被实际引用的编号
 * 匹配 [1], [2], [1][2] 等格式
 */
function extractCitedIndices(content: string): Set<number> {
  const citedIndices = new Set<number>();
  // 匹配 [数字] 但排除 Markdown 链接格式
  const citationRegex = /\[(\d+)\](?!\(|[^\]]*\]\()/g;
  let match;
  while ((match = citationRegex.exec(content)) !== null) {
    citedIndices.add(parseInt(match[1], 10));
  }
  return citedIndices;
}

/**
 * 过滤并重新编号来源列表，只保留被引用的来源
 */
function filterAndRenumberSources(
  sources: Source[],
  citedIndices: Set<number>
): { filteredSources: Source[]; indexMap: Map<number, number> } {
  // 过滤出被引用的来源
  const citedSources = sources.filter((s) => citedIndices.has(s.index));

  // 按原始 index 排序
  citedSources.sort((a, b) => a.index - b.index);

  // 创建新旧编号映射（保持原始编号，不重新编号）
  const indexMap = new Map<number, number>();
  citedSources.forEach((s) => {
    indexMap.set(s.index, s.index);
  });

  return { filteredSources: citedSources, indexMap };
}

/**
 * 生成参考来源列表的 Markdown
 */
function generateSourcesList(sources: Source[]): string {
  if (sources.length === 0) return "";

  const lines = ["\n\n---\n\n### 参考来源\n"];
  for (const source of sources) {
    lines.push(`- [${source.index}] [${source.title}](${source.url})`);
  }
  return lines.join("\n");
}

/**
 * 移除 LLM 生成的参考来源部分（可能包含错误 URL）
 */
function removeLLMGeneratedSources(content: string): string {
  // 匹配常见的参考来源标题格式
  const patterns = [
    /\n+---\s*\n+###?\s*(?:参考来源|参考文献|Sources|References)\s*\n[\s\S]*$/i,
    /\n+###?\s*(?:参考来源|参考文献|Sources|References)\s*\n[\s\S]*$/i,
  ];

  let result = content;
  for (const pattern of patterns) {
    result = result.replace(pattern, "");
  }
  return result.trim();
}

export const MarkdownContent = React.memo<MarkdownContentProps>(
  ({ content, sources: externalSources, className = "", showSourcesList = false }) => {
    // 优先使用外部传入的真实 sources（从工具调用提取）
    // 如果没有，则从内容中解析（兜底方案）
    const sources = useMemo(() => {
      if (externalSources && externalSources.length > 0) {
        return externalSources;
      }
      return extractSourcesFromContent(content);
    }, [content, externalSources]);

    // 预处理内容：
    // 1. 移除 LLM 生成的参考来源（可能有错误 URL）
    // 2. 转换引文为可点击链接
    // 3. 只在 showSourcesList=true 时添加参考来源列表（仅显示被引用的来源）
    const processedContent = useMemo(() => {
      if (sources.length === 0) {
        return content;
      }

      // 移除 LLM 生成的参考来源部分
      let result = removeLLMGeneratedSources(content);

      // 提取文中实际引用的编号
      const citedIndices = extractCitedIndices(result);

      // 过滤出被引用的来源
      const { filteredSources } = filterAndRenumberSources(sources, citedIndices);

      // 转换引文标记为链接（使用完整的 sources 以支持所有引用）
      result = processCitations(result, sources);

      // 只在最终报告时添加参考来源列表（仅显示被引用的来源）
      if (showSourcesList && filteredSources.length > 0) {
        result += generateSourcesList(filteredSources);
      }

      return result;
    }, [content, sources, showSourcesList]);

    return (
      <div className={`${styles.markdown} ${className}`}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw]}
          components={{
            code({ inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || "");
              return !inline && match ? (
                <SyntaxHighlighter
                  style={oneDark as any}
                  language={match[1]}
                  PreTag="div"
                  className={styles.codeBlock}
                >
                  {String(children).replace(/\n$/, "")}
                </SyntaxHighlighter>
              ) : (
                <code className={styles.inlineCode} {...props}>
                  {children}
                </code>
              );
            },
            pre({ children }: any) {
              return <div className={styles.preWrapper}>{children}</div>;
            },
            a({ href, children, className: linkClassName, title }: any) {
              // 检查是否是引文链接 (通过 class="citation")
              const isCitation = linkClassName === "citation";
              return (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={isCitation ? styles.citation : styles.link}
                  title={title}
                >
                  {children}
                </a>
              );
            },
            blockquote({ children }: any) {
              return (
                <blockquote className={styles.blockquote}>
                  {children}
                </blockquote>
              );
            },
            ul({ children }: any) {
              return <ul className={styles.list}>{children}</ul>;
            },
            ol({ children }: any) {
              return <ol className={styles.orderedList}>{children}</ol>;
            },
            table({ children }: any) {
              return (
                <div className={styles.tableWrapper}>
                  <table className={styles.table}>{children}</table>
                </div>
              );
            },
          }}
        >
          {processedContent}
        </ReactMarkdown>
      </div>
    );
  },
);

MarkdownContent.displayName = "MarkdownContent";
