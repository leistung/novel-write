from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
import os
from pydantic_settings import BaseSettings

class LLMConfig(BaseSettings):
    provider: str = "openai"
    base_url: str = "https://api-inference.modelscope.cn/v1/"
    api_key: str = "xxx"
    model: str = "Qwen/Qwen3.5-35B-A3B"
    temperature: float = 0.7
    max_tokens: int = 8192

    class Config:
        env_file = ".env"
        env_prefix = "inkos_llm_"
        case_sensitive = False

class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            base_url=config.base_url,
            api_key=config.api_key
        )

    def chat_completion(self, messages, tools=None):
        if tools:
            # 处理工具调用
            from langchain_core.messages import HumanMessage
            from langchain_core.tools import Tool
            
            # 创建工具列表
            langchain_tools = []
            for tool in tools:
                langchain_tools.append(
                    Tool(
                        name=tool["name"],
                        func=tool["func"],
                        description=tool["description"]
                    )
                )
            
            # 使用工具调用
            from langchain_core.runnables import RunnablePassthrough
            from langchain_core.output_parsers import JsonOutputParser
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant"),
                ("human", "{input}")
            ])
            
            chain = prompt | self.client.bind_tools(langchain_tools) | StrOutputParser()
            return chain.invoke({"input": messages[0]["content"]})
        else:
            # 普通聊天完成
            prompt = ChatPromptTemplate.from_messages(messages)
            chain = prompt | self.client | StrOutputParser()
            return chain.invoke({})

    def chat_with_tools(self, messages, tools):
        return self.chat_completion(messages, tools)

# 创建 LLM 客户端实例
config = LLMConfig()
llm_client = LLMClient(config)
