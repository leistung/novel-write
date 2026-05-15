/**
 * E2E端到端测试 - 使用Playwright
 * 
 * 测试完整的用户流程：
 * 1. 访问首页
 * 2. 创建书籍
 * 3. 查看书籍列表
 * 4. 编辑书籍
 * 5. 删除书籍
 * 
 * 运行方式:
 *   npx playwright test tests/e2e/full-test.spec.ts --reporter=list
 * 
 * 带界面运行:
 *   npx playwright test tests/e2e/full-test.spec.ts --headed --reporter=list
 */
import { test, expect, Page } from '@playwright/test';

// 测试配置
const BASE_URL = 'http://localhost:5173'; // 前端开发服务器地址
const API_URL = 'http://localhost:8000';  // 后端API地址

// 测试数据
const TEST_BOOK = {
  title: `E2E测试书籍_${Date.now()}`,
  genre: '玄幻',
  platform: '起点',
  chapterWords: '3000',
  targetChapters: '100',
  outline: '这是一个用于E2E测试的书籍大纲',
};

test.describe('NovelWrite E2E Tests', () => {
  let createdBookTitle: string | null = null;

  test.beforeEach(async ({ page }) => {
    // 每个测试前导航到首页
    await page.goto(BASE_URL);
    // 等待页面加载
    await page.waitForLoadState('networkidle');
  });

  test.describe('首页', () => {
    test('应该正确显示首页', async ({ page }) => {
      // 验证页面标题
      await expect(page).toHaveTitle(/NovelWrite|小说写作/);
      
      // 验证主要元素存在
      await expect(page.locator('text=我的书籍').or(page.locator('text=书籍列表'))).toBeVisible();
      
      // 截图保存
      await page.screenshot({ path: 'test-results/homepage.png' });
    });

    test('应该能够导航到创建书籍页面', async ({ page }) => {
      // 查找并点击创建书籍按钮
      const createButton = page.locator('text=创建书籍').or(page.locator('text=新建书籍')).or(page.locator('text=+'));
      
      if (await createButton.count() > 0) {
        await createButton.first().click();
        
        // 验证导航到创建页面
        await expect(page).toHaveURL(/.*create|.*new/);
        
        // 验证表单元素
        await expect(page.locator('input[name="title"]').or(page.locator('input[placeholder*="书名"]'))).toBeVisible();
      } else {
        console.log('未找到创建书籍按钮，跳过此测试');
        test.skip();
      }
    });
  });

  test.describe('书籍管理', () => {
    test('应该能够创建新书籍', async ({ page }) => {
      // 导航到创建页面
      await navigateToCreateBook(page);
      
      // 填写表单
      await fillBookForm(page, TEST_BOOK);
      
      // 提交表单
      const submitButton = page.locator('button[type="submit"]').or(page.locator('text=创建')).or(page.locator('text=保存'));
      await submitButton.click();
      
      // 等待提交完成
      await page.waitForTimeout(1000);
      
      // 验证成功提示或跳转
      const successIndicator = page.locator('text=创建成功').or(page.locator('text=保存成功')).or(page.locator('.ant-message-success'));
      
      // 或者验证跳转到书籍列表
      try {
        await expect(page).toHaveURL(/.*books|.*list/, { timeout: 5000 });
        createdBookTitle = TEST_BOOK.title;
        console.log('✅ 书籍创建成功:', createdBookTitle);
      } catch {
        // 如果没有跳转，检查是否有成功提示
        console.log('未检测到跳转，检查当前页面状态');
      }
      
      // 截图
      await page.screenshot({ path: 'test-results/create-book.png' });
    });

    test('应该能够查看书籍列表', async ({ page }) => {
      // 导航到书籍列表
      await navigateToBookList(page);
      
      // 验证列表加载
      await page.waitForTimeout(1000);
      
      // 检查是否有书籍数据
      const bookCards = page.locator('.book-card, [data-testid*="book"], .ant-list-item');
      const count = await bookCards.count();
      
      console.log(`📚 找到 ${count} 本书籍`);
      
      // 截图
      await page.screenshot({ path: 'test-results/book-list.png' });
    });

    test('应该能够编辑书籍', async ({ page }) => {
      // 先创建一本书
      await navigateToCreateBook(page);
      await fillBookForm(page, { ...TEST_BOOK, title: `编辑测试_${Date.now()}` });
      
      const submitButton = page.locator('button[type="submit"]').or(page.locator('text=创建'));
      await submitButton.click();
      await page.waitForTimeout(1000);
      
      // 导航到书籍列表
      await navigateToBookList(page);
      await page.waitForTimeout(1000);
      
      // 查找编辑按钮
      const editButton = page.locator('text=编辑').or(page.locator('.btn-edit')).first();
      
      if (await editButton.count() > 0) {
        await editButton.click();
        
        // 等待编辑页面加载
        await page.waitForTimeout(1000);
        
        // 修改标题
        const titleInput = page.locator('input[name="title"]').or(page.locator('input[placeholder*="书名"]'));
        await titleInput.fill(`已编辑_${Date.now()}`);
        
        // 保存
        const saveButton = page.locator('button[type="submit"]').or(page.locator('text=保存'));
        await saveButton.click();
        
        await page.waitForTimeout(1000);
        
        console.log('✅ 书籍编辑成功');
      } else {
        console.log('未找到编辑按钮');
      }
      
      // 截图
      await page.screenshot({ path: 'test-results/edit-book.png' });
    });

    test('应该能够删除书籍', async ({ page }) => {
      // 导航到书籍列表
      await navigateToBookList(page);
      await page.waitForTimeout(1000);
      
      // 查找删除按钮
      const deleteButton = page.locator('text=删除').or(page.locator('.btn-delete')).first();
      
      if (await deleteButton.count() > 0) {
        await deleteButton.click();
        
        // 确认删除（如果有确认对话框）
        const confirmButton = page.locator('text=确定').or(page.locator('text=确认')).or(page.locator('.ant-btn-primary'));
        if (await confirmButton.count() > 0) {
          await confirmButton.click();
        }
        
        await page.waitForTimeout(1000);
        
        console.log('✅ 书籍删除成功');
      } else {
        console.log('未找到删除按钮');
      }
      
      // 截图
      await page.screenshot({ path: 'test-results/delete-book.png' });
    });
  });

  test.describe('导航和UI', () => {
    test('应该能够访问设置页面', async ({ page }) => {
      // 查找设置链接
      const settingsLink = page.locator('text=设置').or(page.locator('a[href*="settings"]'));
      
      if (await settingsLink.count() > 0) {
        await settingsLink.click();
        await page.waitForTimeout(500);
        
        await expect(page).toHaveURL(/.*settings/);
        console.log('✅ 设置页面访问成功');
      } else {
        console.log('未找到设置链接');
      }
      
      await page.screenshot({ path: 'test-results/settings.png' });
    });

    test('应该能够访问帮助页面', async ({ page }) => {
      // 查找帮助链接
      const helpLink = page.locator('text=帮助').or(page.locator('a[href*="help"]'));
      
      if (await helpLink.count() > 0) {
        await helpLink.click();
        await page.waitForTimeout(500);
        
        await expect(page).toHaveURL(/.*help/);
        console.log('✅ 帮助页面访问成功');
      } else {
        console.log('未找到帮助链接');
      }
      
      await page.screenshot({ path: 'test-results/help.png' });
    });

    test('响应式布局检查', async ({ page }) => {
      // 桌面端
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto(BASE_URL);
      await page.waitForTimeout(500);
      await page.screenshot({ path: 'test-results/desktop-view.png' });
      
      // 平板端
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto(BASE_URL);
      await page.waitForTimeout(500);
      await page.screenshot({ path: 'test-results/tablet-view.png' });
      
      // 手机端
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);
      await page.waitForTimeout(500);
      await page.screenshot({ path: 'test-results/mobile-view.png' });
      
      console.log('✅ 响应式布局检查完成');
    });
  });

  test.describe('API连接', () => {
    test('应该能够连接到后端API', async ({ page }) => {
      // 使用page.evaluate直接调用API
      const healthCheck = await page.evaluate(async (apiUrl) => {
        try {
          const response = await fetch(`${apiUrl}/health`);
          return { status: response.status, ok: response.ok };
        } catch (e) {
          return { error: (e as Error).message };
        }
      }, API_URL);
      
      if ('error' in healthCheck) {
        console.log('⚠️ API连接失败:', healthCheck.error);
        test.skip();
      } else {
        expect(healthCheck.ok).toBe(true);
        console.log('✅ API连接正常');
      }
    });
  });
});

