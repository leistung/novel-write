"""架构师Agent - 使用 prompts 模板系统"""
import re
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent, AgentResult
from db.crud import get_book, update_book, get_chapter_by_number


class ArchitectAgent(BaseAgent):
    """架构师Agent - 负责小说整体架构规划
    
    Public Methods (4个):
    1. generate_foundation - 生成书籍基础设定
    2. plan_chapter - 规划章节内容
    3. analyze_outline_impact - 分析大纲变动影响
    4. update_book_state - 更新书籍状态
    """
    
    def __init__(self):
        super().__init__("Architect")
    
    async def execute(self, task: str, **kwargs) -> AgentResult:
        """执行架构师任务"""
        if task == "generate_foundation":
            return await self.generate_foundation(**kwargs)
        elif task == "plan_chapter":
            return await self.plan_chapter(**kwargs)
        elif task == "analyze_outline_impact":
            return await self.analyze_outline_impact(**kwargs)
        elif task == "update_book_state":
            return await self.update_book_state(**kwargs)
        else:
            return self.failure(task, f"未知任务: {task}")
    
    # ==================== PUBLIC METHODS ====================
    
    async def generate_foundation(
        self,
        book_data: Dict[str, Any],
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】生成书籍基础设定"""
        title = book_data.get("title", "")
        genre = book_data.get("genre", "")
        platform = book_data.get("platform", "通用")
        outline = book_data.get("outline", "")
        target_chapters = book_data.get("target_chapters", 100)
        chapter_words = book_data.get("chapter_words", 3000)
        
        try:
            # 使用 prompts 渲染提示词
            system_prompt, user_prompt = self._render_prompt("architect/foundation", {
                "genre": genre,
                "theme": outline[:500] if outline else f"{genre}题材小说",
                "style": "",
                "target_length": f"{target_chapters}章，每章{chapter_words}字"
            })
            
            # 添加题材专家知识
            system_prompt = self._build_system_prompt(system_prompt, genre)
            
            # 添加用户大纲到 user_prompt
            user_prompt = f"""{user_prompt}

## 小说基本信息
- 书名：{title}
- 题材：{genre}
- 平台：{platform}
- 目标章数：{target_chapters}章
- 每章字数：{chapter_words}字

## 用户大纲
{outline}

## 题材特征
{self._get_genre_body(genre)}

请按照系统提示词中的格式要求，生成完整的基础设定。
"""
            
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=8000
            )
            
            # 解析生成的内容
            parsed = self._parse_foundation_output(response.content)
            
            return self.success(
                task="generate_foundation",
                data={
                    "story_bible": parsed.get("story_bible", ""),
                    "volume_outline": parsed.get("volume_outline", ""),
                    "book_rules": parsed.get("book_rules", ""),
                    "current_state": parsed.get("current_state", ""),
                    "pending_hooks": parsed.get("pending_hooks", ""),
                    "character_matrix": parsed.get("character_matrix", ""),
                    "emotional_arcs": parsed.get("emotional_arcs", ""),
                    "raw_content": response.content
                },
                feedback="成功生成书籍基础设定",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("generate_foundation", str(e))
    
    async def plan_chapter(
        self,
        book_id: int,
        chapter_num: int,
        chapter_type: str = "normal",
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】规划章节内容"""
        if db is None:
            return self.failure("plan_chapter", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("plan_chapter", f"书籍不存在: {book_id}")
        
        # 获取前一章摘要
        prev_summary = await self._get_previous_chapter_summary(db, book_id, chapter_num)
        
        # 自动判断章节类型
        if chapter_type == "auto":
            chapter_type = self._determine_chapter_type(
                chapter_num, book.target_chapters
            )
        
        # 章节类型说明
        type_instructions = {
            "opening": "这是黄金三章之一，必须快速抛出核心冲突，展示金手指，建立主角形象",
            "volume_start": "这是新卷的开始，需要承上启下，引入新的冲突或目标",
            "volume_end": "这是卷的结尾，需要有阶段性高潮，回收本卷伏笔",
            "pre_climax": "这是高潮前的铺垫，需要积蓄张力，为高潮做准备",
            "climax": "这是高潮章节，需要大场面，强冲突，情绪爆发",
            "ending": "这是结局章节，需要收束主线，回收核心伏笔，给出满意结局",
            "normal": "普通章节，推进剧情，保持节奏"
        }
        
        try:
            # 使用 prompts 渲染提示词
            system_prompt, user_prompt = self._render_prompt("architect/plan_chapter", {
                "title": book.title,
                "genre": book.genre,
                "platform": book.platform,
                "chapter_num": chapter_num,
                "chapter_type": f"{chapter_type} - {type_instructions.get(chapter_type, '普通章节')}",
                "prev_summary": prev_summary if prev_summary != "这是第一章" else "",
                "current_state": book.current_state or "",
                "outline": book.outline or ""
            })
            
            # 添加题材专家知识
            system_prompt = self._build_system_prompt(system_prompt, book.genre)
            
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=4000
            )
            
            return self.success(
                task="plan_chapter",
                data={
                    "chapter_plan": response.content,
                    "chapter_type": chapter_type,
                    "chapter_num": chapter_num
                },
                feedback=f"成功规划第{chapter_num}章({chapter_type})",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("plan_chapter", str(e))
    
    async def analyze_outline_impact(
        self,
        book_id: int,
        new_outline: str,
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】分析大纲变动影响"""
        if db is None:
            return self.failure("analyze_outline_impact", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("analyze_outline_impact", f"书籍不存在: {book_id}")
        
        old_outline = book.outline or "暂无大纲"
        
        try:
            # 使用 prompts 渲染提示词
            system_prompt, user_prompt = self._render_prompt("architect/analyze_impact", {
                "title": book.title,
                "genre": book.genre,
                "old_outline": old_outline,
                "new_outline": new_outline
            })
            
            # 添加题材专家知识
            system_prompt = self._build_system_prompt(system_prompt, book.genre)
            
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=4000
            )
            
            # 解析影响分析
            impact = self._parse_impact_analysis(response.content)
            
            return self.success(
                task="analyze_outline_impact",
                data={
                    "impact_analysis": response.content,
                    "affected_chapters": impact.get("affected_chapters", []),
                    "severity": impact.get("severity", "low"),
                    "recommendations": impact.get("recommendations", [])
                },
                feedback="成功分析大纲变动影响",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("analyze_outline_impact", str(e))
    
    async def update_book_state(
        self,
        book_id: int,
        chapter_num: int,
        chapter_content: str,
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】更新书籍状态"""
        if db is None:
            return self.failure("update_book_state", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("update_book_state", f"书籍不存在: {book_id}")
        
        try:
            # 使用 prompts 渲染提示词
            system_prompt, user_prompt = self._render_prompt("architect/update_state", {
                "title": book.title,
                "genre": book.genre,
                "chapter_num": chapter_num,
                "current_state": book.current_state or "",
                "pending_hooks": book.pending_hooks or "",
                "chapter_content": chapter_content
            })
            
            # 添加题材专家知识
            system_prompt = self._build_system_prompt(system_prompt, book.genre)
            
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=4000
            )
            
            # 解析状态更新
            state_updates = self._parse_state_updates(response.content)
            
            # 更新数据库
            update_data = {
                "current_state": state_updates.get("current_state", book.current_state),
                "pending_hooks": state_updates.get("pending_hooks", book.pending_hooks),
                "character_matrix": state_updates.get("character_matrix", book.character_matrix),
                "emotional_arcs": state_updates.get("emotional_arcs", book.emotional_arcs),
                "subplot_board": state_updates.get("subplot_board", book.subplot_board)
            }
            
            await update_book(db, book_id, update_data)
            
            return self.success(
                task="update_book_state",
                data={
                    "updates": state_updates,
                    "chapter_num": chapter_num
                },
                feedback=f"成功更新第{chapter_num}章后的书籍状态",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("update_book_state", str(e))
    
    # ==================== PRIVATE METHODS ====================
    
    def _get_genre_body(self, genre: str) -> str:
        """【Private】获取题材特征描述"""
        genre_bodies = {
            "玄幻": "以东方神话传说为背景，强调修炼升级体系，主角逆袭成长",
            "奇幻": "以魔法异世界为背景，强调冒险探索，种族文化多样",
            "武侠": "以江湖武林为背景，强调武功招式，侠义精神",
            "仙侠": "以仙魔妖狐为题材，强调道心修为，有飘逸出尘的感觉",
            "都市": "现代都市背景，贴近生活，容易产生代入感",
            "现实": "反映现实社会问题，注重人物内心描写",
            "历史": "以历史为背景，注重史实考证，人物重塑",
            "军事": "以军事战争为题材，强调战术战略",
            "游戏": "以游戏世界为背景，强调系统设定，升级打怪",
            "体育": "以体育运动为题材，强调竞技精神，成长励志",
            "科幻": "以科技为核心，展望未来，注重想象力和逻辑性",
            "悬疑灵幻": "营造恐怖氛围，注重心理描写，悬念迭起",
            "轻小说": "轻松幽默，日常系，萌元素",
            "短篇": "结构紧凑，故事完整，精炼表达",
            "诸天无限": "多元宇宙，副本设计，无限流",
            "古代言情": "古代背景，宫廷斗争，甜宠虐恋",
            "现代言情": "现代都市爱情，职场恋情",
            "玄幻言情": "修仙背景，虐恋情深",
            "悬疑推理": "案件推理，逻辑分析",
            "浪漫青春": "校园生活，青春成长",
            "仙侠奇缘": "仙侠爱情，三世情缘",
            "科幻空间": "星际恋爱，末世生存",
            "游戏竞技": "电竞爱情，竞技热血"
        }
        return genre_bodies.get(genre, "网络小说通用题材特征")
    
    async def _get_previous_chapter_summary(
        self,
        db: AsyncSession,
        book_id: int,
        chapter_num: int
    ) -> str:
        """【Private】获取前一章摘要"""
        if chapter_num <= 1:
            return "这是第一章"
        
        prev_chapter = await get_chapter_by_number(db, book_id, chapter_num - 1)
        if prev_chapter and prev_chapter.content:
            return prev_chapter.content[:500] + "..."
        return "暂无前一章"
    
    def _determine_chapter_type(
        self,
        chapter_num: int,
        total_chapters: int
    ) -> str:
        """【Private】根据章节位置自动判断章节类型"""
        # 黄金三章
        if chapter_num <= 3:
            return "opening"
        
        # 结局章节
        if chapter_num >= total_chapters - 2:
            return "ending"
        
        # 高潮章节（假设在70%位置）
        climax_start = int(total_chapters * 0.68)
        climax_end = int(total_chapters * 0.75)
        if climax_start <= chapter_num <= climax_end:
            if chapter_num == climax_start:
                return "pre_climax"
            return "climax"
        
        # 卷边界（假设每20章一卷）
        if chapter_num % 20 == 1:
            return "volume_start"
        if chapter_num % 20 == 0:
            return "volume_end"
        
        return "normal"
    
    def _parse_foundation_output(self, content: str) -> Dict[str, str]:
        """【Private】解析基础设定输出，支持 JSON 和 SECTION 两种格式"""
        import json
        import re
        
        # 尝试 JSON 格式解析（prompt 模板要求 JSON 输出）
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                # 将 JSON 字段映射到系统期望的字段
                result = {}
                
                # story_bible: 世界观 + 设定
                setting = data.get("setting", {})
                world_parts = []
                if setting.get("era"):
                    world_parts.append(f"时代背景：{setting['era']}")
                if setting.get("location"):
                    world_parts.append(f"主要地点：{setting['location']}")
                if setting.get("rules"):
                    world_parts.append("世界规则：\n" + "\n".join(f"- {r}" for r in setting["rules"]))
                result["story_bible"] = "\n\n".join(world_parts) if world_parts else ""
                
                # 补充 synopsis 到 story_bible
                if data.get("synopsis"):
                    result["story_bible"] = f"## 故事梗概\n{data['synopsis']}\n\n" + result["story_bible"]
                if data.get("logline"):
                    result["story_bible"] = f"## 一句话简介\n{data['logline']}\n\n" + result["story_bible"]
                
                # character_matrix: 角色设定
                characters = data.get("characters", [])
                if characters:
                    char_lines = []
                    for c in characters:
                        char_lines.append(f"### {c.get('name', '未知')}（{c.get('role', '未定')}）")
                        if c.get("personality"):
                            char_lines.append(f"性格：{c['personality']}")
                        if c.get("goals"):
                            char_lines.append(f"目标：{'、'.join(c['goals'])}")
                        char_lines.append("")
                    result["character_matrix"] = "\n".join(char_lines)
                else:
                    result["character_matrix"] = ""
                
                # volume_outline: 幕结构/主线剧情
                acts = data.get("acts", [])
                if acts:
                    act_lines = []
                    for a in acts:
                        act_lines.append(f"## 第{a.get('act_number', '?')}幕：{a.get('title', '')}")
                        if a.get("summary"):
                            act_lines.append(a["summary"])
                        if a.get("key_events"):
                            act_lines.append("关键事件：")
                            for e in a["key_events"]:
                                act_lines.append(f"- {e}")
                        act_lines.append("")
                    result["volume_outline"] = "\n".join(act_lines)
                else:
                    result["volume_outline"] = ""
                
                # 其他字段留空（当前 prompt 不生成这些）
                result["book_rules"] = ""
                result["current_state"] = ""
                result["pending_hooks"] = ""
                result["emotional_arcs"] = ""
                
                return result
            except (json.JSONDecodeError, KeyError, TypeError):
                pass  # JSON 解析失败，尝试 SECTION 格式
        
        # 回退到 SECTION 格式解析
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('=== SECTION:'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.replace('=== SECTION:', '').replace('===', '').strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _parse_impact_analysis(self, content: str) -> Dict[str, Any]:
        """【Private】解析影响分析输出"""
        impact = {
            "severity": "low",
            "affected_chapters": [],
            "recommendations": []
        }
        
        # 简单解析严重程度
        if "high" in content.lower() or "严重" in content:
            impact["severity"] = "high"
        elif "medium" in content.lower() or "中等" in content:
            impact["severity"] = "medium"
        
        return impact
    
    def _parse_state_updates(self, content: str) -> Dict[str, str]:
        """【Private】解析状态更新输出"""
        return self._parse_foundation_output(content)
