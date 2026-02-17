"""Batch processor for multiple topics."""
import argparse
import sys
from pathlib import Path
from typing import List

from src.models import PipelineResult, PipelineStatus
from src.pipeline import run_pipeline


def log(msg: str) -> None:
    print(f"[batch] {msg}")


def run_batch(
    topics: List[str],
    no_upload: bool = False,
    runway_model: str = "gen4_turbo",
) -> List[PipelineResult]:
    """Process multiple topics sequentially."""
    results: List[PipelineResult] = []

    for i, topic in enumerate(topics):
        topic = topic.strip()
        if not topic:
            continue
        log(f"Processing {i + 1}/{len(topics)}: {topic}")
        result = run_pipeline(topic, no_upload=no_upload, runway_model=runway_model)
        results.append(result)

        status = "OK" if result.status == PipelineStatus.COMPLETE else "FAILED"
        log(f"  → {status}")

    # Summary
    succeeded = sum(1 for r in results if r.status == PipelineStatus.COMPLETE)
    failed = sum(1 for r in results if r.status == PipelineStatus.FAILED)
    log(f"Done. {succeeded} succeeded, {failed} failed out of {len(results)}.")

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Faceless Shorts V2 Batch: process multiple topics"
    )
    parser.add_argument("topics", nargs="*", help="Topics (or use --file)")
    parser.add_argument("--file", type=Path,
                        help="Text file with one topic per line")
    parser.add_argument("--no-upload", action="store_true",
                        help="Build videos only; skip YouTube upload")
    parser.add_argument("--runway-model", default="gen4_turbo",
                        choices=["gen4_turbo", "gen4.5"],
                        help="Runway ML model (default: gen4_turbo)")
    args = parser.parse_args()

    topics: List[str] = list(args.topics) if args.topics else []

    if args.file:
        if not args.file.exists():
            log(f"File not found: {args.file}")
            return 1
        topics.extend(
            line.strip()
            for line in args.file.read_text().splitlines()
            if line.strip()
        )

    if not topics:
        log("No topics provided. Pass topics as args or use --file.")
        return 1

    results = run_batch(topics, no_upload=args.no_upload, runway_model=args.runway_model)

    failed = sum(1 for r in results if r.status == PipelineStatus.FAILED)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
