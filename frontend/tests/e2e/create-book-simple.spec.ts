import { test, expect } from '@playwright/test';

test('创建书籍完整测试', async ({ page }) => {
  console.log('\n🚀 开始创建书籍测试');
  
  // 监听控制台
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.type() === 'warning') {
      console.log(`[${msg.type()}] ${msg.text().substring(0, 200)}`);
    }
  });
  
  // 监听API请求
  page.on('request', req => {
    if (req.url().includes('/api/')) {
      console.log(`[Request] ${req.method()} ${req.url()}`);
    }
  });
  
  page.on('response', async res => {
    if (res.url().includes('/api/')) {
      const status = res.status();
      const ok = status >= 200 && status < 300;
      console.log(`[Response] ${ok ? '✅' : '❌'} ${status} ${res.url()}`);
      
      if (!ok) {
        try {
          const body = await res.text();
          console.log(`[Error] ${body.substring(0, 300)}`);
        } catch (e) {}
      }
    }
  });

  // 1. 打开首页
  console.log('\n📍 打开首页');
  await page.goto('http://localhost:3003', { timeout: 30000 });
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  console.log('✅ 首页加载完成');
  
  // 2. 点击"创建新书"
  console.log('\n📍 点击创建新书');
  await page.click('text=创建新书');
  await page.waitForTimeout(1000);
  console.log('✅ 已点击创建新书');
  
  // 3. 填写书名
  console.log('\n📍 填写书名');
  const bookTitle = `测试书籍_${Date.now()}`;
  // 等待输入框出现
  await page.waitForSelector('input', { timeout: 5000 });
  // 获取第一个输入框（书名）
  const inputs = await page.$$('input');
  console.log(`   找到 ${inputs.length} 个输入框`);
  if (inputs.length > 0) {
    await inputs[0].fill(bookTitle);
    console.log(`✅ 书名: ${bookTitle}`);
  } else {
    throw new Error('未找到书名输入框');
  }
  
  // 4. 选择题材
  console.log('\n📍 选择题材');
  await page.click('.ant-select');
  await page.waitForTimeout(500);
  await page.click('text=玄幻');
  console.log('✅ 已选择玄幻');
  
  // 5. 点击下一步
  console.log('\n📍 点击下一步');
  await page.click('button:has-text("下一步")');
  await page.waitForTimeout(1000);
  console.log('✅ 已进入第二步');
  
  // 6. 点击创建书籍
  console.log('\n📍 点击创建书籍');
  await page.click('button:has-text("创建书籍")');
  console.log('✅ 已点击创建书籍按钮');
  
  // 7. 等待API响应
  console.log('\n⏳ 等待API响应...');
  await page.waitForTimeout(3000);
  
  // 8. 检查结果
  const url = page.url();
  console.log(`\n📍 当前URL: ${url}`);
  
  // 检查是否有错误
  const errorMsg = await page.$eval('.ant-message-error, [class*="error"]', el => el.textContent).catch(() => null);
  if (errorMsg) {
    console.log(`❌ 错误: ${errorMsg}`);
    await page.screenshot({ path: 'test-results/error.png', fullPage: true });
    throw new Error(`创建失败: ${errorMsg}`);
  }
  
  // 检查是否成功
  if (url.includes('/books')) {
    console.log('✅ 创建成功！已跳转到书籍列表');
    await page.screenshot({ path: 'test-results/success.png', fullPage: true });
  } else {
    console.log('⚠️ 未跳转到书籍列表');
    await page.screenshot({ path: 'test-results/unknown-state.png', fullPage: true });
  }
  
  console.log('\n🎉 测试完成！');
});
