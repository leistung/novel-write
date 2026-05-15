"""输出验证模块"""
from prompts.schemas.validation import OutputValidator, ValidationResult
from prompts.schemas.novel_schemas import (
    FoundationOutput,
    ChapterOutlineOutput,
    AuditResultOutput,
    RewriteOutput,
    StyleAnalysisOutput,
)

__all__ = [
    "OutputValidator",
    "ValidationResult",
    "FoundationOutput",
    "ChapterOutlineOutput",
    "AuditResultOutput",
    "RewriteOutput",
    "StyleAnalysisOutput",
]
