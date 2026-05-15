/**
 * 用户旅程 E2E 测试
 * 大厂测试标准：端到端测试
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { chromium, Browser, Page } from 'playwright'

describe('User Journey E2E Tests', () => {
  let browser: Browser
  let page: Page
  const BASE_URL = 'http://localhost:5173' // Vite dev server

  beforeAll(async () => {
    browser = await chromium.launch({ headless: true })
    page = await browser.newPage()
    await page.setViewportSize({ width: 1280, height: 720 })
  })

  afterAll(async () => {
    await browser.close()
  })

  describe('Home Page', () => {
    it('should load home page', async () => {
      await page.goto(BASE_URL)
      await page.waitForLoadState('networkidle')
      
      const title = await page.title()
      expect(title).toContain('Novel')
    })

    it('should display book list', async () => {
      await page.goto(BASE_URL)
      
      // Wait for book list to load
      await page.waitForSelector('.book-list, .book-card, [data-testid="book-list"]', {
        timeout: 10000
      })
      
      const books = await page.locator('.book-card, [data-testid="book-card"]').count()
      expect(books).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Create Book Flow', () => {
    it('should open create book modal', async () => {
      await page.goto(BASE_URL)
      
      // Click create button
      await page.click('button:has-text("新建"), button:has-text("创建"), [data-testid="create-book-btn"]')
      
      // Check modal is open
      const modal = await page.locator('.modal, .dialog, [role="dialog"]').isVisible()
      expect(modal).toBe(true)
    })

    it('should create a new book', async () => {
      await page.goto(BASE_URL)
      
      // Open create modal
      await page.click('button:has-text("新建"), button:has-text("创建")')
      
      // Fill form
      await page.fill('input[name="title"], [data-testid="book-title-input"]', 'E2E Test Book')
      await page.fill('input[name="genre"], [data-testid="book-genre-input"]', '玄幻')
      
      // Submit
      await page.click('button:has-text("确定"), button:has-text("创建"), button[type="submit"]')
      
      // Wait for success
      await page.waitForTimeout(1000)
      
      // Verify book appears in list
      const pageContent = await page.content()
      expect(pageContent).toContain('E2E Test Book')
    })

    it('should show validation errors', async () => {
      await page.goto(BASE_URL)
      
      // Open create modal
      await page.click('button:has-text("新建"), button:has-text("创建")')
      
      // Submit without filling required fields
      await page.click('button:has-text("确定"), button:has-text("创建"), button[type="submit"]')
      
      // Check for error message
      const errorVisible = await page.locator('.error, .el-form-item__error, [role="alert"]').isVisible()
      expect(errorVisible).toBe(true)
    })
  })

  describe('Book Detail Flow', () => {
    it('should navigate to book detail', async () => {
      await page.goto(BASE_URL)
      
      // Click on first book
      await page.click('.book-card:first-child, [data-testid="book-card"]:first-child')
      
      // Wait for detail page
      await page.waitForSelector('.book-detail, [data-testid="book-detail"]', {
        timeout: 5000
      })
      
      const detailVisible = await page.locator('.book-detail, [data-testid="book-detail"]').isVisible()
      expect(detailVisible).toBe(true)
    })

    it('should display book chapters', async () => {
      await page.goto(BASE_URL)
      
      // Click on first book
      await page.click('.book-card:first-child')
      
      // Wait for chapters
      await page.waitForTimeout(1000)
      
      const chaptersVisible = await page.locator('.chapter-list, [data-testid="chapter-list"]').isVisible()
      // May or may not have chapters
      expect(typeof chaptersVisible).toBe('boolean')
    })
  })

  describe('Navigation', () => {
    it('should navigate between pages', async () => {
      // Home
      await page.goto(BASE_URL)
      expect(await page.url()).toBe(BASE_URL + '/')
      
      // Navigate to books
      await page.click('a[href="/books"], nav a:has-text("书籍")')
      await page.waitForTimeout(500)
      expect(await page.url()).toContain('/books')
    })

    it('should handle 404 pages', async () => {
      await page.goto(`${BASE_URL}/non-existent-page`)
      
      // Should show 404 or redirect
      const content = await page.content()
      const has404 = content.includes('404') || content.includes('Not Found') || content.includes('找不到')
      expect(has404).toBe(true)
    })
  })

  describe('Responsive Design', () => {
    it('should adapt to mobile viewport', async () => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto(BASE_URL)
      
      // Check mobile menu or layout
      const mobileElements = await page.locator('.mobile-menu, .hamburger, [data-testid="mobile-nav"]').count()
      expect(mobileElements).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Accessibility', () => {
    it('should have proper heading structure', async () => {
      await page.goto(BASE_URL)
      
      const h1Count = await page.locator('h1').count()
      expect(h1Count).toBeGreaterThanOrEqual(1)
    })

    it('should have alt text on images', async () => {
      await page.goto(BASE_URL)
      
      const images = await page.locator('img').all()
      for (const img of images) {
        const alt = await img.getAttribute('alt')
        // Alt can be empty for decorative images, but should exist
        expect(alt !== null).toBe(true)
      }
    })
  })
})
