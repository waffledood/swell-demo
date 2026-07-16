"""RAGAS retrieval-quality harness for swell_agent.retriever (Task 5, deliverable 2).

Evaluates retrieve_context_documents (the function backing the
retrieve_problem_context tool) against evals/retrieval_dataset.yaml using:

  - a cheap deterministic top-1 doc_type check (independent of RAGAS/any LLM)
  - RAGAS Faithfulness, LLMContextPrecisionWithReference, LLMContextRecall,
    computed by having a synthesis LLM answer each query using ONLY the
    retrieved chunks, then scoring that answer + those chunks against a
    hand-written reference answer grounded in the knowledge-base YAML.

Run with: uv run python evals/run_ragas_eval.py
"""

from __future__ import annotations

import json
from pathlib import Path

import _ragas_compat  # noqa: F401 - side-effecting import, must run before `ragas`
import yaml
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, LLMContextPrecisionWithReference, LLMContextRecall

load_dotenv()

from swell_agent.retriever import retrieve_context_documents  # noqa: E402

DATASET_PATH = Path(__file__).parent / "retrieval_dataset.yaml"
RESULTS_DIR = Path(__file__).parent / "results"

SYNTHESIS_PROMPT = """Answer the question using ONLY the context below - do not use \
any outside knowledge. If the context does not contain the answer, say so explicitly.

Question: {query}

Context:
{context}

Answer:"""


def load_dataset() -> list[dict]:
    with DATASET_PATH.open() as f:
        return yaml.safe_load(f)


def main() -> None:
    entries = load_dataset()
    synthesis_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    judge_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini", temperature=0))

    samples = []
    deterministic_rows = []

    for entry in entries:
        docs = retrieve_context_documents(
            entry["query"], doc_type=entry.get("doc_type"), k=4
        )
        contexts = [d.page_content for d in docs]
        retrieved_doc_types = [d.metadata.get("doc_type") for d in docs]
        top1_doc_type = retrieved_doc_types[0] if docs else None
        expected_doc_type = entry.get("expected_doc_type")
        top1_match = expected_doc_type is None or top1_doc_type == expected_doc_type

        context_block = "\n\n---\n\n".join(contexts) if contexts else "(no context retrieved)"
        response = synthesis_llm.invoke(
            SYNTHESIS_PROMPT.format(query=entry["query"], context=context_block)
        ).content

        deterministic_rows.append(
            {
                "id": entry["id"],
                "query": entry["query"],
                "expected_doc_type": expected_doc_type,
                "top1_doc_type": top1_doc_type,
                "retrieved_doc_types": retrieved_doc_types,
                "top1_match": top1_match,
            }
        )

        samples.append(
            SingleTurnSample(
                user_input=entry["query"],
                retrieved_contexts=contexts,
                response=response,
                reference=entry["reference"],
            )
        )

    print("=== Deterministic top-1 doc_type check ===\n")
    n_match = sum(row["top1_match"] for row in deterministic_rows)
    for row in deterministic_rows:
        status = "OK" if row["top1_match"] else "MISS"
        print(
            f"[{status}] {row['id']}: expected={row['expected_doc_type']!r} "
            f"top1={row['top1_doc_type']!r} all={row['retrieved_doc_types']}"
        )
    print(f"\n{n_match}/{len(deterministic_rows)} queries returned the expected doc_type as top-1 result.\n")

    print("=== RAGAS metrics (faithfulness, context precision, context recall) ===\n")
    ragas_dataset = EvaluationDataset(samples=samples)
    result = evaluate(
        ragas_dataset,
        metrics=[Faithfulness(), LLMContextPrecisionWithReference(), LLMContextRecall()],
        llm=judge_llm,
        show_progress=True,
    )

    df = result.to_pandas()
    print(df.to_string())

    means = df.select_dtypes("number").mean(numeric_only=True)
    print("\n=== Mean scores ===")
    print(means.to_string())

    RESULTS_DIR.mkdir(exist_ok=True)
    df.to_json(RESULTS_DIR / "ragas_results.json", orient="records", indent=2)
    with (RESULTS_DIR / "ragas_deterministic.json").open("w") as f:
        json.dump(deterministic_rows, f, indent=2)
    with (RESULTS_DIR / "ragas_summary.json").open("w") as f:
        json.dump(
            {
                "top1_doc_type_match": f"{n_match}/{len(deterministic_rows)}",
                "mean_scores": means.to_dict(),
            },
            f,
            indent=2,
        )
    print(f"\nWrote results to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
