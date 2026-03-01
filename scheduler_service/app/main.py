from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.gzip import GZIPMiddleware
from shared.geoip import GeoIPMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .utils.logging import setup_logging, get_logger
from .jobs import renewal_job

# Setup logging
setup_logging(settings.log_level)
logger = get_logger("scheduler_service")

# Global scheduler instance
scheduler: AsyncIOScheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler
    
    Starts scheduler on startup, shuts down on exit
    """
    global scheduler
    
    logger.info("Starting scheduler service")
    
    # Initialize scheduler
    scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
    
    # Add subscription renewal job
    scheduler.add_job(
        func=renewal_job.execute,
        trigger=CronTrigger.from_crontab(settings.renewal_check_cron),
        id="subscription_renewal",
        name="Subscription Renewal Job",
        max_instances=settings.job_max_instances,
        coalesce=settings.job_coalesce,
        misfire_grace_time=settings.job_misfire_grace_time,
        replace_existing=True,
    )
    
    logger.info(
        f"Scheduled subscription renewal job with cron: {settings.renewal_check_cron}",
        extra={"cron": settings.renewal_check_cron},
    )
    
    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down scheduler")
    scheduler.shutdown(wait=True)
    logger.info("Scheduler shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Scheduler Service",
    description="Background job scheduler for subscription renewals and other tasks",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(GeoIPMiddleware)
app.add_middleware(GZIPMiddleware, minimum_size=500)


@app.get("/health/live")
async def liveness():
    """Liveness probe - process is running"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe - service is ready to handle requests"""
    global scheduler
    
    if scheduler is None:
        return {"status": "not_ready", "reason": "scheduler_not_initialized"}, 503
    
    if not scheduler.running:
        return {"status": "not_ready", "reason": "scheduler_not_running"}, 503
    
    return {"status": "ready"}


@app.get("/scheduler/jobs")
async def list_jobs():
    """List all scheduled jobs"""
    global scheduler
    
    if scheduler is None:
        return {"jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    
    return {"jobs": jobs}


@app.post("/scheduler/jobs/{job_id}/trigger")
async def trigger_job(job_id: str):
    """Manually trigger a job (for testing/admin)"""
    global scheduler
    
    if scheduler is None:
        return {"error": "Scheduler not initialized"}, 503
    
    job = scheduler.get_job(job_id)
    if not job:
        return {"error": f"Job {job_id} not found"}, 404
    
    # Trigger job to run now
    job.modify(next_run_time=asyncio.get_event_loop().time())
    
    logger.info(f"Manually triggered job {job_id}")
    
    return {"status": "triggered", "job_id": job_id}



if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8090,
        reload=False,
        log_level=settings.log_level.lower(),
    )
