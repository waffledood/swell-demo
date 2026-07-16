import { initApiPassthrough } from "langgraph-nextjs-api-passthrough";

// langgraph-nextjs-api-passthrough defaults to "edge" - it's built around Web
// Streams for proxying long-lived SSE connections. We'd previously overridden
// this to "nodejs", which has a hard maxDuration ceiling (60s on Hobby) and
// less streaming-friendly connection handling - every /stream/events call was
// hitting that ceiling regardless of how fast the underlying agent actually
// responded, since the proxied connection wasn't closing cleanly under Node.
export const runtime = "edge";

export const { GET, POST, PUT, PATCH, DELETE, OPTIONS } = initApiPassthrough({
  apiUrl: process.env.LANGGRAPH_API_URL,
  apiKey: process.env.LANGSMITH_API_KEY,
});
