import { Client } from "@langchain/langgraph-sdk";
import { getDeployment } from "./environment/deployments";

export function createClient(accessToken: string) {
  const deployment = getDeployment();
  let apiUrl = deployment?.deploymentUrl || "";

  // 如果是相对路径，转换为完整 URL
  if (apiUrl.startsWith("/")) {
    apiUrl = `${typeof window !== "undefined" ? window.location.origin : ""}${apiUrl}`;
  }

  return new Client({
    apiUrl,
    apiKey: accessToken,
    defaultHeaders: {
      "x-auth-scheme": "langsmith",
    },
  });
}
