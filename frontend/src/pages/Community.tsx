import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth'
import {
  listPosts,
  searchCommunity,
  createPost,
  extractError,
} from '@/lib/api'
import type { Post, PostInput, SearchResult } from '@/types'
import {
  Search,
  Plus,
  MessageSquare,
  Book as BookIcon,
  User,
  Clock,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '@/components/ui/dialog'

const PAGE_SIZE = 20

function formatDate(s: string | null): string {
  if (!s) return ''
  try {
    const d = new Date(s)
    if (Number.isNaN(d.getTime())) return s
    return d.toLocaleString('zh-CN', { hour12: false })
  } catch {
    return s
  }
}

// 将纯文本（含 [[book:id]] 标记）转换为简单 HTML：空行分段，每段 <p>
function textToHtml(text: string): string {
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  return escaped
    .split(/\n{2,}/)
    .map((seg) => `<p>${seg.replace(/\n/g, '<br/>')}</p>`)
    .join('')
}

export default function Community() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()

  const [page, setPage] = useState(1)
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [showEditor, setShowEditor] = useState(false)
  const [editorForm, setEditorForm] = useState<PostInput>({ title: '', content_html: '', content_text: '' })
  const [error, setError] = useState('')

  // 帖子列表
  const { data: postList, isFetching: postsLoading } = useQuery({
    queryKey: ['community-posts', page],
    queryFn: () => listPosts(page, PAGE_SIZE),
    enabled: !submittedQuery,
  })

  // 搜索
  const { data: searchResult, isFetching: searchLoading } = useQuery<SearchResult>({
    queryKey: ['community-search', submittedQuery],
    queryFn: () => searchCommunity(submittedQuery),
    enabled: !!submittedQuery,
  })

  const createMut = useMutation({
    mutationFn: (body: PostInput) => createPost(body),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ['community-posts'] })
      setShowEditor(false)
      setEditorForm({ title: '', content_html: '', content_text: '' })
      setError('')
      navigate(`/post/${p.id}`)
    },
    onError: (err) => setError(extractError(err, '发帖失败')),
  })

  const openEditor = () => {
    if (!user) {
      const from = encodeURIComponent('/community')
      navigate(`/login?from=${from}`)
      return
    }
    setShowEditor(true)
    setError('')
  }

  const submitPost = (e: FormEvent) => {
    e.preventDefault()
    if (!editorForm.title.trim()) {
      setError('请填写标题')
      return
    }
    if (!editorForm.content_text.trim()) {
      setError('请填写内容')
      return
    }
    const body: PostInput = {
      title: editorForm.title.trim(),
      content_text: editorForm.content_text,
      content_html: editorForm.content_html || textToHtml(editorForm.content_text),
    }
    createMut.mutate(body)
  }

  const onSearch = (e: FormEvent) => {
    e.preventDefault()
    const q = query.trim()
    setPage(1)
    setSubmittedQuery(q)
  }

  const clearSearch = () => {
    setQuery('')
    setSubmittedQuery('')
    setPage(1)
  }

  const totalPages = postList ? Math.max(1, Math.ceil(postList.total / PAGE_SIZE)) : 1

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 animate-fade-up">
      {/* 顶部标题 + 发帖按钮 */}
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-2.5">
          <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center shadow-md shadow-indigo-500/25">
            <MessageSquare size={20} />
          </span>
          <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent dark:from-indigo-400 dark:to-purple-400">
            社区
          </span>
        </h1>
        <Button
          onClick={openEditor}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 shadow-md shadow-indigo-500/20"
        >
          <Plus size={16} /> 发帖
        </Button>
      </div>

      {/* 搜索栏 */}
      <form onSubmit={onSearch} className="flex gap-2 mb-6">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索帖子或书籍…"
            className="pl-9 h-11 bg-background/70"
          />
        </div>
        <Button type="submit" size="lg" className="h-11">搜索</Button>
        {submittedQuery && (
          <Button type="button" variant="ghost" size="lg" className="h-11 text-muted-foreground" onClick={clearSearch}>
            清除
          </Button>
        )}
      </form>

      {/* 内容区 */}
      {submittedQuery ? (
        // 搜索结果
        <div className="space-y-6">
          <div className="text-sm text-muted-foreground">
            搜索 “{submittedQuery}” 的结果：
          </div>
          {searchLoading ? (
            <div className="text-muted-foreground/60 text-sm animate-pulse">搜索中…</div>
          ) : searchResult ? (
            <>
              <SearchSection
                title="帖子结果"
                count={searchResult.posts.length}
                empty="没有匹配的帖子"
              >
                {searchResult.posts.map((p) => (
                  <PostCard key={p.id} post={p} onClick={() => navigate(`/post/${p.id}`)} />
                ))}
              </SearchSection>
              <SearchSection
                title="书籍结果"
                count={searchResult.books.length}
                empty="没有匹配的书籍"
              >
                {searchResult.books.map((b) => (
                  <div
                    key={b.id}
                    onClick={() => navigate(`/read/${b.id}`)}
                    className="card-lift border rounded-xl p-3 cursor-pointer bg-card shadow-sm hover:shadow-md flex gap-3 items-center"
                  >
                    <div className="w-12 h-16 bg-muted rounded-lg flex items-center justify-center text-muted-foreground overflow-hidden shrink-0">
                      {b.cover_url ? (
                        <img src={b.cover_url} className="w-full h-full object-cover" alt={b.title} />
                      ) : (
                        <BookIcon size={18} />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-foreground truncate">{b.title}</div>
                      <div className="text-xs text-muted-foreground mt-1 line-clamp-2">{b.intro}</div>
                      <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
                        {b.genre}
                      </span>
                    </div>
                    <ChevronRight size={16} className="text-muted-foreground shrink-0" />
                  </div>
                ))}
              </SearchSection>
            </>
          ) : null}
        </div>
      ) : (
        // 帖子列表
        <div className="space-y-3">
          {postsLoading && !postList ? (
            <div className="text-muted-foreground/60 text-sm animate-pulse">加载中…</div>
          ) : postList && postList.items.length > 0 ? (
            postList.items.map((p) => (
              <PostCard key={p.id} post={p} onClick={() => navigate(`/post/${p.id}`)} />
            ))
          ) : (
            <div className="text-center text-muted-foreground py-16">
              <MessageSquare size={40} className="mx-auto text-muted-foreground/30 mb-3" />
              <div>还没有帖子，点击右上角发帖成为第一个</div>
            </div>
          )}

          {/* 分页 */}
          {postList && postList.total > PAGE_SIZE && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 text-sm border rounded-lg hover:bg-muted disabled:opacity-40 transition"
              >
                上一页
              </button>
              <span className="text-sm text-muted-foreground">
                第 {page} / {totalPages} 页 · 共 {postList.total} 条
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-3 py-1.5 text-sm border rounded-lg hover:bg-muted disabled:opacity-40 transition"
              >
                下一页
              </button>
            </div>
          )}
        </div>
      )}

      {/* 发帖编辑器 */}
      <Dialog open={showEditor} onOpenChange={setShowEditor}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>发布新帖</DialogTitle>
            <DialogDescription>支持纯文本与 [[book:id]] 引用书籍链接。</DialogDescription>
          </DialogHeader>
          <form onSubmit={submitPost} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="post-title">标题 *</Label>
              <Input
                id="post-title"
                value={editorForm.title}
                onChange={(e) => setEditorForm({ ...editorForm, title: e.target.value })}
                placeholder="帖子标题"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="post-content">内容 *</Label>
              <Textarea
                id="post-content"
                rows={12}
                className="font-mono text-sm"
                value={editorForm.content_text}
                onChange={(e) =>
                  setEditorForm({
                    ...editorForm,
                    content_text: e.target.value,
                    content_html: textToHtml(e.target.value),
                  })
                }
                placeholder={'支持纯文本与 [[book:id]] 引用书籍。\n例如：[[book:12]] 会渲染为指向该书籍阅读页的链接。'}
              />
              <div className="text-xs text-muted-foreground">
                提示：使用 <code className="bg-muted px-1 rounded">[[book:id]]</code> 语法引用书籍
              </div>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowEditor(false)}>取消</Button>
              <Button type="submit" disabled={createMut.isPending}>
                {createMut.isPending ? '发布中…' : '发布'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function SearchSection({
  title,
  count,
  empty,
  children,
}: {
  title: string
  count: number
  empty: string
  children: React.ReactNode
}) {
  return (
    <div>
      <div className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
        {title}
        <span className="text-xs text-muted-foreground/70">({count})</span>
      </div>
      {count > 0 ? (
        <div className="space-y-3">{children}</div>
      ) : (
        <div className="text-sm text-muted-foreground py-4 border rounded-xl text-center bg-muted/40">{empty}</div>
      )}
    </div>
  )
}

function PostCard({ post, onClick }: { post: Post; onClick: () => void }) {
  return (
    <Card className="card-lift group relative overflow-hidden p-4 cursor-pointer border-none shadow-sm" onClick={onClick}>
      {/* 左侧渐变装饰条 */}
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-indigo-500 via-purple-500 to-fuchsia-500 opacity-70 group-hover:opacity-100 transition" />
      <div className="font-medium text-foreground truncate pl-2">{post.title}</div>
      <div className="text-sm text-muted-foreground mt-1.5 line-clamp-2 whitespace-pre-wrap pl-2">
        {post.content_text}
      </div>
      <div className="flex items-center gap-3 mt-3 text-xs text-muted-foreground flex-wrap pl-2">
        <span className="flex items-center gap-1">
          <span className="w-4 h-4 rounded-full bg-primary/15 text-primary flex items-center justify-center">
            <User size={10} />
          </span>
          {post.author_name}
        </span>
        {post.created_at && (
          <span className="flex items-center gap-1">
            <Clock size={12} /> {formatDate(post.created_at)}
          </span>
        )}
        {post.book_links.length > 0 && (
          <span className="flex items-center gap-1">
            <BookIcon size={12} />
            {post.book_links.map((bl) => bl.book_title).join(' / ')}
          </span>
        )}
        <ChevronRight size={14} className="ml-auto text-muted-foreground/50 group-hover:text-primary group-hover:translate-x-0.5 transition" />
      </div>
    </Card>
  )
}
