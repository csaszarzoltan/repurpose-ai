"""Example: P1.2 — Validation Gap Analyzer.

Demonstrates ValidationAnalyzer: readability, diff, tone, faithfulness, LLM judge.
"""

import asyncio

from app.models.analytics import ValidationReport
from app.services.analytics.validation_analyzer import ValidationAnalyzer


async def main() -> None:
    analyzer = ValidationAnalyzer(llm_router=None)

    # ── Readability scores ──
    readability = analyzer.compute_readability_scores(
        "The quick brown fox jumps over the lazy dog. "
        "This sentence contains exactly ten words. "
        "Readability metrics are quite useful."
    )
    print(f"Readability: FK={readability['flesch_kincaid']:.1f}, "
          f"DC={readability['dale_chall']:.1f}, "
          f"ARI={readability['ari']:.1f}")

    # Empty text
    empty_read = analyzer.compute_readability_scores("")
    print(f"Empty readability: {empty_read}")

    # ── Diff blocks ──
    draft = "Hello world version A\nThis is the second line."
    published = "Hello world version B\nThis line was changed."
    blocks = analyzer.compute_diff_blocks(draft, published)
    for b in blocks:
        print(f"Diff: {b['type']} -> {repr(b.get('content', ''))[:40]}")

    # Identical content
    same = analyzer.compute_diff_blocks("Hello", "Hello")
    print(f"Identical diff blocks: {same}")

    # ── Tone consistency ──
    tone = await analyzer.compute_tone_consistency(
        draft=draft,
        published=published,
        brand_voice_exemplar="professional",
    )
    print(f"Tone similarity: {tone['similarity']}")

    # ── Faithfulness ──
    faithful = await analyzer.compute_faithfulness(
        draft="AI is transforming diagnostics and healthcare.",
        source_material="AI is transforming diagnostics with machine learning.",
    )
    print(f"Faithfulness: {faithful['faithfulness']:.2f}")

    # ── LLM judge ──
    judge = await analyzer.compute_llm_judge(
        draft="A well-written article about AI.",
        published="A published version of the same article.",
    )
    print(f"LLM Judge: coherence={judge['coherence']}, "
          f"persuasiveness={judge['persuasiveness']}, "
          f"clarity={judge['clarity']}")

    # ── Full validation pipeline ──
    report = await analyzer.validate(
        draft="Draft content for validation.",
        published="Published content that was actually posted.",
        source_material="Original source material.",
        run_llm_judge=True,
    )
    print(f"Full validation: quality_delta={report['quality_delta']}, "
          f"readability_keys={list(report['readability'].keys())}")

    # ── ValidationReport model ──
    model_report = ValidationReport(
        quality_delta=0.15,
        readability={"flesch_kincaid": 12.5, "dale_chall": 8.0, "ari": 14.0},
        tone_consistency={"similarity": 0.85},
        faithfulness={"faithfulness": 0.72},
        llm_judge={"coherence": 0.85},
        diff_blocks=[{"type": "replace", "content": "new text", "original": "old text"}],
    )
    print(f"Model: delta={model_report.quality_delta}, "
          f"tone={model_report.tone_consistency['similarity']}")


if __name__ == "__main__":
    asyncio.run(main())
