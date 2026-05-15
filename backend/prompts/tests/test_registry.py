"""提示词注册中心测试"""
import pytest
import tempfile
from pathlib import Path
from prompts.registry.manager import PromptRegistry, PromptMetadata


class TestPromptRegistry:
    """测试提示词注册中心"""
    
    def test_register_and_get(self):
        """测试注册和获取"""
        registry = PromptRegistry()
        
        content = {
            "system": "你是一个助手",
            "user": "请回答：{{ question }}"
        }
        
        version = registry.register(
            name="test/prompt",
            content=content,
            version="1.0.0",
            metadata=PromptMetadata(name="test/prompt", description="测试")
        )
        
        assert version.version == "1.0.0"
        
        retrieved = registry.get("test/prompt")
        assert retrieved is not None
        assert retrieved.content["system"] == "你是一个助手"
    
    def test_version_management(self):
        """测试版本管理"""
        registry = PromptRegistry()
        
        # 注册多个版本
        registry.register(
            name="test/multi",
            content={"system": "v1", "user": "test"},
            version="1.0.0"
        )
        
        registry.register(
            name="test/multi",
            content={"system": "v2", "user": "test"},
            version="2.0.0"
        )
        
        # 获取特定版本
        v1 = registry.get("test/multi", "1.0.0")
        v2 = registry.get("test/multi", "2.0.0")
        
        assert v1.content["system"] == "v1"
        assert v2.content["system"] == "v2"
        
        # 获取激活版本
        active = registry.get("test/multi")
        assert active.version == "2.0.0"  # 最后注册的默认激活
    
    def test_list_prompts(self):
        """测试列出提示词"""
        registry = PromptRegistry()
        
        registry.register(
            name="architect/foundation",
            content={"system": "", "user": ""},
            metadata=PromptMetadata(name="architect/foundation", tags=["architect"])
        )
        
        registry.register(
            name="writer/chapter",
            content={"system": "", "user": ""},
            metadata=PromptMetadata(name="writer/chapter", tags=["writer"])
        )
        
        all_prompts = registry.list_prompts()
        assert len(all_prompts) == 2
        
        architect_prompts = registry.list_prompts(tag="architect")
        assert len(architect_prompts) == 1
        assert "architect/foundation" in architect_prompts
    
    def test_compare_versions(self):
        """测试版本比较"""
        registry = PromptRegistry()
        
        registry.register(
            name="test/compare",
            content={"system": "old", "user": "test"},
            version="1.0.0"
        )
        
        registry.register(
            name="test/compare",
            content={"system": "new", "user": "test"},
            version="2.0.0"
        )
        
        diff = registry.compare_versions("test/compare", "1.0.0", "2.0.0")
        
        assert diff["version_a"] == "1.0.0"
        assert diff["version_b"] == "2.0.0"
        assert diff["content_diff"]["system_changed"] is True
        assert diff["content_diff"]["user_changed"] is False
    
    def test_load_from_yaml(self, tmp_path):
        """测试从YAML加载"""
        yaml_content = """
name: test/yaml
version: "1.0.0"
description: 从YAML加载的测试
tags: [test]
system_template: |
  系统提示词
user_template: |
  用户提示词 {{ variable }}
parameters:
  variable:
    type: string
    required: true
activate: true
"""
        
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content, encoding='utf-8')
        
        registry = PromptRegistry()
        version = registry.load_from_yaml(yaml_file)
        
        assert version.version == "1.0.0"
        assert version.metadata.name == "test/yaml"
        assert "variable" in version.parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
