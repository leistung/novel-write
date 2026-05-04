from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import time
import logging

logger = logging.getLogger(__name__)

class AgentContext:
    def __init__(self, book_id: str, chapter_num: Optional[int] = None, **kwargs):
        self.book_id = book_id
        self.chapter_num = chapter_num
        self.kwargs = kwargs

class BaseAgent(ABC):
    def __init__(self, llm):
        self.llm = llm
        self.parser = StrOutputParser()
    
    def create_prompt(self, system_prompt: str, user_prompt: str) -> ChatPromptTemplate:
        """创建提示词模板"""
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])
    
    def run_chain(self, prompt: ChatPromptTemplate, inputs: Dict[str, Any] = {}, max_retries: int = 3) -> Dict[str, Any]:
        """运行链，带重试机制"""
        chain = prompt | self.llm
        retries = 0
        
        while retries <= max_retries:
            try:
                response = chain.invoke(inputs)
                
                # 检查响应是否有效
                if response is None:
                    raise ValueError("API 返回 None")
                
                if hasattr(response, 'content') and response.content is None:
                    raise ValueError("API 返回 content 为 None")
                
                # 提取token使用情况
                token_usage = None
                if hasattr(response, 'usage_metadata'):
                    token_usage = response.usage_metadata
                
                # 提取内容
                content = response.content
                
                return {
                    'content': content,
                    'token_usage': token_usage
                }
            
            except TypeError as e:
                if "null value for 'choices'" in str(e):
                    retries += 1
                    wait_time = 2 ** retries
                    logger.warning(f"API 返回异常格式 (choices=null)，第 {retries} 次重试，等待 {wait_time} 秒")
                    time.sleep(wait_time)
                    continue
                raise
            except Exception as e:
                retries += 1
                wait_time = 2 ** retries
                logger.warning(f"API 调用失败，第 {retries} 次重试，等待 {wait_time} 秒: {str(e)}")
                time.sleep(wait_time)
                continue
        
        raise Exception(f"API 调用失败，已重试 {max_retries} 次")
