import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright 配置
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  
  /* 测试文件匹配模式 */
  testMatch: '**/*.spec.ts',
  
  /* 完全并行运行测试 */
  fullyParallel: true,
  
  /* 禁止在 CI 中重复测试 */
  forbidOnly: !!process.env.CI,
  
  /* 非 CI 环境重试失败测试 */
  retries: process.env.CI ? 2 : 0,
  
  /* 非 CI 环境并行工作线程数 */
  workers: process.env.CI ? 1 : undefined,
  
  /* 报告器配置 */
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
  ],
  
  /* 共享项目配置 */
  use: {
    /* 基础 URL */
    baseURL: 'http://localhost:3003',
    
    /* 收集 trace */
    trace: 'on-first-retry',
    
    /* 截图配置 */
    screenshot: 'only-on-failure',
    
    /* 视频配置 */
    video: 'retain-on-failure',
    
    /* 浏览器启动选项 */
    launchOptions: {
      slowMo: 500, // 减慢操作速度，便于观察
    },
  },
  
  /* 项目配置 */
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        /* 使用本地安装的 Chromium */
        executablePath: undefined, // 让 Playwright 自动查找
      },
    },
  ],
  
  /* 测试前启动开发服务器 - 使用已存在的服务器 */
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:3003',
  //   reuseExistingServer: true,
  //   timeout: 120000,
  // },
});
