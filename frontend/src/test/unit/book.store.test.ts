/**
 * Book Store 单元测试
 * 大厂测试标准：状态管理测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useBookStore } from '../../store/book'
import { setActivePinia, createPinia } from 'pinia'

describe('Book Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('State Management', () => {
    it('should initialize with empty books array', () => {
      const store = useBookStore()
      expect(store.books).toEqual([])
    })

    it('should initialize with null currentBook', () => {
      const store = useBookStore()
      expect(store.currentBook).toBeNull()
    })

    it('should initialize loading state as false', () => {
      const store = useBookStore()
      expect(store.loading).toBe(false)
    })

    it('should initialize error as null', () => {
      const store = useBookStore()
      expect(store.error).toBeNull()
    })
  })

  describe('Getters', () => {
    it('should return books count', () => {
      const store = useBookStore()
      store.books = [
        { id: 1, title: 'Book 1' },
        { id: 2, title: 'Book 2' }
      ] as any
      expect(store.booksCount).toBe(2)
    })

    it('should return zero count for empty books', () => {
      const store = useBookStore()
      expect(store.booksCount).toBe(0)
    })

    it('should check if has current book', () => {
      const store = useBookStore()
      expect(store.hasCurrentBook).toBe(false)
      
      store.currentBook = { id: 1, title: 'Test' } as any
      expect(store.hasCurrentBook).toBe(true)
    })
  })

  describe('Actions - fetchBooks', () => {
    it('should set loading true when fetching', async () => {
      const store = useBookStore()
      
      // Mock API call
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([])
      })

      const promise = store.fetchBooks()
      expect(store.loading).toBe(true)
      await promise
    })

    it('should set books on successful fetch', async () => {
      const store = useBookStore()
      const mockBooks = [
        { id: 1, title: 'Test Book' }
      ]

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockBooks)
      })

      await store.fetchBooks()
      expect(store.books).toEqual(mockBooks)
    })

    it('should set error on failed fetch', async () => {
      const store = useBookStore()
      
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

      await store.fetchBooks()
      expect(store.error).toBe('Network error')
    })

    it('should set loading false after fetch completes', async () => {
      const store = useBookStore()
      
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([])
      })

      await store.fetchBooks()
      expect(store.loading).toBe(false)
    })
  })

  describe('Actions - createBook', () => {
    it('should add new book to books array', async () => {
      const store = useBookStore()
      const newBook = { id: 1, title: 'New Book' }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(newBook)
      })

      await store.createBook({ title: 'New Book' })
      expect(store.books).toContainEqual(newBook)
    })

    it('should handle validation errors', async () => {
      const store = useBookStore()
      
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: () => Promise.resolve({ detail: 'Validation error' })
      })

      await store.createBook({ title: '' })
      expect(store.error).toBeTruthy()
    })
  })

  describe('Actions - setCurrentBook', () => {
    it('should set current book by id', () => {
      const store = useBookStore()
      const book = { id: 1, title: 'Test Book' }
      store.books = [book] as any

      store.setCurrentBook(1)
      expect(store.currentBook).toEqual(book)
    })

    it('should set null for non-existent book', () => {
      const store = useBookStore()
      store.books = [{ id: 1, title: 'Test' }] as any

      store.setCurrentBook(999)
      expect(store.currentBook).toBeNull()
    })
  })

  describe('Error Handling', () => {
    it('should clear error when clearError is called', () => {
      const store = useBookStore()
      store.error = 'Some error'
      
      store.clearError()
      expect(store.error).toBeNull()
    })

    it('should handle API timeout', async () => {
      const store = useBookStore()
      
      global.fetch = vi.fn().mockImplementation(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout')), 100)
        )
      )

      await store.fetchBooks()
      expect(store.error).toBe('Timeout')
      expect(store.loading).toBe(false)
    })
  })
})
