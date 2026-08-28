import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Highlight from '@tiptap/extension-highlight'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import api, { extractError, streamChat, streamChapterGenerate, listChatSessions, getChatMessages, polishChapter, continueWriting, analyzeBook } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import type { Book, Chapter, ChapterDetail, Volume, ChatMessage, ChatResponse, ChatSession, ChapterGenerateResponse, AnalyzeSkill, LLMConfig } from '@/types'
import {
  Plus, Save, Home as HomeIcon, Bold, Italic, Heading1, Heading2,
  Highlighter, List, Send, RotateCcw, PenLine, Wand2, CornerDownRight, Sparkles, History,
} from 'lucide-react'
import OutlinePanel from '@/components/OutlinePanel'
import DatabasePanel from '@/components/DatabasePanel'
import ConfigPage from '@/components/ConfigPage'
import ReaderPage from '@/components/ReaderPage'
import BookInfoPage from '@/components/BookInfoPage'
import WorkspaceSettings from '@/components/WorkspaceSettings'
import type { KeyboardEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

const TABS = ['创作', '阅读', '角色', '场景', '物品', '情节', '大纲', '数据库', '书籍信息', '设置'] as const
const ENABLED_TABS: ReadonlySet<string> = new Set(['创作', '阅读', '角色', '场景', '物品', '情节', '大纲', '数据库', '书籍信息', '设置'])

type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

export default function Workspace() {
  const { bookId = '' } = useParams<{ bookId: string }>()
  const bid = Number(bookId)
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const fetchMe = useAuthStore((s) => s.fetchMe)
  const isBusiness = user?.version === 'business'
  const [activeTab, setActiveTab] = useState<typeof TABS[number]>('创作')
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')
  const [chapterTitle, setChapterTitle] = useState('')
  const [error, setError] = useState('')
  const saveTimer = useRef<number | null>(null)
  const lastSavedId = useRef<number | null>(null)

  const { data: book } = useQuery({
    queryKey: ['book', bid],
    queryFn: async () => (await api.get<Book>(`/books/${bid}`)).data,
    enabled: !!bid,
  })
  const { data: chapters } = useQuery({
    queryKey: ['chapters', bid],
    queryFn: async () => (await api.get<Chapter[]>(`/chapters/books/${bid}`)).data,
    enabled: !!bid,
  })
  const { data: volumes } = useQuery({
    queryKey: ['volumes', bid],
    queryFn: async () => (await api.get<Volume[]>(`/books/${bid}/volumes`)).data,
    enabled: !!bid,
  })

  // ===== 模型配置就绪检测（本地版需自配 LLM + Embedding） =====
  const navigate = useNavigate()
  const [autoSaveMs, setAutoSaveMs] = useState(() => {
    const v = Number(localStorage.getItem('sc_autosave_ms'))
    return Number.isFinite(v) && v > 0 ? v : 5000
  })
  const { data: llmConfigs } = useQuery({
    queryKey: ['llm-configs'],
    queryFn: async () => (await api.get<LLMConfig[]>('/llm-configs')).data,
    enabled: !isBusiness,
  })
  const llmReady = isBusiness || (llmConfigs ?? []).some((c) => c.has_key && c.model)
  const embeddingReady = isBusiness || (llmConfigs ?? []).some((c) => c.has_embedding_key && c.embedding_model)

  const requireLlm = (): boolean => {
    if (llmReady) return true
    toast.warning('尚未配置对话模型', { description: '写作、Ask 等需要对话模型，请先到模型配置页完成配置。', action: { label: '去配置', onClick: () => navigate('/llm-configs') } })
    return false
  }
  const requireEmbedding = (): boolean => {
    if (embeddingReady) return true
    toast.warning('尚未配置向量模型（Embedding）', { description: '章节入库与 RAG 检索需要向量模型，请在模型配置中补充。', action: { label: '去配置', onClick: () => navigate('/llm-configs') } })
    return false
  }

  const { data: chapterDetail } = useQuery({
    queryKey: ['chapter', selectedChapterId],
    queryFn: async () => (await api.get<ChapterDetail>(`/chapters/${selectedChapterId}`)).data,
    enabled: !!selectedChapterId,
  })

  const doSave = useCallback(async (html: string, title: string) => {
    if (!selectedChapterId) return
    setSaveStatus('saving')
    setError('')
    try {
      await api.put(`/chapters/${selectedChapterId}`, { content: html, title })
      setSaveStatus('saved')
      qc.invalidateQueries({ queryKey: ['chapters', bid] })
      qc.invalidateQueries({ queryKey: ['book', bid] })
      qc.invalidateQueries({ queryKey: ['stats'] })
    } catch (e) {
      setSaveStatus('error')
      setError(extractError(e, '保存失败'))
    }
  }, [selectedChapterId, bid, qc])

  const editor = useEditor({
    extensions: [StarterKit, Highlight],
    content: '',
    immediatelyRender: false,
    onUpdate: ({ editor: ed }) => {
      setSaveStatus('idle')
      if (streamingRef.current) return  // 流式生成中不自动保存
      if (saveTimer.current) window.clearTimeout(saveTimer.current)
      saveTimer.current = window.setTimeout(() => {
        void doSave(ed.getHTML(), chapterTitle)
      }, autoSaveMs)
    },
  })

  // 选中章节时加载内容到编辑器
  useEffect(() => {
    if (!editor || !chapterDetail) return
    if (lastSavedId.current === chapterDetail.id) return
    lastSavedId.current = chapterDetail.id
    setChapterTitle(chapterDetail.title)
    setSaveStatus('idle')
    editor.commands.setContent(chapterDetail.content || '', { emitUpdate: false })
    setTimeout(() => editor.commands.focus(), 0)
  }, [editor, chapterDetail])

  // 卸载/切换章节时清理定时器
  useEffect(() => {
    return () => {
      if (saveTimer.current) window.clearTimeout(saveTimer.current)
    }
  }, [])

  const manualSave = () => {
    if (!editor) return
    if (saveTimer.current) window.clearTimeout(saveTimer.current)
    void doSave(editor.getHTML(), chapterTitle)
  }

  const titleInputSave = (title: string) => {
    setChapterTitle(title)
    if (editor && selectedChapterId) {
      if (saveTimer.current) window.clearTimeout(saveTimer.current)
      saveTimer.current = window.setTimeout(() => {
        void doSave(editor.getHTML(), title)
      }, 2000)
    }
  }

  const createChapter = useMutation({
    mutationFn: async (title: string) => (await api.post<ChapterDetail>(`/chapters/books/${bid}`, { title })).data,
    onSuccess: (c) => {
      qc.invalidateQueries({ queryKey: ['chapters', bid] })
      setSelectedChapterId(c.id)
    },
    onError: (e) => setError(extractError(e, '新建章节失败')),
  })

  // 自动定位最新章节
  useEffect(() => {
    if (chapters && chapters.length && selectedChapterId === null) {
      setSelectedChapterId(chapters[chapters.length - 1].id)
    }
  }, [chapters, selectedChapterId])

  // ===== Ask 面板 =====
  const [askMessages, setAskMessages] = useState<ChatMessage[]>([])
  const [askInput, setAskInput] = useState('')
  const [threadId, setThreadId] = useState('')
  const [askSending, setAskSending] = useState(false)

  // ===== Ask 历史记录 =====
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)

  const refreshSessions = async () => {
    try {
      const list = await listChatSessions()
      setSessions(list)
    } catch { /* 静默失败，历史面板仍可用 */ }
  }

  useEffect(() => {
    if (historyOpen) {
      setHistoryLoading(true)
      void refreshSessions().finally(() => setHistoryLoading(false))
    }
  }, [historyOpen])

  const toggleHistory = () => {
    setHistoryOpen((v) => {
      const next = !v
      if (next) void refreshSessions()
      return next
    })
  }

  const loadSession = async (thread_id: string) => {
    if (historyLoading) return
    setHistoryLoading(true)
    try {
      const msgs = await getChatMessages(thread_id)
      setAskMessages(msgs)
      setThreadId(thread_id)
    } catch (e) {
      setError(extractError(e, '加载历史失败'))
    } finally {
      setHistoryLoading(false)
    }
  }

  const fmtTime = (iso?: string | null) => {
    if (!iso) return ''
    const d = new Date(iso)
    const now = new Date()
    const sameDay = d.toDateString() === now.toDateString()
    return sameDay
      ? d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      : d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
  }

  const sendAsk = async () => {
    const text = askInput.trim()
    if (!text || askSending) return
    if (!requireLlm()) return
    setAskSending(true)
    setAskInput('')
    const tempId = `temp-${Date.now()}`
    const assistantId = `temp-a-${Date.now()}`
    setAskMessages((prev) => [
      ...prev,
      { id: tempId, role: 'user', content: text },
      { id: assistantId, role: 'assistant', content: '' },
    ])
    await streamChat(
      { message: text, thread_id: threadId || undefined },
      {
        onStart: (d) => { if (d.thread_id) setThreadId(d.thread_id) },
        onState: (s) => {
          if (typeof s.content === 'string') {
            setAskMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: s.content as string } : m,
              ),
            )
          }
        },
        onDone: (d) => {
          const done = d as unknown as ChatResponse
          setAskMessages((prev) => [
            ...prev.filter((m) => m.id !== tempId && m.id !== assistantId),
            { id: tempId, role: 'user', content: text },
            {
              id: String(done.message_id), role: 'assistant', content: done.content,
              model: done.model, in_tokens: done.in_tokens, out_tokens: done.out_tokens,
              credits_cost: done.credits_cost,
            },
          ])
          if (isBusiness) void fetchMe()
        },
        onError: (msg) => {
          setError(msg || '发送失败')
          setAskMessages((prev) => prev.filter((m) => m.id !== tempId && m.id !== assistantId))
        },
      },
    )
    setAskSending(false)
  }

  // ===== 写本章：调用 write-chapter skill =====
  const [generating, setGenerating] = useState(false)
  const streamingRef = useRef(false)
  const generateChapter = async () => {
    if (!selectedChapterId || generating) return
    if (!requireLlm()) return
    const cid = selectedChapterId
    setGenerating(true)
    setError('')
    streamingRef.current = true
    // 清空编辑器，准备流式展示（emitUpdate=false 避免触发自动保存）
    if (editor) {
      editor.commands.setContent('', { emitUpdate: false })
      editor.commands.focus('end')
    }
    try {
      await streamChapterGenerate(
        cid,
        { prompt: `请写本章：${chapterTitle}` },
        {
          onDraft: ({ delta }) => {
            if (editor) editor.commands.insertContent(delta)
          },
          onDone: (res) => {
            // 用后端最终内容（已做空行分段）替换展示
            if (editor) editor.commands.setContent(res.content, { emitUpdate: false })
            if (saveTimer.current) window.clearTimeout(saveTimer.current)
            void doSave(editor?.getHTML() ?? res.content, chapterTitle)
            lastSavedId.current = null
            qc.invalidateQueries({ queryKey: ['chapter', cid] })
            qc.invalidateQueries({ queryKey: ['chapters', bid] })
            qc.invalidateQueries({ queryKey: ['book', bid] })
            if (isBusiness) void fetchMe()
            setError(`已生成 ${res.word_count} 字 · in ${res.in_tokens}/out ${res.out_tokens}${isBusiness ? ` · ${res.credits_cost} 积分` : ''}`)
          },
          onError: (msg) => setError(msg),
        },
      )
    } catch (e) {
      setError(extractError(e, '生成失败'))
    } finally {
      streamingRef.current = false
      setGenerating(false)
    }
  }

  const onAskKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void sendAsk() }
  }

  // ===== P1-6：润色选中 / 段内续写 / 分析 skill =====
  const [polishing, setPolishing] = useState(false)
  const [continuing, setContinuing] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)

  /** 取编辑器选中的纯文本（无 HTML 标签） */
  const getSelectedText = (): string => {
    if (!editor) return ''
    const { state } = editor
    const { from, to, empty } = state.selection
    if (empty) return ''
    return state.doc.textBetween(from, to, '\n')
  }

  /** 取光标前的正文（纯文本，最多 1500 字） */
  const getPrefixText = (): string => {
    if (!editor) return ''
    const { state } = editor
    const from = state.selection.from
    return state.doc.textBetween(0, from, '\n').slice(-1500)
  }

  /** 把 agent 返回的内容插入/替换到编辑器，并触发保存 */
  const applyAgentContent = (text: string, mode: 'replace-selection' | 'append-cursor') => {
    if (!editor) return
    if (mode === 'replace-selection') {
      // 替换选区
      const { from, to, empty } = editor.state.selection
      if (empty) {
        editor.commands.insertContent(text)
      } else {
        editor.chain().focus().deleteRange({ from, to }).insertContent(text).run()
      }
    } else {
      // 在光标处追加续写
      editor.chain().focus().insertContent(text).run()
    }
    // 立即保存
    if (saveTimer.current) window.clearTimeout(saveTimer.current)
    void doSave(editor.getHTML(), chapterTitle)
  }

  const polishSelected = async () => {
    if (!selectedChapterId || polishing) return
    const sel = getSelectedText()
    if (!sel.trim()) {
      setError('请先在编辑器中选中要润色的文本')
      return
    }
    setPolishing(true)
    setError('')
    try {
      const res = await polishChapter(selectedChapterId, {
        selected_text: sel,
        polish_goal: '提升文笔与画面感',
        thread_id: threadId || undefined,
      })
      if (res.thread_id) setThreadId(res.thread_id)
      applyAgentContent(res.content, 'replace-selection')
      lastSavedId.current = null
      qc.invalidateQueries({ queryKey: ['chapter', selectedChapterId] })
      qc.invalidateQueries({ queryKey: ['chapters', bid] })
      if (isBusiness) void fetchMe()
      setError(`已润色 ${res.word_count} 字 · in ${res.in_tokens}/out ${res.out_tokens}${isBusiness ? ` · ${res.credits_cost} 积分` : ''}`)
    } catch (e) {
      setError(extractError(e, '润色失败'))
    } finally {
      setPolishing(false)
    }
  }

  const continueAtCursor = async () => {
    if (!selectedChapterId || continuing) return
    const prefix = getPrefixText()
    if (!prefix.trim()) {
      setError('请把光标放在需要续写的段落位置')
      return
    }
    setContinuing(true)
    setError('')
    try {
      const res = await continueWriting(selectedChapterId, {
        prefix_text: prefix,
        max_words: 600,
        thread_id: threadId || undefined,
      })
      if (res.thread_id) setThreadId(res.thread_id)
      applyAgentContent(res.content, 'append-cursor')
      lastSavedId.current = null
      qc.invalidateQueries({ queryKey: ['chapter', selectedChapterId] })
      qc.invalidateQueries({ queryKey: ['chapters', bid] })
      if (isBusiness) void fetchMe()
      setError(`续写 ${res.word_count} 字 · in ${res.in_tokens}/out ${res.out_tokens}${isBusiness ? ` · ${res.credits_cost} 积分` : ''}`)
    } catch (e) {
      setError(extractError(e, '续写失败'))
    } finally {
      setContinuing(false)
    }
  }

  /** 触发分析 skill，结果回填到 Ask 面板 */
  const runAnalyze = async (skill: AnalyzeSkill) => {
    if (!bid || analyzing) return
    if (!requireLlm()) return
    setAnalyzing(true)
    setError('')
    const tempId = `a-${Date.now()}`
    setAskMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, role: 'user', content: `[分析] ${skill}` },
      { id: tempId, role: 'assistant', content: '生成报告中…' },
    ])
    try {
      const res = await analyzeBook(bid, { skill, book_id: bid })
      if (res.thread_id) setThreadId(res.thread_id)
      setAskMessages((prev) => [
        ...prev.filter((m) => m.id !== tempId),
        {
          id: String(res.message_id), role: 'assistant', content: res.report,
          model: res.model, in_tokens: res.in_tokens, out_tokens: res.out_tokens,
          credits_cost: res.credits_cost,
        },
      ])
      if (isBusiness) void fetchMe()
    } catch (e) {
      setError(extractError(e, '分析失败'))
      setAskMessages((prev) => prev.filter((m) => m.id !== tempId))
    } finally {
      setAnalyzing(false)
    }
  }

  if (!bid) return <div className="p-8 text-muted-foreground">无效书籍</div>

  const chaptersByVol = (volId: number | null) => chapters?.filter((c) => c.volume_id === volId) ?? []

  return (
    <div className="h-screen flex flex-col bg-muted/30">
      {/* 顶栏 */}
      <header className="bg-background border-b flex items-center gap-3 px-4 h-12 shrink-0">
        <Link
          to="/"
          className="text-sm font-medium text-primary hover:bg-primary/10 border border-primary/30 rounded-lg px-2.5 py-1 flex items-center gap-1.5 transition"
        >
          <HomeIcon size={14} /> 返回我的作品
        </Link>
        <span className="font-bold truncate">{book?.title ?? '加载中…'}</span>
        {saveStatus === 'saving' && <span className="text-xs text-amber-600">保存中…</span>}
        {saveStatus === 'saved' && <span className="text-xs text-emerald-600">已保存</span>}
        {saveStatus === 'error' && <span className="text-xs text-destructive">未保存</span>}
        <div className="ml-auto flex items-center gap-2">
          <Button onClick={manualSave} disabled={!editor} size="sm">
            <Save size={14} /> 保存
          </Button>
        </div>
      </header>

      {/* Tab 栏 */}
      <nav className="bg-background border-b flex gap-1 px-4 h-10 shrink-0 overflow-x-auto">
        {TABS.map((t) => {
          const enabled = ENABLED_TABS.has(t)
          return (
            <button key={t} onClick={() => enabled ? setActiveTab(t) : undefined}
              disabled={!enabled}
              className={`px-3 h-full text-sm border-b-2 transition ${
                activeTab === t ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'
              } ${!enabled ? 'opacity-40 cursor-not-allowed' : 'hover:text-foreground'}`}>
              {t}
            </button>
          )
        })}
      </nav>

      {/* 三栏工作区 */}
      <div className="flex-1 min-h-0">
        <PanelGroup direction="horizontal">
          {/* 左：目录树（阅读 tab 时隐藏，由 ReaderPage 提供自己的目录） */}
          {activeTab !== '阅读' && (
            <>
            <Panel key="left-toc" defaultSize={18} minSize={13} className="bg-background border-r">
            <div className="h-full flex flex-col">
              <div className="px-3 py-2 border-b flex items-center justify-between">
                <span className="text-sm font-medium">目录</span>
                <Button variant="ghost" size="icon" className="text-primary h-7 w-7" title="新增章节" onClick={() => {
                  const t = prompt('章节标题', `第 ${(chapters?.length ?? 0) + 1} 章`)
                  if (t) createChapter.mutate(t)
                }}>
                  <Plus size={16} />
                </Button>
              </div>
              <div className="flex-1 overflow-y-auto text-sm">
                <div className="px-3 py-1 text-xs text-muted-foreground font-medium">{book?.title}</div>
                {volumes?.map((v) => (
                  <div key={v.id}>
                    <div className="px-3 py-1.5 text-xs text-muted-foreground font-medium bg-muted">{v.name}</div>
                    {chaptersByVol(v.id).map((c) => (
                      <ChapterItem key={c.id} chapter={c} active={c.id === selectedChapterId} onClick={() => setSelectedChapterId(c.id)} />
                    ))}
                  </div>
                ))}
                {/* 未分卷章节 */}
                {(chaptersByVol(null).length > 0 || (volumes?.length === 0 && (chapters?.length ?? 0) > 0)) && (
                  volumes?.length ? <div className="px-3 py-1.5 text-xs text-muted-foreground font-medium bg-muted">未分卷</div> : null
                )}
                {chaptersByVol(null).map((c) => (
                  <ChapterItem key={c.id} chapter={c} active={c.id === selectedChapterId} onClick={() => setSelectedChapterId(c.id)} />
                ))}
                {chapters?.length === 0 && <div className="px-3 py-4 text-center text-muted-foreground text-xs">点击 + 新建章节</div>}
              </div>
            </div>
            </Panel>
            <PanelResizeHandle className="w-1 bg-muted hover:bg-primary/60 transition" />
            </>
          )}

          {/* 中：编辑器 */}
          <Panel defaultSize={52} minSize={30} className="flex flex-col">
            {activeTab === '大纲' ? (
              <OutlinePanel bookId={bid} />
            ) : activeTab === '数据库' ? (
              <div className="flex flex-col h-full min-h-0">
                {!embeddingReady && (
                  <div className="px-4 py-2 bg-amber-50 dark:bg-amber-950/40 border-b flex items-center justify-between gap-2 shrink-0">
                    <span className="text-xs text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                      <Wand2 size={12} /> 尚未配置向量模型（Embedding），章节入库与 RAG 检索不可用
                    </span>
                    <Button size="sm" variant="outline" className="h-6 px-2 text-[11px] shrink-0" onClick={() => navigate('/llm-configs')}>
                      去配置
                    </Button>
                  </div>
                )}
                <div className="flex-1 min-h-0">
                  <DatabasePanel bookId={bid} onError={(msg) => setError(msg)} />
                </div>
              </div>
            ) : activeTab === '阅读' ? (
              <ReaderPage bid={bid} />
            ) : activeTab === '角色' ? (
              <ConfigPage bid={bid} entityType="character" />
            ) : activeTab === '场景' ? (
              <ConfigPage bid={bid} entityType="scene" />
            ) : activeTab === '物品' ? (
              <ConfigPage bid={bid} entityType="item" />
            ) : activeTab === '情节' ? (
              <ConfigPage bid={bid} entityType="plot" />
            ) : activeTab === '书籍信息' ? (
              <BookInfoPage book={book} bid={bid} onSaved={() => qc.invalidateQueries({ queryKey: ['book', bid] })} />
            ) : activeTab === '设置' ? (
              <WorkspaceSettings
                autoSaveMs={autoSaveMs}
                setAutoSaveMs={(ms) => { setAutoSaveMs(ms); localStorage.setItem('sc_autosave_ms', String(ms)) }}
                llmReady={llmReady}
                embeddingReady={embeddingReady}
                llmConfigs={llmConfigs ?? []}
                onGoConfig={() => navigate('/llm-configs')}
              />
            ) : selectedChapterId ? (
              <>
                <div className="px-6 pt-4 pb-2 bg-background border-b">
                  <Input
                    className="w-full text-xl font-bold outline-none border-transparent shadow-none px-0 focus-visible:ring-0"
                    value={chapterTitle}
                    onChange={(e) => titleInputSave(e.target.value)}
                    placeholder="章节标题"
                  />
                  <div className="text-xs text-muted-foreground mt-1">
                    {chapterDetail ? `第 ${chapterDetail.number} 章 · ${chapterDetail.word_count} 字` : ''}
                  </div>
                </div>
                <div className="px-4 py-1.5 bg-background border-b flex items-center gap-1 flex-wrap">
                  <ToolBtn onClick={() => editor?.chain().focus().toggleBold().run()} active={!!editor?.isActive('bold')} title="加粗"><Bold size={16} /></ToolBtn>
                  <ToolBtn onClick={() => editor?.chain().focus().toggleItalic().run()} active={!!editor?.isActive('italic')} title="斜体"><Italic size={16} /></ToolBtn>
                  <ToolBtn onClick={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()} active={!!editor?.isActive('heading', { level: 1 })} title="一级标题"><Heading1 size={16} /></ToolBtn>
                  <ToolBtn onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()} active={!!editor?.isActive('heading', { level: 2 })} title="二级标题"><Heading2 size={16} /></ToolBtn>
                  <ToolBtn onClick={() => editor?.chain().focus().toggleHighlight().run()} active={!!editor?.isActive('highlight')} title="高亮"><Highlighter size={16} /></ToolBtn>
                  <ToolBtn onClick={() => editor?.chain().focus().toggleBulletList().run()} active={!!editor?.isActive('bulletList')} title="列表"><List size={16} /></ToolBtn>
                  <div className="w-px h-5 bg-muted mx-1" />
                  <Button
                    size="sm"
                    className="bg-purple-600 hover:bg-purple-700 text-white"
                    onClick={() => void generateChapter()}
                    disabled={!selectedChapterId || generating}
                    title="调用 write-chapter skill 生成当前章节正文"
                  >
                    <PenLine size={14} /> {generating ? '生成中…' : '写本章'}
                  </Button>
                  <Button
                    size="sm"
                    className="bg-teal-600 hover:bg-teal-700 text-white"
                    onClick={() => void polishSelected()}
                    disabled={!selectedChapterId || polishing}
                    title="选中一段文本后，调用 polish-chapter skill 润色文笔"
                  >
                    <Wand2 size={14} /> {polishing ? '润色中…' : '润色选中'}
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => void continueAtCursor()}
                    disabled={!selectedChapterId || continuing}
                    title="把光标放在段尾，调用 continue-writing skill 段内续写"
                  >
                    <CornerDownRight size={14} /> {continuing ? '续写中…' : '续写'}
                  </Button>
                </div>
                <div className="flex-1 overflow-y-auto bg-background px-6 py-4 prose max-w-none">
                  <EditorContent editor={editor} />
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <p>选择左侧章节开始创作</p>
                  <Button className="mt-3" onClick={() => {
                    const t = prompt('章节标题', `第 ${(chapters?.length ?? 0) + 1} 章`)
                    if (t) createChapter.mutate(t)
                  }}>
                    <Plus size={16} /> 新建第一章
                  </Button>
                </div>
              </div>
            )}
          </Panel>
          <PanelResizeHandle className="w-1 bg-muted hover:bg-primary/60 transition" />

          {/* 右：Ask 面板 */}
          <Panel defaultSize={30} minSize={18} className="bg-background border-l">
            <PanelGroup direction="horizontal">
              {/* 左：历史记录侧边栏（historyOpen 时渲染，可拖拽调宽） */}
              {historyOpen && (
                <>
                  <Panel defaultSize={26} minSize={12} maxSize={40}
                    className="flex flex-col bg-muted/30 border-r">
                    <div className="px-3 py-2 border-b flex items-center justify-between shrink-0">
                      <span className="text-sm font-medium flex items-center gap-1.5"><History size={14} /> 历史记录</span>
                      <button onClick={toggleHistory} className="text-muted-foreground hover:text-foreground" title="收起历史"><RotateCcw size={13} /></button>
                    </div>
                    <div className="flex-1 overflow-y-auto min-h-0">
                      {historyLoading && <div className="text-center text-muted-foreground text-xs py-4">加载中…</div>}
                      {!historyLoading && sessions.length === 0 && (
                        <div className="text-center text-muted-foreground text-xs py-6 px-3">暂无历史对话<br />在 Ask 中提问后会自动生成会话</div>
                      )}
                      {sessions.map((s) => (
                        <button key={s.thread_id} onClick={() => void loadSession(s.thread_id)}
                          className={`w-full text-left px-3 py-2 border-b hover:bg-muted/70 transition ${s.thread_id === threadId ? 'bg-primary/10' : ''}`}>
                          <div className="text-[12px] font-medium text-foreground truncate">{s.title}</div>
                          <div className="text-[10px] text-muted-foreground mt-0.5 flex items-center justify-between gap-2">
                            <span className="shrink-0">{s.msg_count} 条</span>
                            <span className="shrink-0">{fmtTime(s.last_at)}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </Panel>
                  <PanelResizeHandle className="w-1 bg-muted hover:bg-primary/60 transition" />
                </>
              )}
              {/* 右：对话主体 */}
              <Panel className="flex flex-col">
                <div className="px-3 py-2 border-b flex items-center justify-between">
                  <span className="text-sm font-medium">Ask 助手</span>
                  <button onClick={toggleHistory} title={historyOpen ? '收起历史记录' : '查看历史记录'}
                    className={`p-1.5 rounded hover:bg-muted transition ${historyOpen ? 'text-primary bg-primary/10' : 'text-muted-foreground'}`}>
                    <History size={15} />
                  </button>
                </div>
                {/* P1-6 分析 skill 快捷入口 */}
                <div className="px-2 py-1.5 border-b flex gap-1 flex-wrap bg-muted/40">
                  <span className="text-[10px] text-muted-foreground self-center mr-1 flex items-center gap-0.5"><Sparkles size={10} />分析</span>
                  {([
                    ['outline-planning', '大纲'],
                    ['plot-planning', '情节'],
                    ['character-development', '角色'],
                    ['consistency-check', '一致性'],
                    ['book-summary', '前情提要'],
                  ] as const).map(([skill, label]) => (
                    <Button key={skill} variant="outline" size="sm" className="h-6 px-2 text-[11px]"
                      onClick={() => void runAnalyze(skill)}
                      disabled={analyzing}
                      title={`调用 ${skill} 分析全书并生成报告`}>
                      {label}
                    </Button>
                  ))}
                </div>
                <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0">
                  {askMessages.length === 0 && <div className="text-center text-muted-foreground text-sm py-4">输入问题向 AI 提问（基础对话）</div>}
                  {askMessages.map((m) => (
                    <div key={m.id} className={`text-sm rounded-lg px-3 py-2 ${m.role === 'user' ? 'bg-primary text-primary-foreground ml-6' : 'bg-muted text-foreground mr-6'}`}>
                      <div className="whitespace-pre-wrap break-words">{m.content}</div>
                      {m.role === 'assistant' && (m.in_tokens != null || m.out_tokens != null) && (
                        <div className="mt-1 text-[10px] opacity-70">in {m.in_tokens ?? 0} / out {m.out_tokens ?? 0}{isBusiness && m.credits_cost ? ` · ${m.credits_cost}积分` : ''}</div>
                      )}
                    </div>
                  ))}
                </div>
                <div className="p-2 border-t flex gap-2 items-end">
                  <Textarea rows={2} className="flex-1 text-sm resize-none min-h-9"
                    placeholder="Enter 发送" value={askInput}
                    onChange={(e) => setAskInput(e.target.value)} onKeyDown={onAskKey} />
                  <Button size="icon" className="shrink-0" onClick={() => void sendAsk()} disabled={askSending || !askInput.trim()}>
                    <Send size={16} />
                  </Button>
                </div>
              </Panel>
            </PanelGroup>
          </Panel>
        </PanelGroup>
      </div>

      {error && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-destructive text-white text-sm px-4 py-2 rounded-lg shadow z-50">
          {error}
          <button onClick={() => setError('')} className="ml-2"><RotateCcw size={12} /></button>
        </div>
      )}
    </div>
  )
}

