from typing import Dict, Any, Optional, List, Tuple
from src.agents.base import BaseAgent, AgentContext
from src.prompts import ARCHITECT_PROMPTS
import os

class ArchitectOutput:
    def __init__(self, story_bible: str, volume_outline: str, book_rules: str, current_state: str, pending_hooks: str):
        self.story_bible = story_bible
        self.volume_outline = volume_outline
        self.book_rules = book_rules
        self.current_state = current_state
        self.pending_hooks = pending_hooks

class ChapterPlanOutput:
    def __init__(self, chapter_outline: str, character_states: str, setting: str, plot_points: List[str]):
        self.chapter_outline = chapter_outline
        self.character_states = character_states
        self.setting = setting
        self.plot_points = plot_points

class ArchitectAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm)

    def generate_foundation(self, book: Dict[str, Any], external_context: Optional[str] = None) -> ArchitectOutput:
        """生成完整的基础设定"""
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        target_chapters = book.get('target_chapters', 100)
        chapter_word_count = book.get('chapter_words', 3000)
        title = book.get('title', '未知')
        language = book.get('language', 'zh')
        outline = book.get('outline', '')
        writing_style = book.get('writing_style', '')

        # 读取题材特征（这里简化处理，实际应该从文件读取）
        genre_body = self._get_genre_body(genre)

        context_block = f"\n\n## 外部指令\n以下是来自外部系统的创作指令，请将其融入设定中：\n\n{external_context}\n" if external_context else ""

        outline_block = f"\n\n## 小说大纲\n以下是用户提供的小说大纲，请将其融入设定中：\n\n{outline}\n" if outline else ""

        writing_style_block = f"\n\n## 作者文笔参考\n以下是用户提供的作者文笔参考，请在设定中体现相应的风格：\n\n{writing_style}\n" if writing_style else ""

        numerical_block = "- 有明确的数值/资源体系可追踪\n- 在 book_rules 中定义 numericalSystemOverrides（hardCap、resourceTypes）" if self._has_numerical_system(genre) else "- 本题材无数值系统，不需要资源账本"

        power_block = "- 有明确的战力等级体系" if self._has_power_scaling(genre) else ""

        era_block = "- 需要年代考据支撑（在 book_rules 中设置 eraConstraints）" if self._has_era_research(genre) else ""

        numerical_system_override = "numericalSystemOverrides:\n  hardCap: (根据设定确定)\n  resourceTypes: [(核心资源类型列表)]" if self._has_numerical_system(genre) else ""

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
            numerical_system_override=numerical_system_override
        )

        # 构建用户提示
        user_prompt = f"请为小说《{title}》生成完整的基础设定，包括故事圣经、卷纲、书籍规则、初始状态卡和伏笔池，确保内容详细、丰富、有吸引力。"

        # 创建提示词
        prompt = self.create_prompt(system_prompt, user_prompt)

        # 运行链
        response = self.run_chain(prompt)

        # 解析输出
        return self._parse_sections(response['content'])

    def _parse_sections(self, content: str) -> ArchitectOutput:
        """解析生成的各个部分"""
        sections = {
            'story_bible': '',
            'volume_outline': '',
            'book_rules': '',
            'current_state': '',
            'pending_hooks': ''
        }

        current_section = None
        for line in content.split('\n'):
            if line.startswith('=== SECTION: '):
                current_section = line.split('=== SECTION: ')[1].split(' ===')[0]
            elif current_section:
                sections[current_section] += line + '\n'

        return ArchitectOutput(
            story_bible=sections['story_bible'].strip(),
            volume_outline=sections['volume_outline'].strip(),
            book_rules=sections['book_rules'].strip(),
            current_state=sections['current_state'].strip(),
            pending_hooks=sections['pending_hooks'].strip()
        )

    def _get_genre_body(self, genre: str) -> str:
        """获取题材特征"""
        # 这里简化处理，实际应该从文件读取
        genre_bodies = {
            "玄幻": "玄幻题材的核心特征是：\n- 拥有完整的世界观和修炼体系，通常包含等级分明的修炼境界\n- 主角通常具有特殊体质、金手指或奇遇\n- 包含大量的战斗、冒险和探索元素\n- 强调实力的提升和等级的突破，常有越级挑战的情节\n- 常有门派、家族、势力之间的斗争和博弈\n- 包含宝物、丹药、功法等修炼资源的争夺\n- 世界观通常包含多个位面或世界，有宏大的背景设定",
            "仙侠": "仙侠题材的核心特征是：\n- 以中国传统神话、道教文化和修仙体系为基础\n- 修炼目标是成仙得道，追求长生不老和超凡脱俗\n- 包含飞剑、法术、丹药、符箓等传统修仙元素\n- 强调因果报应、道德修行和天劫考验\n- 常有门派传承、师徒关系和修仙界的等级制度\n- 包含人、仙、妖、魔等不同种族的互动\n- 世界观通常分为人间、仙界、魔界等不同层次",
            "都市": "都市题材的核心特征是：\n- 以现代城市为背景，强调现实感和代入感\n- 主角通常具有特殊能力、系统或机遇，在都市中崛起\n- 包含职场、商业、爱情、友情等现代生活元素\n- 常有商业竞争、权力斗争、黑道冲突等情节\n- 强调主角的成长和逆袭，从平凡到成功的过程\n- 包含现代科技、社会热点和流行文化元素\n- 人物关系复杂，常有多角恋、家族恩怨等情感纠葛",
            "科幻": "科幻题材的核心特征是：\n- 以科学技术为基础，具有一定的科学依据和逻辑\n- 包含未来世界、外星文明、人工智能、太空探索等元素\n- 探讨科技对人类社会的影响，以及人类与科技的关系\n- 常有时间旅行、平行宇宙、星际战争等科幻概念\n- 强调想象力和创造力，同时保持科学合理性\n- 包含硬科幻和软科幻元素，注重世界观的构建\n- 探讨人类的未来命运和存在意义",
            "恐怖": "恐怖题材的核心特征是：\n- 以营造恐怖氛围和心理恐惧为主要目标\n- 包含鬼魂、怪物、超自然现象、连环杀手等恐怖元素\n- 强调紧张感、悬疑感和压迫感\n- 常有密闭空间、孤立环境等经典恐怖场景\n- 探讨人性的黑暗面、恐惧的本质和生存的意义\n- 包含心理恐怖和视觉恐怖元素\n- 结局通常具有反转或开放性，留给读者想象空间",
            "悬疑": "悬疑题材的核心特征是：\n- 以解谜和推理为主要元素，强调逻辑思维和智力挑战\n- 包含案件、线索、伏笔、反转等悬疑元素\n- 主角通常是侦探、警察或普通人，通过调查和推理解决谜团\n- 强调情节的紧凑性和逻辑性，层层递进\n- 常有多重线索和嫌疑人，需要读者参与推理\n- 探讨人性、社会问题和道德困境\n- 结局通常具有意外性和合理性，符合逻辑" ,
            "言情": "言情题材的核心特征是：\n- 以爱情为主线，强调情感描写和人物关系\n- 包含情感纠葛、浪漫场景、误会和和解等元素\n- 主角通常是普通男女，通过相遇、相知、相爱到相守的过程\n- 强调情感的真实性和共鸣，让读者产生代入感\n- 常有甜宠、虐恋、职场爱情、校园爱情等不同类型\n- 探讨爱情的真谛、婚姻的意义和家庭的价值\n- 结局通常是圆满的，符合读者的期待"
        }
        return genre_bodies.get(genre, "该题材的特征描述正在完善中...")

    def _has_numerical_system(self, genre: str) -> bool:
        """判断题材是否需要数值系统"""
        return genre in ['玄幻', '仙侠', '科幻']

    def _has_power_scaling(self, genre: str) -> bool:
        """判断题材是否需要战力等级体系"""
        return genre in ['玄幻', '仙侠']

    def _has_era_research(self, genre: str) -> bool:
        """判断题材是否需要年代考据"""
        return genre in ['历史', '武侠']

    def plan_chapter(self, book: Dict[str, Any], chapter_num: int, current_state: str, previous_chapter_summary: str, external_context: Optional[str] = None) -> ChapterPlanOutput:
        """规划章节内容"""
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        chapter_word_count = book.get('chapter_words', 3000)
        title = book.get('title', '未知')
        outline = book.get('outline', '')
        writing_style = book.get('writing_style', '')

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
            external_context=external_context if external_context else '无'
        )

        # 构建用户提示
        user_prompt = f"请为第{chapter_num}章制定详细的内容规划，包括章节大纲、人物状态、场景设定和情节点。"

        # 创建提示词
        prompt = self.create_prompt(system_prompt, user_prompt)

        # 运行链
        response = self.run_chain(prompt)
        content = response['content']
        token_usage = response['token_usage']

        # 解析输出
        return self._parse_chapter_plan(content)

    def _parse_chapter_plan(self, content: str) -> ChapterPlanOutput:
        """解析章节规划输出"""
        # 这里简化处理，实际应该根据具体输出格式进行解析
        # 假设输出包含章节大纲、人物状态、场景设定和情节点
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

    def analyze_outline_impact(self, old_outline: str, new_outline: str, book: Dict[str, Any], outline_context: Optional[str] = None) -> Dict[str, Any]:
        """分析大纲变化对现有章节的影响"""
        genre = book.get('genre', '未知')
        title = book.get('title', '未知')
        
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
        
        # 调用 LLM 生成内容
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = self.llm_client.chat_completion(messages)
        
        # 解析输出
        return {
            'major_impact': '重大影响' in response,
            'minor_impact': '轻微影响' in response and '重大影响' not in response,
            'affected_chapters': [],
            'suggestions': response,
            'analysis': response
        }

    def update_book_state(self, book: Dict[str, Any], chapter_num: int, chapter_content: str, chapter_summary: str, current_state: str, pending_hooks: str, book_dir: Optional[str] = None) -> Dict[str, Any]:
        """更新书籍状态文件"""
        genre = book.get('genre', '未知')
        title = book.get('title', '未知')
        
        # 构建系统提示
        system_prompt = ARCHITECT_PROMPTS["update_book_state"].format(
            title=title,
            genre=genre,
            chapter_num=chapter_num,
            chapter_content=chapter_content,
            chapter_summary=chapter_summary,
            current_state=current_state,
            pending_hooks=pending_hooks
        )
        
        # 构建用户提示
        user_prompt = "请根据本章内容更新书籍的状态文件。"
        
        # 创建提示词
        prompt = self.create_prompt(system_prompt, user_prompt)
        
        # 运行链
        response = self.run_chain(prompt)
        content = response['content']
        token_usage = response['token_usage']
        
        # 解析输出
        sections = {
            'current_state': '',
            'pending_hooks': '',
            'particle_ledger': '',
            'subplot_board': '',
            'emotional_arcs': '',
            'character_matrix': ''
        }

        current_section = None
        for line in content.split('\n'):
            if line.startswith('=== SECTION: '):
                current_section = line.split('=== SECTION: ')[1].split(' ===')[0]
            elif current_section:
                sections[current_section] += line + '\n'

        return {
            'updated_state': sections['current_state'].strip(),
            'updated_hooks': sections['pending_hooks'].strip(),
            'updated_ledger': sections['particle_ledger'].strip(),
            'updated_subplots': sections['subplot_board'].strip(),
            'updated_emotional_arcs': sections['emotional_arcs'].strip(),
            'updated_character_matrix': sections['character_matrix'].strip()
        }

