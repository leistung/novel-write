"""提示词模块包"""

from .architect import (
    ARCHITECT_PROMPTS,
    generate_foundation_prompt,
    plan_chapter_prompt,
    analyze_outline_impact_prompt,
    update_book_state_prompt
)
from .writer import (
    WRITER_PROMPTS,
    check_chapter_outline_prompt,
    write_chapter_prompt,
    check_self_modification_prompt,
    observer_prompt,
    settler_prompt
)
from .continuity import (
    CONSISTENCY_PROMPTS,
    check_consistency_prompt
)
from .auditor import (
    AUTHOR_PROMPTS,
    score_chapter_prompt
)

__all__ = [
    # 提示词字典（保持向后兼容）
    "ARCHITECT_PROMPTS",
    "WRITER_PROMPTS",
    "CONSISTENCY_PROMPTS",
    "AUTHOR_PROMPTS",
    # 独立提示词变量
    "generate_foundation_prompt",
    "plan_chapter_prompt",
    "analyze_outline_impact_prompt",
    "update_book_state_prompt",
    "check_chapter_outline_prompt",
    "write_chapter_prompt",
    "check_self_modification_prompt",
    "observer_prompt",
    "settler_prompt",
    "check_consistency_prompt",
    "score_chapter_prompt"
]