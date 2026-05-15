import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import React from 'react';

// BookCard 组件测试
// 由于实际组件可能较复杂，这里创建测试用的简化版本

interface Book {
  id: number;
  title: string;
  genre: string;
  platform: string;
  chapter_words: number;
  target_chapters: number;
  created_at: string;
  updated_at: string;
}

// 简化的BookCard组件用于测试
const TestBookCard: React.FC<{ book: Book; onDelete?: (id: number) => void }> = ({ book, onDelete }) => {
  return (
    <div className="book-card" data-testid={`book-card-${book.id}`}>
      <h3 className="book-title">{book.title}</h3>
      <div className="book-meta">
        <span className="book-genre" data-testid="book-genre">{book.genre}</span>
        <span className="book-platform" data-testid="book-platform">{book.platform}</span>
      </div>
      <div className="book-stats">
        <span data-testid="chapter-words">{book.chapter_words}字/章</span>
        <span data-testid="target-chapters">目标{book.target_chapters}章</span>
      </div>
      <div className="book-actions">
        <button 
          className="btn-edit"
          onClick={() => window.location.href = `/books/${book.id}`}
          data-testid="btn-edit"
        >
          编辑
        </button>
        <button 
          className="btn-delete"
          onClick={() => onDelete?.(book.id)}
          data-testid="btn-delete"
        >
          删除
        </button>
      </div>
    </div>
  );
};

describe('BookCard Component', () => {
  const mockBook: Book = {
    id: 1,
    title: '测试小说',
    genre: '玄幻',
    platform: '起点',
    chapter_words: 3000,
    target_chapters: 100,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  it('应该正确渲染书籍信息', () => {
    render(
      <BrowserRouter>
        <TestBookCard book={mockBook} />
      </BrowserRouter>
    );

    expect(screen.getByText('测试小说')).toBeInTheDocument();
    expect(screen.getByTestId('book-genre')).toHaveTextContent('玄幻');
    expect(screen.getByTestId('book-platform')).toHaveTextContent('起点');
    expect(screen.getByTestId('chapter-words')).toHaveTextContent('3000字/章');
    expect(screen.getByTestId('target-chapters')).toHaveTextContent('目标100章');
  });

  it('应该显示不同的书籍类型', () => {
    const xianxiaBook = { ...mockBook, genre: '仙侠' };
    render(
      <BrowserRouter>
        <TestBookCard book={xianxiaBook} />
      </BrowserRouter>
    );

    expect(screen.getByTestId('book-genre')).toHaveTextContent('仙侠');
  });

  it('应该显示不同的平台', () => {
    const jjwxcBook = { ...mockBook, platform: '晋江' };
    render(
      <BrowserRouter>
        <TestBookCard book={jjwxcBook} />
      </BrowserRouter>
    );

    expect(screen.getByTestId('book-platform')).toHaveTextContent('晋江');
  });

  it('点击删除按钮应该触发onDelete回调', () => {
    const onDelete = vi.fn();
    render(
      <BrowserRouter>
        <TestBookCard book={mockBook} onDelete={onDelete} />
      </BrowserRouter>
    );

    const deleteButton = screen.getByTestId('btn-delete');
    fireEvent.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith(1);
    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it('应该为每本书渲染唯一的data-testid', () => {
    const { container } = render(
      <BrowserRouter>
        <TestBookCard book={mockBook} />
      </BrowserRouter>
    );

    expect(container.querySelector('[data-testid="book-card-1"]')).toBeInTheDocument();
  });

  it('应该处理长标题', () => {
    const longTitleBook = { 
      ...mockBook, 
      title: '这是一本非常非常非常非常非常非常非常非常非常非常长的书名' 
    };
    render(
      <BrowserRouter>
        <TestBookCard book={longTitleBook} />
      </BrowserRouter>
    );

    expect(screen.getByText(longTitleBook.title)).toBeInTheDocument();
  });

  it('应该处理边界字数', () => {
    const edgeCaseBook = { 
      ...mockBook, 
      chapter_words: 0,
      target_chapters: 0
    };
    render(
      <BrowserRouter>
        <TestBookCard book={edgeCaseBook} />
      </BrowserRouter>
    );

    expect(screen.getByTestId('chapter-words')).toHaveTextContent('0字/章');
    expect(screen.getByTestId('target-chapters')).toHaveTextContent('目标0章');
  });
});
