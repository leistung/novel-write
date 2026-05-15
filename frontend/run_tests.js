/**
 * 前端测试运行脚本
 * 
 * 运行所有前端测试：
 * 1. 单元测试 (Vitest)
 * 2. 集成测试
 * 3. E2E测试 (Playwright)
 * 
 * 用法:
 *   node run_tests.js [选项]
 * 
 * 选项:
 *   --unit          运行单元测试
 *   --integration   运行集成测试
 *   --e2e           运行E2E测试
 *   --all           运行所有测试
 *   --ui            使用UI模式运行
 * 
 * 示例:
 *   node run_tests.js --all
 *   node run_tests.js --unit --ui
 *   node run_tests.js --e2e
 */

const { execSync } = require('child_process');
const path = require('path');

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function printHeader(title) {
  console.log('\n' + '='.repeat(70));
  console.log(`  ${title}`);
  console.log('='.repeat(70) + '\n');
}

function printSection(title) {
  console.log(`\n${'─'.repeat(70)}`);
  console.log(`  ${title}`);
  console.log(`${'─'.repeat(70)}\n`);
}

function runCommand(command, description) {
  printSection(description);
  console.log(`${colors.cyan}运行命令: ${command}${colors.reset}\n`);
  
  try {
    execSync(command, { 
      stdio: 'inherit',
      cwd: __dirname 
    });
    console.log(`${colors.green}✅ ${description} 完成${colors.reset}\n`);
    return 0;
  } catch (error) {
    console.log(`${colors.red}❌ ${description} 失败${colors.reset}\n`);
    return 1;
  }
}

function runUnitTests(ui = false) {
  const cmd = ui 
    ? 'npx vitest --ui'
    : 'npx vitest run';
  return runCommand(cmd, '单元测试 (Vitest)');
}

function runIntegrationTests() {
  // 集成测试包含在vitest中
  return runCommand('npx vitest run src/test/integration/', '集成测试');
}

function runE2ETests(headed = false) {
  const cmd = headed
    ? 'npx playwright test tests/e2e/ --headed --reporter=list'
    : 'npx playwright test tests/e2e/ --reporter=list';
  return runCommand(cmd, 'E2E测试 (Playwright)');
}

function showHelp() {
  console.log(`
${colors.bright}NovelWrite 前端测试运行脚本${colors.reset}

用法:
  node run_tests.js [选项]

选项:
  --unit          运行单元测试
  --integration   运行集成测试
  --e2e           运行E2E测试
  --all           运行所有测试
  --ui            使用UI模式运行单元测试
  --headed        带浏览器界面运行E2E测试
  --help          显示帮助信息

示例:
  node run_tests.js --all                    # 运行所有测试
  node run_tests.js --unit                   # 只运行单元测试
  node run_tests.js --unit --ui              # 使用UI模式运行单元测试
  node run_tests.js --e2e --headed           # 带界面运行E2E测试
  node run_tests.js --integration            # 运行集成测试
`);
}

function main() {
  const args = process.argv.slice(2);
  
  // 显示帮助
  if (args.includes('--help') || args.length === 0) {
    showHelp();
    return;
  }
  
  const runUnit = args.includes('--unit') || args.includes('--all');
  const runIntegration = args.includes('--integration') || args.includes('--all');
  const runE2E = args.includes('--e2e') || args.includes('--all');
  const useUI = args.includes('--ui');
  const useHeaded = args.includes('--headed');
  
  printHeader('NovelWrite 前端测试套件');
  console.log(`${colors.blue}开始时间: ${new Date().toLocaleString()}${colors.reset}`);
  console.log(`${colors.blue}工作目录: ${__dirname}${colors.reset}\n`);
  
  const results = [];
  
  // 运行单元测试
  if (runUnit) {
    const code = runUnitTests(useUI);
    results.push({ name: '单元测试', code });
  }
  
  // 运行集成测试
  if (runIntegration) {
    const code = runIntegrationTests();
    results.push({ name: '集成测试', code });
  }
  
  // 运行E2E测试
  if (runE2E) {
    const code = runE2ETests(useHeaded);
    results.push({ name: 'E2E测试', code });
  }
  
  // 打印汇总
  printHeader('测试结果汇总');
  results.forEach(({ name, code }) => {
    const status = code === 0 
      ? `${colors.green}✅ 通过${colors.reset}` 
      : `${colors.red}❌ 失败${colors.reset}`;
    console.log(`  ${status} - ${name}`);
  });
  
  const totalFailed = results.filter(r => r.code !== 0).length;
  
  if (totalFailed === 0) {
    console.log(`\n${colors.green}${colors.bright}🎉 所有测试通过！${colors.reset}\n`);
  } else {
    console.log(`\n${colors.yellow}⚠️  ${totalFailed} 个测试类别失败${colors.reset}\n`);
  }
  
  console.log(`${colors.blue}结束时间: ${new Date().toLocaleString()}${colors.reset}`);
  
  process.exit(totalFailed);
}

main();
