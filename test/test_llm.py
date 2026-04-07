#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM调用
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.provider import LLMClient


def test_llm_calls():
    """测试LLM调用"""
    print("开始测试LLM调用...")
    
    # 初始化 LLM 客户端
    from src.llm.provider import LLMConfig
    config = LLMConfig()
    llm_client = LLMClient(config)
    print("LLM 客户端初始化完成")
    
    # 测试简单的聊天完成
    print("\n1. 测试简单的聊天完成...")
    try:
        messages = [
            {"role": "system", "content": "你是一个助手，帮助用户回答问题。"},
            {"role": "user", "content": "你好，请问你能做什么？"}
        ]
        response = llm_client.chat_completion(messages=messages)
        print(f"LLM 响应: {response}")
    except Exception as e:
        print(f"LLM 调用失败: {str(e)}")
    
    # 测试生成故事开头
    print("\n2. 测试生成故事开头...")
    try:
        messages = [
            {"role": "system", "content": "你是一个作家，擅长创作玄幻小说。"},
            {"role": "user", "content": "请为一本玄幻小说生成一个开头，主角是一个普通山村少年，意外获得修仙传承。"}
        ]
        response = llm_client.chat_completion(messages=messages)
        print(f"故事开头: {response}")
    except Exception as e:
        print(f"LLM 调用失败: {str(e)}")
    
    # 测试生成章节标题
    print("\n3. 测试生成章节标题...")
    try:
        messages = [
            {"role": "system", "content": "你是一个作家，擅长创作玄幻小说。"},
            {"role": "user", "content": "请为玄幻小说的第一章生成一个标题，内容是主角发现神秘山洞，获得修仙传承。"}
        ]
        response = llm_client.chat_completion(messages=messages)
        print(f"章节标题: {response}")
    except Exception as e:
        print(f"LLM 调用失败: {str(e)}")
    
    # 测试生成故事大纲
    print("\n4. 测试生成故事大纲...")
    try:
        messages = [
            {"role": "system", "content": "你是一个作家，擅长创作玄幻小说。"},
            {"role": "user", "content": "请为一本玄幻小说生成一个大纲，主角是一个普通山村少年，意外获得修仙传承，开始踏上修仙之路。"}
        ]
        response = llm_client.chat_completion(messages=messages)
        print(f"故事大纲: {response}")
    except Exception as e:
        print(f"LLM 调用失败: {str(e)}")
    
    print("\nLLM 调用测试完成！")


if __name__ == "__main__":
    test_llm_calls()
