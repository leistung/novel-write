"""WriterAgent - 写手 Agent，负责章节内容创作"""
from typing import Dict, Any, Optional, List
from src.agents.base import BaseAgent, AgentContext
from src.prompts import WRITER_PROMPTS
import os
import re
import logging

class WriteChapterInput:
    """写章节输入参数"""
    def __init__(self, book: Dict[str, Any], chapter_number: int, 
                 chapter_plan: Dict[str, Any], external_context: Optional[str] = None, 
                 word_count_override: Optional[int] = None, 
                 temperature_override: Optional[float] = None, 
                 book_dir: Optional[str] = None):
        self.book = book
        self.chapter_number = chapter_number
        self.chapter_plan = chapter_plan
        self.external_context = external_context
        self.word_count_override = word_count_override
        self.temperature_override = temperature_override
        self.book_dir = book_dir

class TokenUsage:
    """Token 使用统计"""
    def __init__(self, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens

class WriteChapterOutput:
    """写章节输出结果"""
    def __init__(self, chapter_number: int, title: str, content: str, 
                 word_count: int, pre_write_check: str, post_settlement: str, 
                 updated_state: str, updated_ledger: str, updated_hooks: str, 
                 chapter_summary: str, updated_subplots: str, 
                 updated_emotional_arcs: str, updated_character_matrix: str,
                 post_write_errors: List[Dict[str, Any]], 
                 post_write_warnings: List[Dict[str, Any]], 
                 token_usage: Optional[TokenUsage] = None):
        self.chapter_number = chapter_number
        self.title = title
        self.content = content
        self.word_count = word_count
        self.pre_write_check = pre_write_check
        self.post_settlement = post_settlement
        self.updated_state = updated_state
        self.updated_ledger = updated_ledger
        self.updated_hooks = updated_hooks
        self.chapter_summary = chapter_summary
        self.updated_subplots = updated_subplots
        self.updated_emotional_arcs = updated_emotional_arcs
        self.updated_character_matrix = updated_character_matrix
        self.post_write_errors = post_write_errors
        self.post_write_warnings = post_write_warnings
        self.token_usage = token_usage

class WriterAgent(BaseAgent):
    """写手 Agent - 负责章节内容创作、大纲检查和状态结算"""
    
    def __init__(self, llm):
        super().__init__(llm)
        self.logger = logging.getLogger('writer_agent')
        self.logger.setLevel(logging.DEBUG)
        
        # 添加控制台 handler（避免重复添加）
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def validate_chapter_outline(self, chapter_outline: str, book_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证章节大纲是否合理
        
        Args:
            chapter_outline: 章节大纲内容
            book_data: 书籍信息字典
        
        Returns:
            Dict[str, Any]: 包含 is_valid 和 suggestions 的验证结果
        """
        genre = book_data.get('genre', '未知')
        title = book_data.get('title', '未知')
        
        # 获取题材技能增强
        genre_enhancement = self.get_genre_enhancement(genre)

        # 构建系统提示
        system_prompt = WRITER_PROMPTS["check_chapter_outline"].format(
            genre=genre,
            title=title,
            chapter_outline=chapter_outline,
            genre_enhancement=genre_enhancement if genre_enhancement else ""
        )

        # 创建提示词
        prompt = self.create_prompt(system_prompt, "请评估上述章节大纲的合理性，并提供修改建议。")

        # 运行链
        response = self.run_chain(prompt)
        content = response['content']

        # 解析结果
        is_valid = "合理" in content or "可行" in content
        suggestions = content

        return {
            'is_valid': is_valid,
            'suggestions': suggestions
        }
    
    def write_chapter(self, input_data: WriteChapterInput) -> WriteChapterOutput:
        """生成章节内容
        
        Args:
            input_data: 写章节输入参数对象
        
        Returns:
            WriteChapterOutput: 写章节输出结果对象
        """
        book = input_data.book
        chapter_number = input_data.chapter_number
        chapter_plan = input_data.chapter_plan
        external_context = input_data.external_context
        word_count_override = input_data.word_count_override
        temperature_override = input_data.temperature_override
        book_dir = input_data.book_dir

        # 加载相关文件
        story_bible = self._read_file(book_dir, "story_bible.md") if book_dir else "(故事圣经尚未创建)"
        volume_outline = self._read_file(book_dir, "volume_outline.md") if book_dir else "(卷纲尚未创建)"
        current_state = self._read_file(book_dir, "current_state.md") if book_dir else "(当前状态尚未创建)"
        ledger = self._read_file(book_dir, "particle_ledger.md") if book_dir else "(资源账本尚未创建)"
        hooks = self._read_file(book_dir, "pending_hooks.md") if book_dir else "(伏笔池尚未创建)"
        chapter_summaries = self._read_file(book_dir, "chapter_summaries.md") if book_dir else "(章节摘要尚未创建)"
        subplot_board = self._read_file(book_dir, "subplot_board.md") if book_dir else "(支线进度板尚未创建)"
        emotional_arcs = self._read_file(book_dir, "emotional_arcs.md") if book_dir else "(情感弧线尚未创建)"
        character_matrix = self._read_file(book_dir, "character_matrix.md") if book_dir else "(角色交互矩阵尚未创建)"

        # 加载题材配置
        genre = book.get('genre', '未知')
        genre_profile = self._get_genre_profile(genre)
        book_rules = self._get_book_rules(book)

        # 获取题材技能增强
        genre_enhancement = self.get_genre_enhancement(genre)

        # 第一阶段：创意写作
        resolved_language = book.get('language', 'zh') or genre_profile.get('language', 'zh')
        creative_system_prompt = self._build_writer_system_prompt(
            book, genre_profile, book_rules, chapter_number, 
            resolved_language, genre_enhancement
        )

        # 构建用户提示
        creative_user_prompt = self._build_user_prompt({
            'chapter_number': chapter_number,
            'chapter_plan': chapter_plan,
            'story_bible': story_bible,
            'volume_outline': volume_outline,
            'current_state': current_state,
            'ledger': ledger if genre_profile.get('numericalSystem') else '',
            'hooks': hooks,
            'word_count': word_count_override or book.get('chapter_words', 3000),
            'external_context': external_context,
            'chapter_summaries': chapter_summaries,
            'subplot_board': subplot_board,
            'emotional_arcs': emotional_arcs,
            'character_matrix': character_matrix,
            'language': resolved_language
        })

        # 调用 LLM 进行创意写作
        creative_temperature = temperature_override or 0.7
        target_words = word_count_override or book.get('chapter_words', 3000)

        # 创建提示词
        prompt = self.create_prompt(creative_system_prompt, creative_user_prompt)

        # 打印日志 - 输出完整的提示词内容
        self.logger.info("=" * 80)
        self.logger.info(f"【章节{chapter_number}】开始生成")
        self.logger.info("=" * 80)
        self.logger.info("\n【系统提示词 (System Prompt)】")
        self.logger.info("-" * 60)
        self.logger.info(creative_system_prompt)
        self.logger.info("\n【用户提示词 (User Prompt)】")
        self.logger.info("-" * 60)
        self.logger.info(creative_user_prompt)
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"【章节{chapter_number}】提示词长度: 系统={len(creative_system_prompt)}字, 用户={len(creative_user_prompt)}字")
        self.logger.info("=" * 80 + "\n")

        # 运行链
        creative_response = self.run_chain(prompt, temperature=creative_temperature)
        content = creative_response['content']

        # 打印LLM返回的原始内容用于调试
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"【章节{chapter_number}】LLM原始返回内容")
        self.logger.info("-" * 60)
        self.logger.info(content)
        self.logger.info("=" * 80 + "\n")

        # 解析创意输出
        creative = self._parse_creative_output(chapter_number, content, target_words)

        # 第二阶段：状态结算
        settle_result = self._settle({
            'book': book,
            'genre_profile': genre_profile,
            'book_rules': book_rules,
            'chapter_number': chapter_number,
            'title': creative['title'],
            'content': creative['content'],
            'current_state': current_state,
            'ledger': ledger if genre_profile.get('numericalSystem') else '',
            'hooks': hooks,
            'chapter_summaries': chapter_summaries,
            'subplot_board': subplot_board,
            'emotional_arcs': emotional_arcs,
            'character_matrix': character_matrix,
            'volume_outline': volume_outline,
            'genre_enhancement': genre_enhancement
        })

        settlement = settle_result['settlement']

        # 写后验证
        rule_violations = self._validate_post_write(creative['content'], genre_profile, book_rules)

        post_write_errors = [v for v in rule_violations if v['severity'] == 'error']
        post_write_warnings = [v for v in rule_violations if v['severity'] == 'warning']

        # 构建输出
        return WriteChapterOutput(
            chapter_number=chapter_number,
            title=creative['title'],
            content=creative['content'],
            word_count=creative['word_count'],
            pre_write_check=creative['pre_write_check'],
            post_settlement=settlement['post_settlement'],
            updated_state=settlement['updated_state'],
            updated_ledger=settlement['updated_ledger'],
            updated_hooks=settlement['updated_hooks'],
            chapter_summary=settlement['chapter_summary'],
            updated_subplots=settlement['updated_subplots'],
            updated_emotional_arcs=settlement['updated_emotional_arcs'],
            updated_character_matrix=settlement['updated_character_matrix'],
            post_write_errors=post_write_errors,
            post_write_warnings=post_write_warnings
        )
    
    def _get_genre_profile(self, genre: str) -> Dict[str, Any]:
        """获取题材配置"""
        return {
            'name': genre,
            'language': 'zh',
            'numericalSystem': genre in ['玄幻', '仙侠', '科幻', '游戏'],
            'powerScaling': genre in ['玄幻', '仙侠', '都市', '科幻'],
            'eraResearch': genre in ['历史', '仙侠', '玄幻']
        }
    
    def _get_book_rules(self, book: Dict[str, Any]) -> Dict[str, Any]:
        """获取书籍规则"""
        return {
            'protagonist': {
                'name': '主角',
                'personalityLock': ['勇敢', '聪明', '坚韧'],
                'behavioralConstraints': ['不欺凌弱小', '坚守正义', '重视友情']
            },
            'genreLock': {
                'primary': book.get('genre', '未知'),
                'forbidden': ['恐怖', '色情']
            },
            'prohibitions': ['禁止血腥暴力', '禁止宣扬迷信', '禁止违背社会主义核心价值观']
        }
    
    def _build_writer_system_prompt(self, book: Dict[str, Any], 
                                   genre_profile: Dict[str, Any], 
                                   book_rules: Dict[str, Any], 
                                   chapter_number: int, 
                                   language: str,
                                   genre_enhancement: str) -> str:
        """构建作家系统提示"""
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        chapter_word_count = book.get('chapter_words', 3000)
        writing_style = book.get('writing_style', '')
        
        writing_style_block = f"\n\n## 作者文笔参考\n{writing_style}\n" if writing_style else ""
        
        # 计算最小字数要求
        min_word_count = int(chapter_word_count * 0.9)
        
        return WRITER_PROMPTS["write_chapter"].format(
            genre=genre,
            platform=platform,
            chapter_word_count=chapter_word_count,
            min_word_count=min_word_count,
            writing_style_block=writing_style_block,
            genre_enhancement=genre_enhancement if genre_enhancement else ""
        )
    
    def _build_user_prompt(self, params: Dict[str, Any]) -> str:
        """构建用户提示"""
        chapter_number = params['chapter_number']
        chapter_plan = params['chapter_plan']
        story_bible = params['story_bible']
        volume_outline = params['volume_outline']
        current_state = params['current_state']
        ledger = params['ledger']
        hooks = params['hooks']
        word_count = params['word_count']
        external_context = params['external_context']
        chapter_summaries = params['chapter_summaries']
        subplot_board = params['subplot_board']
        emotional_arcs = params['emotional_arcs']
        character_matrix = params['character_matrix']
        language = params['language']

        context_block = f"\n## 外部指令\n{external_context}\n" if external_context else ""
        ledger_block = f"\n## 资源账本\n{ledger}\n" if ledger else ""
        summaries_block = f"\n## 章节摘要\n{chapter_summaries}\n" if chapter_summaries != "(章节摘要尚未创建)" else ""
        subplot_block = f"\n## 支线进度板\n{subplot_board}\n" if subplot_board != "(支线进度板尚未创建)" else ""
        emotional_block = f"\n## 情感弧线\n{emotional_arcs}\n" if emotional_arcs != "(情感弧线尚未创建)" else ""
        matrix_block = f"\n## 角色交互矩阵\n{character_matrix}\n" if character_matrix != "(角色交互矩阵尚未创建)" else ""

        # 构建章节规划块
        chapter_plan_block = "\n## 章节规划\n"
        if isinstance(chapter_plan, dict):
            if 'chapter_outline' in chapter_plan:
                chapter_plan_block += f"### 章节大纲\n{chapter_plan['chapter_outline']}\n\n"
            if 'character_states' in chapter_plan:
                chapter_plan_block += f"### 人物状态\n{chapter_plan['character_states']}\n\n"
            if 'setting' in chapter_plan:
                chapter_plan_block += f"### 场景设定\n{chapter_plan['setting']}\n\n"
            if 'plot_points' in chapter_plan:
                chapter_plan_block += "### 情节点\n" + "\n".join([f"- {point}" for point in chapter_plan['plot_points']]) + "\n\n"
        else:
            chapter_plan_block += str(chapter_plan) + "\n\n"

        if language == "en":
            return f"""Write chapter {chapter_number}.
{context_block}
{chapter_plan_block}
## Current State
{current_state}
{ledger_block}
## Plot Threads
{hooks}
{summaries_block}{subplot_block}{emotional_block}{matrix_block}

## Worldbuilding
{story_bible}

## Volume Outline (Hard Constraint)
{volume_outline}

Requirements:
- Chapter body must be at least {word_count} words
- Output PRE_WRITE_CHECK first, then the chapter
- Output only PRE_WRITE_CHECK, CHAPTER_TITLE, and CHAPTER_CONTENT blocks"""
        else:
            return f"""请续写第{chapter_number}章。
{context_block}
{chapter_plan_block}
## 当前状态卡
{current_state}
{ledger_block}
## 伏笔池
{hooks}
{summaries_block}{subplot_block}{emotional_block}{matrix_block}

## 世界观设定
{story_bible}

## 卷纲（硬约束）
{volume_outline}

要求：
- 正文严格控制在{word_count}字左右，误差不超过10%
- 先输出写作自检表，再写正文
- 只需输出 PRE_WRITE_CHECK、CHAPTER_TITLE、CHAPTER_CONTENT 三个区块"""
    
    def _parse_creative_output(self, chapter_number: int, content: str, 
                              target_words: int = 3000) -> Dict[str, Any]:
        """解析创意输出"""
        title = f"第{chapter_number}章"
        chapter_content = content

        content = content.replace('\r\n', '\n')
        title_match = re.search(r'CHAPTER_TITLE\s*\n\s*(.+?)(?:\n|$)', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()

        content_match = re.search(r'CHAPTER_CONTENT\s*\n([\s\S]+)$', content, re.IGNORECASE)
        if content_match:
            chapter_content = content_match.group(1).strip()

        word_count = len(chapter_content)
        min_word_count = int(target_words * 0.9)
        
        if word_count < min_word_count:
            return {
                'title': title,
                'content': chapter_content,
                'word_count': word_count,
                'pre_write_check': f"写作自检表：本章字数不足，要求{target_words}字，实际{word_count}字",
                'error': f"字数不足"
            }
        else:
            return {
                'title': title,
                'content': chapter_content,
                'word_count': word_count,
                'pre_write_check': f"写作自检表：本章符合卷纲要求，字数{word_count}字"
            }
    
    def _settle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """状态结算 - 分为Observer和Reflector两个阶段"""
        book = params['book']
        genre_profile = params['genre_profile']
        chapter_number = params['chapter_number']
        title = params['title']
        content = params['content']
        current_state = params['current_state']
        ledger = params['ledger']
        hooks = params['hooks']
        chapter_summaries = params['chapter_summaries']
        subplot_board = params['subplot_board']
        emotional_arcs = params['emotional_arcs']
        character_matrix = params['character_matrix']
        volume_outline = params['volume_outline']
        genre_enhancement = params.get('genre_enhancement', '')
        
        resolved_language = book.get('language', 'zh') or genre_profile.get('language', 'zh')
        
        # 第一阶段：Observer - 从章节中提取所有事实变化
        observer_system = self._build_observer_system_prompt(book, genre_profile, resolved_language)
        observer_user = self._build_observer_user_prompt(chapter_number, title, content, resolved_language)
        
        # 创建提示词
        observer_prompt = self.create_prompt(observer_system, observer_user)
        
        # 运行链
        observer_response = self.run_chain(observer_prompt)
        observations = observer_response['content']
        
        # 第二阶段：Reflector - 将观察结果合并到状态文件中
        settler_system = self._build_settler_system_prompt(book, genre_profile, resolved_language, genre_enhancement)
        settler_user = self._build_settler_user_prompt(
            chapter_number, title, content, current_state, ledger, hooks,
            chapter_summaries, subplot_board, emotional_arcs, character_matrix,
            volume_outline, observations
        )
        
        # 创建提示词
        settler_prompt = self.create_prompt(settler_system, settler_user)
        
        # 运行链
        settler_response = self.run_chain(settler_prompt)
        
        # 解析结算输出
        return {
            'settlement': self._parse_settlement_output(settler_response['content'], genre_profile)
        }
    
    def _build_observer_system_prompt(self, book: Dict[str, Any], 
                                     genre_profile: Dict[str, Any], 
                                     language: str) -> str:
        """构建Observer系统提示"""
        is_english = language == "en"
        lang_prefix = "【LANGUAGE OVERRIDE】ALL output MUST be in English.\n\n" if is_english else ""
        
        return f"""{lang_prefix}{WRITER_PROMPTS['observer']}"""
    
    def _build_observer_user_prompt(self, chapter_number: int, title: str, 
                                   content: str, language: str) -> str:
        """构建Observer用户提示"""
        if language == "en":
            return f"""Please extract all factual changes from Chapter {chapter_number}: "{title}"\n\n{content}"""
        else:
            return f"""请从第{chapter_number}章「{title}」中提取所有事实性变化。\n\n{content}"""
    
    def _build_settler_system_prompt(self, book: Dict[str, Any], 
                                    genre_profile: Dict[str, Any], 
                                    language: str,
                                    genre_enhancement: str) -> str:
        """构建Settler系统提示"""
        is_english = language == "en"
        lang_prefix = "【LANGUAGE OVERRIDE】ALL output MUST be in English.\n\n" if is_english else ""
        
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        numerical_block = ""
        
        if genre_profile.get('numericalSystem'):
            numerical_block = "\n- 本题材有数值/资源体系，必须追踪资源变动"
        else:
            numerical_block = "\n- 本题材无数值系统"

        hook_rules = """\n## 伏笔追踪规则\n- 新伏笔：新增 hook_id，标注起始章\n- 推进伏笔：更新状态\n- 回收伏笔：状态改为已回收"""

        book_title = book.get('title', '未知')
        genre_name = genre_profile.get('name', genre)
        
        return f"""{lang_prefix}{WRITER_PROMPTS['settler'].format(
            book_title=book_title,
            genre_name=genre_name,
            genre=genre,
            platform=platform,
            numerical_block=numerical_block,
            hook_rules=hook_rules,
            genre_enhancement=genre_enhancement if genre_enhancement else ""
        )}"""
    
    def _build_settler_user_prompt(self, chapter_number: int, title: str, content: str,
                                   current_state: str, ledger: str, hooks: str,
                                   chapter_summaries: str, subplot_board: str,
                                   emotional_arcs: str, character_matrix: str,
                                   volume_outline: str, observations: str) -> str:
        """构建Settler用户提示"""
        ledger_block = f"\n## 当前资源账本\n{ledger}\n" if ledger else ""
        summaries_block = f"\n## 已有章节摘要\n{chapter_summaries}\n" if chapter_summaries != "(章节摘要尚未创建)" else ""
        subplot_block = f"\n## 当前支线进度板\n{subplot_board}\n" if subplot_board != "(支线进度板尚未创建)" else ""
        emotional_block = f"\n## 当前情感弧线\n{emotional_arcs}\n" if emotional_arcs != "(情感弧线尚未创建)" else ""
        matrix_block = f"\n## 当前角色交互矩阵\n{character_matrix}\n" if character_matrix != "(角色交互矩阵尚未创建)" else ""
        
        return f"""请分析第{chapter_number}章「{title}」的正文，更新所有追踪文件。\n\n## 观察日志\n{observations}\n\n## 本章正文\n{content}\n\n## 当前状态卡\n{current_state}{ledger_block}## 当前伏笔池\n{hooks}{summaries_block}{subplot_block}{emotional_block}{matrix_block}## 卷纲\n{volume_outline}\n\n请按照 === TAG === 格式输出结算结果。"""
    
    def _parse_settlement_output(self, content: str, genre_profile: Dict[str, Any]) -> Dict[str, Any]:
        """解析结算输出"""
        def extract_block(tag: str) -> str:
            pattern = rf'=== {tag} ===\s*(.*?)(?==== |$)'
            match = re.search(pattern, content, re.DOTALL)
            return match.group(1).strip() if match else ""
        
        return {
            'post_settlement': extract_block('POST_SETTLEMENT'),
            'updated_state': extract_block('UPDATED_STATE'),
            'updated_ledger': extract_block('UPDATED_LEDGER') if genre_profile.get('numericalSystem') else "",
            'updated_hooks': extract_block('UPDATED_HOOKS'),
            'chapter_summary': extract_block('CHAPTER_SUMMARY'),
            'updated_subplots': extract_block('UPDATED_SUBPLOTS'),
            'updated_emotional_arcs': extract_block('UPDATED_EMOTIONAL_ARCS'),
            'updated_character_matrix': extract_block('UPDATED_CHARACTER_MATRIX')
        }
    
    def _read_file(self, book_dir: str, filename: str) -> str:
        """读取文件内容"""
        if not book_dir:
            return f"({filename.replace('.md', '').replace('_', ' ')}尚未创建)"
        
        file_path = os.path.join(book_dir, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return f"({filename.replace('.md', '').replace('_', ' ')}读取失败)"
        return f"({filename.replace('.md', '').replace('_', ' ')}尚未创建)"
    
    def _validate_post_write(self, content: str, genre_profile: Dict[str, Any], 
                           book_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """写后验证"""
        return []
    
    def execute(self, context: AgentContext) -> Dict[str, Any]:
        """执行 Agent 核心逻辑
        
        Args:
            context: 执行上下文
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        task_type = context.get('task_type', 'write_chapter')
        
        if task_type == 'validate_outline':
            chapter_outline = context.get('chapter_outline', '')
            book_data = context.get('book', {})
            return self.validate_chapter_outline(chapter_outline, book_data)
        
        elif task_type == 'write_chapter':
            book = context.get('book', {})
            chapter_number = context.chapter_num or 1
            chapter_plan = context.get('chapter_plan', {})
            external_context = context.get('external_context')
            word_count_override = context.get('word_count_override')
            temperature_override = context.get('temperature_override')
            book_dir = context.get('book_dir')
            
            input_data = WriteChapterInput(
                book=book,
                chapter_number=chapter_number,
                chapter_plan=chapter_plan,
                external_context=external_context,
                word_count_override=word_count_override,
                temperature_override=temperature_override,
                book_dir=book_dir
            )
            
            output = self.write_chapter(input_data)
            
            return {
                'content': output.content,
                'word_count': output.word_count,
                'summary': output.chapter_summary,
                'title': output.title,
                'updated_state': output.updated_state,
                'updated_hooks': output.updated_hooks,
                'updated_ledger': output.updated_ledger,
                'updated_subplots': output.updated_subplots,
                'updated_emotional_arcs': output.updated_emotional_arcs,
                'updated_character_matrix': output.updated_character_matrix,
                'errors': output.post_write_errors,
                'warnings': output.post_write_warnings
            }
        
        else:
            raise ValueError(f"未知任务类型: {task_type}")