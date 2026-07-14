"use client";

import { useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import { Chat } from "./chat";

const starterCode = `def two_sum(nums, target):
  # Write your approach here
  pass
`;

const resizerWidth = 8;

function ProblemPanel() {
  return (
    <section className="flex min-h-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-6 py-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
          Array · Hash Table
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-950">Two Sum</h1>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5 text-sm leading-6 text-slate-700">
        <p>
          Given an array of integers <code>nums</code> and an integer{" "}
          <code>target</code>, return indices of the two numbers such that they
          add up to <code>target</code>.
        </p>

        <p className="mt-4">
          You may assume that each input has exactly one solution, and you may
          not use the same element twice.
        </p>

        <p className="mt-4">You can return the answer in any order.</p>

        <h2 className="mt-8 text-sm font-semibold text-slate-950">Examples</h2>

        <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-4 font-mono text-xs leading-5 text-slate-800">
          <p>Input: nums = [2,7,11,15], target = 9</p>
          <p>Output: [0,1]</p>
          <p>Explanation: nums[0] + nums[1] == 9</p>
        </div>

        <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-4 font-mono text-xs leading-5 text-slate-800">
          <p>Input: nums = [3,2,4], target = 6</p>
          <p>Output: [1,2]</p>
        </div>

        <h2 className="mt-8 text-sm font-semibold text-slate-950">
          Constraints
        </h2>

        <ul className="mt-3 list-disc space-y-2 pl-5">
          <li>
            <code>2 &lt;= nums.length &lt;= 10,000</code>
          </li>
          <li>
            <code>-1,000,000,000 &lt;= nums[i] &lt;= 1,000,000,000</code>
          </li>
          <li>
            <code>-1,000,000,000 &lt;= target &lt;= 1,000,000,000</code>
          </li>
          <li>Only one valid answer exists.</li>
        </ul>
      </div>
    </section>
  );
}

function CodingWorkspace() {
  const [code, setCode] = useState(starterCode);

  return (
    <section className="flex min-h-0 flex-col bg-white">
      <div className="flex h-14 items-center justify-between border-b border-slate-200 px-5">
        <div>
          <p className="text-sm font-medium text-slate-950">Workspace</p>
          <p className="text-xs text-slate-500">Python</p>
        </div>
        <div className="rounded-md border border-slate-200 px-2.5 py-1 text-xs text-slate-500">
          v0.1.2
        </div>
      </div>

      <div className="min-h-0 flex-1">
        <Editor
          aria-label="Coding workspace"
          language="python"
          theme="vs"
          value={code}
          onChange={(value) => setCode(value ?? "")}
          options={{
            automaticLayout: true,
            fontSize: 14,
            insertSpaces: true,
            lineHeight: 22,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            tabSize: 4,
            wordWrap: "on",
          }}
        />
      </div>
    </section>
  );
}

export function Workspace() {
  const workspaceRef = useRef(null);
  const [problemPanelWidth, setProblemPanelWidth] = useState(50);
  const [isResizing, setIsResizing] = useState(false);

  function updatePanelWidth(clientX) {
    const workspace = workspaceRef.current;
    if (!workspace) return;

    const rect = workspace.getBoundingClientRect();
    const minProblemPanelWidth = 320;
    const minWorkspacePanelWidth = 360;
    const availablePanelWidth = rect.width - resizerWidth;
    const minPanelWidth = Math.min(
      minProblemPanelWidth,
      availablePanelWidth / 2,
    );
    const maxPanelWidth = Math.max(
      availablePanelWidth - minWorkspacePanelWidth,
      availablePanelWidth / 2,
    );
    const nextPanelWidth = clientX - rect.left - resizerWidth / 2;

    if (availablePanelWidth <= 0) {
      return;
    }

    const clampedPanelWidth = Math.min(
      Math.max(nextPanelWidth, minPanelWidth),
      maxPanelWidth,
    );

    setProblemPanelWidth((clampedPanelWidth / rect.width) * 100);
  }

  function handleResizeStart(event) {
    event.currentTarget.setPointerCapture(event.pointerId);
    setIsResizing(true);
    updatePanelWidth(event.clientX);
  }

  function handleResizeMove(event) {
    if (!isResizing) return;
    updatePanelWidth(event.clientX);
  }

  function handleResizeEnd(event) {
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }

    setIsResizing(false);
  }

  return (
    <main className="flex h-screen flex-col bg-slate-100 text-slate-950">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-5">
        <div className="flex items-center gap-3">
          <img
            src="/swell-icon.svg"
            alt=""
            className="h-9 w-6 object-contain"
            aria-hidden="true"
          />
          <p className="font-brand text-3xl font-medium leading-none tracking-normal text-slate-950">
            swell
          </p>
        </div>
      </header>

      <div
        ref={workspaceRef}
        className="workspace-grid min-h-0 flex-1"
        style={{
          "--problem-panel-width": `${problemPanelWidth}%`,
        }}
      >
        <ProblemPanel />
        <button
          type="button"
          aria-label="Resize problem and coding panels"
          aria-orientation="vertical"
          className="workspace-resizer group relative flex min-h-0 items-center justify-center border-x border-slate-200 bg-slate-100 transition focus:outline-none"
          onPointerDown={handleResizeStart}
          onPointerMove={handleResizeMove}
          onPointerUp={handleResizeEnd}
          onPointerCancel={handleResizeEnd}
        >
          <span
            className={`h-14 w-1 rounded-full bg-slate-300 transition-opacity ${
              isResizing ? "opacity-0" : "opacity-100 group-hover:opacity-0"
            }`}
            aria-hidden="true"
          />
          <span
            className={`absolute h-full w-1 bg-teal-500 transition-opacity ${
              isResizing ? "opacity-100" : "opacity-0 group-hover:opacity-100"
            }`}
            aria-hidden="true"
          />
        </button>
        <CodingWorkspace />
        <Chat />
      </div>
    </main>
  );
}
