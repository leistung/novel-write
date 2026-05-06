"""BaseAgent 基类 - 所有 Agent 的基础类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import time
import logging
from src.skills.loader import get_skill_loader, SkillLoader

logger = logging.getLogger(__name__)

class AgentContext:
    """Agent 执行上下文"""
    
    def __init__(self, book_id: Optional[int] = None, chapter_num: Optional[int] = None, **kwargs):
        self.book_id = book_id
        self.chapter_num = chapter_num
        self.kwargs = kwargs
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文中的值"""
        return self.kwargs.get(key, default)

class BaseAgent(ABC):
    """所有 Agent 的抽象基类"""
    
    def __init__(self, llm):
        self.llm = llm
        self.parser = StrOutputParser()
        self._skill_loader = get_skill_loader()
    
    @property
    def skill_loader(self) -> SkillLoader:
        """获取技能加载器"""
        return self._skill_loader
    
    def create_prompt(self, system_prompt: str, user_prompt: str) -> ChatPromptTemplate:
        """创建提示词模板
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
        
        Returns:
            ChatPromptTemplate: 配置好的提示词模板
        """
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])
    
    def run_chain(self, prompt: ChatPromptTemplate, inputs: Dict[str, Any] = None, 
                  max_retries: int = 3, temperature: float = None) -> Dict[str, Any]:
        """运行 LLM 调用链，带重试机制
        
        Args:
            prompt: 提示词模板
            inputs: 输入参数
            max_retries: 最大重试次数
            temperature: 温度参数（可选）
        
        Returns:
            Dict[str, Any]: 包含 content 和 token_usage 的响应字典
        
        Raises:
            Exception: 多次重试后仍失败
        """
        inputs = inputs or {}
        
        # 配置 LLM
        llm = self.llm
        if temperature is not None:
            llm = llm.with_config({"temperature": temperature})
        
        chain = prompt | llm
        retries = 0
        
        while retries <= max_retries:
            try:
                response = chain.invoke(inputs)
                
                # 检查响应是否有效
                if response is None:
                    raise ValueError("LLM 返回 None")
                
                if hasattr(response, 'content') and response.content is None:
                    raise ValueError("LLM 返回 content 为 None")
                
                # 提取 token 使用情况
                token_usage = None
                if hasattr(response, 'usage_metadata'):
                    token_usage = response.usage_metadata
                
                # 提取内容
                content = response.content if hasattr(response, 'content') else str(response)
                
                return {
                    'content': content,
                    'token_usage': token_usage
                }
            
            except TypeError as e:
                if "null value for 'choices'" in str(e):
                    retries += 1
                    wait_time = 2 ** retries
                    logger.warning(f"LLM 返回异常格式 (choices=null)，第 {retries} 次重试，等待 {wait_time} 秒")
                    time.sleep(wait_time)
                    continue
                raise
            except Exception as e:
                retries += 1
                wait_time = 2 ** retries
                logger.warning(f"LLM 调用失败，第 {retries} 次重试，等待 {wait_time} 秒: {str(e)}")
                time.sleep(wait_time)
                continue
        
        raise Exception(f"LLM 调用失败，已重试 {max_retries} 次")
    
    def get_genre_enhancement(self, genre: str) -> str:
        """获取题材相关的提示词增强内容
        
        Args:
            genre: 题材名称
        
        Returns:
            str: 提示词增强内容
        """
        return self.skill_loader.generate_prompt_enhancement(genre)
    
    @abstractmethod
    def execute(self, context: AgentContext) -> Dict[str, Any]:
        """执行 Agent 核心逻辑
        
        Args:
            context: 执行上下文
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass