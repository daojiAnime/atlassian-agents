"use client";

import React, { useEffect, useMemo } from "react";
import { User, Bot } from "lucide-react";
import { SubAgentIndicator } from "../SubAgentIndicator/SubAgentIndicator";
import { ToolCallBox } from "../ToolCallBox/ToolCallBox";
import { MarkdownContent } from "../MarkdownContent/MarkdownContent";
import type { SubAgent, ToolCall, Source } from "../../types/types";
import { extractSourcesFromToolCalls } from "../../utils/sourceExtractor";
import styles from "./ChatMessage.module.scss";
import { Message } from "@langchain/langgraph-sdk";
import { extractStringFromMessageContent } from "../../utils/utils";

interface ChatMessageProps {
  message: Message;
  toolCalls: ToolCall[];
  showAvatar: boolean;
  onSelectSubAgent: (subAgent: SubAgent) => void;
  selectedSubAgent: SubAgent | null;
  /** 全局 sources（从整个对话的所有 toolCalls 中提取） */
  allSources?: Source[];
}

/** 最终报告判定阈值 */
const FINAL_REPORT_MIN_LENGTH = 500;
const FINAL_REPORT_MIN_CITATIONS = 3;

/**
 * 判断是否是最终报告（应该显示参考来源列表）
 * 标准：内容超过阈值字符 且 包含至少阈值个引文标记
 */
function isFinalReport(content: string): boolean {
  if (!content || content.length < FINAL_REPORT_MIN_LENGTH) {
    return false;
  }
  const citationMatches = content.match(/\[\d+\]/g);
  return citationMatches !== null && citationMatches.length >= FINAL_REPORT_MIN_CITATIONS;
}

export const ChatMessage = React.memo<ChatMessageProps>(
  ({ message, toolCalls, showAvatar, onSelectSubAgent, selectedSubAgent, allSources }) => {
    const isUser = message.type === "human";
    const messageContent = extractStringFromMessageContent(message);
    const hasContent = messageContent && messageContent.trim() !== "";
    const hasToolCalls = toolCalls.length > 0;

    // 判断是否是最终报告
    const isFinalReportMessage = useMemo(
      () => isFinalReport(messageContent || ""),
      [messageContent],
    );

    // 从工具调用中提取当前消息的 sources
    // 对于最终报告，优先使用全局 allSources（包含整个对话的所有来源）
    const sources = useMemo(() => {
      if (isFinalReportMessage && allSources && allSources.length > 0) {
        return allSources;
      }
      return extractSourcesFromToolCalls(toolCalls);
    }, [toolCalls, allSources, isFinalReportMessage]);

    // 只在最终报告显示参考来源列表
    const showSourcesList = isFinalReportMessage;

    const subAgents = useMemo(() => {
      return toolCalls
        .filter((toolCall: ToolCall) => {
          return (
            toolCall.name === "task" &&
            toolCall.args["subagent_type"] &&
            toolCall.args["subagent_type"] !== "" &&
            toolCall.args["subagent_type"] !== null
          );
        })
        .map((toolCall: ToolCall) => {
          return {
            id: toolCall.id,
            name: toolCall.name,
            subAgentName: toolCall.args["subagent_type"],
            input: toolCall.args["description"],
            output: toolCall.result,
            status: toolCall.status,
          };
        });
    }, [toolCalls]);

    const subAgentsString = useMemo(() => {
      return JSON.stringify(subAgents);
    }, [subAgents]);

    useEffect(() => {
      if (
        subAgents.some(
          (subAgent: SubAgent) => subAgent.id === selectedSubAgent?.id,
        )
      ) {
        onSelectSubAgent(
          subAgents.find(
            (subAgent: SubAgent) => subAgent.id === selectedSubAgent?.id,
          )!,
        );
      }
    }, [selectedSubAgent, onSelectSubAgent, subAgentsString]);

    return (
      <div
        className={`${styles.message} ${isUser ? styles.user : styles.assistant}`}
      >
        <div
          className={`${styles.avatar} ${!showAvatar ? styles.avatarHidden : ""}`}
        >
          {showAvatar &&
            (isUser ? (
              <User className={styles.avatarIcon} />
            ) : (
              <Bot className={styles.avatarIcon} />
            ))}
        </div>
        <div className={styles.content}>
          {hasContent && (
            <div className={styles.bubble}>
              {isUser ? (
                <p className={styles.text}>{messageContent}</p>
              ) : (
                <MarkdownContent
                  content={messageContent}
                  sources={sources}
                  showSourcesList={showSourcesList}
                />
              )}
            </div>
          )}
          {hasToolCalls && (
            <div className={styles.toolCalls}>
              {toolCalls.map((toolCall: ToolCall) => {
                if (toolCall.name === "task") return null;
                return <ToolCallBox key={toolCall.id} toolCall={toolCall} />;
              })}
            </div>
          )}
          {!isUser && subAgents.length > 0 && (
            <div className={styles.subAgents}>
              {subAgents.map((subAgent: SubAgent) => (
                <SubAgentIndicator
                  key={subAgent.id}
                  subAgent={subAgent}
                  onClick={() => onSelectSubAgent(subAgent)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    );
  },
);

ChatMessage.displayName = "ChatMessage";
