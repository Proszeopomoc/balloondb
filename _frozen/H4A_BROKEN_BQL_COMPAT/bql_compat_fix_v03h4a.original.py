
import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(r"C:\BalloonOperator")
EVID = ROOT / "06_EVIDENCE" / "BALLOONDB_V03H4A_BQL_COMPAT_RELEASE_FIX"

PATCH_TARGETS = [
    "balloondb_core/bql_error_contract.py",
    "balloondb_core/selftest/run_selftest_v03g1.py",
    "balloondb_core/selftest/run_selftest_v03g2.py",
]

TEST_SCRIPTS = [
    ("V03G1", "09_SCRIPTS/RUN_BQL_SELFTEST_V03G1.ps1"),
    ("V03G2", "09_SCRIPTS/RUN_BQL_SELFTEST_V03G2.ps1"),
    ("V03G3", "09_SCRIPTS/RUN_BQL_SELFTEST_V03G3.ps1"),
    ("V03G4", "09_SCRIPTS/RUN_BQL_SELFTEST_V03G4.ps1"),
    ("V03G7", "09_SCRIPTS/RUN_BQL_REGRESSION_V03G7.ps1"),
    ("V03H4", "09_SCRIPTS/RUN_BALLOONDB_CORE_REGRESSION_GATE_V03H4.ps1"),
]

HELPER = r