from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.copilot.router import router as copilot_router
from app.routers import foods, measurements, metabolism

app = FastAPI(title="Weightloss API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(measurements.router)
app.include_router(foods.router)
app.include_router(metabolism.router)
app.include_router(copilot_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
