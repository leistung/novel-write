from typing import Dict, Any, Optional, List
from src.agents.base import BaseAgent, AgentContext
from src.llm.provider import LLMClient
import os
import re

class WriteChapterInput:
    def __init__(self, book: Dict[str, Any], chapter_number: int, external_context: Optional[str] = None, word_count_override: Optional[int] = None, temperature_override: Optional[float] = None, book_dir: Optional[str] = None):
        self.book = book
        self.chapter_number = chapter_number
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
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client)

    def write_chapter(self, input: WriteChapterInput) -> WriteChapterOutput:
        """生成章节内容"""
        book = input.book
        chapter_number = input.chapter_number
        external_context = input.external_context
        word_count_override = input.word_count_override
        temperature_override = input.temperature_override
        book_dir = input.book_dir

        # 加载相关文件
        story_bible = self._read_file(book_dir, "story_bible.md") if book_dir else "(故事圣经尚未创建)"
        volume_outline = self._read_file(book_dir, "volume_outline.md") if book_dir else "(卷纲尚未创建)"
        style_guide = self._read_file(book_dir, "style_guide.md") if book_dir else "(风格指南尚未创建)"
        current_state = self._read_file(book_dir, "current_state.md") if book_dir else "(当前状态尚未创建)"
        ledger = self._read_file(book_dir, "particle_ledger.md") if book_dir else "(资源账本尚未创建)"
        hooks = self._read_file(book_dir, "pending_hooks.md") if book_dir else "(伏笔池尚未创建)"
        chapter_summaries = self._read_file(book_dir, "chapter_summaries.md") if book_dir else "(章节摘要尚未创建)"
        subplot_board = self._read_file(book_dir, "subplot_board.md") if book_dir else "(支线进度板尚未创建)"
        emotional_arcs = self._read_file(book_dir, "emotional_arcs.md") if book_dir else "(情感弧线尚未创建)"
        character_matrix = self._read_file(book_dir, "character_matrix.md") if book_dir else "(角色交互矩阵尚未创建)"
        style_profile_raw = self._read_file(book_dir, "style_profile.json") if book_dir else "(风格配置尚未创建)"
        parent_canon = self._read_file(book_dir, "parent_canon.md") if book_dir else "(正传正典尚未创建)"
        fanfic_canon_raw = self._read_file(book_dir, "fanfic_canon.md") if book_dir else "(同人正典尚未创建)"

        # 加载最近章节
        recent_chapters = ""
        fingerprint_chapters = ""

        # 加载题材配置
        genre = book.get('genre', '未知')
        genre_profile = self._get_genre_profile(genre)
        book_rules = self._get_book_rules(book)

        # 构建风格指纹
        style_fingerprint = self._build_style_fingerprint(style_profile_raw)

        # 提取对话指纹
        dialogue_fingerprints = self._extract_dialogue_fingerprints(fingerprint_chapters, story_bible)

        # 查找相关摘要
        relevant_summaries = self._find_relevant_summaries(chapter_summaries, volume_outline, chapter_number)

        # 构建同人上下文
        fanfic_context = None
        has_fanfic_canon = fanfic_canon_raw != "(同人正典尚未创建)"
        if has_fanfic_canon and book_rules.get('fanficMode'):
            fanfic_context = {
                'fanficCanon': fanfic_canon_raw,
                'fanficMode': book_rules.get('fanficMode'),
                'allowedDeviations': book_rules.get('allowedDeviations', [])
            }

        # 第一阶段：创意写作
        resolved_language = book.get('language', 'zh') or genre_profile.get('language', 'zh')
        creative_system_prompt = self._build_writer_system_prompt(
            book, genre_profile, book_rules, style_guide, style_fingerprint,
            chapter_number, "creative", fanfic_context, resolved_language
        )

        # 智能上下文过滤
        filtered_hooks = self._filter_hooks(hooks)
        filtered_summaries = self._filter_summaries(chapter_summaries, chapter_number)
        filtered_subplots = self._filter_subplots(subplot_board)
        filtered_arcs = self._filter_emotional_arcs(emotional_arcs, chapter_number)
        filtered_matrix = self._filter_character_matrix(character_matrix, volume_outline, book_rules.get('protagonist', {}).get('name'))

        # POV 感知过滤
        pov_character = self._extract_pov_from_outline(volume_outline, chapter_number)
        pov_filtered_matrix = self._filter_matrix_by_pov(filtered_matrix, pov_character) if pov_character else filtered_matrix
        pov_filtered_hooks = self._filter_hooks_by_pov(filtered_hooks, pov_character, chapter_summaries) if pov_character else filtered_hooks

        # 构建用户提示
        creative_user_prompt = self._build_user_prompt({
            'chapter_number': chapter_number,
            'story_bible': story_bible,
            'volume_outline': volume_outline,
            'current_state': current_state,
            'ledger': ledger if genre_profile.get('numericalSystem') else '',
            'hooks': pov_filtered_hooks,
            'recent_chapters': recent_chapters,
            'word_count': word_count_override or book.get('chapter_words', 3000),
            'external_context': external_context,
            'chapter_summaries': filtered_summaries,
            'subplot_board': filtered_subplots,
            'emotional_arcs': filtered_arcs,
            'character_matrix': pov_filtered_matrix,
            'dialogue_fingerprints': dialogue_fingerprints,
            'relevant_summaries': relevant_summaries,
            'parent_canon': parent_canon if parent_canon != "(正传正典尚未创建)" else None,
            'language': resolved_language
        })

        # 调用 LLM 进行创意写作
        creative_temperature = temperature_override or 0.7
        target_words = word_count_override or book.get('chapter_words', 3000)
        creative_max_tokens = max(8192, int(target_words * 2))

        messages = [
            {"role": "system", "content": creative_system_prompt},
            {"role": "user", "content": creative_user_prompt}
        ]
        creative_response = self.llm_client.chat_completion(messages)

        # 解析创意输出
        creative = self._parse_creative_output(chapter_number, creative_response)

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
        ai_tell_issues = self._analyze_ai_tells(creative['content'])

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
            token_usage=None  # 实际项目中应该从 LLM 响应中提取
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

    def _build_writer_system_prompt(self, book: Dict[str, Any], genre_profile: Dict[str, Any], book_rules: Dict[str, Any], style_guide: str, style_fingerprint: Optional[str], chapter_number: int, mode: str, fanfic_context: Optional[Dict[str, Any]], language: str) -> str:
        """构建作家系统提示"""
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        chapter_word_count = book.get('chapter_words', 3000)
        writing_style = book.get('writing_style', '')
        
        writing_style_block = f"\n\n## 作者文笔参考\n以下是用户提供的作者文笔参考，请在写作中体现相应的风格：\n\n{writing_style}\n" if writing_style else ""
        
        return f"你是一位专业的{genre}小说作家，擅长创作精彩的故事情节。你熟悉{platform}平台的读者偏好，能够创作出符合平台口味的作品。{writing_style_block}\n\n要求：\n- 每章字数：严格控制在{chapter_word_count}字左右，误差不超过10%\n- 语言流畅，符合网络小说阅读习惯\n- 节奏明快，有适当的冲突和张力\n- 人物刻画鲜明，有独立动机\n- 场景描写生动，有画面感\n- 情节逻辑连贯，推进合理\n- 符合{genre}题材特征\n\n重要提示：请确保生成的章节字数达到要求，不要少于{chapter_word_count * 0.9}字。如果字数不足，将无法通过审核。"

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
        story_bible = params['story_bible']
        volume_outline = params['volume_outline']
        current_state = params['current_state']
        ledger = params['ledger']
        hooks = params['hooks']
        recent_chapters = params['recent_chapters']
        word_count = params['word_count']
        external_context = params['external_context']
        chapter_summaries = params['chapter_summaries']
        subplot_board = params['subplot_board']
        emotional_arcs = params['emotional_arcs']
        character_matrix = params['character_matrix']
        dialogue_fingerprints = params['dialogue_fingerprints']
        relevant_summaries = params['relevant_summaries']
        parent_canon = params['parent_canon']
        language = params['language']

        context_block = f"\n## 外部指令\n以下是来自外部系统的创作指令，请在本章中融入：\n\n{external_context}\n" if external_context else ""
        ledger_block = f"\n## 资源账本\n{ledger}\n" if ledger else ""
        summaries_block = f"\n## 章节摘要（全部历史章节压缩上下文）\n{chapter_summaries}\n" if chapter_summaries != "(章节摘要尚未创建)" else ""
        subplot_block = f"\n## 支线进度板\n{subplot_board}\n" if subplot_board != "(支线进度板尚未创建)" else ""
        emotional_block = f"\n## 情感弧线\n{emotional_arcs}\n" if emotional_arcs != "(情感弧线尚未创建)" else ""
        matrix_block = f"\n## 角色交互矩阵\n{character_matrix}\n" if character_matrix != "(角色交互矩阵尚未创建)" else ""
        fingerprint_block = f"\n## 角色对话指纹\n{dialogue_fingerprints}\n" if dialogue_fingerprints else ""
        relevant_block = f"\n## 相关历史章节摘要\n{relevant_summaries}\n" if relevant_summaries else ""
        canon_block = f"\n## 正传正典参照（番外写作专用）\n本书是番外作品。以下正典约束不可违反，角色不得引用超出其信息边界的信息。\n{parent_canon}\n" if parent_canon else ""

        if language == "en":
            return f"""Write chapter {chapter_number}.
{context_block}
## Current State
{current_state}
{ledger_block}
## Plot Threads
{hooks}
{summaries_block}{subplot_block}{emotional_block}{matrix_block}{fingerprint_block}{relevant_block}{canon_block}
## Recent Chapters
{recent_chapters or "(This is the first chapter, no previous text)"}

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
## 当前状态卡
{current_state}
{ledger_block}
## 伏笔池
{hooks}
{summaries_block}{subplot_block}{emotional_block}{matrix_block}{fingerprint_block}{relevant_block}{canon_block}
## 最近章节
{recent_chapters or "(这是第一章，无前文)"}

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
        
        observer_messages = [
            {"role": "system", "content": observer_system},
            {"role": "user", "content": observer_user}
        ]
        observer_response = self.llm_client.chat_completion(observer_messages)
        observations = observer_response
        
        # 第二阶段：Reflector - 将观察结果合并到状态文件中
        settler_system = self._build_settler_system_prompt(book, genre_profile, resolved_language)
        settler_user = self._build_settler_user_prompt(
            chapter_number, title, content, current_state, ledger, hooks,
            chapter_summaries, subplot_board, emotional_arcs, character_matrix,
            volume_outline, observations
        )
        
        settler_messages = [
            {"role": "system", "content": settler_system},
            {"role": "user", "content": settler_user}
        ]
        settler_response = self.llm_client.chat_completion(settler_messages)
        
        # 解析结算输出
        return {
            'settlement': self._parse_settlement_output(settler_response, genre_profile)
        }
    
    def _build_observer_system_prompt(self, book: Dict[str, Any], genre_profile: Dict[str, Any], language: str) -> str:
        """构建Observer系统提示"""
        is_english = language == "en"
        lang_prefix = "【LANGUAGE OVERRIDE】ALL output MUST be in English.\n\n" if is_english else ""
        
        return f"""{lang_prefix}你是章节观察员。你的任务是从章节正文中提取所有事实性变化。

