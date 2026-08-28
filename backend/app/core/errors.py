"""统一 API 错误模型与异常类型。

所有业务异常统一抛 APIError，由 main.py 注册的全局 exception handlers
转成标准错误响应体：

    {
      "error": {
        "code": "book_not_found",
        "message": "书籍不存在",
        "details": {...}   # 可选
      }
    }

这样前端可以依据 `error.code` 做分支处理，而不是解析 message 字符串。
"""

from __future__ import annotations

from typing import Any


class APIError(Exception):
    """业务错误。status_code 为 HTTP 状态码，code 为稳定错误码（机器可读）。"""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def error_body(code: str, message: str, details: Any | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


# ---- 常用业务错误的便捷构造 ----
def not_found(code: str = "not_found", message: str = "资源不存在") -> APIError:
    return APIError(404, code, message)


def forbidden(code: str = "forbidden", message: str = "无权限执行该操作") -> APIError:
    return APIError(403, code, message)


def unauthorized(code: str = "unauthorized", message: str = "请先登录") -> APIError:
    return APIError(401, code, message)


def bad_request(code: str = "bad_request", message: str = "请求参数有误") -> APIError:
    return APIError(400, code, message)


def conflict(code: str = "conflict", message: str = "资源状态冲突") -> APIError:
    return APIError(409, code, message)
