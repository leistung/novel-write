# 🎭 Skill 系统

本文档介绍 NovelWrite AI 的 Skill 系统，包含26种小说类型的专业知识库。

## 目录

- [Skill 概述](#skill-概述)
- [26种小说类型](#26种小说类型)
- [Skill 文件结构](#skill-文件结构)
- [Skill 调用机制](#skill-调用机制)
- [如何编写 Skill](#如何编写-skill)
- [Skill 示例](#skill-示例)

## Skill 概述

Skill 是 NovelWrite AI 的核心知识库，每种小说类型都有专门的 Skill 文件，包含：

- **核心智模型** - 该类型的创作方法论
- **表达DNA** - 句式、节奏、修辞特点
- **决策启发式** - 何时转折、何时高潮等决策规则
- **经典作品分析** - 该类型的标杆作品研究

## 26种小说类型

### 男频（15种）

| 类型 | Skill名称 | 代表风格 |
|------|----------|---------|
| 玄幻 | xuanhuan-novelist | 《斗破苍穹》《凡人修仙传》 |
| 奇幻 | qihuan-novelist | 《盘龙》《神墓》 |
| 武侠 | wuxia-novelist | 《雪中悍刀行》《天龙八部》 |
| 仙侠 | xianxia-novelist | 《凡人修仙传》《仙逆》 |
| 都市 | urban-novelist | 《大王饶命》《修真聊天群》 |
| 现实 | realistic-novelist | 《大江大河》《繁花》 |
| 历史 | historical-novelist | 《庆余年》《赘婿》 |
| 军事 | military-novelist | 《弹痕》《狼群》 |
| 游戏 | game-novelist | 《全职高手》《超神机械师》 |
| 体育 | sports-novelist | 《冠军之心》《禁区之雄》 |
| 科幻 | scifi-novelist | 《三体》《吞噬星空》 |
| 悬疑灵幻 | suspense-supernatural-novelist | 《诡秘之主》《我有一座恐怖屋》 |
| 轻小说 | light-novelist | 《刀剑神域》《Re:从零开始》 |
| 短篇 | short-story-novelist | 知乎盐选短篇 |
| 诸天无限 | infinite-novelist | 《无限恐怖》《惊悚乐园》 |

### 女频（11种）

| 类型 | Skill名称 | 代表风格 |
|------|----------|---------|
| 古代言情 | ancient-romance-novelist | 《知否》《甄嬛传》 |
| 现代言情 | modern-romance-novelist | 《何以笙箫默》《你是我的荣耀》 |
| 玄幻言情 | fantasy-romance-novelist | 《花千骨》《三生三世》 |
| 悬疑推理 | mystery-novelist | 《心理罪》《法医秦明》 |
| 浪漫青春 | youth-romance-novelist | 《最好的我们》《你好旧时光》 |
| 仙侠奇缘 | xianxia-romance-novelist | 《香蜜沉沉烬如霜》 |
| 科幻空间 | scifi-romance-novelist | 《星际之女帝》 |
| 游戏竞技 | esports-romance-novelist | 《微微一笑很倾城》 |
| 轻小说女频 | light-female-novelist | 穿越女尊类 |
| 短篇女频 | short-female-novelist | 知乎盐选女频短篇 |
| 现实生活 | real-life-female-novelist | 《欢乐颂》《都挺好》 |

## Skill 文件结构

每个 Skill 目录结构：

```
skills/{skill-name}/
├── SKILL.md                          # 核心Skill文件
└── references/
    └── research/
        ├── 01-writings.md            # 著作研究
        ├── 02-conversations.md       # 对话风格
        ├── 03-expression-dna.md      # 表达DNA
        ├── 04-external-views.md      # 外部视角
        ├── 05-decisions.md           # 决策启发式
        └── 06-timeline.md            # 时间线
```

### SKILL.md 结构

```markdown
---
name: skill-name
description: Skill描述
---

## 角色扮演规则

你是一位拥有20年经验的XXX类型大神作家...

## 核心智模型

### 1. 模型名称
模型描述和要点...

### 2. 模型名称
...

## 决策启发式

- IF 条件 THEN 行动
- IF 条件 THEN 行动

## 表达DNA

### 叙事节奏
...

### 情绪调动
...

### 对话风格
...

## 经典作品时间线

### 作品名 (年份)
- 借鉴点：...
- 创新点：...

## 价值观与反模式

### 追求
- ...

### 拒绝
- ...

## 智识谱系

- 继承自：...
- 影响：...

## 诚实边界

- 我能：...
- 我不能：...

## 附录：调研来源

- ...
```

## Skill 调用机制

### 调用流程

```
用户创建书籍(指定genre)
    ↓
Agent执行任务
    ↓
BaseAgent._build_system_prompt(base_prompt, genre)
    ↓
SkillLoader.get_skill_prompt_suffix(genre)
    ↓
读取 skills/{genre}/SKILL.md
    ↓
提取核心智模型 + 表达DNA + 决策启发式
    ↓
拼接到 system_prompt
    ↓
调用 LLM API
```

### 代码实现

```python
# skill/loader.py
class SkillLoader:
    def get_skill_prompt_suffix(self, genre: str) -> str:
        """提取Skill的核心内容"""
        skill_name = self._genre_to_skill_name(genre)
        content = self._load_skill_file(skill_name)
        
        # 提取关键部分
        sections = self._extract_sections(content, [
            "核心智模型",
            "表达DNA", 
            "决策启发式"
        ])
        
        # 控制长度
        return self._truncate(sections, max_length=2000)
```

### 注入Prompt示例

```python
# 基础prompt
base_prompt = """你是一位小说创作专家..."""

# 注入Skill后
system_prompt = base_prompt + """

## 题材专家知识库

### 核心智模型

#### 1. 修炼体系金字塔模型
- 底层：基础功法（炼气、筑基）
- 中层：进阶功法（金丹、元婴）
- 顶层：绝世功法（化神、渡劫）

#### 2. 爽点节奏模型
- 压抑期：30%（主角受辱/困境）
- 爆发期：20%（打脸/突破）
- 收获期：30%（奖励/成长）
- 铺垫期：20%（新目标/新冲突）

### 决策启发式

- IF 主角连续3章没有成长 THEN 安排突破或获得宝物
- IF 反派压迫感不足 THEN 增加实力差距或伤害主角亲友

### 表达DNA

#### 叙事节奏
- 每章至少一个爽点
- 每3章一个小高潮
- 每10章一个大高潮
...
"""
```

## 如何编写 Skill

### 1. 确定类型定位

分析该类型的：
- 核心爽点是什么？
- 读者期待什么？
- 与其他类型的区别？

### 2. 设计核心智模型

每个智模型应该：
- 有清晰的名称
- 有结构化的要点
- 可操作、可落地

**示例 - 玄幻的修炼体系金字塔**：
```markdown
### 1. 修炼体系金字塔模型

**结构**：
- 底层（60%）：炼气、筑基、金丹
  - 特点：基础扎实，稳扎稳打
  - 爽点：突破瓶颈，越级挑战
  
- 中层（30%）：元婴、化神、渡劫
  - 特点：神通广大，影响一方
  - 爽点：开宗立派，名震一方
  
- 顶层（10%）：大乘、飞升
  - 特点：绝世强者，改变规则
  - 爽点：无敌于世，飞升仙界

**应用**：
- 每升级一个大境界，必须有质的飞跃
- 境界差距要明显，但不能无法逾越
- 主角可以越1-2个小境界挑战
```

### 3. 编写决策启发式

使用 IF-THEN 格式：

```markdown
## 决策启发式

- IF 主角连续3章没有成长 THEN 安排突破或获得宝物
- IF 反派压迫感不足 THEN 增加实力差距或伤害主角亲友
- IF 剧情推进缓慢 THEN 插入突发事件或冲突
- IF 读者反馈平淡 THEN 加快节奏或增加反转
- IF 伏笔超过10章未回收 THEN 安排回收或提示
```

### 4. 提炼表达DNA

分析该类型的：
- 常用句式
- 节奏特点
- 修辞手法
- 对话风格

**示例**：
```markdown
## 表达DNA

### 叙事节奏
- **开篇**：100字内进入冲突，500字内展现金手指
- **日常**：每章至少一个信息点或进展
- **高潮**：短句为主，加快节奏
- **结尾**：留悬念或预告下章

### 经典句式
- "XXX眼中闪过一丝精光..."
- "就在此时，异变突生！"
- "这...这怎么可能！"

### 对话风格
- 强者：简短有力，不废话
- 反派：嚣张跋扈，死于话多
- 配角：功能性对话，推动剧情
```

## Skill 示例

### 玄幻 Skill 片段

```markdown
## 核心智模型

### 1. 修炼体系金字塔模型
...

### 2. 金手指设计模型

**类型**：
- 系统流：任务奖励，升级明确
- 戒指流：老爷爷指导，传承有序
- 重生流：先知先觉，布局深远
- 签到流：日常奖励，稳定成长

**原则**：
- 金手指要有代价或限制
- 不能无敌，要有挑战
- 随着剧情升级，金手指也要进化

### 3. 爽点节奏模型

**压抑-爆发-收获-铺垫** 循环：
- 压抑期：主角受辱、困境、被轻视（30%）
- 爆发期：打脸、突破、展现实力（20%）
- 收获期：奖励、成长、地位提升（30%）
- 铺垫期：新目标、新冲突、新挑战（20%）

### 4. 地图升级模型

**新手村 → 小城镇 → 大城池 → 州府 → 皇城 → 仙界**

每个地图：
- 有独特的资源/功法/敌人
- 主角达到顶峰后触发升级事件
- 旧地图的敌人/朋友在新地图有新定位

### 5. 反派设计模型

**层次**：
- 小反派（当前地图）：给主角练手
- 中反派（区域级）：制造大冲突
- 大反派（世界级）：最终BOSS

**特点**：
- 有合理的动机，不是纯恶
- 实力始终领先主角半步
- 给主角足够的成长压力
```

### 古代言情 Skill 片段

```markdown
## 核心智模型

### 1. 情感发展曲线

**相识 → 试探 → 心动 → 阻碍 → 确认 → 相守**

- 相识：有趣的相遇，留下印象
- 试探：互相了解，暗生情愫
- 心动：明确好感，但不敢表白
- 阻碍：身份差距、家族反对、误会
- 确认：突破阻碍，确定关系
- 相守：共同面对未来

### 2. 女主成长模型

**从依附到独立**：
- 初期：依附家族/男主，被动接受命运
- 中期：开始反抗，争取自主权
- 后期：独立自主，与男主并肩

### 3. 宅斗/宫斗模型

**势力分布**：
- 盟友：真心帮助女主的人
- 中立：可以争取的人
- 敌人：明确对立的人

**斗争手段**：
- 信息战：掌握秘密，控制舆论
- 联盟战：拉拢盟友，孤立敌人
- 反击战：抓住把柄，一击致命

### 4. 情感张力模型

**制造张力的方法**：
- 身份差距：门第、地位、正邪
- 外部阻碍：家族、政治、战争
- 内部矛盾：性格、价值观、误会
- 时间压力：限期、生死、错过
```

## API 操作

### 查看所有 Skill

```bash
curl "http://localhost:8000/api/v1/skills"
```

### 查看 Skill 详情

```bash
curl "http://localhost:8000/api/v1/skills/xuanhuan-novelist"
```

### 查看小说类型列表

```bash
curl "http://localhost:8000/api/v1/skills/genres/list"
```

### 同步 Skill 到数据库

```bash
curl -X POST "http://localhost:8000/api/v1/skills/sync"
```
