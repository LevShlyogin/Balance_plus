from fastapi import FastAPI
from balance_plus.api.v1.endpoints import auth, projects

app = FastAPI(title="Balance Plus MVP")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects & Tasks"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Balance Plus API"} 