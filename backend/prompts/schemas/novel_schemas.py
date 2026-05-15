"""小说生成相关的Pydantic输出模式"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ActOutline(BaseModel):
    """幕大纲"""
    act_number: int = Field(..., ge=1, le=5, description="幕序号")
    title: str = Field(..., min_length=1, max_length=100, description="幕标题")
    summary: str = Field(..., min_length=10, max_length=2000, description="幕概要")
    key_events: List[str] = Field(default_factory=list, description="关键事件")


class CharacterProfile(BaseModel):
    """角色档案"""
    name: str = Field(..., min_length=1, max_length=50, description="角色名")
    role: str = Field(..., description="角色定位：主角/反派/配角等")
    personality: str = Field(..., min_length=10, max_length=1000, description="性格特征")
    background: str = Field(default="", description="背景故事")
    goals: List[str] = Field(default_factory=list, description="角色目标")
    relationships: Dict[str, str] = Field(default_factory=dict, description="人物关系")


class SettingInfo(BaseModel):
    """世界观设定"""
    world_name: Optional[str] = Field(default=None, description="世界名称")
    era: str = Field(..., description="时代背景")
    location: str = Field(..., description="主要地点")
    rules: List[str] = Field(default_factory=list, description="世界规则")
    atmosphere: str = Field(default="", description="氛围描述")


class FoundationOutput(BaseModel):
    """大纲生成输出"""
    title: str = Field(..., min_length=1, max_length=100, description="作品标题")
    genre: str = Field(..., description="作品类型")
    theme: str = Field(..., description="核心主题")
    logline: str = Field(..., min_length=10, max_length=500, description="一句话简介")
    synopsis: str = Field(..., min_length=50, max_length=5000, description="故事梗概")
    
    outline: Dict[str, Any] = Field(..., description="故事结构")
    acts: List[ActOutline] = Field(..., min_length=1, max_length=5, description="幕结构")
    characters: List[CharacterProfile] = Field(..., min_length=1, max_length=20, description="角色列表")
    setting: SettingInfo = Field(..., description="世界观设定")
    
    target_audience: str = Field(default="", description="目标读者")
    tone_style: str = Field(default="", description="基调风格")
    estimated_length: str = Field(default="", description="预计篇幅")
    
    @field_validator('acts')
    @classmethod
    def validate_act_numbers(cls, v):
        """验证幕序号连续"""
        numbers = [a.act_number for a in v]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("Act numbers must be consecutive starting from 1")
        return v


class ChapterOutline(BaseModel):
    """章节大纲"""
    chapter_number: int = Field(..., ge=1, description="章节序号")
    title: str = Field(..., min_length=1, max_length=100, description="章节标题")
    summary: str = Field(..., min_length=10, max_length=1000, description="章节概要")
    scenes: List[Dict[str, Any]] = Field(default_factory=list, description="场景列表")
    word_count: int = Field(default=3000, ge=500, le=20000, description="预计字数")
    characters_involved: List[str] = Field(default_factory=list, description="涉及角色")
    key_points: List[str] = Field(default_factory=list, description="关键情节点")


class ChapterOutlineOutput(BaseModel):
    """章节大纲生成输出"""
    act_number: int = Field(..., description="所属幕")
    chapters: List[ChapterOutline] = Field(..., min_length=1, max_length=50, description="章节列表")
    total_chapters: int = Field(..., description="总章节数")
    total_word_count: int = Field(..., ge=0, description="总字数")


class AuditIssue(BaseModel):
    """审核发现的问题"""
    category: str = Field(..., description="问题类别：逻辑/人物/节奏/文笔/设定")
    severity: str = Field(..., description="严重程度：critical/major/minor")
    location: str = Field(default="", description="问题位置")
    description: str = Field(..., min_length=5, description="问题描述")
    suggestion: str = Field(default="", description="修改建议")


class AuditResultOutput(BaseModel):
    """审核结果输出"""
    score: int = Field(..., ge=0, le=100, description="综合评分")
    summary: str = Field(..., min_length=10, description="总体评价")
    
    strengths: List[str] = Field(default_factory=list, description="优点")
    weaknesses: List[str] = Field(default_factory=list, description="不足")
    issues: List[AuditIssue] = Field(default_factory=list, description="具体问题")
    
    plot_consistency: int = Field(default=0, ge=0, le=100, description="情节连贯性")
    character_development: int = Field(default=0, ge=0, le=100, description="人物塑造")
    pacing: int = Field(default=0, ge=0, le=100, description="节奏把控")
    writing_quality: int = Field(default=0, ge=0, le=100, description="文笔质量")
    world_building: int = Field(default=0, ge=0, le=100, description="世界观一致性")


class RewriteOutput(BaseModel):
    """改写结果输出"""
    original_text: str = Field(..., description="原文")
    rewritten_text: str = Field(..., min_length=10, description="改写后文本")
    
    changes_made: List[str] = Field(default_factory=list, description="修改内容")
    improvement_areas: List[str] = Field(default_factory=list, description="改进方面")
    
    word_count_change: int = Field(default=0, description="字数变化")
    quality_score_before: int = Field(default=0, ge=0, le=100, description="改写前评分")
    quality_score_after: int = Field(default=0, ge=0, le=100, description="改写后评分")


class StyleFeature(BaseModel):
    """风格特征"""
    feature: str = Field(..., description="特征名称")
    description: str = Field(..., description="特征描述")
    examples: List[str] = Field(default_factory=list, description="示例")


class StyleAnalysisOutput(BaseModel):
    """风格分析输出"""
    overall_style: str = Field(..., description="整体风格")
    
    sentence_structure: str = Field(default="", description="句式特点")
    vocabulary_level: str = Field(default="", description="词汇水平")
    narrative_voice: str = Field(default="", description="叙事视角")
    pacing_style: str = Field(default="", description="节奏特点")
    
    distinctive_features: List[StyleFeature] = Field(default_factory=list, description="独特特征")
    
    sample_text: str = Field(default="", description="风格样本文本")
    imitation_guidance: str = Field(default="", description="模仿指导")


class HookAnalysisOutput(BaseModel):
    """钩子分析输出"""
    hook_type: str = Field(..., description="钩子类型")
    effectiveness_score: int = Field(..., ge=0, le=100, description="有效性评分")
    
    opening_hook: Dict[str, Any] = Field(default_factory=dict, description="开篇钩子")
    cliffhangers: List[Dict[str, Any]] = Field(default_factory=list, description="悬念设置")
    
    reader_engagement: str = Field(default="", description="读者参与度分析")
    improvement_suggestions: List[str] = Field(default_factory=list, description="改进建议")


class ContinuityCheckOutput(BaseModel):
    """连续性检查输出"""
    is_consistent: bool = Field(..., description="是否一致")
    
    timeline_issues: List[Dict[str, Any]] = Field(default_factory=list, description="时间线问题")
    character_issues: List[Dict[str, Any]] = Field(default_factory=list, description="人物设定问题")
    plot_holes: List[Dict[str, Any]] = Field(default_factory=list, description="情节漏洞")
    setting_issues: List[Dict[str, Any]] = Field(default_factory=list, description="设定冲突")
    
    suggestions: List[str] = Field(default_factory=list, description="修复建议")
