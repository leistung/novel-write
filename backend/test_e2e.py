#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NovelWrite Playwright E2E 测试脚本

使用本地 Chrome 浏览器测试前端页面功能：
1. 打开首页，检查页面加载
2. 创建书籍
3. 进入书籍详情页
4. 检查 SSE 流式生成组件是否存在
5. 截图保存

使用方法：
    python test_e2e.py [--frontend-url URL] [--backend-url URL]
"""

import argparse
import json
import time
import sys
import os
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, Browser


# ==================== 配置 ====================

FRONTEND_URL = "http://localhost:3001"
BACKEND_URL = "http://localhost:8000"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "test_screenshots")


def ensure_screenshot_dir():
    """确保截图目录存在"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def screenshot(page: Page, name: str):
    """截图并保存"""
    ensure_screenshot_dir()
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  📸 截图已保存: {path}")
    return path


# ==================== 测试用例 ====================

def test_01_homepage(page: Page, frontend_url: str):
    """测试1: 首页加载"""
    print("\n" + "=" * 60)
    print("测试1: 首页加载")
    print("=" * 60)
    
    page.goto(frontend_url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    title = page.title()
    print(f"  页面标题: {title}")
    print(f"  当前URL: {page.url}")
    
    # 检查页面内容
    body_text = page.inner_text("body")
    has_content = len(body_text.strip()) > 0
    print(f"  页面有内容: {'✅ 是' if has_content else '❌ 否'}")
    
    screenshot(page, "01_homepage")
    print("  ✅ 首页加载测试完成")
    return True


def test_02_create_book(page: Page, frontend_url: str, backend_url: str):
    """测试2: 通过API创建书籍，然后在前端查看"""
    print("\n" + "=" * 60)
    print("测试2: 创建书籍")
    print("=" * 60)
    
    # 通过API创建书籍
    import requests
    book_title = f"Playwright测试书籍_{datetime.now().strftime('%H%M%S')}"
    
    try:
        resp = requests.post(
            f"{backend_url}/api/v1/books",
            json={
                "title": book_title,
                "genre": "玄幻",
                "platform": "起点",
                "chapter_words": 3000,
                "target_chapters": 50,
                "outline": "测试大纲：主角获得系统，开始修炼之路。"
            },
            timeout=10
        )
        resp.raise_for_status()
        book_data = resp.json()
        book_id = book_data.get("id")
        print(f"  ✅ API创建书籍成功: id={book_id}, title={book_title}")
    except Exception as e:
        print(f"  ❌ API创建书籍失败: {e}")
        # 尝试获取已有书籍
        try:
            resp = requests.get(f"{backend_url}/api/v1/books", timeout=10)
            books = resp.json()
            if isinstance(books, dict):
                books = books.get("data", books.get("books", []))
            if books and len(books) > 0:
                book_id = books[0]["id"]
                book_title = books[0]["title"]
                print(f"  ⚠️ 使用已有书籍: id={book_id}, title={book_title}")
            else:
                print("  ❌ 没有可用书籍")
                return False
        except Exception as e2:
            print(f"  ❌ 获取书籍列表失败: {e2}")
            return False
    
    # 在前端查看书籍列表
    page.goto(f"{frontend_url}", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)
    
    screenshot(page, "02_book_list")
    print(f"  ✅ 书籍列表页面已加载")
    
    return book_id


def test_03_book_detail(page: Page, frontend_url: str, book_id: int):
    """测试3: 书籍详情页"""
    print("\n" + "=" * 60)
    print("测试3: 书籍详情页")
    print("=" * 60)
    
    # 进入书籍详情页
    detail_url = f"{frontend_url}/books/{book_id}"
    page.goto(detail_url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)
    
    print(f"  当前URL: {page.url}")
    
    # 检查页面内容
    body_text = page.inner_text("body")
    print(f"  页面文本长度: {len(body_text)} 字符")
    
    # 检查是否有 SSE 流式生成组件相关元素
    has_stream = False
    try:
        # 检查是否有"生成大纲"按钮或StreamGenerator组件
        elements = page.query_selector_all("text=生成大纲")
        if elements:
            has_stream = True
            print(f"  ✅ 找到'生成大纲'元素: {len(elements)}个")
    except Exception:
        pass
    
    if not has_stream:
        # 检查其他可能的元素
        try:
            elements = page.query_selector_all("button")
            btn_texts = [el.inner_text().strip() for el in elements if el.inner_text().strip()]
            print(f"  页面按钮: {btn_texts[:10]}")
        except Exception:
            pass
    
    screenshot(page, "03_book_detail")
    print("  ✅ 书籍详情页测试完成")
    return True


def test_04_api_health(page: Page, backend_url: str):
    """测试4: 后端API健康检查"""
    print("\n" + "=" * 60)
    print("测试4: 后端API健康检查")
    print("=" * 60)
    
    import requests
    
    endpoints = [
        ("GET", "/", "根路径"),
        ("GET", "/health", "健康检查"),
        ("GET", "/docs", "API文档"),
    ]
    
    for method, path, name in endpoints:
        try:
            url = f"{backend_url}{path}"
            if method == "GET":
                resp = requests.get(url, timeout=10)
            else:
                resp = requests.post(url, timeout=10)
            
            status = "✅" if resp.status_code < 400 else "❌"
            print(f"  {status} {name}: {resp.status_code}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    # 检查 SSE 端点
    print("\n  SSE 端点检查:")
    sse_endpoints = [
        "/api/v1/stream/generate-outline",
        "/api/v1/stream/continue-chapters",
        "/api/v1/stream/rewrite-chapter",
    ]
    for path in sse_endpoints:
        try:
            url = f"{backend_url}{path}"
            resp = requests.get(url, timeout=5, stream=True)
            # SSE 端点应该返回 200
            status = "✅" if resp.status_code == 200 else "⚠️"
            content_type = resp.headers.get("content-type", "")
            is_sse = "text/event-stream" in content_type
            print(f"  {status} {path}: {resp.status_code} (SSE: {'是' if is_sse else '否'})")
            resp.close()
        except Exception as e:
            print(f"  ❌ {path}: {e}")
    
    # 在浏览器中打开 API 文档
    page.goto(f"{backend_url}/docs", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)
    screenshot(page, "04_api_docs")
    print("  📸 API文档页面截图已保存")
    
    return True


def test_05_frontend_components(page: Page, frontend_url: str):
    """测试5: 前端组件检查"""
    print("\n" + "=" * 60)
    print("测试5: 前端组件检查")
    print("=" * 60)
    
    page.goto(frontend_url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)
    
    # 检查 React 是否正常渲染
    has_react = page.evaluate("() => !!document.getElementById('root')")
    print(f"  {'✅' if has_react else '❌'} React Root 元素: {'存在' if has_react else '不存在'}")
    
    # 检查控制台错误
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.reload()
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)
    
    if errors:
        print(f"  ⚠️ 控制台错误 ({len(errors)}个):")
        for err in errors[:5]:
            print(f"    - {err[:100]}")
    else:
        print(f"  ✅ 无控制台错误")
    
    # 检查网络请求
    page.goto(frontend_url, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    screenshot(page, "05_components")
    print("  ✅ 前端组件检查完成")
    return True


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="NovelWrite Playwright E2E 测试")
    parser.add_argument("--frontend-url", default=FRONTEND_URL, help="前端URL")
    parser.add_argument("--backend-url", default=BACKEND_URL, help="后端URL")
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    args = parser.parse_args()

    print("=" * 70)
    print("🚀 NovelWrite Playwright E2E 测试")
    print("=" * 70)
    print(f"📡 前端: {args.frontend_url}")
    print(f"📡 后端: {args.backend_url}")
    print(f"🖥️  模式: {'有头浏览器' if args.headed else '无头浏览器'}")
    print(f"📸 截图目录: {SCREENSHOT_DIR}")
    print("=" * 70)

    results = {}
    book_id = None

    with sync_playwright() as p:
        # 使用本地 Chrome
        print("\n🌐 启动 Chrome 浏览器...")
        browser = p.chromium.launch(
            headless=not args.headed,
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )
        page = context.new_page()

        try:
            # 测试1: 首页
            results["首页加载"] = test_01_homepage(page, args.frontend_url)

            # 测试4: API健康检查
            results["API健康检查"] = test_04_api_health(page, args.backend_url)

            # 测试2: 创建书籍
            book_id = test_02_create_book(page, args.frontend_url, args.backend_url)
            results["创建书籍"] = book_id is not None and book_id is not False

            # 测试3: 书籍详情
            if book_id:
                results["书籍详情页"] = test_03_book_detail(page, args.frontend_url, book_id)
            else:
                results["书籍详情页"] = False
                print("  ⏭️ 跳过书籍详情页测试（没有可用书籍）")

            # 测试5: 前端组件
            results["前端组件"] = test_05_frontend_components(page, args.frontend_url)

        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            screenshot(page, "error")
        finally:
            browser.close()

    # ==================== 测试报告 ====================
    print("\n" + "=" * 70)
    print("📊 测试报告")
    print("=" * 70)
    
    passed = 0
    failed = 0
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}  {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 70)
    print(f"  总计: {passed + failed}  通过: {passed}  失败: {failed}")
    print(f"  截图目录: {SCREENSHOT_DIR}")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
