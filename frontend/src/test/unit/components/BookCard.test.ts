/**
 * BookCard 组件单元测试
 * 大厂测试标准：组件测试
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import BookCard from '../../../components/BookCard.vue'

describe('BookCard Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  const mockBook = {
    id: 1,
    title: '测试书籍',
    genre: '玄幻',
    platform: '起点',
    chapter_words: 3000,
    target_chapters: 100,
    created_at: '2024-01-01T00:00:00Z'
  }

  describe('Rendering', () => {
    it('should render book title', () => {
      const wrapper = mount(BookCard, {
        props: { book: mockBook }
      })
      expect(wrapper.text()).toContain('测试书籍')
    })

    it('should render book genre', () => {
      const wrapper = mount(BookCard, {
        props: { book: mockBook }
      })
      expect(wrapper.text()).toContain('玄幻')
    })

    it('should render platform badge', () => {
      const wrapper = mount(BookCard, {
        props: { book: mockBook }
      })
      expect(wrapper.text()).toContain('起点')
    })

    it('should handle missing optional fields', () => {
      const bookWithoutOptionals = {
        id: 1,
        title: '测试书籍'
      }
      const wrapper = mount(BookCard, {
        props: { book: bookWithoutOptionals }
      })
      expect(wrapper.text()).toContain('测试书籍')
    })
  })

  describe('Interactions', () => {
    it('should emit click event when clicked', async () => {
      const wrapper = mount(BookCard, {
        props: { book: mockBook }
      })
      
      await wrapper.trigger('click')
      expect(wrapper.emitted('click')).toBeTruthy()
    })

    it('should emit select event with book id', async () => {
      const wrapper = mount(BookCard, {
        props: { book: mockBook }
      })
      
      await wrapper.find('.select-btn').trigger('click')
      expect(wrapper.emitted('select')).toEqual([[1]])
    })

    it('should emit delete event when delete clicked', async () => {
      const wrapper = mount(BookCard, {
        props: { book: mockBook }
      })
      
      await wrapper.find('.delete-btn').trigger('click')
      expect(wrapper.emitted('delete')).toEqual([[1]])
    })
  })

  describe('Styling', () => {
    it('should have correct CSS classes', () => {
      const wrapper = mount(BookCard, {
        props: { book: mockBook }
      })
      expect(wrapper.classes()).toContain('book-card')
    })

    it('should apply selected class when selected', () => {
      const wrapper = mount(BookCard, {
        props: { 
          book: mockBook,
          selected: true 
        }
      })
      expect(wrapper.classes()).toContain('selected')
    })
  })

  describe('Accessibility', () => {
    it('should have correct aria-label', () => {
      const wrapper = mount(BookCard, {
        props: { book: mockBook }
      })
      expect(wrapper.attributes('aria-label')).toContain('测试书籍')
    })

    it('should be keyboard accessible', async () => {
      const wrapper = mount(BookCard, {
        props: { book: mockBook }
      })
      
      await wrapper.trigger('keydown.enter')
      expect(wrapper.emitted('click')).toBeTruthy()
    })
  })
})
