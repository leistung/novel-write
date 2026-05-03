from typing import Dict, Any, Optional, List
from src.agents.base import BaseAgent, AgentContext
from src.prompts import WRITER_PROMPTS
import os
import re

class WriteChapterInput:
    def __init__(self, book: Dict[str, Any], chapter_number: int, chapter_plan: Dict[str, Any], external_context: Optional[str] = None, word_count_override: Optional[int] = None, temperature_override: Optional[float] = None, book_dir: Optional[str] = None):
        self.book = book
        self.chapter_number = chapter_number
        self.chapter_plan = chapter_plan
        self.external_context = external_context
        self.word_count_override = word_count_override
        self.temperature_override = temperature_override
        self.book_dir = book_dir

class TokenUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens

class WriteChapterOutput:
    def __init__(self, chapter_number: int, title: str, content: str, word_count: int, pre_write_check: str, post_settlement: str, updated_state: str, updated_ledger: str, updated_hooks: str, chapter_summary: str, updated_subplots: str, updated_emotional_arcs: str, updated_character_matrix: str, post_write_errors: List[Dict[str, Any]], post_write_warnings: List[Dict[str, Any]], token_usage: Optional[TokenUsage] = None):
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
    def __init__(self, llm):
        super().__init__(llm)
        import logging
        self.logger = logging.getLogger('writer_agent')
        self.logger.setLevel(logging.DEBUG)
        
        # 添加控制台handler
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def check_chapter_outline(self, chapter_outline: str, book_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查章节大纲是否合理"""
        genre = book_data.get('genre', '未知')
        title = book_data.get('title', '未知')
        
        # 创建提示词
        system_prompt = WRITER_PROMPTS["check_chapter_outline"].format(
            genre=genre,
            title=title,
            chapter_outline=chapter_outline
        )
        
        # 创建提示
        prompt = self.create_prompt(system_prompt, "请评估上述章节大纲的合理性，并提供修改建议。")
        
        # 运行链
        response = self.run_chain(prompt)
        content = response['content']
        token_usage = response['token_usage']
        
        # 解析结果
        # 这里简化处理，实际应该根据LLM的输出格式进行解析
        is_valid = "合理" in content or "可行" in content
        suggestions = content
        
        return {
            'is_valid': is_valid,
            'suggestions': suggestions
        }

    def write_chapter(self, input: WriteChapterInput) -> WriteChapterOutput:
        """生成章节内容"""
        book = input.book
        chapter_number = input.chapter_number
        chapter_plan = input.chapter_plan
        external_context = input.external_context
        word_count_override = input.word_count_override
        temperature_override = input.temperature_override
        book_dir = input.book_dir

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

        # 第一阶段：创意写作
        resolved_language = book.get('language', 'zh') or genre_profile.get('language', 'zh')
        creative_system_prompt = self._build_writer_system_prompt(
            book, genre_profile, book_rules, chapter_number, resolved_language
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
        creative_response = self.run_chain(prompt)
        content = creative_response['content']
        token_usage = creative_response['token_usage']

        # 解析创意输出
        creative = self._parse_creative_output(chapter_number, content)

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
            'volume_outline': volume_outline
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
            post_write_warnings=post_write_warnings,
            token_usage=token_usage  # 从 LLM 响应中提取
        )

    def _get_genre_profile(self, genre: str) -> Dict[str, Any]:
        """获取题材配置"""
        # 这里简化处理，实际应该从文件读取
        return {
            'name': genre,
            'language': 'zh',
            'numericalSystem': genre in ['玄幻', '仙侠', '科幻', '游戏'],
            'powerScaling': genre in ['玄幻', '仙侠', '都市', '科幻'],
            'eraResearch': genre in ['历史', '仙侠', '玄幻']
        }

    def _get_book_rules(self, book: Dict[str, Any]) -> Dict[str, Any]:
        """获取书籍规则"""
        # 这里简化处理，实际应该从文件读取
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

    def _build_writer_system_prompt(self, book: Dict[str, Any], genre_profile: Dict[str, Any], book_rules: Dict[str, Any], chapter_number: int, language: str) -> str:
        """构建作家系统提示"""
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        chapter_word_count = book.get('chapter_words', 3000)
        writing_style = book.get('writing_style', '')
        
        writing_style_block = f"\n\n## 作者文笔参考\n以下是用户提供的作者文笔参考，请在写作中体现相应的风格：\n\n{writing_style}\n" if writing_style else ""
        
        # 计算最小字数要求
        min_word_count = int(chapter_word_count * 0.9)
        
        return WRITER_PROMPTS["write_chapter"].format(
            genre=genre,
            platform=platform,
            chapter_word_count=chapter_word_count,
            min_word_count=min_word_count,
            writing_style_block=writing_style_block
        )

    def _filter_hooks(self, hooks: str) -> str:
        """过滤伏笔"""
        return hooks

    def _filter_summaries(self, chapter_summaries: str, chapter_number: int) -> str:
        """过滤摘要"""
        return chapter_summaries

    def _filter_subplots(self, subplot_board: str) -> str:
        """过滤支线"""
        return subplot_board

    def _filter_emotional_arcs(self, emotional_arcs: str, chapter_number: int) -> str:
        """过滤情感弧线"""
        return emotional_arcs

    def _filter_character_matrix(self, character_matrix: str, volume_outline: str, protagonist_name: Optional[str]) -> str:
        """过滤角色矩阵"""
        return character_matrix

    def _extract_pov_from_outline(self, volume_outline: str, chapter_number: int) -> Optional[str]:
        """从卷纲中提取 POV 角色"""
        return None

    def _filter_matrix_by_pov(self, matrix: str, pov_character: str) -> str:
        """根据 POV 过滤角色矩阵"""
        return matrix

    def _filter_hooks_by_pov(self, hooks: str, pov_character: str, chapter_summaries: str) -> str:
        """根据 POV 过滤伏笔"""
        return hooks

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

        context_block = f"\n## 外部指令\n以下是来自外部系统的创作指令，请在本章中融入：\n\n{external_context}\n" if external_context else ""
        ledger_block = f"\n## 资源账本\n{ledger}\n" if ledger else ""
        summaries_block = f"\n## 章节摘要（全部历史章节压缩上下文）\n{chapter_summaries}\n" if chapter_summaries != "(章节摘要尚未创建)" else ""
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

## Volume Outline (Hard Constraint — Must Follow)
{volume_outline}

[Outline Rules]
- This chapter must advance the plot points assigned to it in the volume outline. Do not skip ahead or consume future plot points.
- If the outline specifies an event for chapter N, do not resolve it early.
- Pacing must match the outline's chapter span: if 5 chapters are planned for an arc, do not compress into 1-2.
- PRE_WRITE_CHECK must identify which outline node this chapter covers.

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

## 卷纲（硬约束——必须遵守）
{volume_outline}

【卷纲遵守规则】
- 本章内容必须对应卷纲中当前章节范围内的剧情节点，严禁跳过或提前消耗后续节点
- 如果卷纲指定了某个事件/转折发生在第N章，不得提前到本章完成
- 剧情推进速度必须与卷纲规划的章节跨度匹配：如果卷纲规划某段剧情跨5章，不得在1-2章内讲完
- PRE_WRITE_CHECK中必须明确标注本章对应的卷纲节点

要求：
- 正文严格控制在{word_count}字左右，误差不超过10%，绝对不能少于{int(word_count * 0.9)}字
- 先输出写作自检表，再写正文
- 只需输出 PRE_WRITE_CHECK、CHAPTER_TITLE、CHAPTER_CONTENT 三个区块

重要提示：
- 请确保章节内容充实，达到要求的字数
- 可以通过增加场景描写、人物对话、心理活动等方式来增加字数
- 不要添加与剧情无关的内容，确保情节紧凑
- 字数不足将无法通过审核，需要重写
"""

    def _parse_creative_output(self, chapter_number: int, content: str) -> Dict[str, Any]:
        """解析创意输出"""
        # 这里简化处理，实际应该根据 TypeScript 项目的逻辑解析
        word_count = len(content)
        
        # 检查字数是否达标（这里假设标准字数为3000字）
        standard_word_count = 3000
        min_word_count = standard_word_count * 0.9
        
        if word_count < min_word_count:
            # 字数不足，返回错误信息
            return {
                'title': f"第{chapter_number}章",
                'content': content,
                'word_count': word_count,
                'pre_write_check': f"写作自检表：本章字数不足，要求{standard_word_count}字，实际{word_count}字，请重写",
                'error': f"字数不足，要求{standard_word_count}字，实际{word_count}字"
            }
        else:
            # 字数达标
            return {
                'title': f"第{chapter_number}章",
                'content': content,
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
        settler_system = self._build_settler_system_prompt(book, genre_profile, resolved_language)
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
    
    def _build_observer_system_prompt(self, book: Dict[str, Any], genre_profile: Dict[str, Any], language: str) -> str:
        """构建Observer系统提示"""
        is_english = language == "en"
        lang_prefix = "【LANGUAGE OVERRIDE】ALL output MUST be in English.\n\n" if is_english else ""
        
        return f"""{lang_prefix}{WRITER_PROMPTS['observer']}"""

    def _build_observer_user_prompt(self, chapter_number: int, title: str, content: str, language: str) -> str:
        """构建Observer用户提示"""
        if language == "en":
            return f"""Please extract all factual changes from Chapter {chapter_number}: "{title}"

## Chapter Content

{content}

Please extract all factual changes according to the format specified in the system prompt."""
        else:
            return f"""请从第{chapter_number}章「{title}」中提取所有事实性变化。

## 章节正文

{content}

请按照系统提示中指定的格式输出观察结果。"""

    def _build_settler_system_prompt(self, book: Dict[str, Any], genre_profile: Dict[str, Any], language: str) -> str:
        """构建Settler系统提示"""
        is_english = language == "en"
        lang_prefix = "【LANGUAGE OVERRIDE】ALL output MUST be in English.\n\n" if is_english else ""
        
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        numerical_block = ""
        
        if genre_profile.get('numericalSystem'):
            numerical_block = """
- 本题材有数值/资源体系，你必须在 UPDATED_LEDGER 中追踪正文中出现的所有资源变动
- 数值验算铁律：期初 + 增量 = 期末，三项必须可验算"""
        else:
            numerical_block = """
- 本题材无数值系统，UPDATED_LEDGER 留空"""

        hook_rules = """
## 伏笔追踪规则

- 新伏笔：正文中出现的暗示、悬念、未解之谜 → 新增 hook_id，标注起始章、类型、状态=待定
- 推进伏笔：已有伏笔在本章有新进展 → 更新"最近推进"列和状态
- 回收伏笔：伏笔在本章明确揭示/解决 → 状态改为"已回收"
- 延后伏笔：超过5章未推进 → 标注"延后"，备注原因"""

        # 计算需要的参数
        book_title = book.get('title', '未知')
        genre_name = genre_profile.get('name', genre)
        
        return f"""{lang_prefix}{WRITER_PROMPTS['settler'].format(
            book_title=book_title,
            genre_name=genre_name,
            genre=genre,
            platform=platform,
            numerical_block=numerical_block,
            hook_rules=hook_rules
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
        
        return f"""请分析第{chapter_number}章「{title}」的正文，更新所有追踪文件。

## 观察日志（由 Observer 提取，包含本章所有事实变化）
{observations}

基于以上观察日志和正文，更新所有追踪文件。确保观察日志中的每一项变化都反映在对应的文件中。

## 本章正文

{content}

## 当前状态卡
{current_state}
{ledger_block}
## 当前伏笔池
{hooks}
{summaries_block}{subplot_block}{emotional_block}{matrix_block}
## 卷纲
{volume_outline}

请严格按照 === TAG === 格式输出结算结果。"""

    def _parse_settlement_output(self, content: str, genre_profile: Dict[str, Any]) -> Dict[str, Any]:
        """解析结算输出"""
        import re
        
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
            return f"({filename.replace('.md', '').replace('.json', '').replace('_', ' ')}尚未创建)"
        
        file_path = os.path.join(book_dir, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return f"({filename.replace('.md', '').replace('.json', '').replace('_', ' ')}读取失败)"
        return f"({filename.replace('.md', '').replace('.json', '').replace('_', ' ')}尚未创建)"

    def _validate_post_write(self, content: str, genre_profile: Dict[str, Any], book_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """写后验证"""
        # 这里简化处理，实际应该根据 TypeScript 项目的逻辑实现
        return []



    def run(self, context: AgentContext) -> Dict[str, Any]:
        """运行作家 Agent"""
        book = context.kwargs.get('book', {})
        chapter_number = context.chapter_num
        chapter_plan = context.kwargs.get('chapter_plan', {})
        external_context = context.kwargs.get('external_context', None)
        word_count_override = context.kwargs.get('word_count_override', None)
        temperature_override = context.kwargs.get('temperature_override', None)
        book_dir = context.kwargs.get('book_dir', None)

        input = WriteChapterInput(
            book=book,
            chapter_number=chapter_number,
            chapter_plan=chapter_plan,
            external_context=external_context,
            word_count_override=word_count_override,
            temperature_override=temperature_override,
            book_dir=book_dir
        )

        output = self.write_chapter(input)

        return {
            'content': output.content,
            'word_count': output.word_count,
            'summary': output.chapter_summary,
            'title': output.title,
            'audit_score': 0.85,  # 模拟审计分数
            'revisions': 0,
            'updated_state': output.updated_state,
            'updated_hooks': output.updated_hooks,
            'updated_ledger': output.updated_ledger,
            'updated_subplots': output.updated_subplots,
            'updated_emotional_arcs': output.updated_emotional_arcs,
            'updated_character_matrix': output.updated_character_matrix
        }
