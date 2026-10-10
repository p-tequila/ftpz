"""Run the final linear and logistic FHE demo into one directory."""

import argparse
import contextlib
import io
from pathlib import Path
import sys

from .data import prepare


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=positive, default=15, help="matched logistic SGD updates")
    parser.add_argument("--seed", type=int, default=42, help="data/batch seed; never a key seed")
    parser.add_argument("--bits", type=int, choices=range(2, 17), default=8, help="inference precision")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/final"))
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("Output directory exists. Choose a new --output-dir to preserve its keys and report.")
    console = sys.stdout
    logs = io.StringIO()
    try:
        with contextlib.redirect_stdout(logs), contextlib.redirect_stderr(logs):
            from .experiments import run
            from .report import write_report
            result = run(prepare(args.seed), args.steps, args.bits, args.seed,
                         lambda message: print(message, file=console, flush=True),
                         args.output_dir / "models")
            result["library_log"] = logs.getvalue()
            write_report(args.output_dir / "report.html", result)
    except Exception as error:
        print(f"Run failed: {error}\n{logs.getvalue()[-2000:]}", file=sys.stderr)
        raise SystemExit(1) from error
    print(f"Done → {(args.output_dir / 'report.html').resolve()}")


if __name__ == "__main__":
    main()
