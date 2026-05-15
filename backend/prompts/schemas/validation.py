"""LLM输出验证 - JSON Schema和Pydantic双保险"""
import json
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional, Type, List, Union
from pydantic import BaseModel, ValidationError, Field, field_validator


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    data: Optional[Dict[str, Any]]
    errors: List[str]
    raw_response: str
    schema_name: str


class OutputValidator:
    """输出验证器
    
    提供多层验证:
    1. JSON格式提取和修复
    2. Pydantic模型验证
    3. 业务规则验证
    """
    
    def __init__(self):
        self._schemas: Dict[str, Type[BaseModel]] = {}
    
    def register_schema(self, name: str, schema_class: Type[BaseModel]):
        """注册验证模式"""
        self._schemas[name] = schema_class
    
    def validate(
        self,
        raw_response: str,
        schema_name: str,
        strict: bool = True
    ) -> ValidationResult:
        """验证LLM输出
        
        Args:
            raw_response: 原始响应文本
            schema_name: 模式名称
            strict: 是否严格模式（失败时返回None）
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        
        # 1. 提取JSON
        json_data, extract_error = self._extract_json(raw_response)
        if extract_error:
            errors.append(f"JSON extraction failed: {extract_error}")
            if strict:
                return ValidationResult(
                    is_valid=False,
                    data=None,
                    errors=errors,
                    raw_response=raw_response,
                    schema_name=schema_name
                )
        
        # 2. Pydantic验证
        schema_class = self._schemas.get(schema_name)
        if schema_class and json_data:
            try:
                validated = schema_class.model_validate(json_data)
                json_data = validated.model_dump()
            except ValidationError as e:
                errors.extend([f"{err['loc']}: {err['msg']}" for err in e.errors()])
                if strict:
                    return ValidationResult(
                        is_valid=False,
                        data=None,
                        errors=errors,
                        raw_response=raw_response,
                        schema_name=schema_name
                    )
        
        # 3. 业务规则验证
        if json_data:
            business_errors = self._validate_business_rules(json_data, schema_name)
            errors.extend(business_errors)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            data=json_data if is_valid or not strict else None,
            errors=errors,
            raw_response=raw_response,
            schema_name=schema_name
        )
    
    def _extract_json(self, text: str) -> tuple[Optional[Dict], Optional[str]]:
        """从文本中提取JSON
        
        支持多种格式:
        - 纯JSON
        - Markdown代码块 ```json
        - 混合文本中的JSON
        """
        text = text.strip()
        
        # 尝试直接解析
        try:
            return json.loads(text), None
        except json.JSONDecodeError:
            pass
        
        # 尝试提取Markdown代码块
        patterns = [
            r'```(?:json)?\s*\n?(.*?)\n?```',  # ```json ... ```
            r'`(.*?)`',  # `...`
            r'\{.*\}',  # 最外层大括号
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # 清理常见格式问题
                    cleaned = self._clean_json_string(match)
                    return json.loads(cleaned), None
                except json.JSONDecodeError:
                    continue
        
        # 尝试修复常见JSON错误
        repaired = self._repair_json(text)
        if repaired:
            try:
                return json.loads(repaired), None
            except json.JSONDecodeError:
                pass
        
        return None, "Could not extract valid JSON from response"
    
    def _clean_json_string(self, text: str) -> str:
        """清理JSON字符串"""
        # 移除BOM
        text = text.lstrip('\ufeff')
        # 移除首尾空白
        text = text.strip()
        # 处理转义
        text = text.replace('\\n', '\n').replace('\\t', '\t')
        return text
    
    def _repair_json(self, text: str) -> Optional[str]:
        """尝试修复损坏的JSON"""
        # 查找最外层的大括号
        start = text.find('{')
        end = text.rfind('}')
        
        if start == -1 or end == -1 or start >= end:
            return None
        
        json_str = text[start:end+1]
        
        # 常见修复
        repairs = [
            # 移除尾随逗号
            (r',(\s*[}\]])', r'\1'),
            # 修复单引号
            (r"'([^']*?)'", r'"\1"'),
            # 修复无引号键
            (r'(\{|,|\s)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3'),
        ]
        
        for pattern, replacement in repairs:
            json_str = re.sub(pattern, replacement, json_str)
        
        return json_str
    
    def _validate_business_rules(
        self,
        data: Dict[str, Any],
        schema_name: str
    ) -> List[str]:
        """业务规则验证"""
        errors = []
        
        if schema_name == "foundation":
            # 大纲结构验证
            if "outline" in data:
                outline = data["outline"]
                if not outline.get("title"):
                    errors.append("Outline title is required")
                if not outline.get("acts"):
                    errors.append("At least one act is required")
        
        elif schema_name == "chapter_outline":
            # 章节验证
            if "chapters" in data:
                for i, ch in enumerate(data["chapters"]):
                    if not ch.get("title"):
                        errors.append(f"Chapter {i+1} missing title")
                    if ch.get("word_count", 0) < 0:
                        errors.append(f"Chapter {i+1} invalid word_count")