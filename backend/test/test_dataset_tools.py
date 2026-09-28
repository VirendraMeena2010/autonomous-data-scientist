from __future__ import annotations

from pathlib import Path

from app.tools.dataset_tools import (
    assess_quality,
    execute_analysis_plan,
    profile_dataset,
)


def test_profile_dataset_csv(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

    result = profile_dataset(path)

    assert result["row_count"] == 2
    assert result["column_count"] == 2
    assert result["columns"][0]["name"] == "a"
    assert result["numeric_summary"]["a"]["mean"] == 2.0


def test_quality_and_plan(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    path.write_text("a,b\n1,2\n1,2\n", encoding="utf-8")

    quality = assess_quality(path)

    assert quality["duplicate_rows"] == 1
    assert 0 <= quality["quality_score"] <= 100

    results = execute_analysis_plan(
        path,
        {
            "objective": "check duplicates",
            "steps": [
                {
                    "name": "summary",
                    "tool": "summary",
                    "parameters": {},
                },
                {
                    "name": "missingness",
                    "tool": "missingness",
                    "parameters": {},
                },
            ],
            "required_columns": [],
            "caveats": [],
        },
    )

    assert len(results) == 2
    assert results[0]["tool"] == "summary"
    assert results[1]["tool"] == "missingness"
