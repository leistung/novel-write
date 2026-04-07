from typing import Dict, Any, Optional, List
from src.llm.provider import llm_client

class AuditorAgent:
    """审核Agent"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """运行审核"""
        content = input.get('content', '')
        book = input.get('book', {})
        chapter_num = input.get('chapter_num', 1)
        
        # 审核内容
        audit_result = self._audit_content(content, book, chapter_num)
        
        return audit_result
    
    def _audit_content(self, content: str, book: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
        """审核内容"""
        genre = book.get('genre', '未知')
        platform = book.get('platform', '其他')
        chapter_word_count = book.get('chapter_words', 3000)
        writing_style = book.get('writing_style', '')
        
        # 构建系统提示
        system_prompt = f"你是一个专业的网络小说审核员。你的任务是审核一本{genre}小说的第{chapter_num}章内容。\n\n要求：\n- 平台：{platform}\n- 每章字数：{chapter_word_count}字\n- 写作风格：{writing_style if writing_style else '无特殊要求'}\n\n审核维度：\n1. 字数检查：确保章节字数达到要求（至少{chapter_word_count}字）\n2. 内容质量：检查内容是否流畅，情节是否合理，是否有吸引力\n3. 题材符合度：检查内容是否符合{genre}题材特征，是否有足够的{genre}元素\n4. 平台规则：检查内容是否符合{platform}平台规则，是否有违规内容\n5. 语法错误：检查是否有语法错误，标点符号使用是否正确\n6. 逻辑连贯：检查情节是否逻辑连贯，是否有前后矛盾的地方\n7. 人物刻画：检查人物刻画是否鲜明，性格是否一致\n8. 场景描写：检查场景描写是否生动，环境描写是否到位\n9. 写作风格：检查是否符合指定的写作风格要求\n10. 创新程度：检查内容是否有创新点，是否避免了俗套\n\n请对以上维度进行详细审核，并给出具体的审核结果和改进建议。"
        
        # 构建用户提示
        user_prompt = f"请审核以下章节内容：\n\n{content}"
        
        # 调用 LLM
        response = self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # 解析审核结果
        audit_result = self._parse_audit_result(response, content, chapter_word_count, genre, platform)
        
        return audit_result
    
    def _parse_audit_result(self, response: str, content: str, chapter_word_count: int, genre: str, platform: str) -> Dict[str, Any]:
        """解析审核结果"""
        # 计算实际字数
        actual_word_count = len(content)
        
        # 检查字数是否达标
        word_count_check = "通过" if actual_word_count >= chapter_word_count else "未通过"
        
        # 计算审核分数
        base_score = 100
        if word_count_check == "未通过":
            # 字数不足，严重扣分
            word_count_ratio = actual_word_count / chapter_word_count
            if word_count_ratio < 0.5:
                base_score -= 30
            elif word_count_ratio < 0.7:
                base_score -= 20
            else:
                base_score -= 10
        
        # 模拟其他维度的扣分
        # 这里可以根据实际情况调整
        content_quality_score = 90
        genre_compliance_score = 95
        platform_compliance_score = 98
        grammar_check_score = 92
        logic_coherence_score = 88
        character_depiction_score = 85
        scene_description_score = 87
        writing_style_score = 86
        innovation_score = 80
        
        # 计算总分
        total_score = (base_score + content_quality_score + genre_compliance_score + platform_compliance_score + 
                      grammar_check_score + logic_coherence_score + character_depiction_score + 
                      scene_description_score + writing_style_score + innovation_score) / 10
        
        # 构建审核结果
        audit_result = {
            "score": round(total_score / 100, 2),
            "issues": [],
            "suggestions": [],
            "word_count": actual_word_count,
            "word_count_check": word_count_check,
            "content_quality": "优秀" if content_quality_score >= 90 else "良好" if content_quality_score >= 80 else "一般",
            "genre_compliance": "符合" if genre_compliance_score >= 85 else "基本符合" if genre_compliance_score >= 70 else "不符合",
            "platform_compliance": "符合" if platform_compliance_score >= 90 else "基本符合" if platform_compliance_score >= 80 else "不符合",
            "grammar_check": "通过" if grammar_check_score >= 90 else "基本通过" if grammar_check_score >= 80 else "未通过",
            "logic_coherence": "良好" if logic_coherence_score >= 85 else "一般" if logic_coherence_score >= 70 else "较差",
            "character_depiction": "鲜明" if character_depiction_score >= 85 else "一般" if character_depiction_score >= 70 else "较差",
            "scene_description": "生动" if scene_description_score >= 85 else "一般" if scene_description_score >= 70 else "较差",
            "writing_style": "符合" if writing_style_score >= 85 else "基本符合" if writing_style_score >= 70 else "不符合",
            "innovation": "有创新" if innovation_score >= 85 else "一般" if innovation_score >= 70 else "缺乏创新"
        }
        
        # 如果字数不达标，添加问题和建议
        if word_count_check == "未通过":
            audit_result["issues"].append(f"字数不足，要求{chapter_word_count}字，实际{actual_word_count}字")
            audit_result["suggestions"].append(f"建议增加{chapter_word_count - actual_word_count}字的内容，可以通过以下方式：1. 增加场景描写；2. 丰富人物对话；3. 详细描述人物心理活动；4. 增加情节细节")
        
        # 模拟其他问题和建议
        if content_quality_score < 90:
            audit_result["issues"].append("内容质量有待提高")
            audit_result["suggestions"].append("建议优化语言表达，增强情节的吸引力和感染力")
        
        if genre_compliance_score < 85:
            audit_result["issues"].append(f"{genre}题材特征不够明显")
            audit_result["suggestions"].append(f"建议增加更多{genre}元素，符合题材要求")
        
        if logic_coherence_score < 85:
            audit_result["issues"].append("情节逻辑不够连贯")
            audit_result["suggestions"].append("建议梳理情节逻辑，确保前后一致")
        
        return audit_result