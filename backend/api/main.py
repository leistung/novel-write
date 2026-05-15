"""FastAPI主应用"""
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# 添加backend目录到Python路径（项目采用扁平导入结构，需要将backend目录加入sys.path）
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

from config.settings import get_settings
from db.database import init_db, close_db
from api.routes import books, chapters, workflows, checkpoints, skills, websocket, book_detail, orchestrator, stream, workflow_control
from core.exceptions import register_exception_handlers
from core.response import success_response

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await init_db()
    logger.info(f"{settings.APP_NAME} 启动成功!")

    yield

    # 关闭时清理
    await close_db()
    logger.info("应用已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI驱动的小说创作系统",
    version=__version__,
    lifespan=lifespan
)

# 注册全局异常处理器
register_exception_handlers(app)

# 请求ID中间件
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """为每个请求生成唯一ID"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# CORS中间件
cors_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["http://localhost:3000", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(books.router, prefix="/api/v1", tags=["books"])
app.include_router(chapters.router, prefix="/api/v1", tags=["chapters"])
app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
app.include_router(checkpoints.router, prefix="/api/v1", tags=["checkpoints"])
app.include_router(skills.router, prefix="/api/v1", tags=["skills"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(book_detail.router, prefix="/api/v1", tags=["book-detail"])
app.include_router(orchestrator.router, prefix="/api/v1/orchestrator", tags=["orchestrator"])
app.include_router(stream.router, prefix="/api/v1", tags=["stream"])
app.include_router(workflow_control.router, prefix="/api/v1", tags=["workflow-control"])


@app.get("/")
async def root(request: Request):
    """根路径"""
    return success_response(
        request_id=getattr(request.state, 'request_id', ''),
        data={
            "app": settings.APP_NAME,
            "version": __version__,
            "docs": "/docs",
        }
    )


@app.get("/health")
async def health_check(request: Request):
    """健康检查"""
    return success_response(
        request_id=getattr(request.state, 'request_id', ''),
        data={
            "status": "healthy",
            "version": __version__,
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
