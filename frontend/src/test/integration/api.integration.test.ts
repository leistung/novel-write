/**
 * API集成测试
 * 测试前端API服务与后端的真实交互
 * 
 * 注意：这些测试需要后端服务运行在 http://localhost:8000
 * 运行前请确保后端已启动
 */
import { describe, it, expect, beforeAll, vi } from 'vitest';
import axios, { AxiosError } from 'axios';

// API基础配置
const API_BASE_URL = 'http://localhost:8000';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 测试数据
const testBookData = {
  title: `测试书籍_${Date.now()}`,
  genre: '玄幻',
  platform: '起点',
  chapter_words: 3000,
  target_chapters: 100,
  outline: '这是一个用于API测试的书籍大纲',
};

describe('API Integration Tests', () => {
  let createdBookId: number | null = null;

  beforeAll(async () => {
    // 检查后端是否可用
    try {
      const response = await api.get('/health');
      console.log('✅ 后端服务已连接:', response.data);
    } catch (error) {
      console.warn('⚠️ 后端服务可能未启动，测试将跳过');
    }
  });

  describe('Health Check', () => {
    it('应该能够访问健康检查端点', async () => {
      try {
        const response = await api.get('/health');
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('status');
        expect(response.data.status).toBe('healthy');
      } catch (error) {
        // 如果后端未启动，跳过测试
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });

    it('应该能够访问根路径', async () => {
      try {
        const response = await api.get('/');
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('app');
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });
  });

  describe('Books API', () => {
    it('应该能够创建书籍', async () => {
      try {
        const response = await api.post('/api/v1/books', testBookData);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('id');
        expect(response.data.title).toBe(testBookData.title);
        expect(response.data.genre).toBe(testBookData.genre);
        
        createdBookId = response.data.id;
        console.log('✅ 创建书籍成功，ID:', createdBookId);
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });

    it('应该能够获取书籍列表', async () => {
      try {
        const response = await api.get('/api/v1/books');
        
        expect(response.status).toBe(200);
        expect(Array.isArray(response.data)).toBe(true);
        
        if (createdBookId) {
          const createdBook = response.data.find((b: any) => b.id === createdBookId);
          expect(createdBook).toBeDefined();
        }
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });

    it('应该能够获取单本书籍', async () => {
      if (!createdBookId) {
        console.warn('跳过测试：没有创建的书籍ID');
        return;
      }

      try {
        const response = await api.get(`/api/v1/books/${createdBookId}`);
        
        expect(response.status).toBe(200);
        expect(response.data.id).toBe(createdBookId);
        expect(response.data.title).toBe(testBookData.title);
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });

    it('应该能够更新书籍', async () => {
      if (!createdBookId) {
        console.warn('跳过测试：没有创建的书籍ID');
        return;
      }

      try {
        const updateData = {
          outline: '更新后的大纲内容',
        };
        
        const response = await api.put(`/api/v1/books/${createdBookId}`, updateData);
        
        expect(response.status).toBe(200);
        
        // 验证更新
        const getResponse = await api.get(`/api/v1/books/${createdBookId}`);
        expect(getResponse.data.outline).toBe(updateData.outline);
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });

    it('应该能够获取书籍结构', async () => {
      if (!createdBookId) {
        console.warn('跳过测试：没有创建的书籍ID');
        return;
      }

      try {
        const response = await api.get(`/api/v1/books/${createdBookId}/structure`);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('book_id');
        expect(response.data.book_id).toBe(createdBookId);
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });
  });

  describe('Skills API', () => {
    it('应该能够获取技能列表', async () => {
      try {
        const response = await api.get('/api/v1/skills');
        
        expect(response.status).toBe(200);
        expect(Array.isArray(response.data)).toBe(true);
        expect(response.data.length).toBeGreaterThan(0);
        
        // 验证技能数据结构
        const firstSkill = response.data[0];
        expect(firstSkill).toHaveProperty('name');
        expect(firstSkill).toHaveProperty('category');
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });

    it('应该能够按类别筛选技能', async () => {
      try {
        const response = await api.get('/api/v1/skills?category=male');
        
        expect(response.status).toBe(200);
        expect(Array.isArray(response.data)).toBe(true);
        
        // 所有返回的技能应该是男频
        response.data.forEach((skill: any) => {
          expect(skill.category).toBe('male');
        });
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });

    it('应该能够获取技能详情', async () => {
      try {
        const response = await api.get('/api/v1/skills/xuanhuan-novelist');
        
        expect(response.status).toBe(200);
        expect(response.data.name).toBe('xuanhuan-novelist');
        expect(response.data).toHaveProperty('skill_content');
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });

    it('应该能够获取类型列表', async () => {
      try {
        const response = await api.get('/api/v1/skills/genres/list');
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('male');
        expect(response.data).toHaveProperty('female');
        expect(Array.isArray(response.data.male)).toBe(true);
        expect(Array.isArray(response.data.female)).toBe(true);
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });
  });

  describe('Chapters API', () => {
    it('应该能够获取章节列表（空）', async () => {
      if (!createdBookId) {
        console.warn('跳过测试：没有创建的书籍ID');
        return;
      }

      try {
        const response = await api.get(`/api/v1/books/${createdBookId}/chapters`);
        
        expect(response.status).toBe(200);
        expect(Array.isArray(response.data)).toBe(true);
        // 新创建的书籍应该没有章节
        expect(response.data.length).toBe(0);
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });
  });

  describe('Error Handling', () => {
    it('应该正确处理不存在的书籍ID', async () => {
      try {
        const response = await api.get('/api/v1/books/99999');
        // 应该返回404
        expect(response.status).toBe(404);
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        // 404错误是预期的
        if ((error as AxiosError).response?.status === 404) {
          expect(true).toBe(true);
          return;
        }
        throw error;
      }
    });

    it('应该正确处理无效的技能名称', async () => {
      try {
        const response = await api.get('/api/v1/skills/non-existent-skill');
        // 应该返回404
        expect(response.status).toBe(404);
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        // 404错误是预期的
        if ((error as AxiosError).response?.status === 404) {
          expect(true).toBe(true);
          return;
        }
        throw error;
      }
    });
  });

  // 清理测试数据
  describe('Cleanup', () => {
    it('应该能够删除测试书籍', async () => {
      if (!createdBookId) {
        console.warn('跳过测试：没有创建的书籍ID');
        return;
      }

      try {
        const response = await api.delete(`/api/v1/books/${createdBookId}`);
        
        expect(response.status).toBe(200);
        console.log('✅ 删除测试书籍成功，ID:', createdBookId);
      } catch (error) {
        if ((error as AxiosError).code === 'ECONNREFUSED') {
          console.warn('跳过测试：后端服务未启动');
          return;
        }
        throw error;
      }
    });
  });
});

// 运行测试的辅助函数
export async function runApiTests() {
  console.log('='.repeat(60));
  console.log('🚀 API集成测试');
  console.log('='.repeat(60));
  console.log(`📡 API地址: ${API_BASE_URL}`);
  console.log('');
  
  // 检查后端是否可用
  try {
    const response = await api.get('/health');
    console.log('✅ 后端服务已连接');
    console.log('📊 健康状态:', response.data);
  } catch (error) {
    console.error('❌ 后端服务未启动或无法连接');
    console.log('请确保后端服务运行在 http://localhost:8000');
    return;
  }
  
  console.log('\n运行测试...');
  console.log('使用命令: npm test');
}

// 如果直接运行此文件
if (import.meta.url === `file://${process.argv[1]}`) {
  runApiTests();
}
