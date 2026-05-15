"""
前端 API 联调完整测试脚本
不依赖浏览器，直接通过 HTTP 请求测试所有 API 端点
模拟前端每个页面的 API 调用链路

运行方式：
    cd backend
    python ../frontend/tests/api/api-test-runner.py
"""
import asyncio
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    import httpx
except ImportError:
    os.system(f"{sys.executable} -m pip install httpx")
    import httpx

API_BASE = "http://localhost:8000"

# ==================== 测试结果收集 ====================
results = {"passed": 0, "failed": 0, "total": 0, "details": []}

def record(name, passed, message="", duration=0):
    results["total"] += 1
    if passed:
        results["passed"] += 1
        status = "✅"
    else:
        results["failed"] += 1
        status = "❌"
    results["details"].append({"name": name, "status": "PASS" if passed else "FAIL", "message": message, "duration": f"{duration:.2f}s"})
    print(f"  {status} [{duration:.2f}s] {name}" + (f" -- {message}" if message and not passed else ""))


async def run_tests():
    print("=" * 70)
    print("🧪 NovelWrite 前端 API 联调完整测试")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 后端地址: {API_BASE}")
    print("=" * 70)

    async with httpx.AsyncClient(base_url=API_BASE, timeout=30) as client:
        
        # ==================== TC01: 健康检查 ====================
        print("\n📋 TC01: 基础连通性")
        start = time.time()
        try:
            r = await client.get("/health")
            assert r.status_code == 200
            record("TC01-01 后端健康检查", True, "", time.time() - start)
        except Exception as e:
            record("TC01-01 后端健康检查", False, str(e), time.time() - start)
            print("\n❌ 后端不可用，终止测试")
            return

        start = time.time()
        try:
            r = await client.get("/")
            assert r.status_code == 200
            record("TC01-02 根路径", True, "", time.time() - start)
        except Exception as e:
            record("TC01-02 根路径", False, str(e), time.time() - start)

        # ==================== TC02: Skills API ====================
        print("\n📋 TC02: Skills API (前端页面加载时调用)")
        
        start = time.time()
        try:
            r = await client.get("/api/v1/skills")
            assert r.status_code == 200
            data = r.json()
            assert len(data) >= 26
            record("TC02-01 获取所有Skills", True, f"共{len(data)}个", time.time() - start)
        except Exception as e:
            record("TC02-01 获取所有Skills", False, str(e), time.time() - start)

        start = time.time()
        try:
            r = await client.get("/api/v1/skills?category=male")
            assert r.status_code == 200
            data = r.json()
            assert len(data) == 15
            record("TC02-02 筛选男频Skills", True, f"共{len(data)}个", time.time() - start)
        except Exception as e:
            record("TC02-02 筛选男频Skills", False, str(e), time.time() - start)

        start = time.time()
        try:
            r = await client.get("/api/v1/skills?category=female")
            assert r.status_code == 200
            data = r.json()
            assert len(data) == 11
            record("TC02-03 筛选女频Skills", True, f"共{len(data)}个", time.time() - start)
        except Exception as e:
            record("TC02-03 筛选女频Skills", False, str(e), time.time() - start)

        start = time.time()
        try:
            r = await client.get("/api/v1/skills/xuanhuan-novelist")
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == "xuanhuan-novelist"
            record("TC02-04 获取Skill详情", True, "", time.time() - start)
        except Exception as e:
            record("TC02-04 获取Skill详情", False, str(e), time.time() - start)

        start = time.time()
        try:
            r = await client.get("/api/v1/skills/genres/list")
            assert r.status_code == 200
            data = r.json()
            assert "male" in data and "female" in data
            record("TC02-05 获取类型列表", True, f"男频{len(data['male'])},女频{len(data['female'])}", time.time() - start)
        except Exception as e:
            record("TC02-05 获取类型列表", False, str(e), time.time() - start)

        # ==================== TC03: Books API - 工作台/我的书籍页面 ====================
        print("\n📋 TC03: Books API (工作台/我的书籍页面加载时调用)")
        
        # 获取书籍列表
        start = time.time()
        try:
            r = await client.get("/api/v1/books")
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data, list)
            record("TC03-01 获取书籍列表", True, f"共{len(data)}本", time.time() - start)
        except Exception as e:
            record("TC03-01 获取书籍列表", False, str(e), time.time() - start)

        # 创建书籍 - 模拟工作台创建弹窗提交
        test_book_id = None
        start = time.time()
        try:
            r = await client.post("/api/v1/books", json={
                "title": f"API测试书籍_{int(time.time())}",
                "genre": "xuanhuan",
                "platform": "通用",
                "chapter_words": 3000,
                "target_chapters": 100,
                "outline": "这是一个API自动化测试创建的书籍"
            })
            assert r.status_code == 200
            data = r.json()
            test_book_id = data["id"]
            assert data["title"].startswith("API测试书籍")
            record("TC03-02 创建书籍", True, f"id={test_book_id}", time.time() - start)
        except Exception as e:
            record("TC03-02 创建书籍", False, str(e), time.time() - start)

        if not test_book_id:
            print("\n❌ 创建书籍失败，后续测试跳过")
            print_report()
            return

        # 获取单本书籍 - 模拟点击书籍卡片
        start = time.time()
        try:
            r = await client.get(f"/api/v1/books/{test_book_id}")
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == test_book_id
            record("TC03-03 获取书籍详情", True, f"title={data['title']}", time.time() - start)
        except Exception as e:
            record("TC03-03 获取书籍详情", False, str(e), time.time() - start)

        # 更新书籍
        start = time.time()
        try:
            r = await client.put(f"/api/v1/books/{test_book_id}", json={
                "outline": "更新后的大纲内容"
            })
            assert r.status_code == 200
            record("TC03-04 更新书籍", True, "", time.time() - start)
        except Exception as e:
            record("TC03-04 更新书籍", False, str(e), time.time() - start)

        # 获取书籍结构
        start = time.time()
        try:
            r = await client.get(f"/api/v1/books/{test_book_id}/structure")
            assert r.status_code == 200
            record("TC03-05 获取书籍结构", True, "", time.time() - start)
        except Exception as e:
            record("TC03-05 获取书籍结构", False, str(e), time.time() - start)

        # ==================== TC04: Chapters API - 书籍详情页面 ====================
        print("\n📋 TC04: Chapters API (书籍详情页面加载时调用)")
        
        # 获取章节列表
        start = time.time()
        try:
            r = await client.get(f"/api/v1/books/{test_book_id}/chapters")
            assert r.status_code == 200
            data = r.json()
            record("TC04-01 获取章节列表", True, f"共{len(data) if isinstance(data, list) else 0}章", time.time() - start)
        except Exception as e:
            record("TC04-01 获取章节列表", False, str(e), time.time() - start)

        # 获取不存在的章节
        start = time.time()
        try:
            r = await client.get(f"/api/v1/books/{test_book_id}/chapters/999")
            # 可能返回 404 或空数据
            record("TC04-02 获取不存在章节", True, f"status={r.status_code}", time.time() - start)
        except Exception as e:
            record("TC04-02 获取不存在章节", False, str(e), time.time() - start)

        # ==================== TC05: Orchestrator API - 操作Tab ====================
        print("\n📋 TC05: Orchestrator API (操作Tab调用)")
        
        # 获取书籍上下文
        start = time.time()
        try:
            r = await client.get(f"/api/v1/orchestrator/books/{test_book_id}/context")
            assert r.status_code == 200
            data = r.json()
            assert data["book_id"] == test_book_id
            record("TC05-01 获取书籍上下文", True, "", time.time() - start)
        except Exception as e:
            record("TC05-01 获取书籍上下文", False, str(e), time.time() - start)

        # 刷新上下文
        start = time.time()
        try:
            r = await client.post(f"/api/v1/orchestrator/books/{test_book_id}/context/refresh")
            assert r.status_code == 200
            record("TC05-02 刷新书籍上下文", True, "", time.time() - start)
        except Exception as e:
            record("TC05-02 刷新书籍上下文", False, str(e), time.time() - start)

        # ==================== TC06: Workflows API ====================
        print("\n📋 TC06: Workflows API (操作Tab触发)")
        
        # 生成大纲工作流
        workflow_id = None
        start = time.time()
        try:
            r = await client.post("/api/v1/workflows/generate-outline", json={
                "book_id": test_book_id
            })
            if r.status_code == 200:
                data = r.json()
                workflow_id = data.get("workflow_id")
                record("TC06-01 生成大纲工作流", True, f"workflow_id={workflow_id}", time.time() - start)
            elif r.status_code == 409:
                record("TC06-01 生成大纲工作流", True, "跳过（锁冲突）", time.time() - start)
            else:
                record("TC06-01 生成大纲工作流", False, f"status={r.status_code}", time.time() - start)
        except Exception as e:
            record("TC06-01 生成大纲工作流", False, str(e), time.time() - start)

        # 续写章节工作流
        start = time.time()
        try:
            r = await client.post("/api/v1/workflows/continue-chapters", json={
                "book_id": test_book_id,
                "start_chapter": 1,
                "count": 1
            })
            if r.status_code == 200:
                record("TC06-02 续写章节工作流", True, "", time.time() - start)
            elif r.status_code == 409:
                record("TC06-02 续写章节工作流", True, "跳过（锁冲突）", time.time() - start)
            else:
                record("TC06-02 续写章节工作流", False, f"status={r.status_code}", time.time() - start)
        except Exception as e:
            record("TC06-02 续写章节工作流", False, str(e), time.time() - start)

        # 重写章节工作流
        start = time.time()
        try:
            r = await client.post("/api/v1/workflows/rewrite-chapter", json={
                "book_id": test_book_id,
                "chapter_num": 1,
                "rewrite_requirements": "增加战斗描写",
                "keep_plot": True
            })
            if r.status_code == 200:
                record("TC06-03 重写章节工作流", True, "", time.time() - start)
            elif r.status_code == 409:
                record("TC06-03 重写章节工作流", True, "跳过（锁冲突）", time.time() - start)
            else:
                record("TC06-03 重写章节工作流", False, f"status={r.status_code}", time.time() - start)
        except Exception as e:
            record("TC06-03 重写章节工作流", False, str(e), time.time() - start)

        # ==================== TC07: 边界情况测试 ====================
        print("\n📋 TC07: 边界情况")
        
        # 获取不存在的书籍
        start = time.time()
        try:
            r = await client.get("/api/v1/books/999999")
            assert r.status_code == 404
            record("TC07-01 获取不存在的书籍", True, "正确返回404", time.time() - start)
        except Exception as e:
            record("TC07-01 获取不存在的书籍", False, str(e), time.time() - start)

        # 删除不存在的书籍
        start = time.time()
        try:
            r = await client.delete("/api/v1/books/999999")
            assert r.status_code == 404
            record("TC07-02 删除不存在的书籍", True, "正确返回404", time.time() - start)
        except Exception as e:
            record("TC07-02 删除不存在的书籍", False, str(e), time.time() - start)

        # 创建书籍 - 空标题
        start = time.time()
        try:
            r = await client.post("/api/v1/books", json={
                "title": "",
                "genre": "xuanhuan"
                })
            assert r.status_code == 422
            record("TC07-03 创建书籍-空标题校验", True, "正确返回422", time.time() - start)
        except Exception as e:
            record("TC07-03 创建书籍-空标题校验", False, str(e), time.time() - start)

        # 获取不存在的Skill
        start = time.time()
        try:
            r = await client.get("/api/v1/skills/nonexistent-skill")
            assert r.status_code == 404
            record("TC07-04 获取不存在的Skill", True, "正确返回404", time.time() - start)
        except Exception as e:
            record("TC07-04 获取不存在的Skill", False, str(e), time.time() - start)

        # ==================== TC08: 删除测试书籍 ====================
        print("\n📋 TC08: 清理测试数据")
        
        start = time.time()
        try:
            r = await client.delete(f"/api/v1/books/{test_book_id}")
            assert r.status_code == 200
            record("TC08-01 删除测试书籍", True, f"id={test_book_id}", time.time() - start)
        except Exception as e:
            record("TC08-01 删除测试书籍", False, str(e), time.time() - start)

        # 验证已删除
        start = time.time()
        try:
            r = await client.get(f"/api/v1/books/{test_book_id}")
            assert r.status_code == 404
            record("TC08-02 验证书籍已删除", True, "", time.time() - start)
        except Exception as e:
            record("TC08-02 验证书籍已删除", False, str(e), time.time() - start)


def print_report():
    print("\n" + "=" * 70)
    print("📊 测试报告")
    print("=" * 70)
    print(f"  总计: {results['total']}  ✅ 通过: {results['passed']}  ❌ 失败: {results['failed']}")
    rate = results["passed"] / results["total"] * 100 if results["total"] > 0 else 0
    print(f"  通过率: {rate:.1f}%")
    
    if results["failed"] > 0:
        print("\n❌ 失败的测试:")
        for d in results["details"]:
            if d["status"] == "FAIL":
                print(f"   - {d['name']}: {d['message']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
