import subprocess
import sys
from pathlib import Path


def run_step(step_name, script_path):
    # Run one pipeline step and stop if it fails
    print(f"\n{'=' * 80}")
    print(f"RUNNING: {step_name}")
    print(f"{'=' * 80}")

    result = subprocess.run([sys.executable, script_path], check=False)

    if result.returncode != 0:
        print(f"\n[FAILED] {step_name}")
        sys.exit(result.returncode)

    print(f"\n[OK] {step_name} completed successfully.")


def main():
    project_root = Path(__file__).resolve().parent

    steps = [
        ("Generate messy raw data", project_root / "src" / "generate_data.py"),
        ("Audit raw data", project_root / "src" / "audit_raw_data.py"),
        ("Transform clean and mart layers", project_root / "src" / "transform_data.py"),
        ("Validate clean and mart layers", project_root / "src" / "validate_data.py"),
        ("Build DuckDB star schema", project_root / "src" / "build_duckdb.py"),
    ]

    for step_name, script_path in steps:
        run_step(step_name, str(script_path))

    print(f"\n{'=' * 80}")
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()