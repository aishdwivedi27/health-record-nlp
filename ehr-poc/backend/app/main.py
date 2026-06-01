from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models.models import Base
from app.routers import patients, encounters, observations, medications, reports, ai, fhir, nlp_query
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Synthetic FHIR EHR PoC", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router)
app.include_router(encounters.router)
app.include_router(observations.router)
app.include_router(medications.router)
app.include_router(reports.router)
app.include_router(ai.router)
app.include_router(nlp_query.router)
app.include_router(fhir.router)


@app.get("/")
def root():
    return {
        "message": "Synthetic FHIR EHR PoC API v2",
        "docs": "/docs",
        "fhir_base": "/fhir",
        "patient_search": "/fhir/Patient?name=james",
    }
