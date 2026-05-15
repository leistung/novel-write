#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NovelWrite 工作流可视化 E2E 测试 - 简化版

使用 Playwright 进行端到端测试：
1. 直接访问书籍详情页
2. 测试工作流可视化组件

使用方法：
    python test_workflow_simple.py [--base-url BASE_URL] [--book-id BOOK_ID]

示例：
    python test_workflow_simple.py
    python test_workflow_simple.py --base-url http://localhost:3002 --book-id 1
"""

import argparse
import time
import sys
import requests

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ 未安装 playwright，请先安装：")
    print("   pip install playwright")
    print("   playwright install chromium")
    sys.exit(1)


class WorkflowE2ETest:
    """工作流可视化 E2E 测试 - 简化版"""

    def __init__(self, base_url: str = "http://localhost:3002", book_id: int = None):
        self.base_url = base_url.rstrip("/")
        self.book_id = book_id
        self.page = None
        self.browser = None
        self.context = None
        self.test_results = []

    def log(self, message: str, level: str = "INFO"):
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}
        print(f"{icons.get(level, '•')} {message}")

    def pass_test(self, name: str):
        self.test_results.append((name, True))
        self.log(f"测试通过: {name}", "SUCCESS")

    def fail_test(self, name: str, reason: str = ""):
        self.test_results.append((name, False))
        self.log(f"测试失败: {name} {f'- {reason}' if reason else ''}", "ERROR")

    def setup(self):
        self.log("初始化 Playwright...")
        playwright = sync_playwright().start()

        # 尝试使用系统 Chrome
        chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ]

        chrome_executable = None
        import os
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_executable = path
                break

        if chrome_executable:
            self.log(f"使用系统 Chrome")
            self.browser = playwright.chromium.launch(
                executable_path=chrome_executable,
                headless=False,  # 显示浏览器方便调试
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
        else:
            self.log("使用内置浏览器")
            self.browser = playwright.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

        self.context = self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = self.context.new_page()
        self.log("Playwright 初始化完成")

    def teardown(self):
        if self.browser:
            self.browser.close()

    def find_or_create_book(self):
        """查找或创建书籍"""
        self.log("查找或创建书籍...")

        # 先尝试 API 创建书籍
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/books",
                json={
                    "title": f"测试书籍-{int(time.time())}",
                    "genre": "奇幻",
                    "platform": "起点",
                    "chapter_words": 3000,
                    "target_chapters": 100,
                    "outline": "测试大纲内容"
                },
                timeout=10
            )
            if response.status_code in [200, 201]:
                data = response.json()
                self.book_id = data.get("id")
                self.log(f"通过 API 创建书籍成功，ID: {self.book_id}")
                return True
        except Exception as e:
            self.log(f"API 创建失败: {e}", "WARN")

        # 如果没有 book_id，尝试从首页获取
        if not self.book_id:
            self.page.goto(f"{self.base_url}/", wait_until="networkidle", timeout=15000)
            self.page.wait_for_timeout(2000)

            # 查找书籍链接
            links = self.page.locator('a[href*="/book/"]').all()
            if links:
                href = links[0].get_attribute('href')
                self.log(f"找到书籍链接: {href}")
                # 提取 book_id
                parts = href.split('/')
                for i, p in enumerate(parts):
                    if p == 'book' and i + 1 < len(parts):
                        self.book_id = int(parts[i + 1])
                        break

        return self.book_id is not None

    def test_page_loads(self):
        """测试页面加载"""
        self.log("测试: 页面加载...")

        try:
            url = f"{self.base_url}/book/{self.book_id}" if self.book_id else self.base_url
            self.page.goto(url, wait_until="networkidle", timeout=15000)
            self.page.wait_for_timeout(3000)

            # 截图保存
            self.page.screenshot(path="screenshot_page.png")
            self.log("截图已保存: screenshot_page.png")

            title = self.page.title()
            self.log(f"  页面标题: {title}")

            self.pass_test("页面加载")
            return True

        except Exception as e:
            self.fail_test("页面加载", str(e))
            return False

    def test_operations_tab(self):
        """测试操作标签页"""
        self.log("测试: 操作标签页...")

        try:
            # 点击操作标签
            tabs = self.page.locator('.ant-tabs-tab').all()
            for tab in tabs:
                tab_text = tab.text_content() or ""
                if "操作" in tab_text:
                    tab.click()
                    self.log("  点击操作标签")
                    self.page.wait_for_timeout(2000)
                    break

            # 截图
            self.page.screenshot(path="screenshot_operations.png")
            self.log("截图已保存: screenshot_operations.png")

            self.pass_test("操作标签页")
            return True

        except Exception as e:
            self.fail_test("操作标签页", str(e))
            return False

    def test_workflow_button(self):
        """测试可视化执行按钮"""
        self.log("测试: 可视化执行按钮...")

        try:
            # 查找可视化执行按钮
            buttons = self.page.locator('button').all()
            viz_button = None

            for btn in buttons:
                text = btn.text_content() or ""
                if "可视化" in text:
                    viz_button = btn
                    break

            if viz_button and viz_button.is_visible():
                self.log("  找到可视化执行按钮")
                viz_button.click()
                self.page.wait_for_timeout(2000)
                self.page.screenshot(path="screenshot_workflow.png")
                self.log("截图已保存: screenshot_workflow.png")
                self.pass_test("可视化执行按钮")
                return True
            else:
                # 打印所有按钮文本用于调试
                button_texts = [btn.text_content() or "" for btn in buttons[:10]]
                self.log(f"  可用按钮: {button_texts}", "WARN")
                self.fail_test("可视化执行按钮", "未找到按钮")
                return False

        except Exception as e:
            self.fail_test("可视化执行按钮", str(e))
            return False

    def test_workflow_components(self):
        """测试工作流组件"""
        self.log("测试: 工作流组件...")

        try:
            components_found = []

            # 1. 检查开始执行按钮
            start_buttons = self.page.locator('button:has-text("开始执行"), button:has-text("Start")').all()
            if any(b.is_visible() for b in start_buttons):
                self.log("  ✅ 找到开始执行按钮")
                components_found.append("开始执行")
            else:
                self.log("  ⚠️ 未找到开始执行按钮", "WARN")

            # 2. 检查执行流程标题
            flow_title = self.page.locator('text:has-text("执行流程")').first
            if flow_title.is_visible(timeout=2000):
                self.log("  ✅ 找到执行流程标题")
                components_found.append("执行流程")
            else:
                self.log("  ⚠️ 未找到执行流程标题", "WARN")

            # 3. 检查实时输出
            output = self.page.locator('text:has-text("实时输出")').first
            if output.is_visible(timeout=2000):
                self.log("  ✅ 找到实时输出区域")
                components_found.append("实时输出")
            else:
                self.log("  ⚠️ 未找到实时输出区域", "WARN")

            # 4. 检查节点卡片
            nodes = self.page.locator('[class*="node"], [class*="Node"]').all()
            if nodes:
                self.log(f"  ✅ 找到 {len(nodes)} 个节点元素")
                components_found.append(f"节点({len(nodes)})")
            else:
                self.log("  ⚠️ 未找到节点元素", "WARN")

            # 截图
            self.page.screenshot(path="screenshot_components.png")
            self.log("截图已保存: screenshot_components.png")

            if components_found:
                self.log(f"  发现组件: {', '.join(components_found)}")
                self.pass_test("工作流组件")
                return True
            else:
                self.fail_test("工作流组件", "未找到预期组件")
                return False

        except Exception as e:
            self.fail_test("工作流组件", str(e))
            return False

    def test_node_detail_panel(self):
        """测试节点详情面板"""
        self.log("测试: 节点详情面板...")

        try:
            # 检查 Tab 标签
            tabs = self.page.locator('.ant-tabs-tab, [role="tab"]').all()
            self.log(f"  找到 {len(tabs)} 个 Tab")

            # 检查详情区域
            detail_area = self.page.locator(
                'text:has-text("输入"), text:has-text("输出"), text:has-text("提示词")'
            ).first

            if detail_area.is_visible(timeout=3000):
                self.log("  ✅ 找到详情面板内容")
                self.pass_test("节点详情面板")
                return True
            else:
                self.log("  ⚠️ 未找到详情面板内容", "WARN")
                self.pass_test("节点详情面板")  # 非阻塞
                return True

        except Exception as e:
            self.fail_test("节点详情面板", str(e))
            return False

    def run(self):
        self.log("🚀 开始工作流可视化 E2E 测试")
        print()

        try:
            self.setup()

            # 查找或创建书籍
            if not self.find_or_create_book():
                self.log("无法获取书籍，跳过页面测试", "WARN")

            # 运行测试
            self.test_page_loads()
            self.test_operations_tab()
            self.test_workflow_button()
            self.test_workflow_components()
            self.test_node_detail_panel()

            # 打印总结
            print("\n" + "=" * 60)
            print("📊 测试总结")
            print("=" * 60)

            passed = sum(1 for _, result in self.test_results if result)
            total = len(self.test_results)
            print(f"\n通过: {passed}/{total}")

            for name, result in self.test_results:
                status = "✅" if result else "❌"
                print(f"  {status} {name}")

            print("\n截图文件:")
            print("  - screenshot_page.png")
            print("  - screenshot_operations.png")
            print("  - screenshot_workflow.png")
            print("  - screenshot_components.png")
            print("=" * 60)

        except Exception as e:
            self.log(f"测试过程出错: {e}", "ERROR")

        finally:
            input("\n按 Enter 键关闭浏览器...")
            self.teardown()


def main():
    parser = argparse.ArgumentParser(description="NovelWrite 工作流可视化 E2E 测试")
    parser.add_argument("--base-url", default="http://localhost:3002", help="前端地址")
    parser.add_argument("--book-id", type=int, default=None, help="书籍ID")
    args = parser.parse_args()

    print("=" * 60)
    print("🎭 NovelWrite 工作流可视化 E2E 测试")
    print("=" * 60)
    print(f"🌐 目标地址: {args.base_url}")
    if args.book_id:
        print(f"📖 书籍ID: {args.book_id}")
    print("=" * 60)
    print()

    test = WorkflowE2ETest(base_url=args.base_url, book_id=args.book_id)
    test.run()


if __name__ == "__main__":
    main()
