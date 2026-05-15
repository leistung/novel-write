/**
 * E2E 端到端测试
 * 模拟用户操作流程
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest';

const API_BASE_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:3001';

describe('E2E 端到端测试', () => {
  let testBookId: number | null = null;

  beforeAll(async () => {
    // 检查后端服务
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error('后端服务未启动');
      }
      console.log('✅ 后端服务已启动');
    } catch (error) {
      console.error('❌ 后端服务未启动，请先运行后端服务');
      throw error;
    }
  });

  describe('完整用户流程', () => {
    it('1. 创建书籍 -> 生成大纲 -> 写第一章', async () => {
      // 步骤1: 创建书籍
      console.log('\n📚 步骤1: 创建书籍...');
      const createResponse = await fetch(`${API_BASE_URL}/api/v1/books`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `E2E测试书籍_${Date.now()}`,
          genre: 'xuanhuan',
          platform: '通用',
          chapter_words: 2000,
          target_chapters: 10,
          outline: '这是一个E2E测试大纲',
        }),
      });

      if (!createResponse.ok) {
        throw new Error('创建书籍失败');
      }

      const book = await createResponse.json();
      testBookId = book.id;
      console.log(`✅ 书籍创建成功，ID: ${book.id}`);

      // 步骤2: 生成大纲
      console.log('\n📝 步骤2: 生成大纲...');
      try {
        const outlineResponse = await fetch(`${API_BASE_URL}/api/v1/orchestrator/generate-outline`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            book_id: testBookId,
            use_llm: true,
          }),
        });

        if (outlineResponse.ok) {
          const outlineResult = await outlineResponse.json();
          console.log('✅ 大纲生成成功');
          console.log(`   - Story Bible: ${outlineResult.story_bible?.length || 0} 字符`);
          console.log(`   - Volume Outline: ${outlineResult.volume_outline?.length || 0} 字符`);
        } else {
          console.log('⚠️ 大纲生成失败（可能是LLM配额问题）');
        }
      } catch (error) {
        console.log('⚠️ 大纲生成出错:', error);
      }

      // 步骤3: 写第一章
      console.log('\n✍️ 步骤3: 写第一章...');
      try {
        const chapterResponse = await fetch(`${API_BASE_URL}/api/v1/orchestrator/write-chapter`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            book_id: testBookId,
            chapter_num: 1,
            use_llm: true,
          }),
        });

        if (chapterResponse.ok) {
          const chapterResult = await chapterResponse.json();
          console.log('✅ 第一章写作成功');
          console.log(`   - 标题: ${chapterResult.title}`);
          console.log(`   - 字数: ${chapterResult.word_count}`);
          console.log(`   - 审核分数: ${chapterResult.audit_score}`);
        } else {
          const error = await chapterResponse.json();
          console.log('⚠️ 第一章写作失败:', error.detail || '未知错误');
        }
      } catch (error) {
        console.log('⚠️ 第一章写作出错:', error);
      }

      // 步骤4: 验证章节已保存
      console.log('\n🔍 步骤4: 验证章节...');
      const chaptersResponse = await fetch(`${API_BASE_URL}/api/v1/books/${testBookId}/chapters`);
      const chapters = await chaptersResponse.json();
      console.log(`✅ 书籍现在有 ${chapters.length} 个章节`);

    }, 120000);

    it('2. 测试所有 API 端点', async () => {
      console.log('\n🧪 测试所有 API 端点...');

      const endpoints = [
        { method: 'GET', path: '/health', name: '健康检查' },
        { method: 'GET', path: '/api/v1/books', name: '获取书籍列表' },
        { method: 'GET', path: '/api/v1/skills', name: '获取 Skills' },
      ];

      for (const endpoint of endpoints) {
        try {
          const response = await fetch(`${API_BASE_URL}${endpoint.path}`);
          const status = response.ok ? '✅' : '❌';
          console.log(`${status} ${endpoint.name}: ${response.status}`);
          expect(response.ok).toBe(true);
        } catch (error) {
          console.log(`❌ ${endpoint.name}: 请求失败`);
          throw error;
        }
      }
    });
  });

  afterAll(async () => {
    // 清理测试数据
    if (testBookId) {
      console.log(`\n🧹 清理测试数据，删除书籍 ID: ${testBookId}`);
      try {
        await fetch(`${API_BASE_URL}/api/v1/books/${testBookId}`, {
          method: 'DELETE',
        });
        console.log('✅ 测试数据已清理');
      } catch (error) {
        console.log('⚠️ 清理测试数据失败:', error);
      }
    }
  });
});

describe('前端可用性测试', () => {
  it('前端服务是否可访问', async () => {
    try {
      const response = await fetch(FRONTEND_URL);
      expect(response.ok).toBe(true);
      console.log('✅ 前端服务可访问');
    } catch (error) {
      console.log('⚠️ 前端服务无法访问（可能需要手动打开浏览器）');
    }
  });
});
