"""提示词输入净化和安全防护

防范提示词注入攻击、恶意内容、敏感信息泄露
"""
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum


class RiskLevel(Enum):
    """风险等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SanitizationResult:
    """净化结果"""
    original: str
    sanitized: str
    risk_level: RiskLevel
    issues: List[Dict]
    is_safe: bool
    modifications: List[str]


class PromptSanitizer:
    """提示词输入净化器
    
    防范以下攻击:
    1. 提示词注入 (Prompt Injection)
    2. 越狱攻击 (Jailbreak)
    3. 数据提取攻击
    4. 指令覆盖攻击
    """
    
    # 危险模式 - 提示词注入
    DANGEROUS_PATTERNS = [
        # 指令覆盖
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(all\s+)?(above|previous)",
        r"forget\s+(all\s+)?(your\s+)?instructions",
        r"new\s+instructions?:",
        r"system\s*:\s*",
        r"user\s*:\s*",
        r"assistant\s*:\s*",
        # 角色扮演攻击
        r"pretend\s+(to\s+be|you\s+are)",
        r"act\s+as\s+(if\s+)?you\s+(are|were)",
        r"you\s+are\s+now\s+",
        r"from\s+now\s+on\s+you\s+are",
        # 越狱关键词
        r"jailbreak",
        r"DAN\s*\(Do\s+Anything\s+Now\)",
        r"developer\s+mode",
        r"sudo\s+mode",
        # 提示词泄露
        r"repeat\s+(the\s+)?(words|text|prompt|instructions)",
        r"output\s+(the\s+)?(initial|above|previous)\s+(prompt|instruction)",
        r"what\s+are\s+your\s+instructions",
        r"show\s+me\s+your\s+system\s+prompt",
    ]
    
    # 敏感信息模式
    SENSITIVE_PATTERNS = [
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # 信用卡
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}",  # 邮箱
        r"\b(?:password|pwd|secret|key|token)\s*[=:]\s*\S+",  # 凭证
        r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",  # 私钥
        r"sk-[a-zA-Z0-9]{48}",  # OpenAI API Key
        r"[a-zA-Z0-9_-]{39}",  # AWS Access Key ID
    ]
    
    # 分隔符 - 用于隔离用户输入
    DELIMITERS = {
        "xml": ("<user_input>", "</user_input>"),
        "json": ('{"user_input": "', '"}'),
        "markdown": ("```\n", "\n```"),
        "quote": ('"""\n', '\n"""'),
    }
    
    def __init__(
        self,
        max_length: int = 10000,
        allow_markdown: bool = True,
        delimiter_type: str = "xml",
        custom_patterns: Optional[List[str]] = None
    ):
        self.max_length = max_length
        self.allow_markdown = allow_markdown
        self.delimiter_type = delimiter_type
        self.custom_patterns = custom_patterns or []
        
        # 编译正则
        self._dangerous_regex = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
        self._sensitive_regex = [re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_PATTERNS]
        self._custom_regex = [re.compile(p, re.IGNORECASE) for p in self.custom_patterns]
    
    def sanitize(
        self,
        text: str,
        context: str = "user_input",
        strict_mode: bool = False
    ) -> SanitizationResult:
        """净化输入文本
        
        Args:
            text: 原始输入
            context: 上下文标识
            strict_mode: 严格模式（拒绝任何可疑内容）
            
        Returns:
            SanitizationResult: 净化结果
        """
        issues = []
        modifications = []
        original = text
        
        # 1. 长度检查
        if len(text) > self.max_length:
            issues.append({
                "type": "length_exceeded",
                "severity": RiskLevel.MEDIUM,
                "message": f"Input exceeds max length ({len(text)} > {self.max_length})"
            })
            text = text[:self.max_length]
            modifications.append("truncated_to_max_length")
        
        # 2. 检测危险模式
        for pattern in self._dangerous_regex:
            matches = pattern.findall(text)
            if matches:
                issues.append({
                    "type": "injection_attempt",
                    "severity": RiskLevel.HIGH,
                    "pattern": pattern.pattern[:50],
                    "matches": matches[:3]
                })
        
        # 3. 检测敏感信息
        for pattern in self._sensitive_regex:
            matches = pattern.findall(text)
            if matches:
                issues.append({
                    "type": "sensitive_data",
                    "severity": RiskLevel.CRITICAL,
                    "pattern": pattern.pattern[:50],
                    "count": len(matches)
                })
                # 脱敏处理
                text = pattern.sub("[REDACTED]", text)
                modifications.append("sensitive_data_redacted")
        
        # 4. 检测自定义模式
        for pattern in self._custom_regex:
            matches = pattern.findall(text)
            if matches:
                issues.append({
                    "type": "custom_violation",
                    "severity": RiskLevel.MEDIUM,
                    "pattern": pattern.pattern[:50]
                })
        
        # 5. 控制字符清理
        cleaned_text = self._clean_control_chars(text)
        if cleaned_text != text:
            modifications.append("control_chars_removed")
            text = cleaned_text
        
        # 6. 添加分隔符隔离
        if self.delimiter_type != "none":
            text = self._wrap_with_delimiter(text, context)
            modifications.append(f"wrapped_with_{self.delimiter_type}_delimiter")
        
        # 7. 计算风险等级
        risk_level = self._calculate_risk_level(issues)
        is_safe = risk_level not in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # 严格模式下，任何风险都视为不安全
        if strict_mode and issues:
            is_safe = False
        
        return SanitizationResult(
            original=original,
            sanitized=text,
            risk_level=risk_level,
            issues=issues,
            is_safe=is_safe,
            modifications=modifications
        )
    
    def _clean_control_chars(self, text: str) -> str:
        """清理控制字符"""
        # 保留换行、制表符，移除其他控制字符
        allowed = set('\n\r\t')
        return ''.join(c for c in text if c >= ' ' or c in allowed)
    
    def _wrap_with_delimiter(self, text: str, context: str) -> str:
        """使用分隔符包装文本"""
        start, end = self.DELIMITERS.get(self.delimiter_type, self.DELIMITERS["xml"])
        # 转义结束分隔符，防止注入
        escaped_text = text.replace(end, end.replace(">", "&gt;").replace("\"", "&quot;"))
        return f"{start}{escaped_text}{end}"
    
    def _calculate_risk_level(self, issues: List[Dict]) -> RiskLevel:
        """计算整体风险等级"""
        if not issues:
            return RiskLevel.SAFE
        
        severity_order = {
            RiskLevel.CRITICAL: 4,
            RiskLevel.HIGH: 3,
            RiskLevel.MEDIUM: 2,
            RiskLevel.LOW: 1,
            RiskLevel.SAFE: 0
        }
        
        max_severity = max(
            (severity_order.get(i["severity"], 0) for i in issues),
            default=0
        )
        
        for level, order in severity_order.items():
            if order == max_severity:
                return level
        
        return RiskLevel.SAFE
    
    def validate_batch(
        self,
        texts: List[str],
        fail_fast: bool = False
    ) -> Tuple[List[SanitizationResult], bool]:
        """批量验证
        
        Returns:
            (results, all_safe)
        """
        results = []
        all_safe = True
        
        for text in texts:
            result = self.sanitize(text)
            results.append(result)
            
            if not result.is_safe:
                all_safe = False
                if fail_fast:
                    break
        
        return results, all_safe
    
    def create_safe_template(
        self,
        template: str,
        variable_name: str = "user_input"
    ) -> str:
        """创建安全模板 - 在变量位置添加防护
        
        Args:
            template: 原始模板
            variable_name: 需要保护的变量名
            
        Returns:
            加固后的模板
        """
        start, end = self.DELIMITERS.get(self.delimiter_type, self.DELIMITERS["xml"])
        
        # 替换变量引用
        patterns = [
            rf"{{{variable_name}}}",  # {user_input}
            rf"{{{{\s*{variable_name}\s*}}}}",  # {{ user_input }}
        ]
        
        safe_template = template
        for pattern in patterns:
            replacement = f"{start}{{{variable_name}}}{end}"
            safe_template = re.sub(pattern, replacement, safe_template)
        
        return safe_template
