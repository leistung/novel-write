"""自定义异常类和全局异常处理"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from core.response import error_response


# ==================== 业务异常 ====================

class NovelWriteException(Exception):
    """基础业务异常"""
    def __init__(self, message: str, code: int = 50000, details: dict = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)


class NotFoundException(NovelWriteException):
    """资源不存在异常"""
    def __init__(self, message: str = "资源不存在", details: dict = None):
        super().__init__(message, code=40400, details=details)


class ValidationException(NovelWriteException):
    """参数验证异常"""
    def __init__(self, message: str = "参数验证失败", details: dict = None):
        super().__init__(message, code=40000, details=details)


class ConflictException(NovelWriteException):
    """资源冲突异常"""
    def __init__(self, message: str = "资源冲突", details: dict = None):
        super().__init__(message, code=40900, details=details)


class UnauthorizedException(NovelWriteException):
    """未授权异常"""
    def __init__(self, message: str = "未授权访问", details: dict = None):
        super().__init__(message, code=40100, details=details)


class ForbiddenException(NovelWriteException):
    """禁止访问异常"""
    def __init__(self, message: str = "禁止访问", details: dict = None):
        super().__init__(message, code=40300, details=details)


class RateLimitException(NovelWriteException):
    """限流异常"""
    def __init__(self, message: str = "请求过于频繁", details: dict = None):
        super().__init__(message, code=42900, details=details)


class LLMException(NovelWriteException):
    """LLM调用异常"""
    def __init__(self, message: str = "LLM服务异常", details: dict = None):
        super().__init__(message, code=50300, details=details)


class WorkflowException(NovelWriteException):
    """工作流异常"""
    def __init__(self, message: str = "工作流执行异常", details: dict = None):
        super().__init__(message, code=50001, details=details)


# ==================== 全局异常处理器 ====================

async def novelwrite_exception_handler(request: Request, exc: NovelWriteException):
    """处理自定义业务异常"""
    return JSONResponse(
        status_code=_get_http_status(exc.code),
        content=error_response(
            request_id=getattr(request.state, 'request_id', ''),
            message=exc.message,
            code=exc.code,
            details=exc.details
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求参数验证异常"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            request_id=getattr(request.state, 'request_id', ''),
            message="请求参数验证失败",
            code=42200,
            details={"errors": errors}
        )
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """处理数据库完整性错误"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Database integrity error: {exc}")

    # 判断错误类型
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
        message = "数据已存在"
        code = 40901
    elif "foreign key" in error_msg.lower():
        message = "关联数据不存在"
        code = 40001
    else:
        message = "数据完整性错误"
        code = 50002

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response(
            request_id=getattr(request.state, 'request_id', ''),
            message=message,
            code=code
        )
    )


async def operational_error_handler(request: Request, exc: OperationalError):
    """处理数据库操作错误"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Database operational error: {exc}")

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response(
            request_id=getattr(request.state, 'request_id', ''),
            message="数据库服务暂时不可用",
            code=50301
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    import logging
    logger = logging.getLogger(__name__)
    logger.exception(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            request_id=getattr(request.state, 'request_id', ''),
            message="服务器内部错误",
            code=50000,
            details=None
        )
    )


def _get_http_status(code: int) -> int:
    """根据业务码获取HTTP状态码"""
    http_status_map = {
        40000: status.HTTP_400_BAD_REQUEST,
        40100: status.HTTP_401_UNAUTHORIZED,
        40300: status.HTTP_403_FORBIDDEN,
        40400: status.HTTP_404_NOT_FOUND,
        40900: status.HTTP_409_CONFLICT,
        42200: status.HTTP_422_UNPROCESSABLE_ENTITY,
        42900: status.HTTP_429_TOO_MANY_REQUESTS,
        50000: status.HTTP_500_INTERNAL_SERVER_ERROR,
        50001: status.HTTP_500_INTERNAL_SERVER_ERROR,
        50002: status.HTTP_500_INTERNAL_SERVER_ERROR,
        50300: status.HTTP_503_SERVICE_UNAVAILABLE,
        50301: status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    return http_status_map.get(code, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 注册异常处理器 ====================

def register_exception_handlers(app):
    """注册所有异常处理器到FastAPI应用"""
    app.add_exception_handler(NovelWriteException, novelwrite_exception_handler)
    app.add_exception_handler(NotFoundException, novelwrite_exception_handler)
    app.add_exception_handler(ValidationException, novelwrite_exception_handler)
    app.add_exception_handler(ConflictException, novelwrite_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(OperationalError, operational_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
