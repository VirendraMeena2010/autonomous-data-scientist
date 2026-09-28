from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.graph.schemas import AnalysisPlan


class DatasetToolError(RuntimeError):
    pass


# ============================================================
# Dataset loading
# ============================================================

def load_dataset(path: Path) -> pd.DataFrame:
    """
    Load a supported dataset into a pandas DataFrame.

    Supported:
    - CSV
    - Parquet
    - JSONL
    - JSON
    """
    path = Path(path)

    if not path.exists():
        raise DatasetToolError(
            f"dataset_file_not_found:{path}"
        )

    if not path.is_file():
        raise DatasetToolError(
            f"dataset_path_is_not_file:{path}"
        )

    suffix = path.suffix.lower()

    try:
        if suffix == ".csv":
            return pd.read_csv(path)

        if suffix == ".parquet":
            return pd.read_parquet(path)

        if suffix == ".jsonl":
            return pd.read_json(path, lines=True)

        if suffix == ".json":
            return pd.read_json(path)

    except Exception as exc:
        raise DatasetToolError(
            f"dataset_read_failed:{path.name}"
        ) from exc

    raise DatasetToolError(
        f"unsupported_dataset_format:{suffix}"
    )


# Backwards-compatible alias.
# Existing code using load_frame() will continue to work.
def load_frame(path: Path) -> pd.DataFrame:
    return load_dataset(path)


# ============================================================
# Profiling
# ============================================================

def profile_dataset(path: Path) -> dict[str, Any]:
    try:
        frame = load_dataset(path)
    except DatasetToolError:
        raise
    except Exception as exc:
        raise DatasetToolError("unable_to_load_dataset") from exc

    columns: list[dict[str, Any]] = []

    for column in frame.columns:
        series = frame[column]

        columns.append(
            {
                "name": str(column),
                "dtype": str(series.dtype),
                "missing_count": int(series.isna().sum()),
                "missing_rate": float(series.isna().mean()),
                "unique_count": int(series.nunique(dropna=True)),
                "numeric": bool(
                    pd.api.types.is_numeric_dtype(series)
                ),
                "datetime": bool(
                    pd.api.types.is_datetime64_any_dtype(series)
                ),
                "sample_values": _clean_value(
                    series.dropna().head(5).tolist()
                ),
            }
        )

    numeric_summary: dict[str, Any] = {}

    numeric_columns = frame.select_dtypes(
        include=[np.number]
    ).columns

    for column in numeric_columns:
        series = frame[column]

        numeric_summary[str(column)] = {
            "count": int(series.count()),
            "mean": _safe_float(series.mean()),
            "std": _safe_float(series.std()),
            "min": _clean_value(series.min()),
            "median": _clean_value(series.median()),
            "max": _clean_value(series.max()),
        }

    return _jsonable(
        {
            "row_count": int(len(frame)),
            "column_count": int(len(frame.columns)),
            "memory_bytes": int(
                frame.memory_usage(deep=True).sum()
            ),
            "columns": columns,
            "numeric_summary": numeric_summary,
            "sample_rows": frame.head(5).to_dict(
                orient="records"
            ),
        }
    )


# ============================================================
# Quality assessment
# ============================================================

def assess_quality(path: Path) -> dict[str, Any]:
    try:
        frame = load_dataset(path)
    except DatasetToolError:
        raise
    except Exception as exc:
        raise DatasetToolError("unable_to_load_dataset") from exc

    total_cells = int(frame.shape[0] * frame.shape[1]) or 1

    missing_cells = int(
        frame.isna().sum().sum()
    )

    duplicate_rows = int(
        frame.duplicated().sum()
    )

    missing_rate = missing_cells / total_cells

    duplicate_rate = (
        duplicate_rows / max(len(frame), 1)
    )

    constant_columns: list[str] = []
    high_cardinality_columns: list[str] = []

    for column in frame.columns:
        series = frame[column]
        non_null = series.dropna()

        if (
            len(non_null) > 0
            and non_null.nunique() == 1
        ):
            constant_columns.append(str(column))

        if (
            non_null.nunique()
            > max(100, int(len(non_null) * 0.8))
        ):
            high_cardinality_columns.append(
                str(column)
            )

    # --------------------------------------------------------
    # Outliers
    # --------------------------------------------------------

    outlier_summary: dict[str, Any] = {}

    numeric_columns = frame.select_dtypes(
        include=[np.number]
    ).columns

    for column in numeric_columns:
        series = frame[column].dropna()

        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            outlier_summary[str(column)] = {
                "outlier_count": 0,
                "outlier_rate": 0.0,
            }
            continue

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outlier_count = int(
            (
                (series < lower)
                | (series > upper)
            ).sum()
        )

        outlier_summary[str(column)] = {
            "outlier_count": outlier_count,
            "outlier_rate": float(
                outlier_count / len(series)
            ),
        }

    mean_outlier_rate = (
        float(
            np.mean(
                [
                    item["outlier_rate"]
                    for item in outlier_summary.values()
                ]
            )
        )
        if outlier_summary
        else 0.0
    )

    # --------------------------------------------------------
    # Quality score
    # --------------------------------------------------------

    score = 100.0

    score -= min(
        40.0,
        missing_rate * 100 * 2,
    )

    score -= min(
        30.0,
        duplicate_rate * 100 * 3,
    )

    score -= min(
        10.0,
        len(constant_columns)
        / max(len(frame.columns), 1)
        * 10,
    )

    score -= min(
        20.0,
        mean_outlier_rate * 100,
    )

    return _jsonable(
        {
            "quality_score": max(
                0.0,
                min(100.0, score),
            ),
            "missing_cells": missing_cells,
            "missing_rate": float(missing_rate),
            "duplicate_rows": duplicate_rows,
            "duplicate_rate": float(duplicate_rate),
            "constant_columns": constant_columns,
            "high_cardinality_columns": high_cardinality_columns,
            "numeric_outliers": outlier_summary,
        }
    )


