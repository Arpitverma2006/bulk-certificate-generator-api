from fastapi import FastAPI
from app.database import engine, Base
from app.routers import certificates
from app.services.certificate_service import ensure_template_exists

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator API",
    description="Backend API for generating, tracking, and downloading bulk certificates efficiently.",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    ensure_template_exists()

app.include_router(certificates.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Bulk Certificate Generator API. Visit /docs for interactive Swagger UI."}
