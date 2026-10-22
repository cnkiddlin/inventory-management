import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging


configure_logging(settings.debug)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "库存管理系统 API。所有核心库存变更均在服务层内使用数据库事务、"
        "行级锁与状态校验，适合库存管理 AI 智能体直接调用。"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part != "body"]
        details.append({"field": ".".join(location), "message": error.get("msg", "参数错误")})
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "请求参数校验失败",
                "details": details,
            }
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Database operation failed", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "database_error",
                "message": "数据库操作失败，请稍后重试",
                "details": None,
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "服务内部错误",
                "details": None,
            }
        },
    )


@app.get("/", include_in_schema=False)
def root():
    if (STATIC_DIR / "index.html").is_file():
        return FileResponse(STATIC_DIR / "index.html")
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": f"{settings.api_v1_prefix}/health",
    }


app.include_router(api_router, prefix=settings.api_v1_prefix)


if STATIC_DIR.is_dir():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
    def serve_frontend(full_path: str) -> FileResponse | JSONResponse:
        if full_path.startswith("api/"):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "not_found",
                        "message": "接口不存在",
                        "details": None,
                    }
                },
            )
        static_root = STATIC_DIR.resolve()
        candidate = (static_root / full_path).resolve()
        if candidate.is_file() and static_root in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(static_root / "index.html")
