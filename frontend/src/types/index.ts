/** 书籍类型 */
export interface Book {
  id: number;
  title: string;
  genre: string;
  platform: string;
  chapter_words: number;
  target_chapters: number;
  outline: string;
  writing_style: string;
  created_at: string;
  updated_at: string;
}

/** 章节类型 */
export interface Chapter {
  id: number;
  book_id: number;
  chapter_number: number;
  title: string;
  content: string;
  word_count: number;
  audit_score: number;
  continuity_score: number;
  chapter_type: string;
  status: string;
  audit_details: Record<string, unknown>;
  continuity_details: Record<string, unknown>;
}

/** 工作流执行记录 */
export interface WorkflowExecution {
  workflow_id: string;
  book_id: number;
  workflow_type: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed';
  current_node: string;
  progress: number;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  error_message: string;
  started_at: string;
  completed_at: string;
  nodes: Record<string, WorkflowNode>;
}

/** 工作流节点 */
export interface WorkflowNode {
  node_id: string;
  node_type: string;
  node_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  stream_output: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number;
  token_usage: TokenUsage;
  error_message: string;
}

/** Token用量 */
export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

/** 大纲文件 */
export interface OutlineFile {
  key: string;
  name: string;
  label: string;
  exists: boolean;
}

/** 书籍统计 */
export interface BookStatistics {
  book_id: number;
  title: string;
  genre: string;
  total_chapters: number;
  target_chapters: number;
  total_words: number;
  avg_audit_score: number;
  avg_continuity_score: number;
  type_distribution: Record<string, number>;
  recent_scores: Array<{ chapter: number; audit: number; continuity: number }>;
  progress_percent: number;
  active_locks: string[];
}

/** 书籍状态 */
export interface BookState {
  book_id: number;
  current_state: string;
  pending_hooks: string;
  character_matrix: string;
  emotional_arcs: string;
  subplot_board: string;
  chapter_summaries: string;
}

/** Skill类型 */
export interface Skill {
  id: number;
  name: string;
  genre: string;
  category: 'male' | 'female';
  description: string;
  usage_count: number;
}

/** 小说题材 */
export interface GenreItem {
  key: string;
  name: string;
  category: string;
}

/** 创建书籍请求 */
export interface CreateBookRequest {
  title: string;
  genre: string;
  platform: string;
  chapter_words: number;
  target_chapters: number;
  outline: string;
}

/** 续写章节请求 */
export interface ContinueChaptersRequest {
  book_id: number;
  start_chapter: number;
  count: number;
  external_context?: string;
}

/** 重写章节请求 */
export interface RewriteChapterRequest {
  book_id: number;
  chapter_num: number;
  rewrite_requirements: string;
  keep_plot: boolean;
}
