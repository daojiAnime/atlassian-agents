export function getDeployment() {
  return {
    name: "Deep Agent",
    deploymentUrl: process.env.NEXT_PUBLIC_API_URL || "/api",
    agentId: process.env.NEXT_PUBLIC_AGENT_ID || "deepagent",
  };
}
