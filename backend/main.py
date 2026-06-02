from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import measurements

app = FastAPI(title="Weightloss API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(measurements.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