# ============================================================
# Execute analysis plan
# ============================================================

def execute_analysis_plan(
    path: Path,
    plan_dict: dict[str, Any],
) -> list[dict[str, Any]]:
    try:
        plan = AnalysisPlan.model_validate(plan_dict)
    except Exception as exc:
        raise DatasetToolError(
            "invalid_analysis_plan"
        ) from exc

    try:
        frame = load_dataset(path)
    except DatasetToolError:
        raise
    except Exception as exc:
        raise DatasetToolError(
            "unable_to_load_dataset"
        ) from exc

    results: list[dict[str, Any]] = []

    for step in plan.steps:
        try:
            result = _run_step(
                frame,
                step.tool,
                step.parameters,
            )

            results.append(
                {
                    "step": step.name,
                    "tool": step.tool,
                    "parameters": _jsonable(
                        step.parameters
                    ),
                    "result": _jsonable(result),
                }
            )

        except Exception as exc:
            results.append(
                {
                    "step": step.name,
                    "tool": step.tool,
                    "parameters": _jsonable(
                        step.parameters
                    ),
                    "error": str(exc),
                }
            )

    return _jsonable(results)


# ============================================================
# Analysis tools
# ============================================================

def _run_step(
    frame: pd.DataFrame,
    tool: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    if tool == "summary":
        return {
            "shape": list(frame.shape),
            "dtypes": {
                str(column): str(dtype)
                for column, dtype
                in frame.dtypes.items()
            },
            "describe": _clean_value(
                frame.describe(
                    include="all"
                ).to_dict(
                    orient="index"
                )
            ),
        }

    # --------------------------------------------------------
    # Missingness
    # --------------------------------------------------------

    if tool == "missingness":
        column = _optional_column(
            parameters,
            frame,
        )

        if column:
            series = frame[column]

            return {
                column: {
                    "missing_count": int(
                        series.isna().sum()
                    ),
                    "missing_rate": float(
                        series.isna().mean()
                    ),
                }
            }

        missing = (
            frame.isna()
            .sum()
            .sort_values(
                ascending=False
            )
        )

        return {
            str(column): {
                "missing_count": int(count),
                "missing_rate": float(
                    count / max(len(frame), 1)
                ),
            }
            for column, count in missing.items()
        }

    # --------------------------------------------------------
    # Distribution
    # --------------------------------------------------------

    if tool == "distribution":
        column = _required_column(
            parameters,
            frame,
            "column",
        )

        series = frame[column].dropna()

        if pd.api.types.is_numeric_dtype(series):
            return {
                "column": column,
                "count": int(series.count()),
                "mean": _safe_float(series.mean()),
                "median": _clean_value(
                    series.median()
                ),
                "std": _safe_float(series.std()),
                "min": _clean_value(series.min()),
                "max": _clean_value(series.max()),
                "quantiles": {
                    str(q): _clean_value(
                        series.quantile(q)
                    )
                    for q in [
                        0.25,
                        0.5,
                        0.75,
                    ]
                },
            }

        counts = (
            series
            .value_counts()
            .head(20)
        )

        return {
            "column": column,
            "top_values": [
                {
                    "value": _clean_value(value),
                    "count": int(count),
                }
                for value, count in counts.items()
            ],
        }

    # --------------------------------------------------------
    # Correlation
    # --------------------------------------------------------

    if tool == "correlation":
        numeric = frame.select_dtypes(
            include=[np.number]
        )

        requested = parameters.get("columns")

        if (
            isinstance(requested, list)
            and requested
        ):
            valid = [
                str(column)
                for column in requested
                if str(column)
                in numeric.columns
            ]

            if valid:
                numeric = numeric[valid]

        if numeric.shape[1] < 2:
            return {
                "warning": "not_enough_numeric_columns"
            }

        corr = numeric.corr(
            numeric_only=True
        )

        pairs: list[dict[str, Any]] = []

        for i in range(len(corr.columns)):
            for j in range(
                i + 1,
                len(corr.columns),
            ):
                left = corr.columns[i]
                right = corr.columns[j]

                value = corr.iloc[i, j]

                if pd.isna(value):
                    continue

                pairs.append(
                    {
                        "column_a": str(left),
                        "column_b": str(right),
                        "correlation": float(value),
                    }
                )

        pairs.sort(
            key=lambda item: abs(
                item["correlation"]
            ),
            reverse=True,
        )

        return {
            "matrix": _clean_value(
                corr.to_dict(
                    orient="index"
                )
            ),
            "top_pairs": pairs[:20],
        }

    # --------------------------------------------------------
    # Group summary
    # --------------------------------------------------------

    if tool == "group_summary":
        group_column = _required_column(
            parameters,
            frame,
            "group_column",
        )

        value_column = _required_column(
            parameters,
            frame,
            "value_column",
        )

        agg = str(
            parameters.get(
                "agg",
                "mean",
            )
        )

        allowed_aggs = {
            "mean",
            "sum",
            "min",
            "max",
            "count",
            "median",
        }

        if agg not in allowed_aggs:
            raise DatasetToolError(
                "unsupported_aggregation"
            )

        grouped = frame.groupby(
            group_column,
            dropna=False,
        )[value_column]

        if agg == "count":
            result = grouped.count()
        elif agg == "median":
            result = grouped.median()
        else:
            result = getattr(
                grouped,
                agg,
            )()

        rows = []

        for index, value in result.sort_values(
            ascending=False
        ).items():
            rows.append(
                {
                    "group": _clean_value(index),
                    "value": _clean_value(value),
                }
            )

        return {
            "group_column": group_column,
            "value_column": value_column,
            "agg": agg,
            "rows": rows,
        }

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    if tool == "trend":
        date_column = _required_column(
            parameters,
            frame,
            "date_column",
        )

        value_column = _required_column(
            parameters,
            frame,
            "value_column",
        )

        dates = pd.to_datetime(
            frame[date_column],
            errors="coerce",
        )

        values = pd.to_numeric(
            frame[value_column],
            errors="coerce",
        )

        temp = pd.DataFrame(
            {
                "date": dates,
                "value": values,
            }
        ).dropna()

        if temp.empty:
            return {
                "warning": "no_valid_trend_data"
            }

        temp = temp.sort_values("date")

        first = float(
            temp["value"].iloc[0]
        )

        last = float(
            temp["value"].iloc[-1]
        )

        percent_change = (
            ((last - first) / abs(first)) * 100
            if first
            else None
        )

        return {
            "date_column": date_column,
            "value_column": value_column,
            "start_date": _clean_value(
                temp["date"].iloc[0]
            ),
            "end_date": _clean_value(
                temp["date"].iloc[-1]
            ),
            "first_value": first,
            "last_value": last,
            "absolute_change": last - first,
            "percent_change": percent_change,
            "min_value": float(
                temp["value"].min()
            ),
            "max_value": float(
                temp["value"].max()
            ),
        }

    raise DatasetToolError(
        f"unsupported_tool:{tool}"
    )


# ============================================================
# Column helpers
# ============================================================

def _required_column(
    parameters: dict[str, Any],
    frame: pd.DataFrame,
    key: str,
) -> str:
    column = parameters.get(key)

    if (
        not isinstance(column, str)
        or column not in frame.columns
    ):
        raise DatasetToolError(
            f"invalid_column:{column}"
        )

    return column


def _optional_column(
    parameters: dict[str, Any],
    frame: pd.DataFrame,
) -> str | None:
    column = parameters.get("column")

    if column is None:
        return None

    if (
        not isinstance(column, str)
        or column not in frame.columns
    ):
        raise DatasetToolError(
            f"invalid_column:{column}"
        )

    return column


# ============================================================
# Serialization helpers
# ============================================================

def _safe_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    try:
        if np.isinf(value):
            return None
    except TypeError:
        return None

    return float(value)


def _jsonable(value: Any) -> Any:
    return json.loads(
        json.dumps(
            _clean_value(value),
            default=str,
        )
    )


def _clean_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, np.generic):
        return _clean_value(
            value.item()
        )

    if isinstance(
        value,
        (
            datetime,
            date,
            pd.Timestamp,
        ),
    ):
        return value.isoformat()

    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            return None

    if isinstance(value, dict):
        return {
            str(key): _clean_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _clean_value(item)
            for item in value
        ]

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value