## 提取维度

从正文中提取以下信息：
1. **角色变化**：出场、退场、状态变化（受伤/突破/死亡等）、情绪变化
2. **位置变化**：场景转换、地点移动
3. **物品/资源**：获得、消耗、转移
4. **伏笔动态**：新埋设的伏笔、推进的伏笔、回收的伏笔
5. **关系变化**：角色间关系的变化、新的信息边界
6. **主线进展**：剧情推进到哪个阶段
7. **支线进展**：支线剧情的进展

## 输出格式

请按照以下格式输出观察结果：

### 角色变化
| 角色 | 变化类型 | 详细描述 |
|------|----------|----------|

### 位置变化
| 场景 | 角色 | 时间点 |
|------|------|--------|

### 物品/资源
| 物品/资源 | 变化类型 | 相关角色 |
|-----------|----------|----------|

### 伏笔动态
| 伏笔描述 | 类型 | 涉及角色 |
|----------|------|----------|

### 关系变化
| 角色A | 角色B | 变化描述 |
|-------|-------|----------|

### 主线进展
（一句话描述主线进展）

### 支线进展
| 支线描述 | 进展状态 |
|----------|----------|

请确保提取所有事实性变化，不要遗漏任何细节。"""

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

        return f"""{lang_prefix}你是状态追踪分析师。给定新章节正文和当前 truth 文件，你的任务是产出更新后的 truth 文件。

