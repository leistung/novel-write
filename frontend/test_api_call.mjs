/**
 * 测试前端 API 调用
 */
import axios from 'axios';

// 模拟前端的 api 配置
const api = axios.create({
  baseURL: '/api/v1',  // 前端配置
  timeout: 30000,
});

async function testFrontendAPI() {
  console.log('🧪 测试前端 API 调用（通过 Vite 代理）...\n');
  
  try {
    // 测试1: 获取书籍列表
    console.log('📍 测试1: GET /api/v1/books');
    const books = await api.get('/books');
    console.log('✅ 获取书籍列表成功!');
    console.log('   数量:', books.data.length);
    console.log('   第一本书:', books.data[0]?.title || '无');
    
    // 测试2: 创建书籍
    console.log('\n📍 测试2: POST /api/v1/books');
    const newBookData = {
      title: `前端测试书籍_${Date.now()}`,
      genre: 'xuanhuan',
      platform: '起点',
      chapter_words: 3000,
      target_chapters: 100
    };
    console.log('   发送数据:', JSON.stringify(newBookData));
    const newBook = await api.post('/books', newBookData);
    console.log('✅ 创建书籍成功!');
    console.log('   响应:', JSON.stringify(newBook.data));
    
    // 测试3: 获取单本书籍
    const bookId = newBook.data.id;
    console.log('\n📍 测试3: GET /api/v1/books/' + bookId);
    const book = await api.get(`/books/${bookId}`);
    console.log('✅ 获取书籍详情成功!');
    
    // 测试4: 删除书籍
    console.log('\n📍 测试4: DELETE /api/v1/books/' + bookId);
    await api.delete(`/books/${bookId}`);
    console.log('✅ 删除书籍成功!');
    
    console.log('\n' + '='.repeat(50));
    console.log('✅✅✅ 所有测试通过！');
    console.log('='.repeat(50));
    console.log('\n前端代理配置正确，API 调用完全正常！');
    
  } catch (error) {
    console.error('\n❌ 测试失败:');
    if (error.response) {
      console.error('状态码:', error.response.status);
      console.error('响应数据:', error.response.data);
      console.error('请求URL:', error.config?.url);
    } else if (error.request) {
      console.error('请求已发送但没有收到响应');
      console.error('这通常意味着代理没有正确转发请求');
      console.error('错误:', error.message);
    } else {
      console.error('错误:', error.message);
    }
  }
}

testFrontendAPI();
