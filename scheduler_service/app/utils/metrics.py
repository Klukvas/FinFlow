from prometheus_client import Counter, Histogram, Gauge
from typing import Dict

# Job execution metrics
job_executions_total = Counter(
    "scheduler_job_executions_total",
    "Total number of job executions",
    ["job_name", "status"]
)

job_execution_duration = Histogram(
    "scheduler_job_execution_duration_seconds",
    "Job execution duration in seconds",
    ["job_name"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]
)

job_items_processed = Counter(
    "scheduler_job_items_processed_total",
    "Total items processed by job",
    ["job_name", "status"]
)

# Renewal-specific metrics
renewals_attempted_total = Counter(
    "scheduler_renewals_attempted_total",
    "Total renewal attempts",
    ["status"]
)

renewals_payment_failed_total = Counter(
    "scheduler_renewals_payment_failed_total",
    "Total failed renewal payments",
    ["reason"]
)

renewals_skipped_total = Counter(
    "scheduler_renewals_skipped_total",
    "Total skipped renewals",
    ["reason"]
)

active_jobs_gauge = Gauge(
    "scheduler_active_jobs",
    "Number of currently running jobs"
)

# Helper functions
def record_job_execution(job_name: str, status: str):
    """Record job execution"""
    job_executions_total.labels(job_name=job_name, status=status).inc()


def record_job_duration(job_name: str, duration: float):
    """Record job execution duration"""
    job_execution_duration.labels(job_name=job_name).observe(duration)


def record_items_processed(job_name: str, status: str, count: int = 1):
    """Record items processed"""
    job_items_processed.labels(job_name=job_name, status=status).inc(count)


def record_renewal_attempt(status: str):
    """Record renewal attempt"""
    renewals_attempted_total.labels(status=status).inc()


def record_payment_failure(reason: str):
    """Record payment failure"""
    renewals_payment_failed_total.labels(reason=reason).inc()


def record_renewal_skipped(reason: str):
    """Record skipped renewal"""
    renewals_skipped_total.labels(reason=reason).inc()