function ChapterItem({ chapter, active, onClick }: { chapter: Chapter; active: boolean; onClick: () => void }) {
  const ragColor = chapter.rag_status === 'loaded'
    ? 'bg-green-500'
    : chapter.word_count > 0
      ? 'bg-amber-400'
      : 'bg-muted-foreground/40'
  const ragTitle = chapter.rag_status === 'loaded' ? '已入库 RAG' : chapter.word_count > 0 ? '有内容未入库' : '无内容'
  return (
    <button onClick={onClick} className={`w-full text-left px-3 py-1.5 flex items-center justify-between hover:bg-primary/10 ${active ? 'bg-primary/10 text-primary' : 'text-foreground'}`}>
      <span className="truncate flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${ragColor}`} title={ragTitle} />
        {chapter.title}
      </span>
      <span className="text-[10px] text-muted-foreground ml-1 shrink-0">{chapter.word_count}</span>
    </button>
  )
}

function ToolBtn({ onClick, active, title, children }: { onClick: () => void; active: boolean; title: string; children: React.ReactNode }) {
  return (
    <button onClick={onClick} title={title}
      className={`p-1.5 rounded hover:bg-muted ${active ? 'bg-primary/10 text-primary' : 'text-muted-foreground'}`}>
      {children}
    </button>
  )
}
