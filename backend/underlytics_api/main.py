from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from underlytics_api.api.agent_outputs import router as agent_outputs_router
from underlytics_api.api.applications import router as applications_router
from underlytics_api.api.document_lists import router as document_lists_router
from underlytics_api.api.documents import router as documents_router
from underlytics_api.api.loan_products import router as loan_products_router
from underlytics_api.api.manual_review import router as manual_review_router
from underlytics_api.api.users import router as users_router
from underlytics_api.api.workflow import router as workflow_router
from underlytics_api.db.database import engine
from underlytics_api.models.base import Base

app = FastAPI(title="Underlytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Underlytics API is running"}


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}


app.include_router(users_router)
app.include_router(loan_products_router)
app.include_router(applications_router)
app.include_router(documents_router)
app.include_router(document_lists_router)
app.include_router(workflow_router)
app.include_router(agent_outputs_router)
app.include_router(manual_review_router)
