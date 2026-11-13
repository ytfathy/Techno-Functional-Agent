"""Read-only smoke test against the active profile.  Usage:  .venv\\Scripts\\python scripts\\smoke_test.py [test|dev|prod]"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if len(sys.argv) > 1:
    os.environ["ORACLE_PROFILE"] = sys.argv[1]

from oracle_fusion_mcp.smoke import smoke_test  # noqa: E402

report = smoke_test()
print(json.dumps(report["env"], indent=2))
print(f"\nPassed {report['passed']}\n")
for row in report["checks"]:
    line = f"{row['area']:<26} {row['result']}"
    if row.get("needs"):
        line += f"\n{'':<26} -> needs: {row['needs']}"
    print(line)
