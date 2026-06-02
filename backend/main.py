from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.copilot.router import router as copilot_router
from app.routers import foods, measurements, metabolism

settings = get_settings()

app = FastAPI(title="Weightloss API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
