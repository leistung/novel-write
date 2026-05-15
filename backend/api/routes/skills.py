"""Skill API路由"""
import re
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.crud import get_skill_template, get_skill_templates, create_skill_template

router = APIRouter()

# Skill文件根目录
SKILLS_ROOT = Path(__file__).parent.parent.parent.parent / "skills"


# ==================== 公共工具函数 ====================

def _extract_description(content: str) -> str:
    """从SKILL.md内容中提取description"""
    # 优先从frontmatter解析
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            for line in frontmatter.split("\n"):
                if line.startswith("description:"):
                    return line.replace("description:", "").strip().strip('"').strip("'")
    # 回退：逐行查找
    for line in content.split("\n"):
        if line.startswith("description:"):
            return line.replace("description:", "").strip().strip('"').strip("'")
    return ""


def _match_category(skill_name: str) -> str:
    """根据skill名称匹配category"""
    if "-female-" in skill_name:
        return "female"
    for genre_key, gen_info in GENRE_DEFINITIONS.items():
        if gen_info.get("skill_name") == skill_name:
            return gen_info["category"]
    return "male"


class SkillCreate(BaseModel):
    """创建Skill请求"""
    name: str
    genre: str
    category: str  # male/female
    description: str = ""
    skill_content: str = ""


class SkillResponse(BaseModel):
    """Skill响应"""
    id: int
    name: str
    genre: str
    category: str
    description: str
    usage_count: int

    class Config:
        from_attributes = True


# 26种小说类型定义
GENRE_DEFINITIONS = {
    # 男频
    "xuanhuan": {"name": "玄幻", "category": "male", "skill_name": "xuanhuan-novelist"},
    "qihuan": {"name": "奇幻", "category": "male", "skill_name": "qihuan-novelist"},
    "wuxia": {"name": "武侠", "category": "male", "skill_name": "wuxia-novelist"},
    "xianxia": {"name": "仙侠", "category": "male", "skill_name": "xianxia-novelist"},
    "urban": {"name": "都市", "category": "male", "skill_name": "urban-novelist"},
    "realistic": {"name": "现实", "category": "male", "skill_name": "realistic-novelist"},
    "historical": {"name": "历史", "category": "male", "skill_name": "historical-novelist"},
    "military": {"name": "军事", "category": "male", "skill_name": "military-novelist"},
    "game": {"name": "游戏", "category": "male", "skill_name": "game-novelist"},
    "sports": {"name": "体育", "category": "male", "skill_name": "sports-novelist"},
    "scifi": {"name": "科幻", "category": "male", "skill_name": "scifi-novelist"},
    "suspense_supernatural": {"name": "悬疑灵幻", "category": "male", "skill_name": "suspense-supernatural-novelist"},
    "light": {"name": "轻小说", "category": "male", "skill_name": "light-novelist"},
    "short_story": {"name": "短篇", "category": "male", "skill_name": "short-story-novelist"},
    "infinite": {"name": "诸天无限", "category": "male", "skill_name": "infinite-novelist"},
    # 女频
    "ancient_romance": {"name": "古代言情", "category": "female", "skill_name": "ancient-romance-novelist"},
    "modern_romance": {"name": "现代言情", "category": "female", "skill_name": "modern-romance-novelist"},
    "fantasy_romance": {"name": "玄幻言情", "category": "female", "skill_name": "fantasy-romance-novelist"},
    "mystery": {"name": "悬疑推理", "category": "female", "skill_name": "mystery-novelist"},
    "youth_romance": {"name": "浪漫青春", "category": "female", "skill_name": "youth-romance-novelist"},
    "xianxia_romance": {"name": "仙侠奇缘", "category": "female", "skill_name": "xianxia-romance-novelist"},
    "scifi_romance": {"name": "科幻空间", "category": "female", "skill_name": "scifi-romance-novelist"},
    "esports_romance": {"name": "游戏竞技", "category": "female", "skill_name": "esports-romance-novelist"},
    "light_female": {"name": "轻小说", "category": "female", "skill_name": "light-female-novelist"},
    "short_female": {"name": "短篇", "category": "female", "skill_name": "short-female-novelist"},
    "real_life_female": {"name": "现实生活", "category": "female", "skill_name": "real-life-female-novelist"},
}


def get_skill_file_path(skill_name: str) -> Path:
    """获取skill文件路径（含路径遍历防护）"""
    safe_name = re.sub(r'[^\w\-]', '', skill_name)
    return SKILLS_ROOT / safe_name / "SKILL.md"


def get_skill_references_path(skill_name: str) -> Path:
    """获取skill references目录路径（含路径遍历防护）"""
    safe_name = re.sub(r'[^\w\-]', '', skill_name)
    return SKILLS_ROOT / safe_name / "references" / "research"


def load_skill_from_file(skill_name: str) -> dict:
    """从文件系统加载skill内容"""
    skill_file = get_skill_file_path(skill_name)
    references_dir = get_skill_references_path(skill_name)

    if not skill_file.exists():
        return None

    # 读取SKILL.md
    content = skill_file.read_text(encoding="utf-8")

    # 读取references
    references = {}
    if references_dir.exists():
        for ref_file in references_dir.glob("*.md"):
            ref_name = ref_file.stem  # 文件名不含扩展名
            references[ref_name] = ref_file.read_text(encoding="utf-8")

    return {
        "content": content,
        "references": references
    }


