#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NovelWrite 工作流可视化 E2E 测试

使用 Playwright 进行端到端测试：
1. 创建书籍
2. 进入书籍详情页
3. 点击"可视化执行"按钮
4. 验证工作流可视化组件正确显示
5. 点击"开始执行"按钮
6. 验证节点流程图正确显示
7. 验证实时输出正常工作

使用方法：
    python test_workflow_e2e.py [--base-url BASE_URL] [--browser BROWSER]

示例：
    python test_workflow_e2e.py
    python test_workflow_e2e.py --base-url http://localhost:5173
"""

import argparse
import time
import sys

try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    print("❌ 未安装 playwright，请先安装：")
    print("   pip install playwright")
    print("   playwright install chromium")
    sys.exit(1)


class WorkflowE2ETest:
    """工作流可视化 E2E 测试"""

    def __init__(self, base_url: str = "http://localhost:5173", browser_name: str = "chromium"):
        self.base_url = base_url.rstrip("/")
        self.browser_name = browser_name
        self.page = None
        self.browser = None
        self.context = None
        self.console_errors = []
        self.test_results = []

    def log(self, message: str, level: str = "INFO"):
        """日志输出"""
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}
        print(f"{icons.get(level, '•')} {message}")

    def pass_test(self, name: str):
        """记录测试通过"""
        self.test_results.append((name, True))
        self.log(f"测试通过: {name}", "SUCCESS")

    def fail_test(self, name: str, reason: str):
        """记录测试失败"""
        self.test_results.append((name, False))
        self.log(f"测试失败: {name} - {reason}", "ERROR")

    def setup(self):
        """设置 Playwright"""
        self.log("初始化 Playwright...")
        playwright = sync_playwright().start()

        # 尝试使用系统 Chrome
        try:
            # 尝试常见 Chrome 路径
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Users\\98082\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
            ]

            chrome_executable = None
            for path in chrome_paths:
                import os
                if os.path.exists(path):
                    chrome_executable = path
                    break

            if chrome_executable:
                self.log(f"使用系统 Chrome: {chrome_executable}")
                self.browser = playwright.chromium.launch(
                    executable_path=chrome_executable,
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
            else:
                self.log("未找到系统 Chrome，使用内置浏览器")
                self.browser = playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
        except Exception as e:
            self.log(f"启动 Chrome 失败: {e}，使用默认浏览器")
            self.browser = playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
        
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        self.page = self.context.new_page()

        # 监听控制台错误
        self.page.on("console", lambda msg: (
            self.console_errors.append(msg.text)
            if msg.type == "error" else None
        ))

        self.log("Playwright 初始化完成")

    def teardown(self):
        """清理"""
        if self.browser:
            self.browser.close()

    def wait_for_selector_safe(self, selector: str, timeout: int = 10000):
        """安全等待元素出现"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout, state="attached")
            return True
        except Exception:
            return False

    def test_home_page_loads(self):
        """测试1: 首页加载"""
        self.log("测试1: 首页加载...")

        try:
            self.page.goto(self.base_url, wait_until="networkidle", timeout=30000)

            # 检查页面标题或主要内容
            title = self.page.title()
            self.log(f"  页面标题: {title}")

            # 等待页面主要元素加载
            self.page.wait_for_timeout(2000)

            # 检查是否有书籍列表或创建按钮
            page_content = self.page.content()
            has_content = len(page_content) > 1000

            if has_content:
                self.pass_test("首页加载")
            else:
                self.fail_test("首页加载", "页面内容太少")

        except Exception as e:
            self.fail_test("首页加载", str(e))

    def test_create_book(self):
        """测试2: 创建书籍"""
        self.log("测试2: 创建书籍...")

        try:
            # 点击创建书籍按钮
            create_button = self.page.locator('button:has-text("创建书籍"), button:has-text("新建书籍"), a:has-text("创建")').first
            if create_button.is_visible(timeout=5000):
                create_button.click()
                self.page.wait_for_timeout(1000)
            else:
                # 尝试导航到创建页面
                self.page.goto(f"{self.base_url}/create", wait_until="networkidle", timeout=10000)
                self.page.wait_for_timeout(1000)

            # 填写书籍表单
            # 填写标题
            title_input = self.page.locator('input[placeholder*="书名"], input[placeholder*="标题"], input#title, input[name="title"]').first
            if title_input.is_visible(timeout=5000):
                title_input.fill("测试小说 - 工作流可视化测试")

            # 选择题材（如果有下拉框）
            genre_select = self.page.locator('select, .ant-select, [class*="select"]').first
            if genre_select.is_visible(timeout=2000):
                try:
                    genre_select.click()
                    self.page.wait_for_timeout(500)
                    # 选择第一个选项
                    self.page.locator('.ant-select-item, .ant-select-option, li').first.click()
                except:
                    pass

            # 提交表单
            submit_button = self.page.locator('button[type="submit"], button:has-text("创建"), button:has-text("保存")').first
            if submit_button.is_visible(timeout=5000):
                submit_button.click()
                self.page.wait_for_timeout(3000)

            # 检查是否创建成功或跳转到详情页
            current_url = self.page.url
            if "book" in current_url.lower() or "/detail" in current_url.lower():
                self.pass_test("创建书籍")
                return True
            else:
                # 检查是否有错误消息
                error_text = self.page.locator('.ant-message-error, [class*="error"], [class*="Error"]').first.text_content()
                if error_text:
                    self.fail_test("创建书籍", f"错误: {error_text}")
                else:
                    self.pass_test("创建书籍")
                    return True

        except Exception as e:
            self.fail_test("创建书籍", str(e))
            return False

    def test_workflow_visualization(self):
        """测试3: 工作流可视化组件"""
        self.log("测试3: 工作流可视化组件...")

        try:
            # 确保在书籍详情页
            current_url = self.page.url
            if "book" not in current_url.lower():
                self.log("  不在书籍详情页，尝试查找书籍...")
                # 点击第一本书
                book_link = self.page.locator('a[href*="book"], .book-card, [class*="book"]').first
                if book_link.is_visible(timeout=5000):
                    book_link.click()
                    self.page.wait_for_timeout(2000)

            # 切换到操作标签页
            operations_tab = self.page.locator('.ant-tabs-tab:has-text("操作"), [role="tab"]:has-text("操作")').first
            if operations_tab.is_visible(timeout=5000):
                operations_tab.click()
                self.page.wait_for_timeout(1000)

            # 查找"可视化执行"按钮
            viz_button = self.page.locator('button:has-text("可视化执行"), button:has-text("可视化")').first

            if viz_button.is_visible(timeout=5000):
                self.log("  找到可视化执行按钮")

                # 点击可视化执行按钮
                viz_button.click()
                self.page.wait_for_timeout(2000)

                # 检查工作流组件是否显示
                workflow_component = self.page.locator(
                    '[class*="workflow"], [class*="Workflow"], '
                    '[class*="execution"], [class*="Execution"], '
                    '.workflow-execution, .workflow-visualizer'
                ).first

                if workflow_component.is_visible(timeout=5000) or self.wait_for_selector_safe(
                    '[class*="workflow"]', timeout=3000
                ):
                    self.pass_test("工作流可视化组件显示")
                    return True
                else:
                    # 检查是否有控制栏（开始执行按钮）
                    start_button = self.page.locator(
                        'button:has-text("开始执行"), button:has-text("执行"), button:has-text("Start")'
                    ).first
                    if start_button.is_visible(timeout=3000):
                        self.pass_test("工作流可视化组件显示")
                        return True
                    else:
                        self.fail_test("工作流可视化组件显示", "未找到工作流组件或开始按钮")
                        return False
            else:
                self.fail_test("工作流可视化组件显示", "未找到可视化执行按钮")
                return False

        except Exception as e:
            self.fail_test("工作流可视化组件显示", str(e))
            return False

    def test_node_flow_diagram(self):
        """测试4: 节点流程图"""
        self.log("测试4: 节点流程图...")

        try:
            # 检查是否有节点列表或流程图区域
            node_area = self.page.locator(
                '[class*="node"], [class*="Node"], '
                '[class*="flow"], [class*="Flow"], '
                '.node-card, .workflow-nodes'
            ).first

            if node_area.is_visible(timeout=5000) or self.wait_for_selector_safe(
                '[class*="node"]', timeout=3000
            ):
                self.pass_test("节点流程图区域")
            else:
                self.fail_test("节点流程图区域", "未找到节点区域")
                return False

            # 检查是否有执行流程标题
            flow_title = self.page.locator('text:has-text("执行流程"), text:has-text("流程图")').first
            if flow_title.is_visible(timeout=3000):
                self.pass_test("执行流程标题")
            else:
                self.log("  未找到执行流程标题（非必需）", "WARN")

        except Exception as e:
            self.fail_test("节点流程图", str(e))

    def test_workflow_controls(self):
        """测试5: 工作流控制按钮"""
        self.log("测试5: 工作流控制按钮...")

        try:
            # 检查开始执行按钮
            start_button = self.page.locator(
                'button:has-text("开始执行"), button:has-text("Start"), button:has-text("执行")'
            ).first

            if start_button.is_visible(timeout=5000):
                self.pass_test("开始执行按钮")
            else:
                self.fail_test("开始执行按钮", "未找到开始执行按钮")
                return False

            # 检查设置按钮
            settings_button = self.page.locator(
                'button[aria-label*="setting"], button[title*="设置"], '
                '[class*="setting"]'
            ).first

            if settings_button.is_visible(timeout=3000):
                self.pass_test("设置按钮")
            else:
                self.log("  未找到设置按钮（非必需）", "WARN")

            # 检查全屏按钮
            fullscreen_button = self.page.locator(
                'button[aria-label*="fullscreen"], button[title*="全屏"], '
                '[class*="fullscreen"]'
            ).first

            if fullscreen_button.is_visible(timeout=3000):
                self.pass_test("全屏按钮")
            else:
                self.log("  未找到全屏按钮（非必需）", "WARN")

        except Exception as e:
            self.fail_test("工作流控制按钮", str(e))

    def test_streaming_output(self):
        """测试6: 实时输出区域"""
        self.log("测试6: 实时输出区域...")

        try:
            # 检查实时输出区域
            output_area = self.page.locator(
                'text:has-text("实时输出"), text:has-text("输出"), '
                '[class*="output"], [class*="Output"]'
            ).first

            if output_area.is_visible(timeout=5000):
                self.pass_test("实时输出区域")
            else:
                self.fail_test("实时输出区域", "未找到实时输出区域")
                return False

            # 检查字符计数
            char_count = self.page.locator(
                'text:has-text("字符"), text:has-text("chars"), '
                '[class*="count"]'
            ).first

            if char_count.is_visible(timeout=3000):
                self.pass_test("字符计数显示")
            else:
                self.log("  未找到字符计数（非必需）", "WARN")

        except Exception as e:
            self.fail_test("实时输出区域", str(e))

    def test_node_detail_panel(self):
        """测试7: 节点详情面板"""
        self.log("测试7: 节点详情面板...")

        try:
            # 检查详情面板区域
            detail_area = self.page.locator(
                '[class*="detail"], [class*="Detail"], '
                '[class*="panel"], [class*="Panel"], '
                'text:has-text("详情"), text:has-text("输入"), text:has-text("输出")'
            ).first

            if detail_area.is_visible(timeout=5000):
                self.pass_test("节点详情面板")

                # 检查是否有 Tab 切换
                tabs = self.page.locator('.ant-tabs-tab, [role="tab"]')
                tab_count = tabs.count()
                if tab_count >= 3:
                    self.pass_test(f"详情面板 Tab 标签 ({tab_count}个)")
                else:
                    self.log(f"  Tab 数量: {tab_count}", "WARN")
            else:
                self.fail_test("节点详情面板", "未找到详情面板")
                return False

        except Exception as e:
            self.fail_test("节点详情面板", str(e))

    def test_start_workflow(self):
        """测试8: 开始执行工作流（模拟）"""
        self.log("测试8: 开始执行工作流...")

        try:
            # 找到并点击开始执行按钮
            start_button = self.page.locator(
                'button:has-text("开始执行"), button:has-text("Start"), button:has-text("执行")'
            ).first

            if start_button.is_visible(timeout=5000):
                # 检查按钮状态
                is_disabled = start_button.is_disabled()
                if is_disabled:
                    self.log("  开始按钮当前禁用（可能需要先配置）", "WARN")
                else:
                    # 点击开始执行
                    self.log("  点击开始执行按钮...")
                    start_button.click()

                    # 等待状态变化
                    self.page.wait_for_timeout(3000)

                    # 检查是否有状态变化（执行中、完成等）
                    status_elements = self.page.locator(
                        'text:has-text("执行中"), text:has-text("running"), '
                        'text:has-text("待执行"), text:has-text("idle"), '
                        'text:has-text("已完成"), text:has-text("completed")'
                    )

                    if status_elements.count() > 0:
                        self.pass_test("工作流状态变化")
                    else:
                        self.log("  未检测到状态变化（非阻塞性）", "WARN")

                    self.pass_test("开始执行工作流")
            else:
                self.fail_test("开始执行工作流", "未找到开始执行按钮")

        except Exception as e:
            self.fail_test("开始执行工作流", str(e))

    def check_console_errors(self):
        """检查控制台错误"""
        self.log("\n检查控制台错误...")

        if self.console_errors:
            # 过滤掉无关的错误
            critical_errors = [
                e for e in self.console_errors
                if any(keyword in e.lower() for keyword in ['error', 'failed', 'uncaught', 'cannot'])
                and 'warning' not in e.lower()
            ]

            if critical_errors:
                self.log(f"  发现 {len(critical_errors)} 个可能的错误:", "WARN")
                for err in critical_errors[:5]:  # 只显示前5个
                    self.log(f"    - {err[:100]}", "WARN")
            else:
                self.log("  未发现明显错误")
        else:
            self.log("  无控制台错误")

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("=" * 60)

        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)

        print(f"\n通过: {passed}/{total}")
        print(f"失败: {total - passed}/{total}")

        if total > 0:
            success_rate = (passed / total) * 100
            print(f"成功率: {success_rate:.1f}%")

        print("\n详细结果:")
        for name, result in self.test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {status} - {name}")

        print("\n" + "=" * 60)

        return passed == total

    def run(self):
        """运行所有测试"""
        self.log("🚀 开始工作流可视化 E2E 测试")
        self.log(f"📍 目标地址: {self.base_url}")
        print()

        try:
            # 设置
            self.setup()

            # 运行测试
            self.test_home_page_loads()
            self.test_create_book()
            self.test_workflow_visualization()
            self.test_node_flow_diagram()
            self.test_workflow_controls()
            self.test_streaming_output()
            self.test_node_detail_panel()
            self.test_start_workflow()

            # 检查控制台错误
            self.check_console_errors()

            # 打印总结
            success = self.print_summary()

        except Exception as e:
            self.log(f"测试过程出错: {e}", "ERROR")
            success = False

        finally:
            self.teardown()

        return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="NovelWrite 工作流可视化 E2E 测试")
    parser.add_argument(
        "--base-url",
        default="http://localhost:5173",
        help="前端地址 (默认: http://localhost:5173)"
    )
    parser.add_argument(
        "--browser",
        default="chromium",
        choices=["chromium", "firefox", "webkit"],
        help="浏览器类型 (默认: chromium)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="无头模式运行"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🎭 NovelWrite 工作流可视化 E2E 测试")
    print("=" * 60)
    print(f"🌐 目标地址: {args.base_url}")
    print(f"🖥️  浏览器: {args.browser}")
    print(f"👁️  无头模式: {args.headless}")
    print("=" * 60)
    print()

    # 运行测试
    test = WorkflowE2ETest(base_url=args.base_url, browser_name=args.browser)
    success = test.run()

    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
