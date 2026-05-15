import { test, expect, Page } from '@playwright/test';

// 测试配置
const BASE_URL = 'http://localhost:3003';

// 等待函数
const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// 截图函数
async function takeScreenshot(page: Page, name: string) {
  await page.screenshot({ 
    path: `test-results/${name}.png`,
    fullPage: true 
  });
  console.log(`📸 截图已保存: test-results/${name}.png`);
}

test.describe('创建书籍完整流程测试', () => {
  test('一步步测试创建书籍', async ({ page }) => {
    console.log('\n' + '='.repeat(60));
    console.log('🚀 开始创建书籍测试');
    console.log('='.repeat(60));

    // 监听控制台消息
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      console.log(`[Console ${type}] ${text.substring(0, 200)}`);
    });

    // 监听网络请求
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        console.log(`[Request] ${request.method()} ${request.url()}`);
      }
    });

    // 监听网络响应
    page.on('response', async response => {
      if (response.url().includes('/api/')) {
        const status = response.status();
        const statusText = status >= 400 ? '❌' : '✅';
        console.log(`[Response] ${statusText} ${status} ${response.url()}`);
        
        if (status >= 400) {
          try {
            const body = await response.text();
            console.log(`[Error Body] ${body.substring(0, 500)}`);
          } catch (e) {
            // ignore
          }
        }
      }
    });

    // ========== 步骤 1: 打开首页 ==========
    console.log('\n📍 步骤 1: 打开首页');
    await page.goto(BASE_URL, { timeout: 30000 });
    await page.waitForLoadState('networkidle');
    await wait(2000);
    
    console.log('✅ 首页加载完成');
    console.log(`   当前URL: ${page.url()}`);
    await takeScreenshot(page, '01-homepage');

    // ========== 步骤 2: 查找并点击"创建书籍"按钮 ==========
    console.log('\n📍 步骤 2: 查找并点击"创建书籍"按钮');
    
    // 先查看页面上有什么按钮
    const buttons = await page.$$('button, a');
    console.log(`   页面上有 ${buttons.length} 个按钮/链接`);
    
    for (let i = 0; i < Math.min(buttons.length, 10); i++) {
      const text = await buttons[i].textContent();
      const tag = await buttons[i].evaluate(el => el.tagName);
      console.log(`   [${i}] ${tag}: ${text?.trim() || '(无文本)'}`);
    }

    // 尝试多种方式查找创建书籍按钮
    const createButtonSelectors = [
      'text=创建书籍',
      'text=新建书籍',
      'text=创建新书',
      'a[href="/create"]',
      'button:has-text("创建")',
      '[class*="create"]',
      'button >> nth=0',  // 第一个按钮
    ];

    let createButton = null;
    let usedSelector = '';
    
    for (const selector of createButtonSelectors) {
      try {
        createButton = await page.waitForSelector(selector, { timeout: 3000 });
        if (createButton) {
          usedSelector = selector;
          console.log(`   ✅ 找到按钮，使用选择器: ${selector}`);
          break;
        }
      } catch (e) {
        console.log(`   ❌ 选择器失败: ${selector}`);
      }
    }

    if (!createButton) {
      console.log('❌ 未找到创建书籍按钮，测试终止');
      await takeScreenshot(page, '02-no-create-button');
      throw new Error('未找到创建书籍按钮');
    }

    // 获取按钮信息
    const buttonText = await createButton.textContent();
    console.log(`   按钮文本: ${buttonText}`);
    
    // 点击按钮
    await createButton.click();
    console.log('   ✅ 已点击创建书籍按钮');
    
    await wait(2000);
    console.log(`   当前URL: ${page.url()}`);
    await takeScreenshot(page, '02-after-click-create');

    // ========== 步骤 3: 等待创建页面加载 ==========
    console.log('\n📍 步骤 3: 等待创建页面加载');
    
    // 等待表单元素出现
    try {
      await page.waitForSelector('input, form, .ant-form', { timeout: 10000 });
      console.log('✅ 表单元素已加载');
    } catch (e) {
      console.log('❌ 表单元素未加载');
      await takeScreenshot(page, '03-form-not-loaded');
      throw e;
    }

    // 查看页面内容
    const pageTitle = await page.$eval('h1, h2, .title', el => el.textContent).catch(() => '未找到标题');
    console.log(`   页面标题: ${pageTitle}`);
    
    await takeScreenshot(page, '03-create-page');

    // ========== 步骤 4: 填写书名 ==========
    console.log('\n📍 步骤 4: 填写书名');
    
    // 查找书名输入框
    const titleSelectors = [
      'input[name="title"]',
      'input[placeholder*="书名"]',
      'input[placeholder*="名字"]',
      '.ant-form-item:has-text("书名") input',
      'input >> nth=0',
    ];

    let titleInput = null;
    for (const selector of titleSelectors) {
      try {
        titleInput = await page.waitForSelector(selector, { timeout: 3000 });
        if (titleInput) {
          console.log(`   ✅ 找到书名输入框: ${selector}`);
          break;
        }
      } catch (e) {
        // continue
      }
    }

    if (!titleInput) {
      console.log('❌ 未找到书名输入框');
      await takeScreenshot(page, '04-no-title-input');
      throw new Error('未找到书名输入框');
    }

    const bookTitle = `Playwright测试书籍_${Date.now()}`;
    await titleInput.fill(bookTitle);
    console.log(`   ✅ 已填写书名: ${bookTitle}`);
    
    await takeScreenshot(page, '04-title-filled');

    // ========== 步骤 5: 选择题材 ==========
    console.log('\n📍 步骤 5: 选择题材');
    
    // 查找题材选择器
    const genreSelectors = [
      '.ant-select:has-text("题材")',
      '.ant-form-item:has-text("题材") .ant-select',
      '.ant-select >> nth=0',
    ];

    let genreSelect = null;
    for (const selector of genreSelectors) {
      try {
        genreSelect = await page.waitForSelector(selector, { timeout: 3000 });
        if (genreSelect) {
          console.log(`   ✅ 找到题材选择器: ${selector}`);
          break;
        }
      } catch (e) {
        // continue
      }
    }

    if (!genreSelect) {
      console.log('❌ 未找到题材选择器，跳过此步骤');
    } else {
      await genreSelect.click();
      console.log('   ✅ 已点击题材选择器');
      
      await wait(500);
      
      // 选择"玄幻"
      try {
        const xuanhuanOption = await page.waitForSelector('text=玄幻', { timeout: 3000 });
        await xuanhuanOption.click();
        console.log('   ✅ 已选择"玄幻"');
      } catch (e) {
        console.log('   ⚠️ 未找到"玄幻"选项');
      }
    }
    
    await takeScreenshot(page, '05-genre-selected');

    // ========== 步骤 6: 点击下一步 ==========
    console.log('\n📍 步骤 6: 点击下一步');
    
    const nextButtonSelectors = [
      'button:has-text("下一步")',
      'button:has-text("Next")',
      'button[type="button"] >> nth=-1',
    ];

    let nextButton = null;
    for (const selector of nextButtonSelectors) {
      try {
        nextButton = await page.waitForSelector(selector, { timeout: 3000 });
        if (nextButton) {
          console.log(`   ✅ 找到下一步按钮: ${selector}`);
          break;
        }
      } catch (e) {
        // continue
      }
    }

    if (!nextButton) {
      console.log('❌ 未找到下一步按钮');
      await takeScreenshot(page, '06-no-next-button');
      throw new Error('未找到下一步按钮');
    }

    await nextButton.click();
    console.log('   ✅ 已点击下一步');
    
    await wait(2000);
    await takeScreenshot(page, '06-step-2');

    // ========== 步骤 7: 填写详细设置 ==========
    console.log('\n📍 步骤 7: 填写详细设置');
    
    // 查找字数输入框
    const wordCountSelectors = [
      'input[name="chapter_words"]',
      'input[placeholder*="字数"]',
      '.ant-form-item:has-text("字数") input',
    ];

    for (const selector of wordCountSelectors) {
      try {
        const input = await page.waitForSelector(selector, { timeout: 2000 });
        if (input) {
          await input.fill('3000');
          console.log('   ✅ 已填写每章字数: 3000');
          break;
        }
      } catch (e) {
        // continue
      }
    }

    // 查找目标章数输入框
    const chapterCountSelectors = [
      'input[name="target_chapters"]',
      'input[placeholder*="章数"]',
      '.ant-form-item:has-text("章数") input',
    ];

    for (const selector of chapterCountSelectors) {
      try {
        const input = await page.waitForSelector(selector, { timeout: 2000 });
        if (input) {
          await input.fill('100');
          console.log('   ✅ 已填写目标章数: 100');
          break;
        }
      } catch (e) {
        // continue
      }
    }
    
    await takeScreenshot(page, '07-details-filled');

    // ========== 步骤 8: 点击创建书籍 ==========
    console.log('\n📍 步骤 8: 点击创建书籍按钮');
    
    const submitButtonSelectors = [
      'button:has-text("创建书籍")',
      'button:has-text("提交")',
      'button:has-text("保存")',
      'button[type="submit"]',
      'button >> nth=-1',
    ];

    let submitButton = null;
    for (const selector of submitButtonSelectors) {
      try {
        submitButton = await page.waitForSelector(selector, { timeout: 3000 });
        if (submitButton) {
          const text = await submitButton.textContent();
          console.log(`   ✅ 找到提交按钮: ${selector} (文本: ${text})`);
          break;
        }
      } catch (e) {
        // continue
      }
    }

    if (!submitButton) {
      console.log('❌ 未找到创建书籍按钮');
      await takeScreenshot(page, '08-no-submit-button');
      throw new Error('未找到创建书籍按钮');
    }

    // 点击前记录当前URL
    const urlBeforeSubmit = page.url();
    console.log(`   提交前URL: ${urlBeforeSubmit}`);

    await submitButton.click();
    console.log('   ✅ 已点击创建书籍按钮');

    // ========== 步骤 9: 等待API响应 ==========
    console.log('\n📍 步骤 9: 等待API响应 (最多10秒)');
    
    await wait(3000);
    
    // 检查URL是否变化
    const urlAfterSubmit = page.url();
    console.log(`   提交后URL: ${urlAfterSubmit}`);

    // 检查是否有错误提示
    const errorSelectors = [
      '.ant-message-error',
      '.ant-notification-notice-error',
      '[class*="error"]',
      'text=创建失败',
      'text=错误',
    ];

    let hasError = false;
    let errorText = '';
    
    for (const selector of errorSelectors) {
      try {
        const errorEl = await page.$(selector);
        if (errorEl) {
          const text = await errorEl.textContent();
          if (text && text.length > 0) {
            hasError = true;
            errorText = text;
            console.log(`   ❌ 发现错误提示: ${text.substring(0, 200)}`);
            break;
          }
        }
      } catch (e) {
        // ignore
      }
    }

    await takeScreenshot(page, '09-after-submit');

    // ========== 步骤 10: 验证结果 ==========
    console.log('\n📍 步骤 10: 验证结果');
    
    if (hasError) {
      console.log('❌ 创建书籍失败！');
      console.log(`   错误信息: ${errorText}`);
      
      // 尝试展开日志面板
      try {
        const logButton = await page.$('text=查看日志, button:has-text("日志")');
        if (logButton) {
          await logButton.click();
          await wait(1000);
          await takeScreenshot(page, '10-error-with-logs');
        }
      } catch (e) {
        // ignore
      }
      
      throw new Error(`创建书籍失败: ${errorText}`);
    }

    if (urlAfterSubmit.includes('/books')) {
      console.log('✅ 创建书籍成功！已跳转到书籍列表');
      await takeScreenshot(page, '10-success');
      
      // 验证书籍是否在列表中
      await wait(1000);
      const pageContent = await page.content();
      if (pageContent.includes(bookTitle)) {
        console.log(`✅ 验证成功: 书籍 "${bookTitle}" 出现在列表中`);
      } else {
        console.log(`⚠️ 警告: 书籍 "${bookTitle}" 未在列表中找到`);
      }
    } else {
      console.log('⚠️ 未跳转到书籍列表，检查当前页面状态');
      
      // 检查是否有成功提示
      const successSelectors = [
        '.ant-message-success',
        'text=创建成功',
        'text=成功',
      ];
      
      let hasSuccess = false;
      for (const selector of successSelectors) {
        try {
          const successEl = await page.$(selector);
          if (successEl) {
            const text = await successEl.textContent();
            if (text) {
              hasSuccess = true;
              console.log(`   ✅ 发现成功提示: ${text}`);
              break;
            }
          }
        } catch (e) {
          // ignore
        }
      }
      
      if (!hasSuccess) {
        console.log('   ⚠️ 未发现成功或错误提示');
      }
    }

    console.log('\n' + '='.repeat(60));
    console.log('✅ 测试完成！');
    console.log('='.repeat(60));
  });
});
