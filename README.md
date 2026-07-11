# swell-demo

A demo repo for swell, an AI software engineering coach that helps you practice data structures and algorithms through realistic technical interviews.

## Task 1: Defining Problem, Audience, and Scope

Software engineers struggle to prepare effectively for technical interviews because practicing coding problems alone does not replicate the experience of a real interview.

A mid-level software engineer preparing for a first FAANG-style coding round in the next 8 weeks needs to develop both strong data structures and algorithms skills and the ability to solve problems under interview conditions. Their goal is not only to arrive at the correct solution, but also to communicate their thought process, respond to hints, justify trade-offs, and collaborate effectively with an interviewer.

Today, most candidates prepare by solving problems on platforms like LeetCode or HackerRank, watching solution videos, or practicing occasionally with friends through mock interviews. While these approaches help build algorithmic knowledge, they provide little opportunity to practice the interactive aspects of a real interview, such as verbalizing reasoning, receiving incremental feedback, handling interviewer prompts, or adapting to changing requirements. As a result, many candidates enter interviews technically prepared but lacking confidence and experience in the collaborative problem-solving process that interviewers actually evaluate.

```mermaid
flowchart TD
    A[Decide to prepare for technical interviews]
    B[Find DSA problems<br/>LeetCode, HackerRank, etc.]
    C[Solve problems independently<br/>in an IDE]
    D[Review editorials,<br/>discussion forums,<br/>or YouTube videos]
    E[Practice explaining solution<br/>alone or skip entirely]
    F[Occasionally schedule<br/>a mock interview<br/>with a friend or interviewer]
    G[Attend a real<br/>technical interview]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G

    P1{{Finding relevant<br/>questions is time-consuming}}
    P2{{Limited feedback<br/>on reasoning}}
    P3{{Static solutions don't adapt<br/>to the learner}}
    P4{{Communication skills<br/>rarely practiced}}
    P5{{Scheduling mock interviews<br/>is difficult}}

    B -.-> P1
    C -.-> P2
    D -.-> P3
    E -.-> P4
    F -.-> P5

    classDef pain fill:#ffe5e5,stroke:#d9534f,color:#a94442;
    class P1,P2,P3,P4,P5 pain;
```

### Midterm vertical slice

The full vision above (multi-problem bank, long-term candidate memory across sessions, etc.) is
the target state, not the midterm deliverable. Per instructor feedback, the midterm scopes down to
a single vertical slice through the product:

- **One problem**: Two Sum problem only — no problem bank or selection of problems flow.
- **One language**: Python only — no multi-language execution/support.
- **Chat + simple editor**: a basic code editor pane alongside the chat interface — no advanced
  IDE features (multi-file, linting, etc.).
- **Session memory**: state persists for the duration of a single interview session (see the core
  state model below) — no long-term memory across sessions or candidates yet.
- **Explicitly out of scope for the midterm**: multi-problem bank, long-term/cross-session memory.

Everything below (Tasks 2-7) should be read against this narrowed scope unless otherwise noted.

Scenario input-output pairs to evaluate the application (anchored on the Two Sum problem):

| #   | Input (candidate action / event)                                                        | Expected coach behavior                                                                                                 |
| --- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| 1   | Candidate's first message pastes the complete optimal Two Sum solution (hash map, O(n)) | Coach withholds confirmation of correctness; asks candidate to explain their reasoning and complexity before validating |
| 2   | Candidate message: "just give me the answer"                                            | Coach declines, redirects with a guiding question (e.g. "What have you tried so far?")                                  |
| 3   | Candidate message: "I'll use a hash map to store seen values"                           | Coach asks for expected time/space complexity before letting them start implementing                                    |
| 4   | Candidate proposes a working brute-force nested-loop approach (O(n²))                   | Coach confirms it's valid, then asks if they can do better, rather than revealing the hash map approach                 |
| 5   | Candidate goes idle 45s immediately after a failed code run                             | Coach gives a level-1 hint — a nudge toward checking the failing case, not the fix itself                               |
| 6   | Candidate goes idle 30s with no failed run yet                                          | Coach asks an open-ended nudge ("What are you thinking so far?") rather than issuing a hint                             |
| 7   | Candidate explicitly requests a hint twice in a row                                     | Second hint is strictly more specific than the first (e.g. names the data structure), never the full solution           |
| 8   | Candidate's code run fails three times in a row                                         | Coach shifts from approach-level hints to a targeted debugging question (e.g. "what input might break this?")           |
| 9   | Candidate asks "can the array have duplicate values?" before proposing an approach      | Coach answers directly and encourages further clarification if needed                                                   |
| 10  | Candidate's code passes all tests                                                       | Coach doesn't end the interview immediately; asks a follow-up (edge cases, alternative approach) first                  |
| 11  | Interview session ends                                                                  | Feedback report cites specific milestones and evidence from the session, not generic praise                             |

## Task 2: Propose a Solution

swell is an AI-powered software engineering coach that simulates realistic technical interviews to help engineers master data structures and algorithms through pair programming.

### Infrastructure Diagram

