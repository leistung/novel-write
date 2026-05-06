"""ArchitectAgent - 架构师 Agent，负责小说设定和章节规划"""
from typing import Dict, Any, Optional, List, Tuple
from src.agents.base import BaseAgent, AgentContext
from src.prompts import ARCHITECT_PROMPTS
import os

class FoundationOutput:
    """基础设定输出"""
    def __init__(self, story_bible: str, volume_outline: str, book_rules: str, 
                 current_state: str, pending_hooks: str):
        self.story_bible = story_bible
        self.volume_outline = volume_outline
        self.book_rules = book_rules
        self.current_state = current_state
        self.pending_hooks = pending_hooks

class ChapterPlanOutput:
    """章节规划输出"""
    def __init__(self, chapter_outline: str, character_states: str, 
                 setting: str, plot_points: List[str]):
        self.chapter_outline = chapter_outline
        self.character_states = character_states
        self.setting = setting
        self.plot_points = plot_points

class OutlineImpactOutput:
    """大纲影响分析输出"""
    def __init__(self, major_impact: bool, minor_impact: bool, 
                 affected_chapters: List[int], suggestions: str, analysis: str):
        self.major_impact = major_impact
        self.minor_impact = minor_impact
        self.affected_chapters = affected_chapters
        self.suggestions = suggestions
        self.analysis = analysis

class BookStateOutput:
    """书籍状态更新输出"""
    def __init__(self, updated_state: str, updated_hooks: str, updated_ledger: str,
                 updated_subplots: str, updated_emotional_arcs: str, 
                 updated_character_matrix: str):
        self.updated_state = updated_state
        self.updated_hooks = updated_hooks
        self.updated_ledger = updated_ledger
        self.updated_subplots = updated_subplots
        self.updated_emotional_arcs = updated_emotional_arcs
        self.updated_character_matrix = updated_character_matrix

