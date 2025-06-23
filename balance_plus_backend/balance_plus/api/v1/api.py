from fastapi import APIRouter
from .endpoints import projects, tasks, jobs

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"]) 