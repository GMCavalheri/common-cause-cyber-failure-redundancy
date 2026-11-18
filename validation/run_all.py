"""Rerun every validation script, in phase order, and report the time each took.

    uv run python validation/run_all.py

Every result is exact or computed from a seeded generator, and rounding-level errors are
reported as bounds, so a rerun reproduces the tables in ``validation/results/`` byte for byte;
CI checks that with ``git diff``. Figures go to ``docs/figures/`` (their pixels can differ
slightly between platforms' font setups, so CI does not compare them).
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = [
    ("independence.py", "Phase 1: independence baseline"),
    ("physical_ccf.py", "Phase 2: physical common-cause failure"),
    ("cyber_ccf.py", "Phase 3: cyber common-cause failure"),
    ("reduction_checks.py", "Derivation: numerical checks of the propositions"),
    ("diversity.py", "Phase 4: architecture diversity trade-off"),
    ("case_study.py", "Phase 5: case study"),
    ("time_dependent.py", "Extra: availability with repair and Monte Carlo checks"),
    ("posture.py", "Extra: NIST SP 800-82r3 posture rubric"),
]


def main() -> int:
    for name, title in SCRIPTS:
        print(f"== {title}", flush=True)
        t0 = time.perf_counter()
        done = subprocess.run([sys.executable, str(HERE / name)], cwd=HERE.parent)
        if done.returncode:
            print(f"   {name} failed (exit {done.returncode})", flush=True)
            return done.returncode
        print(f"   done in {time.perf_counter() - t0:.1f} s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
