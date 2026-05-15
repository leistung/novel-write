/**
 * SSE (Server-Sent Events) 服务
 * 
 * 用于接收后端 LLM 流式输出
 */

export interface SSEEvent {
  type: 'start' | 'token' | 'node_end' | 'progress' | 'done' | 'error';
  node?: string;
  text?: string;
  value?: number;
  ok?: boolean;
  error?: string;
  data?: Record<string, unknown>;
}

export type SSEEventHandler = (event: SSEEvent) => void;
export type SSEErrorHandler = (error: Error) => void;
export type SSECloseHandler = () => void;

export class SSEClient {
  private eventSource: EventSource | null = null;
  private onEvent: SSEEventHandler;
  private onError: SSEErrorHandler;
  private onClose: SSECloseHandler;

  constructor(
    onEvent: SSEEventHandler,
    onError: SSEErrorHandler,
    onClose: SSECloseHandler
  ) {
    this.onEvent = onEvent;
    this.onError = onError;
    this.onClose = onClose;
  }

  /**
   * 连接到 SSE 端点
   */
  connect(url: string): void {
    if (this.eventSource) {
      this.disconnect();
    }

    this.eventSource = new EventSource(url);

    this.eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as SSEEvent;
        this.onEvent(data);
      } catch (err) {
        this.onError(new Error(`解析 SSE 数据失败: ${e.data}`));
      }
    };

    this.eventSource.onerror = (e) => {
      this.onError(new Error('SSE 连接错误'));
      this.disconnect();
    };

    this.eventSource.onopen = () => {
      console.log('[SSE] 连接已建立:', url);
    };
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.onClose();
      console.log('[SSE] 连接已关闭');
    }
  }

  /**
   * 是否已连接
   */
  isConnected(): boolean {
    return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN;
  }
}

// ========== 便捷函数 ==========

const API_BASE = '/api/v1';

/**
 * 生成大纲（流式）
 */
export function streamGenerateOutline(
  bookId: number,
  onEvent: SSEEventHandler,
  onError: SSEErrorHandler,
  onClose: SSECloseHandler
): SSEClient {
  const client = new SSEClient(onEvent, onError, onClose);
  client.connect(`${API_BASE}/stream/generate-outline?book_id=${bookId}`);
  return client;
}

/**
 * 续写章节（流式）
 */
export function streamContinueChapters(
  bookId: number,
  startChapter: number,
  count: number,
  onEvent: SSEEventHandler,
  onError: SSEErrorHandler,
  onClose: SSECloseHandler
): SSEClient {
  const client = new SSEClient(onEvent, onError, onClose);
  client.connect(
    `${API_BASE}/stream/continue-chapters?book_id=${bookId}&start_chapter=${startChapter}&count=${count}`
  );
  return client;
}

/**
 * 重写章节（流式）
 */
export function streamRewriteChapter(
  bookId: number,
  chapterNum: number,
  rewriteRequirements: string,
  keepPlot: boolean,
  onEvent: SSEEventHandler,
  onError: SSEErrorHandler,
  onClose: SSECloseHandler
): SSEClient {
  const client = new SSEClient(onEvent, onError, onClose);
  const params = new URLSearchParams({
    book_id: String(bookId),
    chapter_num: String(chapterNum),
    rewrite_requirements: rewriteRequirements,
    keep_plot: String(keepPlot),
  });
  client.connect(`${API_BASE}/stream/rewrite-chapter?${params.toString()}`);
  return client;
}
