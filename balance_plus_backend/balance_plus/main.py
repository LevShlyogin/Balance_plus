from fastapi import FastAPI
from balance_plus.api.v1.api import api_router

app = FastAPI()

app.include_router(api_router, prefix="/api/v1") 