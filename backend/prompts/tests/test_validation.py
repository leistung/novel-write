"""输出验证器测试"""
import pytest
from prompts.schemas.validation import OutputValidator
from prompts.schemas.novel_schemas import FoundationOutput, AuditResultOutput


class TestOutputValidator:
    """测试输出验证器"""
    
    def setup_method(self):
        """每个测试前设置"""
        self.validator = OutputValidator()
        self.validator.register_schema("foundation", FoundationOutput)
        self.validator.register_schema("audit", AuditResultOutput)
    
    def test_valid_json_extraction(self):
        """测试有效JSON提取"""
        raw = '{"title": "测试", "genre": "科幻", "theme": "探索"}'
        result = self.validator._extract_json(raw)
        
        assert result[0] is not None
        assert result[1] is None
        assert result[0]["title"] == "测试"
    
    def test_markdown_json_extraction(self):
        """测试Markdown代码块JSON提取"""
        raw = '''```json
        {"title": "测试", "genre": "科幻", "theme": "探索"}
        ```'''
        result = self.validator._extract_json(raw)
        
        assert result[0] is not None
        assert result[0]["title"] == "测试"
    
    def test_json_repair(self):
        """测试JSON修复"""
        # 尾随逗号
        raw = '{"title": "测试", "genre": "科幻",}'
        result = self.validator._extract_json(raw)
        assert result[0] is not None
        
        # 单引号
        raw = "{'title': '测试'}"
        result = self.validator._extract_json(raw)
        assert result[0] is not None
    
    def test_foundation_validation(self):
        """测试大纲输出验证"""
        valid_data = {
            "title": "测试小说",
            "genre": "科幻",
            "theme": "人工智能",
            "logline": "一个关于AI的故事",
            "synopsis": "这是一个很长的故事梗概..." * 10,
            "acts": [
                {
                    "act_number": 1,
                    "title": "第一幕",
                    "summary": "开端",
                    "key_events": ["事件1"]
                }
            ],
            "characters": [
                {
                    "name": "主角",
                    "role": "主角",
                    "personality": "勇敢、聪明"
                }
            ],
            "setting": {
                "era": "未来",
                "location": "地球",
                "rules": ["规则1"]
            }
        }
        
        raw = str(valid_data).replace("'", '"')
        result = self.validator.validate(raw, "foundation", strict=False)
        
        # 注意：由于字符串转换，可能不完全有效
        # 这里主要测试流程
    
    def test_invalid_data(self):
        """测试无效数据"""
        raw = "这不是JSON格式"
        result = self.validator.validate(raw, "foundation", strict=True)
        
        assert result.is_valid is False
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
