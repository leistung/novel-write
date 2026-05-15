import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';

// 日志存储
interface LogEntry {
  id: string;
  timestamp: Date;
  type: 'request' | 'response' | 'error' | 'info';
  method?: string;
  url?: string;
  status?: number;
  data?: unknown;
  error?: string;
  duration?: number;
  requestId?: string;
}

class APILogger {
  private logs: LogEntry[] = [];
  private maxLogs = 100;
  private listeners: ((logs: LogEntry[]) => void)[] = [];

  addLog(entry: Omit<LogEntry, 'id' | 'timestamp'>) {
    const log: LogEntry = {
      ...entry,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    
    this.logs.unshift(log);
    if (this.logs.length > this.maxLogs) {
      this.logs.pop();
    }
    
    // 通知监听器
    this.notifyListeners();
    
    // 同时输出到控制台
    this.logToConsole(log);
    
    return log.id;
  }

  private logToConsole(log: LogEntry) {
    const time = log.timestamp.toLocaleTimeString();
    const prefix = `[${time}]`;
    
    switch (log.type) {
      case 'request':
        console.log(
          `%c${prefix} REQUEST%c ${log.method} ${log.url}`,
          'color: #3b82f6; font-weight: bold',
          'color: #64748b'
        );
        if (log.data) {
          console.log('  Data:', log.data);
        }
        break;
      case 'response':
        const isSuccess = log.status && log.status >= 200 && log.status < 300;
        console.log(
          `%c${prefix} RESPONSE%c ${log.method} ${log.url} ${log.status} (${log.duration}ms)`,
          isSuccess ? 'color: #10b981; font-weight: bold' : 'color: #f59e0b; font-weight: bold',
          'color: #64748b'
        );
        if (log.data) {
          console.log('  Response:', log.data);
        }
        break;
      case 'error':
        console.error(
          `%c${prefix} ERROR%c ${log.method} ${log.url} ${log.status}`,
          'color: #ef4444; font-weight: bold',
          'color: #64748b'
        );
        console.error('  Error:', log.error);
        break;
      case 'info':
        console.log(
          `%c${prefix} INFO`,
          'color: #8b5cf6; font-weight: bold'
        );
        console.log('  ', log.data);
        break;
    }
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener([...this.logs]));
  }

  onUpdate(callback: (logs: LogEntry[]) => void) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback);
    };
  }

  getLogs() {
    return [...this.logs];
  }

  clearLogs() {
    this.logs = [];
    this.notifyListeners();
  }

  getFailedRequests(): LogEntry[] {
    return this.logs.filter(log => log.type === 'error');
  }
}

export const apiLogger = new APILogger();

// API 实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // Token 注入
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 生成请求ID
    const requestId = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    config.headers['X-Request-ID'] = requestId;

    // 记录请求
    apiLogger.addLog({
      type: 'request',
      method: config.method?.toUpperCase(),
      url: `${config.baseURL}${config.url}`,
      data: config.data,
      requestId,
    });

    return config;
  },
  (error) => {
    apiLogger.addLog({
      type: 'error',
      error: `Request setup error: ${error.message}`,
    });
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // @ts-ignore - metadata 是动态添加的属性
    const startTime = response.config.metadata?.startTime;
    const duration = startTime ? Date.now() - startTime : undefined;
    
    apiLogger.addLog({
      type: 'response',
      method: response.config.method?.toUpperCase(),
      url: `${response.config.baseURL}${response.config.url}`,
      status: response.status,
      data: response.data,
      duration,
      requestId: response.config.headers['x-request-id'] as string,
    });
    
    return response;
  },
  async (error: AxiosError) => {
    // @ts-ignore - metadata 是动态添加的属性
    const startTime = error.config?.metadata?.startTime;
    const duration = startTime ? Date.now() - startTime : undefined;
    
    // 提取详细错误信息
    let errorMessage = error.message;
    let errorDetails: unknown = null;
    
    if (error.response) {
      const data = error.response.data as { detail?: string; message?: string };
      errorMessage = data?.detail || data?.message || error.message;
      errorDetails = data;
    } else if (error.request) {
      // 请求已发送但没有收到响应
      errorMessage = `网络错误: ${error.message}`;
    }
    
    apiLogger.addLog({
      type: 'error',
      method: error.config?.method?.toUpperCase(),
      url: error.config ? `${error.config.baseURL}${error.config.url}` : undefined,
      status: error.response?.status,
      error: errorMessage,
      data: errorDetails,
      duration,
      requestId: error.config?.headers?.['x-request-id'] as string,
    });
    
    return Promise.reject(error);
  }
);

