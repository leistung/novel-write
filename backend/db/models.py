"""数据库模型定义 - 规范化设计"""
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    Float, ForeignKey, JSON, Boolean, Index
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """基础模型类"""
    pass


# ==================== 书籍相关模型 ====================

class Book(Base):
    """书籍模型 - 精简主表"""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    genre = Column(String(50), nullable=False, index=True)
    platform = Column(String(100), default="通用")
    chapter_words = Column(Integer, default=3000)
    target_chapters = Column(Integer, default=100)
    outline = Column(Text, default="", nullable=True)  # 用户输入的大纲

    # 状态管理
    status = Column(String(50), default="draft", index=True)  # draft/active/completed/archived

    # 动态状态缓存字段（由工作流引擎维护，冗余存储以避免频繁JOIN）
    # 这些字段的数据源头是 BookState 和 BookOutline 表
    story_bible = Column(Text, default="", nullable=True)
    volume_outline = Column(Text, default="", nullable=True)
    current_state = Column(Text, default="", nullable=True)
    pending_hooks = Column(Text, default="", nullable=True)
    character_matrix = Column(Text, default="", nullable=True)
    emotional_arcs = Column(Text, default="", nullable=True)
    subplot_board = Column(Text, default="", nullable=True)
    chapter_summaries = Column(Text, default="", nullable=True)
    writing_style = Column(Text, default="", nullable=True)

    # 元数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 预留多租户

    # 关联关系
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan", lazy="noload")
    workflows = relationship("WorkflowExecution", back_populates="book", cascade="all, delete-orphan")
    outlines = relationship("BookOutline", back_populates="book", cascade="all, delete-orphan")
    states = relationship("BookState", back_populates="book", cascade="all, delete-orphan", order_by="desc(BookState.version)")
    hooks = relationship("StoryHook", back_populates="book", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="book", cascade="all, delete-orphan")
    settings_data = relationship("SettingData", back_populates="book", cascade="all, delete-orphan")

    # 复合索引
    __table_args__ = (
        Index('ix_books_genre_status', 'genre', 'status'),
        Index('ix_books_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<Book(id={self.id})>"


class BookOutline(Base):
    """书籍大纲 - 分表存储，支持版本控制"""
    __tablename__ = "book_outlines"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)

    # 大纲类型
    outline_type = Column(String(50), nullable=False, index=True)  # worldview/characters/plot/volume/outline/rules

    # 内容
    content = Column(Text, default="")

    # 版本控制
    version = Column(Integer, default=1, index=True)
    is_active = Column(Boolean, default=True, index=True)  # 当前生效版本

    # 元数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String(100), default="system")  # system/user/workflow

    # 关联关系
    book = relationship("Book", back_populates="outlines")

    # 复合索引
    __table_args__ = (
        Index('ix_outline_book_type_version', 'book_id', 'outline_type', 'version', unique=True),
        Index('ix_outline_book_active', 'book_id', 'outline_type', 'is_active'),
    )

    def __repr__(self):
        return f"<BookOutline(id={self.id})>"


class BookState(Base):
    """书籍动态状态 - 支持历史版本"""
    __tablename__ = "book_states"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)

    # 状态类型
    state_type = Column(String(50), nullable=False, index=True)  # current/pending_hooks/subplot/emotional/character/summary

    # 内容（JSON格式，结构化存储）
    content = Column(JSON, default=dict)

    # 版本控制
    version = Column(Integer, default=1, index=True)

    # 元数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    chapter_from = Column(Integer, default=0)  # 涵盖的起始章节
    chapter_to = Column(Integer, default=0)    # 涵盖的结束章节

    # 关联关系
    book = relationship("Book", back_populates="states")

    # 复合索引
    __table_args__ = (
        Index('ix_state_book_type_version', 'book_id', 'state_type', 'version'),
    )

    def __repr__(self):
        return f"<BookState(id={self.id})>"


