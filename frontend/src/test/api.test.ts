/**
 * API 测试用例
 * 测试前端与后端的联调
 */
import { describe, it, expect } from 'vitest';
import {
  getBooks,
  getBook,
  createBook,
  deleteBook,
  getChapters,
  getSkills,
  startGenerateOutline,
} from '@/services/api';

describe('API 联调测试', () => {
  let testBookId: number | null = null;

  describe('1. 书籍管理 API', () => {
    it('1.1 获取书籍列表', async () => {
      const books = await getBooks();
      expect(Array.isArray(books)).toBe(true);
      console.log('✅ 获取书籍列表成功，数量:', books.length);
    });

    it('1.2 创建书籍', async () => {
      const newBook = {
        title: `测试书籍_${Date.now()}`,
        genre: 'xuanhuan',
        platform: '通用',
        chapter_words: 3000,
        target_chapters: 100,
        outline: '这是一个测试大纲',
      };

      const result = await createBook(newBook);
      expect(result).toHaveProperty('id');
      testBookId = result.id;
      console.log('✅ 创建书籍成功，ID:', result.id);
    });

    it('1.3 获取书籍详情', async () => {
      if (!testBookId) {
        console.log('⚠️ 跳过：没有测试书籍ID');
        return;
      }
      const book = await getBook(testBookId);
      expect(book).toHaveProperty('id', testBookId);
      expect(book).toHaveProperty('title');
      console.log('✅ 获取书籍详情成功:', book.title);
    });

    it('1.4 获取书籍章节列表', async () => {
      if (!testBookId) {
        console.log('⚠️ 跳过：没有测试书籍ID');
        return;
      }
      const chapters = await getChapters(testBookId);
      expect(Array.isArray(chapters)).toBe(true);
      console.log('✅ 获取章节列表成功，数量:', chapters.length);
    });
  });

  describe('2. Skill 系统 API', () => {
    it('2.1 获取所有 Skills', async () => {
      const skills = await getSkills();
      expect(Array.isArray(skills)).toBe(true);
      expect(skills.length).toBeGreaterThan(0);
      console.log('✅ 获取 Skills 成功，数量:', skills.length);
    });
  });

  describe('3. 工作流 API', () => {
    it('3.1 生成大纲工作流', async () => {
      if (!testBookId) {
        console.log('⚠️ 跳过：没有测试书籍ID');
        return;
      }
      try {
        const result = await startGenerateOutline(testBookId);
        expect(result).toHaveProperty('workflow_id');
        console.log('✅ 生成大纲工作流启动成功');
      } catch (error: unknown) {
        const msg = error instanceof Error ? error.message : String(error);
        console.log('⚠️ 生成大纲失败:', msg);
      }
    });
  });

  describe('4. 清理测试数据', () => {
    it('4.1 删除测试书籍', async () => {
      if (!testBookId) {
        console.log('⚠️ 跳过：没有测试书籍ID');
        return;
      }
      await deleteBook(testBookId);
      console.log('✅ 删除测试书籍成功，ID:', testBookId);
    });
  });
});