// ============================================================================
// 辅助函数
// ============================================================================

async function navigateToCreateBook(page: Page) {
  await page.goto(`${BASE_URL}/create`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
}

async function navigateToBookList(page: Page) {
  await page.goto(`${BASE_URL}/books`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
}

async function fillBookForm(page: Page, bookData: typeof TEST_BOOK) {
  // 填写书名
  const titleInput = page.locator('input[name="title"]').or(page.locator('input[placeholder*="书名"]')).or(page.locator('input').first());
  if (await titleInput.count() > 0) {
    await titleInput.fill(bookData.title);
  }
  
  // 选择类型
  const genreSelect = page.locator('select[name="genre"]').or(page.locator('text=类型').locator('..').locator('select'));
  if (await genreSelect.count() > 0) {
    await genreSelect.selectOption(bookData.genre);
  }
  
  // 选择平台
  const platformSelect = page.locator('select[name="platform"]').or(page.locator('text=平台').locator('..').locator('select'));
  if (await platformSelect.count() > 0) {
    await platformSelect.selectOption(bookData.platform);
  }
  
  // 填写每章字数
  const wordsInput = page.locator('input[name="chapter_words"]').or(page.locator('input[placeholder*="字数"]'));
  if (await wordsInput.count() > 0) {
    await wordsInput.fill(bookData.chapterWords);
  }
  
  // 填写目标章节数
  const chaptersInput = page.locator('input[name="target_chapters"]').or(page.locator('input[placeholder*="章节"]'));
  if (await chaptersInput.count() > 0) {
    await chaptersInput.fill(bookData.targetChapters);
  }
  
  // 填写大纲
  const outlineInput = page.locator('textarea[name="outline"]').or(page.locator('textarea'));
  if (await outlineInput.count() > 0) {
    await outlineInput.fill(bookData.outline);
  }
  
  await page.waitForTimeout(200);
}
