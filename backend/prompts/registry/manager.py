"""提示词注册中心 - 统一管理所有提示词"""
import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import yaml


@dataclass
class PromptMetadata:
    """提示词元数据"""
    name: str
    description: str = ""
    author: str = "system"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    model_compatibility: List[str] = field(default_factory=lambda: ["openai", "anthropic"])
    estimated_tokens: int = 0


@dataclass
class PromptVersion:
    """提示词版本"""
    version: str
    content: Dict[str, str]  # {system: ..., user: ...}
    metadata: PromptMetadata
    parameters: Dict[str, Any] = field(default_factory=dict)
    output_schema: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def content_hash(self) -> str:
        """计算内容哈希"""
        content_str = json.dumps(self.content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]


@dataclass
class RenderedPrompt:
    """渲染后的提示词"""
    system: str
    user: str
    version: str
    metadata: PromptMetadata
    estimated_tokens: int = 0


class PromptRegistry:
    """提示词注册中心"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self._prompts: Dict[str, Dict[str, PromptVersion]] = {}
        self._active_versions: Dict[str, str] = {}
        self._loaders: List[Callable] = []
        self.storage_path = storage_path or Path("./data/prompts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def register(
        self,
        name: str,
        content: Dict[str, str],
        version: str = "1.0.0",
        metadata: Optional[PromptMetadata] = None,
        parameters: Optional[Dict[str, Any]] = None,
        output_schema: Optional[str] = None,
        activate: bool = True
    ) -> PromptVersion:
        """
        注册提示词
        
        Args:
            name: 提示词名称（如 architect/foundation）
            content: 提示词内容 {system: ..., user: ...}
            version: 版本号
            metadata: 元数据
            parameters: 参数定义
            output_schema: 输出模式名称
            activate: 是否立即激活此版本
        """
        if metadata is None:
            metadata = PromptMetadata(name=name)
        
        version_obj = PromptVersion(
            version=version,
            content=content,
            metadata=metadata,
            parameters=parameters or {},
            output_schema=output_schema
        )
        
        if name not in self._prompts:
            self._prompts[name] = {}
        
        self._prompts[name][version] = version_obj
        
        if activate:
            self.activate(name, version)
        
        # 持久化
        self._save_prompt(name, version, version_obj)
        
        return version_obj
    
    def get(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[PromptVersion]:
        """获取提示词版本"""
        if name not in self._prompts:
            return None
        
        if version is None:
            version = self._active_versions.get(name)
        
        if version is None:
            # 返回最新版本
            versions = self._prompts[name]
            if not versions:
                return None
            version = max(versions.keys(), 
                         key=lambda v: versions[v].created_at)
        
        return self._prompts[name].get(version)
    
    def activate(self, name: str, version: str) -> bool:
        """激活指定版本"""
        if name in self._prompts and version in self._prompts[name]:
            self._active_versions[name] = version
            self._save_active_version(name, version)
            return True
        return False
    
    def list_versions(self, name: str) -> List[str]:
        """列出所有版本"""
        if name not in self._prompts:
            return []
        return list(self._prompts[name].keys())
    
    def list_prompts(self, tag: Optional[str] = None) -> List[str]:
        """列出所有提示词名称"""
        if tag is None:
            return list(self._prompts.keys())
        
        return [
            name for name, versions in self._prompts.items()
            if any(tag in v.metadata.tags for v in versions.values())
        ]
    
    def load_from_yaml(self, file_path: Path) -> PromptVersion:
        """从YAML文件加载提示词"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        name = data.get('name')
        version = data.get('version', '1.0.0')
        
        metadata = PromptMetadata(
            name=name,
            description=data.get('description', ''),
            author=data.get('author', 'system'),
            tags=data.get('tags', []),
            model_compatibility=data.get('model_compatibility', ['openai', 'anthropic']),
            estimated_tokens=data.get('estimated_tokens', 0)
        )
        
        content = {
            'system': data.get('system_template', ''),
            'user': data.get('user_template', '')
        }
        
        return self.register(
            name=name,
            content=content,
            version=version,
            metadata=metadata,
            parameters=data.get('parameters', {}),
            output_schema=data.get('output_schema'),
            activate=data.get('activate', True)
        )
    
    def load_directory(self, directory: Path) -> int:
        """从目录加载所有YAML提示词"""
        count = 0
        for yaml_file in directory.rglob("*.yaml"):
            try:
                self.load_from_yaml(yaml_file)
                count += 1
            except Exception as e:
                print(f"Failed to load {yaml_file}: {e}")
        return count
    
    def _save_prompt(self, name: str, version: str, prompt: PromptVersion):
        """持久化提示词到文件"""
        prompt_dir = self.storage_path / name.replace('/', '_')
        prompt_dir.mkdir(exist_ok=True)
        
        file_path = prompt_dir / f"{version}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(prompt), f, indent=2, default=str)
    
    def _save_active_version(self, name: str, version: str):
        """保存激活版本"""
        active_file = self.storage_path / "active_versions.json"
        
        active_versions = {}
        if active_file.exists():
            with open(active_file, 'r') as f:
                active_versions = json.load(f)
        
        active_versions[name] = version
        
        with open(active_file, 'w') as f:
            json.dump(active_versions, f, indent=2)
    
    def compare_versions(
        self,
        name: str,
        version_a: str,
        version_b: str
    ) -> Dict[str, Any]:
        """比较两个版本"""
        prompt_a = self.get(name, version_a)
        prompt_b = self.get(name, version_b)
        
        if not prompt_a or not prompt_b:
            return {"error": "Version not found"}
        
        return {
            "version_a": version_a,
            "version_b": version_b,
            "content_diff": {
                "system_changed": prompt_a.content['system'] != prompt_b.content['system'],
                "user_changed": prompt_a.content['user'] != prompt_b.content['user'],
            },
            "metadata_diff": {
                "description_changed": prompt_a.metadata.description != prompt_b.metadata.description,
                "tags_changed": prompt_a.metadata.tags != prompt_b.metadata.tags,
            },
            "performance_diff": {
                k: prompt_b.performance_metrics.get(k, 0) - prompt_a.performance_metrics.get(k, 0)
                for k in set(prompt_a.performance_metrics) | set(prompt_b.performance_metrics)
            }
        }
