"use client";

import { useState } from "react";
import { useStream } from "@langchain/react";

const ASSISTANT_ID = "swell_agent";

// @langchain/langgraph-sdk's streaming transport calls `new URL(apiUrl)` with
// no base, which throws on a relative path like "/api" - needs to be absolute.
function getApiUrl() {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== "undefined") return `${window.location.origin}/api`;
  return "/api";
}

function extractText(message) {
  const content = message.content;
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return "";

  return content
    .filter((block) => block && typeof block === "object" && block.type === "text")
    .map((block) => block.text ?? "")
    .join("");
}

function makeEventId() {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function ChatMessage({ message }) {
  const isCandidate = message.type === "human";
  const text = extractText(message);
  if (!text) return null;

  return (
    <div className={`flex ${isCandidate ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-5 ${
          isCandidate
            ? "bg-teal-600 text-white"
            : "bg-slate-100 text-slate-900"
        }`}
      >
        {text}
      </div>
    </div>
  );
}

export function Chat() {
  const [input, setInput] = useState("");
  const stream = useStream({ apiUrl: getApiUrl(), assistantId: ASSISTANT_ID });

  const hintLevel = stream.values?.hint_level ?? 0;
  const candidateStatus = stream.values?.candidate_status;

  function submitEvent(type, payload) {
    stream.submit({
      incoming_event: { event_id: makeEventId(), type, payload },
    });
  }

  function handleSend(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || stream.isLoading) return;

    submitEvent("CANDIDATE_MESSAGE", { text });
    setInput("");
  }

  function handleRequestHint() {
    if (stream.isLoading) return;
    submitEvent("HINT_REQUESTED", {});
  }

  const visibleMessages = (stream.messages ?? []).filter(
    (message) => message.type === "human" || message.type === "ai",
  );

  return (
    <section className="flex min-h-0 flex-col border-l border-slate-200 bg-white">
      <div className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 px-4">
        <p className="text-sm font-medium text-slate-950">Interview Chat</p>
        {candidateStatus && candidateStatus !== "PROGRESSING" && (
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
            {candidateStatus.replaceAll("_", " ").toLowerCase()}
          </span>
        )}
      </div>

      {stream.error != null && (
        <p className="border-b border-red-100 bg-red-50 px-4 py-2 text-xs text-red-700">
          Something went wrong reaching the coach. Try sending your message again.
        </p>
      )}

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {visibleMessages.length === 0 && (
          <p className="text-sm text-slate-500">
            Say hello to start the interview.
          </p>
        )}
        {visibleMessages.map((message, index) => (
          <ChatMessage key={message.id ?? index} message={message} />
        ))}
        {stream.isLoading && (
          <p className="text-xs text-slate-400">swell is thinking…</p>
        )}
      </div>

      <form
        onSubmit={handleSend}
        className="shrink-0 border-t border-slate-200 p-3"
      >
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Type your response…"
            disabled={stream.isLoading}
            className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={stream.isLoading || !input.trim()}
            className="shrink-0 rounded-md bg-teal-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-teal-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
        <button
          type="button"
          onClick={handleRequestHint}
          disabled={stream.isLoading}
          className="mt-2 text-xs font-medium text-teal-700 hover:underline disabled:opacity-50"
        >
          Request a hint (level {hintLevel})
        </button>
      </form>
    </section>
  );
}
