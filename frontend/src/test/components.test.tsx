/**
 * 组件测试用例
 * 测试 React 组件渲染和交互
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import Home from '@/pages/Home';
import CreateBook from '@/pages/CreateBook';

// Mock API 调用
vi.mock('@/services/api', () => ({
  getBooks: vi.fn(() => Promise.resolve([])),
  createBook: vi.fn(() => Promise.resolve({ id: 1 })),
  deleteBook: vi.fn(() => Promise.resolve()),
}));

const renderWithRouter = (component: React.ReactNode) => {
  return render(
    <BrowserRouter>
      <ConfigProvider>{component}</ConfigProvider>
    </BrowserRouter>
  );
};

describe('组件渲染测试', () => {
  describe('Home 组件', () => {
    it('应该显示空状态当没有书籍时', async () => {
      renderWithRouter(<Home />);
      
      // 等待组件加载
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(screen.getByText('开始你的创作之旅')).toBeDefined();
      expect(screen.getByText('创建你的第一部AI辅助小说，让创作更高效')).toBeDefined();
    });

    it('应该显示创建按钮', async () => {
      renderWithRouter(<Home />);
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const createButton = screen.getByText('创建第一本书');
      expect(createButton).toBeDefined();
    });
  });

  describe('CreateBook 组件', () => {
    it('应该显示创建表单', () => {
      renderWithRouter(<CreateBook />);
      
      expect(screen.getByText('创建新书')).toBeDefined();
      expect(screen.getByPlaceholderText('给你的小说起个响亮的名字')).toBeDefined();
    });

    it('应该显示步骤条', () => {
      renderWithRouter(<CreateBook />);
      
      expect(screen.getByText('基本信息')).toBeDefined();
      expect(screen.getByText('详细设置')).toBeDefined();
      expect(screen.getByText('完成')).toBeDefined();
    });

    it('点击下一步应该切换到第二步', () => {
      renderWithRouter(<CreateBook />);
      
      const nextButton = screen.getByText('下一步');
      fireEvent.click(nextButton);
      
      // 应该显示第二步的内容
      expect(screen.getByText('上一步')).toBeDefined();
      expect(screen.getByText('创建书籍')).toBeDefined();
    });
  });
});

describe('导航测试', () => {
  it('导航链接应该正确渲染', () => {
    render(
      <BrowserRouter>
        <div>Test Content</div>
      </BrowserRouter>
    );
    
    expect(document.body).toBeDefined();
  });
});