def get_all_skill_names_from_filesystem() -> List[str]:
    """从文件系统获取所有skill名称"""
    if not SKILLS_ROOT.exists():
        return []

    skill_names = []
    for item in SKILLS_ROOT.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            skill_names.append(item.name)

    return sorted(skill_names)


@router.get("/skills")
async def list_skills(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取Skill列表 - 从文件系统和数据库合并"""
    skills = []
    skill_names = get_all_skill_names_from_filesystem()

    # 从文件系统获取skill元数据
    for name in skill_names:
        skill_data = load_skill_from_file(name)
        if skill_data:
            description = _extract_description(skill_data["content"])
            skill_category = _match_category(name)

            if category and skill_category != category:
                continue

            # 根据skill名称匹配genre
            matched_genre = None
            for genre_key, gen_info in GENRE_DEFINITIONS.items():
                if gen_info.get("skill_name") == name:
                    matched_genre = genre_key
                    break

            skills.append({
                "id": len(skills) + 1,  # 虚拟ID
                "name": name,
                "genre": matched_genre or name,
                "category": skill_category,
                "description": description,
                "usage_count": 0
            })

    # 如果数据库中有skill，合并（数据库优先）
    db_skills = await get_skill_templates(db, category=category)
    for skill in db_skills:
        skills.append({
            "id": skill.id,
            "name": skill.name,
            "genre": skill.genre,
            "category": skill.category,
            "description": skill.description,
            "usage_count": skill.usage_count
        })

    return skills


@router.get("/skills/{skill_name}")
async def get_skill_detail(
    skill_name: str,
    db: AsyncSession = Depends(get_db)
):
    """获取Skill详情 - 先查数据库，没有则从文件系统读取"""
    # 先查数据库
    skill = await get_skill_template(db, skill_name)

    if skill:
        return {
            "id": skill.id,
            "name": skill.name,
            "genre": skill.genre,
            "category": skill.category,
            "description": skill.description,
            "skill_content": skill.skill_content,
            "references": skill.references,
            "usage_count": skill.usage_count,
            "source": "database"
        }

    # 从文件系统读取
    skill_data = load_skill_from_file(skill_name)
    if not skill_data:
        raise HTTPException(status_code=404, detail="Skill不存在")

    content = skill_data["content"]
    description = _extract_description(content)
    skill_category = _match_category(skill_name)

    return {
        "id": 0,  # 文件系统skill无ID
        "name": skill_name,
        "genre": skill_name,
        "category": skill_category,
        "description": description,
        "skill_content": content,
        "references": skill_data["references"],
        "usage_count": 0,
        "source": "filesystem"
    }


@router.post("/skills", response_model=SkillResponse)
async def create_new_skill(
    request: SkillCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新Skill"""
    try:
        skill = await create_skill_template(
            db=db,
            name=request.name,
            genre=request.genre,
            category=request.category,
            description=request.description,
            skill_content=request.skill_content
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "unique" in error_msg or "duplicate" in error_msg:
            raise HTTPException(status_code=409, detail=f"Skill '{request.name}' 已存在")
        raise HTTPException(status_code=500, detail=f"创建Skill失败: {str(e)}")

    return {
        "id": skill.id,
        "name": skill.name,
        "genre": skill.genre,
        "category": skill.category,
        "description": skill.description,
        "usage_count": skill.usage_count
    }


@router.get("/skills/genres/list")
async def list_genres():
    """获取所有小说类型"""
    return {
        "male": [
            {"key": k, "name": v["name"], "category": v["category"]}
            for k, v in GENRE_DEFINITIONS.items()
            if v["category"] == "male"
        ],
        "female": [
            {"key": k, "name": v["name"], "category": v["category"]}
            for k, v in GENRE_DEFINITIONS.items()
            if v["category"] == "female"
        ]
    }


@router.post("/skills/sync")
async def sync_skills_from_filesystem(db: AsyncSession = Depends(get_db)):
    """从文件系统同步skill到数据库"""
    skill_names = get_all_skill_names_from_filesystem()
    synced_count = 0

    for skill_name in skill_names:
        skill_data = load_skill_from_file(skill_name)
        if not skill_data:
            continue

        content = skill_data["content"]

        # 解析description
        description = _extract_description(content)

        # 匹配category和genre
        skill_category = _match_category(skill_name)
        matched_genre = skill_name
        for genre_key, gen_info in GENRE_DEFINITIONS.items():
            if gen_info.get("skill_name") == skill_name:
                skill_category = gen_info["category"]
                matched_genre = genre_key
                break

        # 检查是否已存在
        existing = await get_skill_template(db, skill_name)
        if not existing:
            await create_skill_template(
                db=db,
                name=skill_name,
                genre=matched_genre,
                category=skill_category,
                description=description,
                skill_content=content
            )
            synced_count += 1

    await db.commit()

    return {
        "message": f"成功同步 {synced_count} 个skill到数据库",
        "total_found": len(skill_names),
        "synced": synced_count
    }


@router.get("/skills/filesystem/list")
async def list_skills_from_filesystem():
    """直接从文件系统获取所有skill列表"""
    skill_names = get_all_skill_names_from_filesystem()

    skills = []
    for name in skill_names:
        skill_data = load_skill_from_file(name)
        if skill_data:
            description = _extract_description(skill_data["content"])
            skill_category = _match_category(name)

            # 统计references
            ref_count = len(skill_data["references"])

            skills.append({
                "name": name,
                "category": skill_category,
                "description": description,
                "reference_count": ref_count,
                "has_skill_md": True
            })

    return {
        "total": len(skills),
        "skills": skills
    }
