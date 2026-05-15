"""技能加载器 - 加载题材技能包（支持 JSON 和 Markdown 格式）"""
import os
import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# genre -> skill_name 映射
GENRE_TO_SKILL_MAP: Dict[str, str] = {
    # 英文key
    "xuanhuan": "xuanhuan-novelist",
    "qihuan": "qihuan-novelist",
    "wuxia": "wuxia-novelist",
    "xianxia": "xianxia-novelist",
    "urban": "urban-novelist",
    "realistic": "realistic-novelist",
    "historical": "historical-novelist",
    "military": "military-novelist",
    "game": "game-novelist",
    "sports": "sports-novelist",
    "scifi": "scifi-novelist",
    "suspense_supernatural": "suspense-supernatural-novelist",
    "light": "light-novelist",
    "short_story": "short-story-novelist",
    "infinite": "infinite-novelist",
    "ancient_romance": "ancient-romance-novelist",
    "modern_romance": "modern-romance-novelist",
    "fantasy_romance": "fantasy-romance-novelist",
    "mystery": "mystery-novelist",
    "youth_romance": "youth-romance-novelist",
    "xianxia_romance": "xianxia-romance-novelist",
    "scifi_romance": "scifi-romance-novelist",
    "esports_romance": "esports-romance-novelist",
    "light_female": "light-female-novelist",
    "short_female": "short-female-novelist",
    "real_life_female": "real-life-female-novelist",
    # 中文key（兼容）
    "玄幻": "xuanhuan-novelist",
    "奇幻": "qihuan-novelist",
    "武侠": "wuxia-novelist",
    "仙侠": "xianxia-novelist",
    "都市": "urban-novelist",
    "现实": "realistic-novelist",
    "历史": "historical-novelist",
    "军事": "military-novelist",
    "游戏": "game-novelist",
    "体育": "sports-novelist",
    "科幻": "scifi-novelist",
    "悬疑灵幻": "suspense-supernatural-novelist",
    "轻小说": "light-novelist",
    "短篇": "short-story-novelist",
    "诸天无限": "infinite-novelist",
    "古代言情": "ancient-romance-novelist",
    "现代言情": "modern-romance-novelist",
    "玄幻言情": "fantasy-romance-novelist",
    "悬疑推理": "mystery-novelist",
    "浪漫青春": "youth-romance-novelist",
    "仙侠奇缘": "xianxia-romance-novelist",
    "科幻空间": "scifi-romance-novelist",
    "游戏竞技": "esports-romance-novelist",
}

# 需要提取的关键段落标题（用于拼接prompt suffix）
_KEY_SECTIONS = ["核心智模型", "表达DNA", "决策启发式"]


