"""提示词缓存系统"""
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import pickle


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl_seconds: int = 3600  # 默认1小时
    max_size: int = 1000  # 最大缓存条目
    persist_path: Optional[Path] = None  # 持久化路径
    compression: bool = True  # 是否压缩


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PromptCache:
    """提示词缓存管理器
    
    功能:
    1. 基于内容哈希的缓存键
    2. TTL过期机制
    3. LRU淘汰策略
    4. 持久化支持
    5. 命中率统计
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
        
        # 加载持久化缓存
        if self.config.persist_path:
            self._load_from_disk()
    
    def _generate_key(
        self,
        prompt_name: str,
        variables: Dict[str, Any],
        model: str,
        version: str
    ) -> str:
        """生成缓存键
        
        基于提示词名称、变量、模型和版本的组合哈希
        """
        # 标准化变量（排序键）
        normalized_vars = json.dumps(variables, sort_keys=True, default=str)
        
        # 组合关键信息
        key_data = f"{prompt_name}:{version}:{model}:{normalized_vars}"
        
        # 生成哈希
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def get(
        self,
        prompt_name: str,
        variables: Dict[str, Any],
        model: str,
        version: str = "1.0.0"
    ) -> Optional[Any]:
        """获取缓存值"""
        key = self._generate_key(prompt_name, variables, model, version)
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        # 检查过期
        if datetime.utcnow() > entry.expires_at:
            del self._cache[key]
            self._misses += 1
            return None
        
        # 更新访问统计
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()
        
        self._hits += 1
        return entry.value
    
    def set(
        self,
        prompt_name: str,
        variables: Dict[str, Any],
        model: str,
        value: Any,
        version: str = "1.0.0",
        ttl: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        """设置缓存值"""
        key = self._generate_key(prompt_name, variables, model, version)
        
        # 检查容量，必要时淘汰
        if len(self._cache) >= self.config.max_size:
            self._evict_lru()
        
        ttl_seconds = ttl or self.config.ttl_seconds
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds),
            metadata=metadata or {}
        )
        
        self._cache[key] = entry
        
        # 持久化
        if self.config.persist_path:
            self._save_to_disk()
    
    def invalidate(
        self,
        prompt_name: Optional[str] = None,
        version: Optional[str] = None
    ) -> int:
        """使缓存失效
        
        Args:
            prompt_name: 指定提示词名称，None表示全部
            version: 指定版本，None表示全部版本
            
        Returns:
            失效的条目数
        """
        if prompt_name is None:
            count = len(self._cache)
            self._cache.clear()
            return count
        
        to_remove = []
        for key, entry in self._cache.items():
            meta = entry.metadata
            if meta.get("prompt_name") == prompt_name:
                if version is None or meta.get("version") == version:
                    to_remove.append(key)
        
        for key in to_remove:
            del self._cache[key]
        
        return len(to_remove)
    
    def _evict_lru(self):
        """LRU淘汰策略"""
        if not self._cache:
            return
        
        # 找到最少访问的条目
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (
                self._cache[k].last_accessed,
                self._cache[k].access_count
            )
        )
        
        del self._cache[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        # 清理过期条目
        now = datetime.utcnow()
        expired = [k for k, v in self._cache.items() if v.expires_at < now]
        for k in expired:
            del self._cache[k]
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4),
            "size": len(self._cache),
            "max_size": self.config.max_size,
            "expired_cleaned": len(expired),
        }
    
    def _save_to_disk(self):
        """持久化到磁盘"""
        if not self.config.persist_path:
            return
        
        try:
            self.config.persist_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "cache": self._cache,
                "hits": self._hits,
                "misses": self._misses,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(self.config.persist_path, 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            print(f"Failed to save cache: {e}")
    
    def _load_from_disk(self):
        """从磁盘加载"""
        if not self.config.persist_path or not self.config.persist_path.exists():
            return
        
        try:
            with open(self.config.persist_path, 'rb') as f:
                data = pickle.load(f)
            
            # 只加载未过期的条目
            now = datetime.utcnow()
            for key, entry in data.get("cache", {}).items():
                if entry.expires_at > now:
                    self._cache[key] = entry
            
            self._hits = data.get("hits", 0)
            self._misses = data.get("misses", 0)
            
        except Exception as e:
            print(f"Failed to load cache: {e}")
    
    def get_cache_key_info(
        self,
        prompt_name: str,
        variables: Dict[str, Any],
        model: str,
        version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """获取缓存键信息（用于调试）"""
        key = self._generate_key(prompt_name, variables, model, version)
        entry = self._cache.get(key)
        
        return {
            "key": key,
            "exists": entry is not None,
            "expires_at": entry.expires_at.isoformat() if entry else None,
            "access_count": entry.access_count if entry else 0,
        }
