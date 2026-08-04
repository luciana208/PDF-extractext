from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from beanie import init_beanie
from contextlib import asynccontextmanager

from app.business.domain.exceptions import DocumentNotFoundError, DuplicatePDFError, InvalidFileError, ProblemDetailError
from app.data.database.mongo_connection import connect, disconnect, get_database
from app.data.models.document_model import DocumentModel
from app.presentation.routers.document_router import router as document_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect()
    await init_beanie(database=get_database(), document_models=[DocumentModel])
    yield
    # Shutdown
    await disconnect()


app = FastAPI(lifespan=lifespan)


def build_problem_detail(status_code: int, title: str, detail: str) -> dict[str, object]:
    return {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
    }


@app.exception_handler(ProblemDetailError)
async def problem_detail_handler(request: Request, exc: ProblemDetailError) -> JSONResponse:
    body = build_problem_detail(exc.status_code, exc.title, exc.detail)
    # RFC 9457 requires an "instance" member identifying the specific occurrence.
    body["instance"] = str(request.url)
    # If the exception exposes a specific type, use it.
    if getattr(exc, "type", None):
        body["type"] = exc.type
    return JSONResponse(status_code=exc.status_code, content=body)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



# Registrar el router de documentos
app.include_router(document_router)