class SkillLoader:
    """技能加载器 - 管理题材技能包"""
    
    def __init__(self, skills_dir: str = None):
        if skills_dir is None:
            skills_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "skills"
            )
        self.skills_dir = Path(skills_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._suffix_cache: Dict[str, str] = {}
    
    def load_skill(self, genre: str) -> Dict[str, Any]:
        """加载指定题材的技能包"""
        if genre in self._cache:
            return self._cache[genre]
        
        skill_file = self.skills_dir / f"{genre}.json"
        skill_md_dir = self.skills_dir / f"{genre}-novelist"
        
        if skill_file.exists():
            return self._load_json_skill(skill_file)
        elif skill_md_dir.exists():
            return self._load_markdown_skill(skill_md_dir, genre)
        else:
            return self._get_default_skill(genre)
    
    def _load_json_skill(self, skill_file: Path) -> Dict[str, Any]:
        """加载 JSON 格式的技能包"""
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                skill_data = json.load(f)
                self._cache[skill_file.stem] = skill_data
                return skill_data
        except Exception:
            return {}
    
    def _load_markdown_skill(self, skill_dir: Path, genre: str) -> Dict[str, Any]:
        """加载 Markdown 格式的技能包"""
        skill_md_file = skill_dir / "SKILL.md"
        
        if not skill_md_file.exists():
            return self._get_default_skill(genre)
        
        try:
            with open(skill_md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            skill_data = {
                "name": f"{genre}-novelist",
                "format": "markdown",
                "content": content,
                "metadata": self._extract_frontmatter(content)
            }
            
            self._cache[genre] = skill_data
            return skill_data
        except Exception:
            return self._get_default_skill(genre)
    
    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """提取 YAML frontmatter"""
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return {}
        
        frontmatter = {}
        for line in match.group(1).split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()
        
        return frontmatter
    
    def get_skill_prompt(self, genre: str, skill_name: str) -> Optional[str]:
        """获取技能包中的特定提示词"""
        skill_data = self.load_skill(genre)
        return skill_data.get(skill_name)
    
    def get_genre_enhancement(self, genre: str) -> str:
        """获取题材增强提示"""
        skill_data = self.load_skill(genre)
        
        if skill_data.get("format") == "markdown":
            content = skill_data.get("content", "")
            return self._extract_role_play_rules(content)
        
        return skill_data.get("genre_enhancement", "")
    
    def get_role_play_prompt(self, genre: str) -> str:
        """获取角色扮演提示词"""
        skill_data = self.load_skill(genre)
        
        if skill_data.get("format") == "markdown":
            content = skill_data.get("content", "")
            return self._extract_role_play_section(content)
        
        return ""
    
    def get_writing_rules(self, genre: str) -> str:
        """获取写作规则"""
        skill_data = self.load_skill(genre)
        return skill_data.get("writing_rules", "")
    
    def get_plot_templates(self, genre: str) -> list:
        """获取情节模板"""
        skill_data = self.load_skill(genre)
        return skill_data.get("plot_templates", [])
    
    def list_available_genres(self) -> list:
        """列出所有可用的题材"""
        if not self.skills_dir.exists():
            return []
        
        genres = set()
        
        for file in self.skills_dir.glob("*.json"):
            genres.add(file.stem)
        
        for dir in self.skills_dir.glob("*-novelist"):
            genre_name = dir.stem.replace("-novelist", "")
            genres.add(genre_name)
        
        return sorted(list(genres))
    
    def _extract_role_play_rules(self, content: str) -> str:
        """从 Markdown 内容中提取角色扮演规则"""
        rules = []
        
        role_section = re.search(r'## 角色扮演规则.*?(?=##|\Z)', content, re.DOTALL)
        if role_section:
            rules.append(role_section.group(0))
        
        decision_heuristics = re.search(r'## 决策启发式.*?(?=##|\Z)', content, re.DOTALL)
        if decision_heuristics:
            rules.append(decision_heuristics.group(0))
        
        return "\n\n".join(rules) if rules else ""
    
    def _extract_role_play_section(self, content: str) -> str:
        """提取角色扮演完整章节"""
        role_section = re.search(
            r'(## 角色扮演规则.*?)(?=## [^角色]|## 核心心智|## 决策启发式|\Z)',
            content,
            re.DOTALL
        )
        
        if role_section:
            return role_section.group(1).strip()
        
        return ""
    
    def _get_default_skill(self, genre: str) -> Dict[str, Any]:
        """获取默认技能包"""
        defaults = {
            "玄幻": {
                "genre_enhancement": "强调升级体系和逆袭情节，主角成长迅速。参考《斗破苍穹》《凡人修仙传》等经典作品。",
                "writing_rules": "禁止主角无故降智，禁止反派强行降智，保持战斗逻辑自洽。",
                "plot_templates": ["废柴逆袭", "家族崛起", "宗门成长", "星际修真"]
            },
            "仙侠": {
                "genre_enhancement": "强调道心修为和飘逸脱俗的描写。参考《诛仙》《蜀山剑侠传》等经典作品。",
                "writing_rules": "禁止主角滥杀无辜，禁止道心不稳，保持仙侠韵味。",
                "plot_templates": ["凡人流", "古典仙侠", "现代修真"]
            },
            "都市": {
                "genre_enhancement": "贴近现实生活，容易产生代入感。参考《都市重生》《职场商战》等题材。",
                "writing_rules": "禁止过度YY，禁止违背现实逻辑，保持合理爽点。",
                "plot_templates": ["都市重生", "职场商战", "都市异能", "神医流"]
            },
            "科幻": {
                "genre_enhancement": "注重想象力和科技细节。参考《三体》《星际穿越》等作品。",
                "writing_rules": "禁止科技树跳跃过大，禁止逻辑漏洞，保持科幻感。",
                "plot_templates": ["星际文明", "末世危机", "虚拟现实", "高武科技"]
            },
            "历史": {
                "genre_enhancement": "尊重历史背景，注重时代特色。参考《明朝那些事儿》等历史小说。",
                "writing_rules": "禁止严重歪曲历史，保持历史逻辑，融入合理虚构。",
                "plot_templates": ["穿越历史", "架空历史", "历史悬疑"]
            }
        }
        
        return defaults.get(genre, {
            "genre_enhancement": f"{genre}题材网络小说创作指导",
            "writing_rules": "禁止违规内容，保持逻辑自洽",
            "plot_templates": []
        })

    def get_skill_prompt_suffix(self, genre: str) -> str:
        """从SKILL.md中提取核心智模型、表达DNA、决策启发式，拼接成一段
        可以附加到system_prompt后面的文本（控制在2000字以内）。

        如果skill文件不存在或无法解析，返回空字符串。
        """
        # 使用缓存
        if genre in self._suffix_cache:
            return self._suffix_cache[genre]

        skill_name = GENRE_TO_SKILL_MAP.get(genre)
        if not skill_name:
            self._suffix_cache[genre] = ""
            return ""

        skill_file = self.skills_dir / skill_name / "SKILL.md"
        if not skill_file.exists():
            self._suffix_cache[genre] = ""
            return ""

        try:
            content = skill_file.read_text(encoding="utf-8")
            suffix = self._extract_key_sections(content)
            # 控制在2000字以内
            if len(suffix) > 2000:
                suffix = suffix[:2000] + "\n\n...(内容已截断)"
            self._suffix_cache[genre] = suffix
            return suffix
        except Exception as e:
            logger.error("Failed to read skill file %s: %s", skill_file, e)
            self._suffix_cache[genre] = ""
            return ""

    @staticmethod
    def _extract_key_sections(content: str) -> str:
        """从SKILL.md全文中提取关键段落，拼接为紧凑文本。"""
        parts: list[str] = []

        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 检查是否匹配到关键段落标题（## 级别）
            for section_title in _KEY_SECTIONS:
                if line.startswith("## ") and section_title in line:
                    # 收集该段落直到下一个 ## 级标题或文件末尾
                    section_lines: list[str] = [line]
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        if next_line.strip().startswith("## "):
                            break
                        section_lines.append(next_line)
                        i += 1
                    parts.append("\n".join(section_lines).strip())
                    # 已经前进到下一行，跳过外层 i+=1
                    i -= 1
                    break
            i += 1

        return "\n\n".join(parts)

    @staticmethod
    def get_genre_to_skill_map() -> dict:
        """返回genre到skill_name的映射（副本）。"""
        return dict(GENRE_TO_SKILL_MAP)

    def load_skill_content(self, genre: str) -> dict:
        """根据genre加载对应skill的SKILL.md全文内容。

        Returns:
            {"skill_name": str, "content": str} 或空dict（找不到时）
        """
        skill_name = GENRE_TO_SKILL_MAP.get(genre)
        if not skill_name:
            return {}

        skill_file = self.skills_dir / skill_name / "SKILL.md"
        if not skill_file.exists():
            logger.warning("Skill file not found: %s", skill_file)
            return {}

        try:
            content = skill_file.read_text(encoding="utf-8")
            return {"skill_name": skill_name, "content": content}
        except Exception as e:
            logger.error("Failed to read skill file %s: %s", skill_file, e)
            return {}

    def load_skill_references(self, genre: str) -> dict:
        """加载skill的references目录下所有文件内容。

        Returns:
            {"skill_name": str, "references": {filename: content, ...}} 或空dict
        """
        skill_name = GENRE_TO_SKILL_MAP.get(genre)
        if not skill_name:
            return {}

        ref_dir = self.skills_dir / skill_name / "references"
        if not ref_dir.exists():
            logger.warning("References dir not found: %s", ref_dir)
            return {}

        references: Dict[str, str] = {}
        try:
            for md_file in sorted(ref_dir.rglob("*.md")):
                rel_key = str(md_file.relative_to(ref_dir))
                references[rel_key] = md_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error("Failed to read references for %s: %s", skill_name, e)

        return {"skill_name": skill_name, "references": references}


skill_loader = SkillLoader()
