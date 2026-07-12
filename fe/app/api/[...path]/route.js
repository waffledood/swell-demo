import { initApiPassthrough } from "langgraph-nextjs-api-passthrough";

export const runtime = "nodejs";
export const maxDuration = 60;

export const { GET, POST, PUT, PATCH, DELETE, OPTIONS } = initApiPassthrough({
  apiUrl: process.env.LANGGRAPH_API_URL,
  apiKey: process.env.LANGSMITH_API_KEY,
});
