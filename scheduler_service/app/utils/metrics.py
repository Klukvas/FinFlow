"""No-op metrics stubs (monitoring stack removed)."""


class _NoOpGauge:
    def inc(self): pass
    def dec(self): pass


active_jobs_gauge = _NoOpGauge()


def record_job_execution(job_name: str, status: str): pass
def record_job_duration(job_name: str, duration: float): pass
def record_items_processed(job_name: str, status: str, count: int = 1): pass
def record_renewal_attempt(status: str): pass
def record_payment_failure(reason: str): pass
def record_renewal_skipped(reason: str): pass