![swell-arch-diagram](./media/swell-arch.svg)

Examples of events emitted:

- `CANDIDATE_MESSAGE` (a message submitted by the candidate to the AI Interview Chat panel)

  ```json
  {
    "type": "CANDIDATE_MESSAGE",
    "payload": {
      "text": "I think I can use a hash map to store previously seen values."
    }
  }
  ```

- `CODE_SNAPSHOT` (a snapshot of the code from the Code Editor)

  ```json
  {
    "type": "CODE_SNAPSHOT",
    "payload": {
      "language": "python",
      "code": "def two_sum(nums, target):\n    seen = {}",
      "change_summary": {
        "lines_added": 2,
        "lines_removed": 0
      }
    }
  }
  ```

- `CANDIDATE_IDLE` (the candidate has been idle for `N` time)
  ```json
  {
    "type": "CANDIDATE_IDLE",
    "payload": {
      "duration_seconds": 30,
      "last_activity_type": "CODE_SNAPSHOT"
    }
  }
  ```

### Agent Workflow Diagram

```mermaid
flowchart TD

    Start([Start Interview])

    Load[Load problem and session memory]

    Display[Display problem and editor]

    Event[Receive candidate event]

    Context[Build interview context]

    NeedRAG{Need additional knowledge?}

    Retrieve[RAG retrieves rubric, hints and edge cases]

    Decide[LLM evaluates interview state]

    Action{Next action?}

    Ask[Ask follow-up question]

    Hint[Provide progressive hint]

    RunCode[Execute code]

    Wait[Wait for candidate]

    Update[Update memory and milestones]

    Finish{Interview finished?}

    Feedback[Generate feedback]

    Save[Save long-term memory]

    End([Return report])

    Start --> Load
    Load --> Display
    Display --> Event
    Event --> Context

    Context --> NeedRAG

    NeedRAG -- Yes --> Retrieve
    NeedRAG -- No --> Decide

    Retrieve --> Decide

    Decide --> Action

    Action -->|Question| Ask
    Action -->|Hint| Hint
    Action -->|Run code| RunCode
    Action -->|Nothing| Wait

    Ask --> Update
    Hint --> Update
    RunCode --> Update
    Wait --> Event

    Update --> Finish

    Finish -- No --> Event
    Finish -- Yes --> Feedback

    Feedback --> Save
    Save --> End
```

#### Core state model

The core state model of each interview session would look something like:

```json
{
  "session_id": "session-123",
  "problem_id": "two-sum",
  "status": "IN_PROGRESS",
  "current_phase": "APPROACH_DISCUSSION",
  "candidate_status": "PROGRESSING",
  "completed_milestones": ["UNDERSTANDS_PROBLEM"],
  "milestones": {
    "UNDERSTANDS_PROBLEM": {
      "status": "COMPLETED",
      "confidence": 0.94,
      "evidence_event_ids": ["evt-10"]
    },
    "CLARIFIES_CONSTRAINTS": {
      "status": "PARTIAL",
      "confidence": 0.61,
      "evidence_event_ids": ["evt-12"]
    },
    "PROPOSES_APPROACH": {
      "status": "IN_PROGRESS",
      "confidence": 0.52,
      "evidence_event_ids": ["evt-15"]
    }
  },
  "hint_level": 0,
  "failed_run_count": 0,
  "last_activity_at": "2026-07-10T14:10:00Z",
  "latest_code_snapshot_id": "snapshot-24",
  "pending_action": null
}
```

#### Event processing flow

When an event arrives:

```
Candidate event
    ↓
Normalize event
    ↓
Apply deterministic rules
    ↓
Ask LLM to interpret ambiguous evidence
    ↓
Update milestones and phase
    ↓
Choose next interviewer action
    ↓
Persist state
```

For example:

```json
{
  "type": "CANDIDATE_MESSAGE",
  "payload": {
    "text": "I'll store each number and its index in a hash map."
  }
}
```

The LLM evaluator might return structured output:

```json
{
  "observations": [
    {
      "milestone_id": "PROPOSES_HASH_MAP",
      "status": "COMPLETED",
      "confidence": 0.96,
      "evidence": "Candidate explicitly proposed storing values and indices in a hash map."
    }
  ],
  "candidate_status": "PROGRESSING",
  "recommended_action": "ASK_COMPLEXITY_QUESTION"
}
```

The engine validates that output, updates state, and then asks the interviewer model to generate the actual wording:

> “Good. What time and space complexity would that approach have?”

### Deterministic Rules

Some things should not require an LLM.

Examples:

```python
if event.type == "CODE_RUN_COMPLETED" and event.payload["all_tests_passed"]:
    mark_milestone("IMPLEMENTS_CORRECT_SOLUTION", completed=True)

if event.type == "HINT_REQUESTED":
    state.hint_level += 1

if event.type == "CANDIDATE_IDLE":
    if event.payload["duration_seconds"] >= 30:
        state.candidate_status = "POSSIBLY_STUCK"

if state.failed_run_count >= 3:
    state.candidate_status = "DEBUGGING_DIFFICULTY"
```
