from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

SERVICES = {
    "ingestion-gateway": Path("services/ingestion-gateway/app/main.py"),
    "connector-service": Path("services/connector-service/app/main.py"),
    "query-api": Path("services/query-api/app/main.py"),
    "consent-identity-service": Path("services/consent-identity-service/app/main.py"),
    "governance-agent": Path("services/governance-agent/app/main.py"),
    "ehr-integration": Path("services/ehr-integration/app/main.py"),
    "ops-console": Path("services/ops-console/app/main.py"),
}


def main() -> None:
    root = Path(".").resolve()
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "packages" / "openpulse_core"))
    sys.path.insert(0, str(root / "packages" / "openpulse_data"))

    output_dir = Path("generated/openapi")
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, file_path in SERVICES.items():
        context = runpy.run_path(str(file_path))
        app = context["app"]
        spec = app.openapi()
        output_path = output_dir / f"{name}.openapi.json"
        output_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
