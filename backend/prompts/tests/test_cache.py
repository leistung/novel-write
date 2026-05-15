"""缓存系统测试"""
import pytest
import time
from pathlib import Path
from prompts.optimization.cache import PromptCache, CacheConfig


class TestPromptCache:
    """测试缓存系统"""
    
    def test_basic_cache_operations(self):
        """测试基本缓存操作"""
        cache = PromptCache()
        
        # 设置缓存
        cache.set(
            "test/prompt",
            {"var": "value"},
            "gpt-4",
            {"result": "test"},
            version="1.0.0"
        )
        
        # 获取缓存
        result = cache.get("test/prompt", {"var": "value"}, "gpt-4", "1.0.0")
        assert result is not None
        assert result["result"] == "test"
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = PromptCache()
        
        result = cache.get("nonexistent", {}, "gpt-4")
        assert result is None
        
        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0
    
    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = PromptCache(CacheConfig(ttl_seconds=1))
        
        cache.set("test/expire", {}, "gpt-4", {"data": "test"})
        
        # 立即获取应该命中
        result = cache.get("test/expire", {}, "gpt-4")
        assert result is not None
        
        # 等待过期
        time.sleep(2)
        
        # 过期后获取应该失败
        result = cache.get("test/expire", {}, "gpt-4")
        assert result is None
    
    def test_cache_invalidation(self):
        """测试缓存失效"""
        cache = PromptCache()
        
        cache.set("test/invalid", {}, "gpt-4", {"data": "1"})
        cache.set("test/keep", {}, "gpt-4", {"data": "2"})
        
        # 失效特定提示词
        count = cache.invalidate("test/invalid")
        assert count == 1
        
        assert cache.get("test/invalid", {}, "gpt-4") is None
        # 注意：由于键生成方式，可能需要更精确的测试
    
    def test_lru_eviction(self):
        """测试LRU淘汰"""
        cache = PromptCache(CacheConfig(max_size=2))
        
        cache.set("test/1", {}, "gpt-4", {"data": "1"})
        cache.set("test/2", {}, "gpt-4", {"data": "2"})
        cache.set("test/3", {}, "gpt-4", {"data": "3"})  # 应该淘汰test/1
        
        stats = cache.get_stats()
        assert stats["size"] <= 2
    
    def test_cache_stats(self):
        """测试缓存统计"""
        cache = PromptCache()
        
        # 产生一些命中和未命中
        cache.get("missing", {}, "gpt-4")
        cache.set("exists", {}, "gpt-4", {"data": "test"})
        cache.get("exists", {}, "gpt-4")
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
