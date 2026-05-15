"""Token优化器 - 减少token使用，降低成本"""
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TokenStats:
    """Token统计"""
    original_tokens: int
    optimized_tokens: int
    savings: int
    savings_percent: float


class TokenOptimizer:
    """Token优化器
    
    优化策略:
    1. 去除冗余空白
    2. 简化标点
    3. 移除注释
    4. 缩写常见短语
    5. 智能截断
    """
    
    # 常见冗余短语映射
    REDUNDANT_PHRASES = {
        "请确保": "确保",
        "你必须": "",
        "重要的是": "",
        "请注意": "注意",
        "需要做的是": "",
        "换句话说": "即",
        "例如说": "如",
        "等等": "等",
        "等等等等": "等",
        "非常": "",
        "特别": "",
        "相当": "",
    }
    
    # 可以移除的填充词
    FILLER_WORDS = [
        r'\s+很\s+',
        r'\s+非常\s+',
        r'\s+特别\s+',
        r'\s+相当\s+',
        r'\s+真的\s+',
        r'\s+确实\s+',
    ]
    
    def __init__(self, aggressive: bool = False):
        self.aggressive = aggressive
        self._removed_chars = 0
    
    def optimize(
        self,
        text: str,
        max_tokens: Optional[int] = None,
        preserve_structure: bool = True
    ) -> Tuple[str, TokenStats]:
        """优化文本以减少token
        
        Args:
            text: 原始文本
            max_tokens: 最大token限制
            preserve_structure: 是否保留结构（如JSON格式）
            
        Returns:
            (优化后文本, 统计信息)
        """
        original = text
        original_tokens = self._estimate_tokens(original)
        
        # 1. 清理空白
        text = self._clean_whitespace(text)
        
        # 2. 移除注释（非结构保留模式）
        if not preserve_structure:
            text = self._remove_comments(text)
        
        # 3. 简化冗余短语
        text = self._simplify_phrases(text)
        
        # 4. 移除填充词
        if self.aggressive:
            text = self._remove_fillers(text)
        
        # 5. 智能截断
        if max_tokens:
            text = self._smart_truncate(text, max_tokens, preserve_structure)
        
        optimized_tokens = self._estimate_tokens(text)
        savings = original_tokens - optimized_tokens
        
        stats = TokenStats(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            savings=savings,
            savings_percent=round(savings / original_tokens * 100, 2) if original_tokens > 0 else 0
        )
        
        return text, stats
    
    def optimize_prompt(
        self,
        system: Optional[str],
        user: str,
        max_tokens: Optional[int] = None
    ) -> Tuple[Optional[str], str, TokenStats]:
        """优化提示词对"""
        opt_system = None
        if system:
            opt_system, stats_sys = self.optimize(system, preserve_structure=True)
        else:
            stats_sys = TokenStats(0, 0, 0, 0)
        
        opt_user, stats_user = self.optimize(user, preserve_structure=False)
        
        # 合并统计
        total_stats = TokenStats(
            original_tokens=stats_sys.original_tokens + stats_user.original_tokens,
            optimized_tokens=stats_sys.optimized_tokens + stats_user.optimized_tokens,
            savings=stats_sys.savings + stats_user.savings,
            savings_percent=round(
                (stats_sys.savings + stats_user.savings) / 
                (stats_sys.original_tokens + stats_user.original_tokens) * 100, 2
            ) if (stats_sys.original_tokens + stats_user.original_tokens) > 0 else 0
        )
        
        return opt_system, opt_user, total_stats
    
    def _estimate_tokens(self, text: str) -> int:
        """估算token数量"""
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - english_chars - chinese_chars
        
        return int(english_chars / 4 + chinese_chars / 1.5 + other_chars / 6)
    
    def _clean_whitespace(self, text: str) -> str:
        """清理多余空白"""
        # 合并多个空格
        text = re.sub(r' +', ' ', text)
        # 合并多个换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 移除行尾空格
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        return text.strip()
    
    def _remove_comments(self, text: str) -> str:
        """移除注释"""
        # Python风格注释
        text = re.sub(r'#.*$', '', text, flags=re.MULTILINE)
        # HTML风格注释
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        return text
    
    def _simplify_phrases(self, text: str) -> str:
        """简化冗余短语"""
        for phrase, replacement in self.REDUNDANT_PHRASES.items():
            text = text.replace(phrase, replacement)
        return text
    
    def _remove_fillers(self, text: str) -> str:
        """移除填充词"""
        for pattern in self.FILLER_WORDS:
            text = re.sub(pattern, ' ', text)
        return self._clean_whitespace(text)
    
    def _smart_truncate(
        self,
        text: str,
        max_tokens: int,
        preserve_structure: bool
    ) -> str:
        """智能截断"""
        current_tokens = self._estimate_tokens(text)
        
        if current_tokens <= max_tokens:
            return text
        
        if preserve_structure:
            # 尝试保留结构的前提下截断
            return self._structured_truncate(text, max_tokens)
        else:
            # 简单截断
            chars_to_keep = int(max_tokens * 3)  # 粗略估计
            return text[:chars_to_keep] + "..."
    
    def _structured_truncate(self, text: str, max_tokens: int) -> str:
        """结构化截断 - 尝试保留关键部分"""
        lines = text.split('\n')
        
        # 优先级：指令 > 示例 > 说明
        priority_lines = []
        normal_lines = []
        example_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('```', '###', '##')):
                priority_lines.append(line)
            elif '示例' in stripped or 'example' in stripped.lower():
                example_lines.append(line)
            else:
                normal_lines.append(line)
        
        # 组合，优先保留高优先级内容
        result_lines = priority_lines.copy()
        current_text = '\n'.join(result_lines)
        
        for line in normal_lines:
            test_text = current_text + '\n' + line
            if self._estimate_tokens(test_text) <= max_tokens:
                result_lines.append(line)
                current_text = test_text
            else:
                break
        
        return '\n'.join(result_lines) + "\n..."
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """分析文本的token使用情况"""
        lines = text.split('\n')
        
        analysis = {
            "total_chars": len(text),
            "total_lines": len(lines),
            "estimated_tokens": self._estimate_tokens(text),
            "empty_lines": sum(1 for l in lines if not l.strip()),
            "avg_line_length": len(text) / len(lines) if lines else 0,
            "whitespace_chars": len(re.findall(r'\s', text)),
            "chinese_chars": len(re.findall(r'[\u4e00-\u9fff]', text)),
            "english_words": len(re.findall(r'[a-zA-Z]+', text)),
        }
        
        # 找出最长的行
        if lines:
            longest_line = max(lines, key=len)
            analysis["longest_line_length"] = len(longest_line)
            analysis["longest_line_preview"] = longest_line[:100]
        
        return analysis
    
    def get_optimization_suggestions(self, text: str) -> List[str]:
        """获取优化建议"""
        suggestions = []
        analysis = self.analyze(text)
        
        if analysis["empty_lines"] > analysis["total_lines"] * 0.2:
            suggestions.append("空白行过多，建议清理")
        
        if analysis["whitespace_chars"] > analysis["total_chars"] * 0.3:
            suggestions.append("空白字符占比高，建议优化格式")
        
        if analysis["avg_line_length"] > 200:
            suggestions.append("行平均长度过长，建议分行")
        
        # 检查冗余短语
        for phrase in self.REDUNDANT_PHRASES:
            if phrase in text:
                suggestions.append(f"发现冗余短语: '{phrase}'")
                break
        
        return suggestions