// ========== 书籍 API ==========

export async function getBooks() {
  const { data } = await api.get('/books');
  return data;
}

export async function getBook(bookId: number) {
  const { data } = await api.get(`/books/${bookId}`);
  return data;
}

export async function createBook(params: {
  title: string;
  genre: string;
  platform?: string;
  chapter_words?: number;
  target_chapters?: number;
  outline?: string;
}) {
  const { data } = await api.post('/books', params);
  return data;
}

export async function updateBook(bookId: number, params: Record<string, unknown>) {
  const { data } = await api.put(`/books/${bookId}`, params);
  return data;
}

export async function deleteBook(bookId: number) {
  const { data } = await api.delete(`/books/${bookId}`);
  return data;
}

// ========== 章节 API ==========

export async function getChapters(bookId: number) {
  const { data } = await api.get(`/books/${bookId}/chapters`);
  return data;
}

export async function getChapter(bookId: number, chapterNum: number) {
  const { data } = await api.get(`/books/${bookId}/chapters/${chapterNum}`);
  return data;
}

export async function updateChapter(bookId: number, chapterNum: number, params: Record<string, unknown>) {
  const { data } = await api.put(`/books/${bookId}/chapters/${chapterNum}`, params);
  return data;
}

// ========== 工作流 API ==========

export async function startGenerateOutline(bookId: number) {
  const { data } = await api.post('/workflows/generate-outline', { book_id: bookId });
  return data;
}

export async function startContinueChapters(params: {
  book_id: number;
  start_chapter: number;
  count: number;
  external_context?: string;
}) {
  const { data } = await api.post('/workflows/continue-chapters', params);
  return data;
}

export async function startRewriteChapter(params: {
  book_id: number;
  chapter_num: number;
  rewrite_requirements: string;
  keep_plot: boolean;
}) {
  const { data } = await api.post('/workflows/rewrite-chapter', params);
  return data;
}

export async function getWorkflowNodes(workflowId: string) {
  const { data } = await api.get(`/workflows/${workflowId}/nodes`);
  return data;
}

export async function getNodeDetail(workflowId: string, nodeId: string) {
  const { data } = await api.get(`/workflows/${workflowId}/nodes/${nodeId}`);
  return data;
}

export async function retryNode(workflowId: string, nodeId: string) {
  const { data } = await api.post(`/workflows/${workflowId}/retry/${nodeId}`);
  return data;
}

// ========== 大纲 API ==========

export async function getOutlineFiles(bookId: number) {
  const { data } = await api.get(`/books/${bookId}/outline`);
  return data;
}

export async function getOutlineContent(bookId: number, key: string) {
  const { data } = await api.get(`/books/${bookId}/outline`, { params: { key } });
  return data;
}

export async function updateOutlineFile(bookId: number, key: string, content: string) {
  const { data } = await api.put(`/books/${bookId}/outline`, { key, content });
  return data;
}

export async function getBookState(bookId: number) {
  const { data } = await api.get(`/books/${bookId}/state`);
  return data;
}

// ========== Workflow Control API ==========

export async function pauseWorkflow(workflowId: string) {
  const { data } = await api.post(`/workflow/pause?workflow_id=${workflowId}`);
  return data;
}

export async function resumeWorkflow(workflowId: string) {
  const { data } = await api.post(`/workflow/resume?workflow_id=${workflowId}`);
  return data;
}

export async function getWorkflowStatus(workflowId: string) {
  const { data } = await api.get(`/workflow/status?workflow_id=${workflowId}`);
  return data;
}

// ========== Skill API ==========

export async function getGenres() {
  const { data } = await api.get('/skills/genres/list');
  return data;
}

export async function getSkills(category?: string) {
  const { data } = await api.get('/skills', { params: { category } });
  return data;
}

export default api;