class StoryHook(Base):
    """故事伏笔 - 独立表，支持追踪"""
    __tablename__ = "story_hooks"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)

    # 伏笔信息
    hook_name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    importance = Column(String(20), default="normal")  # minor/normal/major/critical

    # 追踪信息
    chapter_introduced = Column(Integer, index=True)  # 引入章节
    chapter_resolved = Column(Integer, nullable=True, index=True)  # 回收章节
    status = Column(String(50), default="pending", index=True)  # pending/active/resolved/abandoned

    # 关联伏笔（伏笔可能关联其他伏笔）
    parent_hook_id = Column(Integer, ForeignKey("story_hooks.id"), nullable=True)

    # 元数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    # 关联关系
    book = relationship("Book", back_populates="hooks")
    parent_hook = relationship("StoryHook", remote_side=[id], backref="child_hooks")

    # 复合索引
    __table_args__ = (
        Index('ix_hooks_book_status', 'book_id', 'status'),
    )

    def __repr__(self):
        return f"<StoryHook(id={self.id})>"


class Character(Base):
    """角色信息 - 独立表"""
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)

    # 角色信息
    name = Column(String(100), nullable=False)
    aliases = Column(JSON, default=list)  # 别名列表
    role_type = Column(String(50), default="supporting")  # protagonist/antagonist/supporting/minor

    # 角色设定
    description = Column(Text, default="")
    background = Column(Text, default="")
    personality = Column(Text, default="")
    goals = Column(Text, default="")
    relationships = Column(JSON, default=dict)  # 与其他角色的关系

    # 追踪信息
    first_appearance = Column(Integer, default=0)  # 首次出场章节
    last_appearance = Column(Integer, default=0)   # 最后出场章节

    # 元数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 关联关系
    book = relationship("Book", back_populates="characters")

    # 复合索引
    __table_args__ = (
        Index('ix_characters_book_role', 'book_id', 'role_type'),
    )

    def __repr__(self):
        return f"<Character(id={self.id})>"


class SettingData(Base):
    """世界观设定 - 独立表"""
    __tablename__ = "settings_data"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)

    # 设定类型
    setting_type = Column(String(50), nullable=False, index=True)  # world/power_system/organization/location/item

    # 设定名称
    name = Column(String(200), nullable=False)

    # 设定内容
    description = Column(Text, default="")
    details = Column(JSON, default=dict)  # 结构化详情

    # 追踪信息
    first_mentioned = Column(Integer, default=0)  # 首次提及章节

    # 元数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 关联关系
    book = relationship("Book", back_populates="settings_data")

    # 复合索引
    __table_args__ = (
        Index('ix_settings_book_type', 'book_id', 'setting_type'),
    )

    def __repr__(self):
        return f"<SettingData(id={self.id})>"


# ==================== 章节模型 ====================

class Chapter(Base):
    """章节模型 - 优化索引"""
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    chapter_number = Column(Integer, nullable=False, index=True)

    # 基本信息
    title = Column(String(200), default="")
    content = Column(Text, default="")
    word_count = Column(Integer, default=0)

    # 审核评分
    audit_score = Column(Float, default=0.0, index=True)
    continuity_score = Column(Float, default=0.0)

    # 审核详情（JSON格式）
    audit_details = Column(JSON, default=dict)
    continuity_details = Column(JSON, default=dict)

    # 章节类型
    chapter_type = Column(String(50), default="normal", index=True)  # normal/opening/climax/ending/transition

    # 状态
    status = Column(String(50), default="draft", index=True)  # draft/writing/review/published/locked

    # 版本控制
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True, index=True)

    # 元数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 关联关系
    book = relationship("Book", back_populates="chapters")
    rag_docs = relationship("RAGDocument", back_populates="chapter", cascade="all, delete-orphan")

    # 复合索引
    __table_args__ = (
        Index('ix_chapters_book_number', 'book_id', 'chapter_number', unique=True),
        Index('ix_chapters_status_book', 'status', 'book_id'),
    )

    def __repr__(self):
        return f"<Chapter(id={self.id})>"


# ==================== 工作流模型 ====================

