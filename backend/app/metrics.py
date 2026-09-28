from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

ANALYSIS_STARTED = Counter(
    "ads_analysis_started_total",
    "Number of analyses started",
    ["project_id", "dataset_id"],
)

ANALYSIS_COMPLETED = Counter(
    "ads_analysis_completed_total",
    "Number of analyses completed",
    ["status"],
)

ANALYSIS_DURATION = Histogram(
    "ads_analysis_duration_seconds",
    "Analysis duration in seconds",
    ["status"],
    buckets=(
        1,
        5,
        15,
        30,
        60,
        120,
        300,
        600,
        1200,
        1800,
        3600,
    ),
)

DATASET_UPLOADED = Counter(
    "ads_dataset_uploaded_total",
    "Number of datasets uploaded",
    ["media_type"],
)

ACTIVE_ANALYSES = Gauge(
    "ads_active_analyses",
    "Number of active analyses",
)

API_REQUESTS = Counter(
    "ads_api_requests_total",
    "Number of API requests",
    ["method", "path", "status_code"],
)