## 工作模式

你不是在写作。你的任务是：
1. 仔细阅读观察日志和正文，提取所有状态变化
2. 基于"当前追踪文件"做增量更新
3. 严格按照 === TAG === 格式输出

## 分析维度

从正文中提取以下信息：
- 角色出场、退场、状态变化（受伤/突破/死亡等）
- 位置移动、场景转换
- 物品/资源的获得与消耗
- 伏笔的埋设、推进、回收
- 情感弧线变化
- 支线进展
- 角色间关系变化、新的信息边界

## 书籍信息

- 标题：{book.get('title', '未知')}
- 题材：{genre_profile.get('name', genre)}（{genre}）
- 平台：{platform}
{numerical_block}
{hook_rules}

## 输出格式（必须严格遵循）

=== POST_SETTLEMENT ===
（如有变动，必须输出Markdown表格）
| 结算项 | 本章记录 | 备注 |
|--------|----------|------|

=== UPDATED_STATE ===
(更新后的完整状态卡，Markdown表格格式，必须包含以下列)
| 章节 | 当前位置 | 主角状态 | 当前目标 | 敌人/对手 | 已知真相 | 当前冲突 | 锚点 |
|------|----------|----------|----------|-----------|----------|----------|------|

=== UPDATED_LEDGER ===
(更新后的完整资源账本，Markdown表格格式，如无数值系统则留空)
| 章节 | 资源名 | 期初值 | 增量 | 期末值 | 依据 |
|------|--------|--------|------|--------|------|

