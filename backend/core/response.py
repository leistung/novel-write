"""统一API响应格式"""
import time
import uuid
from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应模型"""
    code: int = Field(default=0, description="业务状态码，0表示成功")
    message: str = Field(default="success", description="状态描述")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000), description="时间戳（毫秒）")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="请求唯一标识")
    
    class Config:
        arbitrary_types_allowed = True


class ApiError(BaseModel):
    """API错误详情"""
    code: int = Field(description="错误码")
    message: str = Field(description="错误信息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细错误信息")


class PaginationData(BaseModel, Generic[T]):
    """分页数据模型"""
    items: list[T] = Field(description="数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    total_pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class PaginationResponse(ApiResponse[PaginationData[T]], Generic[T]):
    """分页响应模型"""
    pass


# ==================== 便捷函数 ====================

def success_response(
    request_id: str,
    data: Any = None,
    message: str = "success",
    code: int = 0
) -> Dict[str, Any]:
    """创建成功响应"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
        "request_id": request_id
    }


def error_response(
    request_id: str,
    message: str,
    code: int = 50000,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """创建错误响应"""
    response = {
        "code": code,
        "message": message,
        "data": None,
        "timestamp": int(time.time() * 1000),
        "request_id": request_id
    }
    if details:
        response["details"] = details
    return response


def pagination_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建分页响应"""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "timestamp": int(time.time() * 1000),
        "request_id": request_id or str(uuid.uuid4())
    }
