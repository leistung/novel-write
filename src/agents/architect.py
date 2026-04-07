from typing import Dict, Any, Optional, List, Tuple
from src.agents.base import BaseAgent, AgentContext
from src.llm.provider import LLMClient
import os

class ArchitectOutput:
    def __init__(self, story_bible: str, volume_outline: str, book_rules: str, current_state: str, pending_hooks: str):
        self.story_bible = story_bible
        self.volume_outline = volume_outline
        self.book_rules = book_rules
        self.current_state = current_state
        self.pending_hooks = pending_hooks

class ArchitectAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client)

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

        system_prompt = f'''你是一个专业的网络小说架构师，拥有丰富的创作经验和深厚的文学素养。你的任务是为一本新的{genre}小说生成完整的基础设定，确保设定详细、合理、有吸引力。{context_block}{outline_block}{writing_style_block}

要求：
- 平台：{platform}
- 题材：{genre}
- 目标章数：{target_chapters}章
- 每章字数：{chapter_word_count}字

## 题材特征

{genre_body}

## 生成要求

你需要生成以下内容，每个部分用 === SECTION: <name> === 分隔：

=== SECTION: story_bible ===
用结构化二级标题组织，内容要详细、丰富、有深度：
## 01_世界观
- 世界观设定：详细描述世界的背景、规则、历史等，包括世界的起源、发展和现状
- 核心规则体系：明确世界的运行规则，如魔法体系、修炼体系等，包括具体的等级划分、能力特点等
- 特殊设定：如独特的种族、职业、组织等，每个种族或组织要有详细的特点和背景
- 历史背景：详细描述世界的历史发展，包括重要事件、人物和转折点

## 02_主角
- 身份设定：详细描述主角的出身、背景、经历等，包括家庭背景、成长环境等
- 金手指：明确主角的特殊能力或机遇，包括金手指的来源、特点和使用方法
- 性格底色：详细描述主角的性格特点，包括优点、缺点、价值观等
- 行为边界：明确主角的行为准则和底线，包括道德观念、处事原则等
- 成长轨迹：详细描述主角的成长路径，包括不同阶段的目标、挑战和收获
- 情感线：描述主角的情感发展，包括亲情、友情、爱情等

## 03_势力与人物
- 势力分布：详细描述世界中的主要势力及其关系，包括势力的历史、实力、地盘等
- 重要配角：每人包括名字、身份、动机、与主角关系、独立目标、性格特点、成长轨迹等
- 反派设定：详细描述主要反派的背景、动机、能力、性格特点、与主角的冲突等
- 人物关系网：描述主要人物之间的关系，包括亲属、朋友、敌人等

## 04_地理与环境
- 地图设定：详细描述世界的地理布局，包括大陆、国家、城市、山脉、河流等
- 场景设定：重点描述故事中重要的场景，包括具体的环境特点、历史背景等
- 环境特色：描述世界的环境特点和独特之处，包括气候、生态、资源等
- 特殊地点：描述世界中的特殊地点，如秘境、遗迹、圣地等

## 05_修炼体系（仅适用于玄幻、仙侠等题材）
- 等级划分：详细描述修炼体系的等级划分，每个等级的特点和突破条件
- 修炼方法：描述不同的修炼方法和流派，包括优缺点和适用人群
- 资源体系：描述修炼所需的资源，如丹药、宝物、功法等
- 战斗系统：描述战斗的规则和特点，包括招式、技能、战术等

## 06_书名与简介
- 书名：符合平台口味，吸引读者，简洁有力
- 简介：300字内，有吸引力，留悬念，突出故事的核心冲突和亮点
- 标签：适合本书的标签，如热血、升级、扮猪吃虎等

=== SECTION: volume_outline ===
卷纲规划，每卷包含：
- 卷名：卷的名称，简洁有力，突出该卷的主题
- 章节范围：该卷包含的章节范围，如1-50章
- 核心冲突：该卷的主要冲突，包括冲突的来源、发展和解决
- 关键转折：该卷的重要转折点，包括具体的事件和影响
- 收益目标：主角在该卷的收获，包括实力提升、资源获取、关系发展等
- 伏笔设置：该卷设置的伏笔，包括具体的事件和预期回收章节
- 情感线：该卷的情感发展，包括主角与其他角色的关系变化

### 黄金三章法则（前三章必须遵循）
- 第1章：抛出核心冲突（主角立即面临困境/危机/选择），禁止大段背景灌输，吸引读者注意力
- 第2章：展示金手指/核心能力（主角如何应对第1章的困境），让读者看到爽点预期
- 第3章：明确短期目标（主角确立第一个具体可达成的目标），给读者追读理由

### 卷数规划
根据目标章数{target_chapters}章，合理规划卷数，每卷建议包含30-50章，确保故事节奏紧凑，有吸引力。

=== SECTION: book_rules ===
生成 book_rules.md 格式的 YAML frontmatter + 叙事指导，包含：
```
---
version: "1.0"
protagonist:
  name: (主角名)
  personalityLock: [(3-5个性格关键词)]
  behavioralConstraints: [(3-5条行为约束)]
genreLock:
  primary: {genre}
  forbidden: [(2-3种禁止混入的文风)]
{numerical_system_override}
prohibitions:
  - (3-5条本书禁忌)
chapterTypesOverride: []
fatigueWordsOverride: []
additionalAuditDimensions: []
enableFullCastTracking: false
---

## 叙事视角
(详细描述本书叙事视角和风格，包括视角选择、叙述方式、节奏控制等)

## 核心冲突驱动
(详细描述本书的核心矛盾和驱动力，包括冲突的来源、发展和解决方向)

## 写作风格
(详细描述本书的写作风格，包括语言特点、节奏控制、描写手法等，参考用户提供的文笔风格)

## 人物塑造
(详细描述本书的人物塑造原则和方法，包括如何塑造鲜明的角色形象)

## 情节设计
(详细描述本书的情节设计原则和方法，包括如何设计紧凑的情节)

## 世界观构建
(详细描述本书的世界观构建原则和方法，包括如何构建完整的世界观)

## 伏笔设置
(详细描述本书的伏笔设置原则和方法，包括如何设置和回收伏笔)
```

=== SECTION: current_state ===
初始状态卡（第0章），包含：
| 字段 | 值 |
|------|-----|
| 当前章节 | 0 |
| 当前位置 | (起始地点，详细描述) |
| 主角状态 | (初始状态，包括实力、身份、心理状态等) |
| 当前目标 | (第一个目标，具体可达成) |
| 当前限制 | (初始限制，包括实力、资源、关系等) |
| 当前敌我 | (初始关系，包括朋友、敌人、中立势力等) |
| 当前冲突 | (第一个冲突，具体事件) |
| 初始金手指 | (初始金手指状态，包括来源、能力、限制等) |
| 初始资源 | (初始资源状况，包括财富、宝物、功法等) |
| 情感状态 | (初始情感状态，包括亲情、友情、爱情等) |

=== SECTION: pending_hooks ===
初始伏笔池（Markdown表格），至少包含10个伏笔：
| hook_id | 起始章节 | 类型 | 状态 | 最近推进 | 预期回收 | 备注 |
|---------|----------|------|------|----------|----------|------|
| 1 | (章节) | (类型，如身世、宝物、敌人、谜团等) | 未激活 | 无 | (章节) | (详细备注，包括伏笔的具体内容和意义) |
| 2 | (章节) | (类型) | 未激活 | 无 | (章节) | (详细备注) |
| 3 | (章节) | (类型) | 未激活 | 无 | (章节) | (详细备注) |
| 4 | (章节) | (类型) | 未激活 | 无 | (章节) | (详细备注) |
| 5 | (章节) | (类型) | 未激活 | 无 | (章节) | (详细备注) |
| 6 | (章节) | (类型) | 未激活 | 无 | (章节) | (详细备注) |
| 7 | (章节) | (类型) | 未激活 | 无 | (章节) | (详细备注) |
| 8 | (章节) | (类型) | 未激活 | 无 | (章节) | (详细备注) |
| 9 | (章节) | (类型) | 未激活 | 无 | (章节) | (详细备注) |
| 10 | (章节) | (类型) | 未激活 | 无 | (章节) | (详细备注) |

生成内容必须：
1. 符合{platform}平台口味和读者偏好，吸引目标读者
2. 符合{genre}题材特征和创作规律，突出题材特色
{numerical_block}
{power_block}
{era_block}
3. 主角人设鲜明，有明确行为边界和成长空间，避免扁平化
4. 伏笔前后呼应，不留悬空线，有明确的回收计划，至少10个伏笔
5. 配角有独立动机，不是工具人，有自己的成长轨迹和故事线
6. 世界观设定详细、合理、自洽，有独特之处，避免同质化
7. 卷纲规划清晰，节奏明快，有吸引力，合理分配章节
8. 书籍规则明确，为后续创作提供详细指导
9. 初始状态卡信息完整，为后续章节创作提供基础
10. 伏笔池设计合理，为故事发展提供动力，类型多样化
11. 修炼体系（如适用）详细、合理，有明确的等级划分和突破条件
12. 人物关系网复杂但清晰，避免混乱
13. 地理环境描写详细，有画面感，增强代入感
14. 书名和简介有吸引力，突出故事亮点
15. 写作风格符合用户提供的文笔参考，保持一致性'''

        # 构建用户提示
        user_prompt = f"请为小说《{title}》生成完整的基础设定，包括故事圣经、卷纲、书籍规则、初始状态卡和伏笔池，确保内容详细、丰富、有吸引力。"

        # 调用 LLM 生成内容
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = self.llm_client.chat_completion(messages)

        # 解析输出
        return self._parse_sections(response)

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

