from __future__ import annotations

import asyncio
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


class DatasetMetadataError(RuntimeError):
    pass


async def extract_dataset_metadata(
    path: Path,
    filename: str,
) -> dict[str, Any]:
    suffix = Path(filename).suffix.lower()

    if suffix == ".csv":
        return await asyncio.to_thread(_extract_csv, path)

    if suffix == ".parquet":
        return await asyncio.to_thread(_extract_parquet, path)

    if suffix == ".jsonl":
        return await asyncio.to_thread(_extract_jsonl, path)

    if suffix == ".json":
        return await asyncio.to_thread(_extract_json, path)

    raise DatasetMetadataError("unsupported_dataset_format")


def _extract_csv(path: Path) -> dict[str, Any]:
    try:
        header = pd.read_csv(path, nrows=0)
    except Exception as exc:
        raise DatasetMetadataError("invalid_csv") from exc

    columns = [str(column) for column in header.columns]
    dtypes = {
        str(column): str(dtype)
        for column, dtype in header.dtypes.items()
    }
    nullable = {column: False for column in columns}

    row_count = 0
    sample_rows: list[dict[str, Any]] = []

    try:
        reader = pd.read_csv(path, chunksize=50_000)

        for chunk in reader:
            row_count += len(chunk)

            for column in chunk.columns:
                key = str(column)

                if chunk[column].isna().any():
                    nullable[key] = True

            if not sample_rows:
                sample_rows = _records(chunk.head(5))

    except Exception as exc:
        raise DatasetMetadataError("invalid_csv") from exc

    return _build_metadata(
        format_name="csv",
        row_count=row_count,
        columns=columns,
        dtypes=dtypes,
        nullable=nullable,
        sample_rows=sample_rows,
    )


def _extract_parquet(path: Path) -> dict[str, Any]:
    try:
        parquet_file = pq.ParquetFile(path)
        row_count = parquet_file.metadata.num_rows

        columns = [
            {
                "name": field.name,
                "dtype": str(field.type),
                "nullable": bool(field.nullable),
            }
            for field in parquet_file.schema_arrow
        ]

        sample_rows: list[dict[str, Any]] = []

        if row_count > 0:
            table = parquet_file.read_row_group(0)
            sample_rows = _records(table.slice(0, min(5, table.num_rows)).to_pandas())

    except Exception as exc:
        raise DatasetMetadataError("invalid_parquet") from exc

    return {
        "format": "parquet",
        "row_count": int(row_count),
        "column_count": len(columns),
        "columns": columns,
        "sample_rows": sample_rows,
    }


def _extract_jsonl(path: Path) -> dict[str, Any]:
    row_count = 0
    sample_rows: list[dict[str, Any]] = []
    nullable: dict[str, bool] = {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue

                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise DatasetMetadataError(
                        f"invalid_jsonl_line:{line_number}"
                    ) from exc

                row_count += 1

                if isinstance(value, dict):
                    row = value

                    for key, item in row.items():
                        nullable.setdefault(str(key), False)

                        if item is None:
                            nullable[str(key)] = True

                else:
                    row = {"value": value}
                    nullable.setdefault("value", False)

                    if value is None:
                        nullable["value"] = True

                if len(sample_rows) < 5:
                    sample_rows.append(row)

    except OSError as exc:
        raise DatasetMetadataError("unable_to_read_jsonl") from exc

    frame = pd.DataFrame(sample_rows)
    columns = [str(column) for column in frame.columns]
    dtypes = {
        str(column): str(dtype)
        for column, dtype in frame.dtypes.items()
    }

    return _build_metadata(
        format_name="jsonl",
        row_count=row_count,
        columns=columns,
        dtypes=dtypes,
        nullable=nullable,
        sample_rows=_records(frame.head(5)),
    )


def _extract_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        raise DatasetMetadataError("invalid_json") from exc

    rows = data if isinstance(data, list) else [data]
    frame = pd.DataFrame(rows)

    columns = [str(column) for column in frame.columns]
    dtypes = {
        str(column): str(dtype)
        for column, dtype in frame.dtypes.items()
    }
    nullable = {
        column: bool(frame[column].isna().any())
        for column in columns
    }

    return _build_metadata(
        format_name="json",
        row_count=len(rows),
        columns=columns,
        dtypes=dtypes,
        nullable=nullable,
        sample_rows=_records(frame.head(5)),
    )


def _build_metadata(
    *,
    format_name: str,
    row_count: int,
    columns: list[str],
    dtypes: dict[str, str],
    nullable: dict[str, bool],
    sample_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "format": format_name,
        "row_count": int(row_count),
        "column_count": len(columns),
        "columns": [
            {
                "name": column,
                "dtype": dtypes.get(column, "unknown"),
                "nullable": bool(nullable.get(column, True)),
            }
            for column in columns
        ],
        "sample_rows": sample_rows,
    }


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {
            str(key): _clean_value(value)
            for key, value in row.items()
        }
        for row in frame.to_dict(orient="records")
    ]


def _clean_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, np.generic):
        return _clean_value(value.item())

    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()

    if isinstance(value, float) and np.isnan(value):
        return None

    if isinstance(value, dict):
        return {
            str(key): _clean_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_clean_value(item) for item in value]

    try:
        missing = pd.isna(value)

        if isinstance(missing, bool) and missing:
            return None
    except (TypeError, ValueError):
        pass

    return value
