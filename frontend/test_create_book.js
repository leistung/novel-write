/**
 * 创建书籍自动化测试
 */
const { chromium } = require('playwright');

async function testCreateBook() {
  console.log('🚀 启动浏览器...');
  
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--no-sandbox']
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // 监听控制台消息
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error' || type === 'warning') {
      console.log(`[Console ${type}] ${text}`);
    }
  });
  
  // 监听网络请求
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      console.log(`[Request] ${request.method()} ${request.url()}`);
    }
  });
  
  // 监听网络响应
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      console.log(`[Response] ${response.status()} ${response.url()}`);
    }
  });
  
  try {
    // 1. 导航到首页
    console.log('\n📍 步骤1: 导航到首页...');
    await page.goto('http://localhost:3003', { timeout: 30000 });
    await page.waitForLoadState('networkidle');
    console.log('✅ 首页加载成功');
    
    // 2. 等待页面加载
    await page.waitForTimeout(2000);
    
    // 3. 查找并点击"创建书籍"按钮
    console.log('\n📍 步骤2: 点击创建书籍...');
    
    // 尝试多种方式查找按钮
    let createButton = null;
    const selectors = [
      'text=创建书籍',
      'text=新建书籍',
      'text=创建新书',
      'a[href="/create"]',
      'button:has-text("创建")',
      '[class*="create"]'
    ];
    
    for (const selector of selectors) {
      try {
        createButton = await page.waitForSelector(selector, { timeout: 3000 });
        if (createButton) {
          console.log(`✅ 找到按钮: ${selector}`);
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    if (!createButton) {
      // 截图查看页面内容
      await page.screenshot({ path: 'test-results/homepage.png' });
      console.log('❌ 未找到创建书籍按钮');
      console.log('请查看 test-results/homepage.png 了解页面状态');
      return;
    }
    
    await createButton.click();
    console.log('✅ 点击创建书籍按钮');
    
    // 4. 等待创建页面加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    console.log('✅ 创建页面加载成功');
    
    // 5. 填写书名
    console.log('\n📍 步骤3: 填写书名...');
    
    const titleInput = await page.waitForSelector('input[placeholder*="书名"], input[name="title"]', { timeout: 5000 });
    await titleInput.fill('Playwright自动化测试书籍');
    console.log('✅ 书名填写完成');
    
    // 6. 选择题材
    console.log('\n📍 步骤4: 选择题材...');
    
    // 点击题材选择器
    const genreSelect = await page.waitForSelector('.ant-select', { timeout: 5000 });
    await genreSelect.click();
    await page.waitForTimeout(500);
    
    // 选择"玄幻"
    const xuanhuanOption = await page.waitForSelector('text=玄幻', { timeout: 5000 });
    await xuanhuanOption.click();
    console.log('✅ 题材选择完成');
    
    // 7. 点击下一步
    console.log('\n📍 步骤5: 点击下一步...');
    const nextButton = await page.waitForSelector('button:has-text("下一步")', { timeout: 5000 });
    await nextButton.click();
    console.log('✅ 点击下一步');
    
    // 8. 等待第二步加载
    await page.waitForTimeout(1000);
    console.log('✅ 第二步页面加载成功');
    
    // 9. 点击创建书籍按钮
    console.log('\n📍 步骤6: 点击创建书籍...');
    
    const submitButton = await page.waitForSelector('button:has-text("创建书籍"), button:has-text("提交")', { timeout: 5000 });
    await submitButton.click();
    console.log('✅ 点击创建书籍按钮');
    
    // 10. 等待结果
    console.log('\n⏳ 等待API响应...');
    await page.waitForTimeout(5000);
    
    // 检查是否成功
    const currentUrl = page.url();
    console.log(`\n📍 当前URL: ${currentUrl}`);
    
    // 检查页面是否有错误提示
    const errorCard = await page.$('[class*="error"]');
    if (errorCard) {
      console.log('\n❌ 检测到错误！');
      const errorText = await errorCard.textContent();
      console.log(`错误信息: ${errorText}`);
      
      // 截图
      await page.screenshot({ path: 'test-results/error-state.png' });
      console.log('截图已保存: test-results/error-state.png');
    }
    
    // 检查是否跳转到书籍列表
    if (currentUrl.includes('/books')) {
      console.log('\n✅ 创建书籍成功！已跳转到书籍列表');
      
      // 截图成功状态
      await page.screenshot({ path: 'test-results/success-state.png' });
      console.log('截图已保存: test-results/success-state.png');
    } else {
      console.log('\n⚠️ 未跳转到书籍列表，检查页面状态...');
      
      // 获取页面上的消息提示
      const messages = await page.$$eval('.ant-message', els => els.map(el => el.textContent));
      if (messages.length > 0) {
        console.log('页面消息:', messages);
      }
      
      // 截图当前状态
      await page.screenshot({ path: 'test-results/current-state.png' });
      console.log('截图已保存: test-results/current-state.png');
    }
    
    // 打印控制台错误日志
    console.log('\n📋 测试完成！');
    
  } catch (error) {
    console.error('\n❌ 测试失败:', error.message);
    
    // 截图
    await page.screenshot({ path: 'test-results/error.png' });
    console.log('错误截图已保存: test-results/error.png');
    
    // 获取页面内容
    const content = await page.content();
    console.log('\n页面HTML片段:', content.substring(0, 2000));
    
  } finally {
    await browser.close();
    console.log('\n浏览器已关闭');
  }
}

testCreateBook().catch(console.error);