class ArchitectAgent(BaseAgent):
    """架构师 Agent - 负责小说设定生成、章节规划和状态更新"""
    
    def __init__(self, llm):
        super().__init__(llm)
        self._genre_features = self._load_genre_features()
    
    def _load_genre_features(self) -> Dict[str, Dict[str, Any]]:
        """加载题材特征配置"""
        return {
            "玄幻": {
                "description": "拥有完整的世界观和修炼体系，包含等级分明的修炼境界",
                "has_numerical_system": True,
                "has_power_scaling": True,
                "has_era_research": False
            },
            "仙侠": {
                "description": "以中国传统神话、道教文化和修仙体系为基础",
                "has_numerical_system": True,
                "has_power_scaling": True,
                "has_era_research": True
            },
            "都市": {
                "description": "以现代城市为背景，强调现实感和代入感",
                "has_numerical_system": False,
                "has_power_scaling": True,
                "has_era_research": False
            },
            "科幻": {
                "description": "以科学技术为基础，具有一定的科学依据和逻辑",
                "has_numerical_system": True,
                "has_power_scaling": True,
                "has_era_research": False
            },
            "历史": {
                "description": "以真实历史为背景，注重历史真实性",
                "has_numerical_system": False,
                "has_power_scaling": False,
                "has_era_research": True
            },
            "悬疑": {
                "description": "以解谜和推理为主要元素，强调逻辑思维",
                "has_numerical_system": False,
                "has_power_scaling": False,
                "has_era_research": False
            },
            "言情": {
                "description": "以爱情为主线，强调情感描写和人物关系",
                "has_numerical_system": False,
                "has_power_scaling": False,
                "has_era_research": False
            },
            "恐怖": {
                "description": "以营造恐怖氛围和心理恐惧为主要目标",
                "has_numerical_system": False,
                "has_power_scaling": False,
                "has_era_research": False
            },
            "武侠": {
                "description": "以中国传统武侠文化为基础，强调武功和侠义精神",
                "has_numerical_system": False,
                "has_power_scaling": True,
                "has_era_research": True
            }
        }
    
    def generate_foundation(self, book: Dict[str, Any], 
                           external_context: Optional[str] = None) -> FoundationOutput:
        """生成完整的基础设定
        
        Args:
            book: 书籍信息字典
            external_context: 外部创作指令
        
        Returns:
            FoundationOutput: 包含故事圣经、卷纲、书籍规则等的输出对象
        """
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        target_chapters = book.get('target_chapters', 100)
        chapter_word_count = book.get('chapter_words', 3000)
        title = book.get('title', '未知')
        language = book.get('language', 'zh')
        outline = book.get('outline', '')
        writing_style = book.get('writing_style', '')

        # 获取题材特征
        genre_feature = self._genre_features.get(genre, {})
        genre_body = genre_feature.get('description', '该题材的特征描述正在完善中...')

        # 构建上下文块
        context_block = f"\n\n## 外部指令\n{external_context}\n" if external_context else ""
        outline_block = f"\n\n## 小说大纲\n{outline}\n" if outline else ""
        writing_style_block = f"\n\n## 作者文笔参考\n{writing_style}\n" if writing_style else ""

        # 构建数值系统配置
        has_numerical = genre_feature.get('has_numerical_system', False)
        has_power = genre_feature.get('has_power_scaling', False)
        has_era = genre_feature.get('has_era_research', False)

        numerical_block = "- 有明确的数值/资源体系可追踪\n- 在 book_rules 中定义 numericalSystemOverrides" if has_numerical else "- 本题材无数值系统"
        power_block = "- 有明确的战力等级体系" if has_power else ""
        era_block = "- 需要年代考据支撑" if has_era else ""
        numerical_system_override = "numericalSystemOverrides:\n  hardCap: (根据设定确定)\n  resourceTypes: [(核心资源类型列表)]" if has_numerical else ""

        # 获取题材技能增强
        genre_enhancement = self.get_genre_enhancement(genre)

        # 构建系统提示词
        system_prompt = ARCHITECT_PROMPTS["generate_foundation"].format(
            genre=genre,
            platform=platform,
            target_chapters=target_chapters,
            chapter_word_count=chapter_word_count,
            genre_body=genre_body,
            context_block=context_block,
            outline_block=outline_block,
            writing_style_block=writing_style_block,
            numerical_block=numerical_block,
            power_block=power_block,
            era_block=era_block,
            numerical_system_override=numerical_system_override,
            genre_enhancement=genre_enhancement if genre_enhancement else ""
        )

        # 构建用户提示
        user_prompt = f"请为小说《{title}》生成完整的基础设定，包括故事圣经、卷纲、书籍规则、初始状态卡和伏笔池。"

        # 创建提示词并运行
        prompt = self.create_prompt(system_prompt, user_prompt)
        response = self.run_chain(prompt)

        # 解析输出
        return self._parse_foundation_response(response['content'])
    
    def plan_chapter(self, book: Dict[str, Any], chapter_num: int, 
                    current_state: str, previous_chapter_summary: str,
                    external_context: Optional[str] = None) -> ChapterPlanOutput:
        """规划章节内容
        
        Args:
            book: 书籍信息字典
            chapter_num: 章节号
            current_state: 当前状态
            previous_chapter_summary: 上一章摘要
            external_context: 外部创作指令
        
        Returns:
            ChapterPlanOutput: 章节规划输出对象
        """
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        chapter_word_count = book.get('chapter_words', 3000)
        title = book.get('title', '未知')
        outline = book.get('outline', '')
        writing_style = book.get('writing_style', '')

        # 获取题材技能增强
        genre_enhancement = self.get_genre_enhancement(genre)

        # 构建系统提示
        system_prompt = ARCHITECT_PROMPTS["plan_chapter"].format(
            chapter_num=chapter_num,
            title=title,
            genre=genre,
            platform=platform,
            chapter_word_count=chapter_word_count,
            current_state=current_state,
            previous_chapter_summary=previous_chapter_summary,
            outline=outline,
            writing_style=writing_style,
            external_context=external_context if external_context else '无',
            genre_enhancement=genre_enhancement if genre_enhancement else ""
        )

        # 构建用户提示
        user_prompt = f"请为第{chapter_num}章制定详细的内容规划。"

        # 创建提示词并运行
        prompt = self.create_prompt(system_prompt, user_prompt)
        response = self.run_chain(prompt)

        # 解析输出
        return self._parse_chapter_plan(response['content'])
    
    def analyze_outline_impact(self, old_outline: str, new_outline: str, 
                              book: Dict[str, Any], 
                              outline_context: Optional[str] = None) -> OutlineImpactOutput:
        """分析大纲变化对现有章节的影响
        
        Args:
            old_outline: 旧大纲
            new_outline: 新大纲
            book: 书籍信息字典
            outline_context: 大纲变更上下文
        
        Returns:
            OutlineImpactOutput: 大纲影响分析输出对象
        """
        title = book.get('title', '未知')
        genre = book.get('genre', '未知')

        # 构建系统提示
        system_prompt = ARCHITECT_PROMPTS["analyze_outline_impact"].format(
            title=title,
            genre=genre,
            old_outline=old_outline,
            new_outline=new_outline,
            outline_context=outline_context if outline_context else '无'
        )

        # 构建用户提示
        user_prompt = "请分析大纲变化对现有章节的影响，并提供具体的修改建议。"

        # 创建提示词并运行
        prompt = self.create_prompt(system_prompt, user_prompt)
        response = self.run_chain(prompt)

        # 解析输出
        return self._parse_outline_impact(response['content'])
    
    def update_book_state(self, book: Dict[str, Any], chapter_num: int, 
                         chapter_content: str, chapter_summary: str,
                         current_state: str, pending_hooks: str,
                         book_dir: Optional[str] = None) -> BookStateOutput:
        """更新书籍状态文件
        
        Args:
            book: 书籍信息字典
            chapter_num: 章节号
            chapter_content: 章节内容
            chapter_summary: 章节摘要
            current_state: 当前状态
            pending_hooks: 当前伏笔池
            book_dir: 书籍目录路径
        
        Returns:
            BookStateOutput: 书籍状态更新输出对象
        """
        genre = book.get('genre', '未知')
        title = book.get('title', '未知')

        # 获取题材技能增强
        genre_enhancement = self.get_genre_enhancement(genre)

        # 构建系统提示
        system_prompt = ARCHITECT_PROMPTS["update_book_state"].format(
            title=title,
            genre=genre,
            chapter_num=chapter_num,
            chapter_content=chapter_content,
            chapter_summary=chapter_summary,
            current_state=current_state,
            pending_hooks=pending_hooks,
            genre_enhancement=genre_enhancement if genre_enhancement else ""
        )

        # 构建用户提示
        user_prompt = "请根据本章内容更新书籍的状态文件。"

        # 创建提示词并运行
        prompt = self.create_prompt(system_prompt, user_prompt)
        response = self.run_chain(prompt)

        # 解析输出
        return self._parse_book_state(response['content'])
    
    def _parse_foundation_response(self, content: str) -> FoundationOutput:
        """解析基础设定响应"""
        sections = self._parse_sections(content, [
            'story_bible', 'volume_outline', 'book_rules', 
            'current_state', 'pending_hooks'
        ])
        
        return FoundationOutput(
            story_bible=sections['story_bible'],
            volume_outline=sections['volume_outline'],
            book_rules=sections['book_rules'],
            current_state=sections['current_state'],
            pending_hooks=sections['pending_hooks']
        )
    
    def _parse_chapter_plan(self, content: str) -> ChapterPlanOutput:
        """解析章节规划响应"""
        chapter_outline = content
        character_states = ""
        setting = ""
        plot_points = []

        # 尝试从输出中提取各个部分
        if "章节大纲" in content:
            chapter_outline = content.split("章节大纲")[1].split("人物状态")[0] if "人物状态" in content else content.split("章节大纲")[1]
        if "人物状态" in content:
            character_states = content.split("人物状态")[1].split("场景设定")[0] if "场景设定" in content else content.split("人物状态")[1]
        if "场景设定" in content:
            setting = content.split("场景设定")[1].split("情节点")[0] if "情节点" in content else content.split("场景设定")[1]
        if "情节点" in content:
            plot_points_section = content.split("情节点")[1]
            plot_points = [point.strip() for point in plot_points_section.split("\n") if point.strip()]

        return ChapterPlanOutput(
            chapter_outline=chapter_outline.strip(),
            character_states=character_states.strip(),
            setting=setting.strip(),
            plot_points=plot_points
        )
    
    def _parse_outline_impact(self, content: str) -> OutlineImpactOutput:
        """解析大纲影响分析响应"""
        major_impact = '重大影响' in content
        minor_impact = '轻微影响' in content and '重大影响' not in content
        
        # 提取受影响章节（简化处理）
        affected_chapters = []
        
        return OutlineImpactOutput(
            major_impact=major_impact,
            minor_impact=minor_impact,
            affected_chapters=affected_chapters,
            suggestions=content,
            analysis=content
        )
    
    def _parse_book_state(self, content: str) -> BookStateOutput:
        """解析书籍状态更新响应"""
        sections = self._parse_sections(content, [
            'current_state', 'pending_hooks', 'particle_ledger',
            'subplot_board', 'emotional_arcs', 'character_matrix'
        ])
        
        return BookStateOutput(
            updated_state=sections['current_state'],
            updated_hooks=sections['pending_hooks'],
            updated_ledger=sections['particle_ledger'],
            updated_subplots=sections['subplot_board'],
            updated_emotional_arcs=sections['emotional_arcs'],
            updated_character_matrix=sections['character_matrix']
        )
    
    def _parse_sections(self, content: str, section_names: List[str]) -> Dict[str, str]:
        """解析响应中的各个部分
        
        支持多种输出格式：
        1. === SECTION: name ===
        2. === SECTION: <name> ===
        3. ## name (Markdown二级标题)
        """
        sections = {name: '' for name in section_names}
        current_section = None
        
        for line in content.split('\n'):
            stripped_line = line.strip()
            
            # 格式1: === SECTION: name === 或 === SECTION: <name> ===
            if stripped_line.startswith('=== SECTION: '):
                # 提取section名称
                section_part = stripped_line.split('=== SECTION: ')[1].rsplit(' ===')[0].strip()
                # 移除可能的尖括号
                current_section = section_part.strip('<>').strip()
            
            # 格式2: ## name (Markdown二级标题)
            elif stripped_line.startswith('## ') and not stripped_line.startswith('### '):
                # 提取标题名称
                title_name = stripped_line[3:].strip().lower().replace(' ', '_')
                # 匹配已知的section名称
                for known_name in section_names:
                    if known_name.lower() in title_name or title_name in known_name.lower():
                        current_section = known_name
                        break
            
            # 如果找到了有效的section，并且当前行不是section标记行，则添加内容
            if current_section and current_section in sections:
                # 跳过section标记行本身
                if not stripped_line.startswith('=== SECTION: ') and not (stripped_line.startswith('## ') and not stripped_line.startswith('### ')):
                    sections[current_section] += line + '\n'
        
        # 清理内容，去除多余空行
        cleaned_sections = {}
        for k, v in sections.items():
            # 去除首尾空白
            cleaned = v.strip()
            # 去除多余空行
            lines = [line for line in cleaned.split('\n') if line.strip()]
            cleaned_sections[k] = '\n'.join(lines)
        
        # 如果所有section都为空，尝试直接提取内容（作为fallback）
        if all(not v for v in cleaned_sections.values()) and content.strip():
            # 尝试按Markdown标题分割
            for name in section_names:
                # 尝试查找各种可能的标题格式
                patterns = [
                    f'## {name}',
                    f'## {name.replace("_", " ")}',
                    f'=== SECTION: {name} ===',
                    f'=== SECTION: <{name}> ==='
                ]
                for pattern in patterns:
                    if pattern.lower() in content.lower():
                        # 找到该section，提取内容
                        parts = content.split(pattern)
                        if len(parts) > 1:
                            # 获取该section的内容（到下一个section之前）
                            section_content = parts[1]
                            # 检查是否有下一个section
                            for next_name in section_names:
                                next_patterns = [
                                    f'## {next_name}',
                                    f'## {next_name.replace("_", " ")}',
                                    f'=== SECTION: {next_name} ===',
                                    f'=== SECTION: <{next_name}> ==='
                                ]
                                for np in next_patterns:
                                    if np.lower() in section_content.lower():
                                        idx = section_content.lower().find(np.lower())
                                        section_content = section_content[:idx]
                                        break
                            cleaned_sections[name] = section_content.strip()
                        break
        
        return cleaned_sections
    
    def execute(self, context: AgentContext) -> Dict[str, Any]:
        """执行 Agent 核心逻辑
        
        Args:
            context: 执行上下文
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        task_type = context.get('task_type', 'plan_chapter')
        
        if task_type == 'generate_foundation':
            book = context.get('book', {})
            external_context = context.get('external_context')
            result = self.generate_foundation(book, external_context)
            return {
                'story_bible': result.story_bible,
                'volume_outline': result.volume_outline,
                'book_rules': result.book_rules,
                'current_state': result.current_state,
                'pending_hooks': result.pending_hooks
            }
        
        elif task_type == 'plan_chapter':
            book = context.get('book', {})
            chapter_num = context.chapter_num or 1
            current_state = context.get('current_state', '')
            previous_chapter_summary = context.get('previous_chapter_summary', '')
            external_context = context.get('external_context')
            result = self.plan_chapter(book, chapter_num, current_state, 
                                      previous_chapter_summary, external_context)
            return {
                'chapter_outline': result.chapter_outline,
                'character_states': result.character_states,
                'setting': result.setting,
                'plot_points': result.plot_points
            }
        
        elif task_type == 'analyze_outline_impact':
            old_outline = context.get('old_outline', '')
            new_outline = context.get('new_outline', '')
            book = context.get('book', {})
            outline_context = context.get('outline_context')
            result = self.analyze_outline_impact(old_outline, new_outline, book, outline_context)
            return {
                'major_impact': result.major_impact,
                'minor_impact': result.minor_impact,
                'affected_chapters': result.affected_chapters,
                'suggestions': result.suggestions,
                'analysis': result.analysis
            }
        
        elif task_type == 'update_book_state':
            book = context.get('book', {})
            chapter_num = context.chapter_num or 1
            chapter_content = context.get('chapter_content', '')
            chapter_summary = context.get('chapter_summary', '')
            current_state = context.get('current_state', '')
            pending_hooks = context.get('pending_hooks', '')
            book_dir = context.get('book_dir')
            result = self.update_book_state(book, chapter_num, chapter_content,
                                           chapter_summary, current_state, pending_hooks, book_dir)
            return {
                'updated_state': result.updated_state,
                'updated_hooks': result.updated_hooks,
                'updated_ledger': result.updated_ledger,
                'updated_subplots': result.updated_subplots,
                'updated_emotional_arcs': result.updated_emotional_arcs,
                'updated_character_matrix': result.updated_character_matrix
            }
        
        else:
            raise ValueError(f"未知任务类型: {task_type}")