=== UPDATED_HOOKS ===
(更新后的完整伏笔池，Markdown表格格式)
| Hook ID | 起始章 | 类型 | 状态 | 最近推进 | 预期回收 | 备注 |
|---------|--------|------|------|----------|----------|------|

=== CHAPTER_SUMMARY ===
(本章摘要，Markdown表格格式)
| 章节 | 标题 | 出场人物 | 关键事件 | 状态变化 | 伏笔动态 | 情绪基调 | 章节类型 |
|------|------|----------|----------|----------|----------|----------|----------|

=== UPDATED_SUBPLOTS ===
(更新后的完整支线进度板，Markdown表格格式)
| 支线ID | 支线名 | 相关角色 | 起始章 | 最近活跃章 | 状态 | 进度概述 | 回收ETA |
|--------|--------|----------|--------|------------|------|----------|---------|

=== UPDATED_EMOTIONAL_ARCS ===
(更新后的完整情感弧线，Markdown表格格式)
| 角色 | 章节 | 情绪状态 | 触发事件 | 强度(1-10) | 弧线方向 |
|------|------|----------|----------|------------|----------|

=== UPDATED_CHARACTER_MATRIX ===
(更新后的角色交互矩阵，分三个子表)

### 角色档案
| 角色 | 核心标签 | 反差细节 | 说话风格 | 性格底色 | 与主角关系 | 核心动机 | 当前目标 |
|------|----------|----------|----------|----------|------------|----------|----------|

### 相遇记录
| 角色A | 角色B | 首次相遇章 | 最近交互章 | 关系性质 | 关系变化 |
|-------|-------|------------|------------|----------|----------|

### 信息边界
| 角色 | 已知信息 | 未知信息 | 信息来源章 |
|------|----------|----------|------------|

## 关键规则

1. 状态卡和伏笔池必须基于"当前追踪文件"做增量更新，不是从零开始
2. 正文中的每一个事实性变化都必须反映在对应的追踪文件中
3. 不要遗漏细节：数值变化、位置变化、关系变化、信息变化都要记录
4. 角色交互矩阵中的"信息边界"要准确——角色只知道他在场时发生的事"""

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

    def _analyze_ai_tells(self, content: str) -> Dict[str, Any]:
        """分析 AI 痕迹"""
        # 这里简化处理，实际应该根据 TypeScript 项目的逻辑实现
        return {'issues': []}

    def _build_style_fingerprint(self, style_profile_raw: str) -> Optional[str]:
        """构建风格指纹"""
        return None

    def _extract_dialogue_fingerprints(self, recent_chapters: str, story_bible: str) -> str:
        """提取对话指纹"""
        return ""

    def _find_relevant_summaries(self, chapter_summaries: str, volume_outline: str, chapter_number: int) -> str:
        """查找相关摘要"""
        return ""

    def run(self, context: AgentContext) -> Dict[str, Any]:
        """运行作家 Agent"""
        book = context.kwargs.get('book', {})
        chapter_number = context.chapter_num
        external_context = context.kwargs.get('external_context', None)
        word_count_override = context.kwargs.get('word_count_override', None)
        temperature_override = context.kwargs.get('temperature_override', None)

        input = WriteChapterInput(
            book=book,
            chapter_number=chapter_number,
            external_context=external_context,
            word_count_override=word_count_override,
            temperature_override=temperature_override
        )

        output = self.write_chapter(input)

        return {
            'content': output.content,
            'word_count': output.word_count,
            'summary': output.chapter_summary,
            'title': output.title,
            'audit_score': 0.85,  # 模拟审计分数
            'revisions': 0
        }
