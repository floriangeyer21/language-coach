"""LanguageCoach API entrypoint. Run: uvicorn main:app --reload (from app/server)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from openai import APIStatusError, OpenAIError

from config import get_settings
from routers import auth, chat, memory, vocabulary
from storage import get_storage

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bootstrap the data source (e.g. MySQL DDL). No-op for backends without init().
    store = get_storage()
    init = getattr(store, "init", None)
    if init is not None:
        await init()
    yield


app = FastAPI(title="LanguageCoach API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Consistent error envelope: { "error": { "code", "message" } }  (see api/overview.md)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    code = detail if isinstance(detail, str) else "error"
    message = detail if isinstance(detail, str) else str(detail)
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": code, "message": message}})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": str(exc.errors())}})


@app.exception_handler(OpenAIError)
async def openai_exception_handler(request: Request, exc: OpenAIError):
    # Surface upstream AI failures (quota, auth, rate limit) as a clean 502.
    code = "ai_unavailable"
    message = "The AI provider is currently unavailable."
    if isinstance(exc, APIStatusError):
        try:
            body = exc.response.json().get("error", {})
            code = body.get("code") or code
            message = body.get("message") or message
        except Exception:
            pass
    return JSONResponse(status_code=502, content={"error": {"code": code, "message": message}})


@app.get("/api/health")
async def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(memory.router)
app.include_router(vocabulary.router)