class WorkflowExecution(Base):
    """工作流执行记录 - 优化索引"""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(100), unique=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    workflow_type = Column(String(50), nullable=False, index=True)

    # 执行状态
    status = Column(String(50), default="pending", index=True)  # pending/queued/running/paused/completed/failed/cancelled
    current_node = Column(String(100), default="")
    progress = Column(Integer, default=0)  # 0-100

    # 优先级（支持优先级队列）
    priority = Column(Integer, default=5)  # 1-10, 数字越小优先级越高

    # 输入输出
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error_message = Column(Text, default="")

    # 重试信息
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # 时间记录
    started_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # 关联关系
    book = relationship("Book", back_populates="workflows")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan", lazy="selectin")

    # 复合索引
    __table_args__ = (
        Index('ix_workflow_book_status', 'book_id', 'status'),
        Index('ix_workflow_type_status', 'workflow_type', 'status'),
        Index('ix_workflow_priority_created', 'priority', 'created_at'),
    )

    def __repr__(self):
        return f"<WorkflowExecution(id={self.id})>"


class WorkflowNode(Base):
    """工作流节点执行记录"""
    __tablename__ = "workflow_nodes"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False, index=True)
    node_id = Column(String(100), nullable=False)
    node_type = Column(String(50), nullable=False)  # agent/function/condition/subflow
    node_name = Column(String(200), default="")

    # 执行状态
    status = Column(String(50), default="pending", index=True)

    # 输入输出
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    stream_output = Column(Text, default="")

    # 执行信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, default=0)

    # Token消耗
    token_usage = Column(JSON, default=dict)

    # 错误信息
    error_message = Column(Text, default="")

    # 关联关系
    workflow = relationship("WorkflowExecution", back_populates="nodes")

    # 复合索引
    __table_args__ = (
        Index('ix_node_workflow_status', 'workflow_id', 'status'),
    )

    def __repr__(self):
        return f"<WorkflowNode(id={self.id})>"


# ==================== 检查点模型 ====================

class Checkpoint(Base):
    """检查点记录"""
    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(100), index=True)
    checkpoint_id = Column(String(100), unique=True, index=True)

    # 状态数据
    state_data = Column(JSON, default=dict)

    # 元数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    node_id = Column(String(100), default="")
    description = Column(String(500), default="")

    # 是否为自动保存
    is_auto_save = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Checkpoint(id={self.id})>"


# ==================== Skill模型 ====================

class SkillTemplate(Base):
    """Skill模板"""
    __tablename__ = "skill_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    genre = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # male/female/universal
    description = Column(Text, default="")

    # Skill内容
    skill_content = Column(Text, default="")
    references = Column(JSON, default=dict)

    # 使用统计
    usage_count = Column(Integer, default=0)

    # 版本控制
    version = Column(String(20), default="1.0.0")

    # 元数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 复合索引
    __table_args__ = (
        Index('ix_skills_genre_category', 'genre', 'category'),
    )

    def __repr__(self):
        return f"<SkillTemplate(id={self.id})>"


# ==================== RAG模型 ====================

class RAGDocument(Base):
    """RAG文档"""
    __tablename__ = "rag_documents"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True, index=True)

    # 文档内容
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="chapter", index=True)

    # 元数据
    doc_metadata = Column(JSON, default=dict)

    # Chroma ID
    chroma_id = Column(String(100), default="", index=True)

    # 嵌入向量维度（用于验证）
    embedding_dim = Column(Integer, default=384)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # 关联关系
    chapter = relationship("Chapter", back_populates="rag_docs")

    # 复合索引
    __table_args__ = (
        Index('ix_rag_book_type', 'book_id', 'content_type'),
    )

    def __repr__(self):
        return f"<RAGDocument(id={self.id})>"


# ==================== 用户模型（预留多租户）====================

class User(Base):
    """用户模型 - 预留多租户支持"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False)

    # 密码（哈希存储）
    password_hash = Column(String(255), nullable=False)

    # 用户状态
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)

    # 配额限制
    max_books = Column(Integer, default=10)
    max_chapters_per_book = Column(Integer, default=500)

    # 元数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id})>"
