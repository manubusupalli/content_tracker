from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import tasks

app = FastAPI(title="Telusko Workflow Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
