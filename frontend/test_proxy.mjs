/**
 * 测试前端代理是否正常工作
 */
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:3003/api',  // 代理路径（不带/v1）
  timeout: 30000,
});

async function testProxy() {
  console.log('🧪 测试前端代理...\n');
  
  try {
    // 测试1: 获取书籍列表
    console.log('📍 测试1: 获取书籍列表 (通过代理)');
    const books = await api.get('/books');
    console.log('✅ 获取书籍列表成功, 数量:', books.data.length);
    
    // 测试2: 创建书籍
    console.log('\n📍 测试2: 创建书籍 (通过代理)');
    const newBook = await api.post('/books', {
      title: `前端测试书籍_${Date.now()}`,
      genre: 'xuanhuan',
      platform: '起点',
      chapter_words: 3000,
      target_chapters: 100
    });
    console.log('✅ 创建书籍成功:', newBook.data);
    
    // 测试3: 验证创建
    console.log('\n📍 测试3: 验证创建');
    const allBooks = await api.get('/books');
    const bookTitles = allBooks.data.map((b) => `${b.id}: ${b.title}`);
    console.log('✅ 书籍列表:', bookTitles);
    
    console.log('\n✅ 所有测试通过！代理配置正确。');
    
  } catch (error) {
    console.error('\n❌ 测试失败:');
    if (error.response) {
      console.error('状态码:', error.response.status);
      console.error('响应数据:', error.response.data);
    } else if (error.request) {
      console.error('请求已发送但没有收到响应');
      console.error('错误:', error.message);
    } else {
      console.error('错误:', error.message);
    }
  }
}

testProxy();
