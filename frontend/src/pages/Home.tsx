import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth'
import api, { extractError, listPosts } from '@/lib/api'
import type { Book, BookInput, Stats } from '@/types'
import {
  Plus, Book as BookIcon, BookOpen, MessageCircle,
  PenLine, Database, Sparkles, ArrowRight, CalendarDays,
} from 'lucide-react'
import type { FormEvent } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button, buttonVariants } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'

const GENRES = ['都市', '玄幻', '仙侠', '历史', '科幻', '悬疑', '言情', '其他']
const PLATFORMS = ['起点', '番茄', '晋江', '七猫', '黑岩', '知乎盐选']

const emptyForm: BookInput = {
  title: '', intro: '', genre: '都市', platforms: [], cover_url: '',
  target_chapters: 20, target_words: 60000, per_chapter_words: 3000,
  protagonist_name: '', protagonist_intro: '',
  generate_outline: false, generate_plots: false, generate_characters: false,
}

function StatCard({ label, value, icon: Icon, grad }: { label: string; value: number; icon: typeof PenLine; grad: string }) {
  return (
    <Card className="card-lift border-none shadow-sm">
      <CardContent className="p-4 flex items-center gap-3">
        <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${grad} text-white flex items-center justify-center shrink-0 shadow-md`}>
          <Icon size={19} />
        </div>
        <div className="min-w-0">
          <div className="text-xs text-muted-foreground">{label}</div>
          <div className="text-2xl font-bold text-foreground mt-0.5 tracking-tight">{value.toLocaleString()}</div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function Home() {
  const user = useAuthStore((s) => s.user)
  const isBusiness = user?.version === 'business'
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState<BookInput>(emptyForm)
  const [error, setError] = useState('')

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => (await api.get<Stats>('/books/stats')).data,
    enabled: !!user,
  })
  const { data: books } = useQuery({
    queryKey: ['books'],
    queryFn: async () => (await api.get<Book[]>('/books')).data,
    enabled: !!user,
  })
  // 主页社区精选（登录/未登录都拉取）
  const { data: featured } = useQuery({
    queryKey: ['featured-posts'],
    queryFn: () => listPosts(1, 3),
  })

  const openBook = (id: number) => window.open(`/workspace/${id}`, '_blank')

  const recompute = (next: Partial<BookInput>) => {
    const merged = { ...form, ...next }
    if (merged.target_chapters > 0 && (next.target_words !== undefined || next.target_chapters !== undefined)) {
      merged.per_chapter_words = Math.round(merged.target_words / merged.target_chapters)
    }
    setForm(merged)
  }

  const togglePlatform = (p: string) => {
    recompute({ platforms: form.platforms.includes(p) ? form.platforms.filter((x) => x !== p) : [...form.platforms, p] })
  }

  const createMutation = useMutation({
    mutationFn: async () => (await api.post<Book>('/books', form)).data,
    onSuccess: (b) => {
      qc.invalidateQueries({ queryKey: ['books'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
      setShowModal(false)
      setForm(emptyForm)
      setError('')
      openBook(b.id)
    },
    onError: (err) => setError(extractError(err, '创建失败')),
  })

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!form.title.trim()) { setError('请填写书名'); return }
    setError('')
    createMutation.mutate()
  }

  if (!user) {
    return (
      <div className="relative">
        {/* Hero */}
        <section className="max-w-5xl mx-auto px-4 pt-20 md:pt-24 pb-12 text-center animate-fade-up">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium mb-6 border border-primary/20">
            <Sparkles size={14} /> AI 辅助小说创作平台
          </div>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-foreground leading-tight">
            让 AI 陪你写完
            <span className="bg-gradient-to-r from-indigo-500 via-purple-500 to-fuchsia-500 bg-clip-text text-transparent"> 每一部小说</span>
          </h1>
          <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
            大纲规划、章节写作、角色与场景设定、向量+图谱长期记忆……
            <br className="hidden md:block" />一个工作台，从灵感到完本。
          </p>
          <div className="mt-10 flex gap-3 justify-center flex-wrap">
            <Link
              to="/register"
              className={buttonVariants({
                size: 'lg',
                className: 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30 transition-shadow',
              })}
            >
              免费开始创作 <ArrowRight size={16} />
            </Link>
            <Link
              to="/community"
              className={buttonVariants({ size: 'lg', variant: 'outline', className: 'bg-background/60' })}
            >
              <BookOpen size={16} /> 逛逛社区
            </Link>
          </div>
        </section>

        {/* 特性 */}
        <section className="w-full px-4 pb-16">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { icon: PenLine, title: '章节写作', desc: '写本章 / 写多章 Skill，按大纲自动成文', grad: 'from-indigo-500 to-blue-500' },
              { icon: Database, title: '向量+图谱记忆', desc: 'Milvus 向量 + Neo4j 图谱，跨章保一致', grad: 'from-purple-500 to-fuchsia-500' },
              { icon: BookOpen, title: '作品管理', desc: '封面、简介、分卷、预计字数一目了然', grad: 'from-emerald-500 to-teal-500' },
              { icon: MessageCircle, title: 'Ask 助手', desc: '对话式问角色、大纲、设定，边写边查', grad: 'from-amber-500 to-orange-500' },
            ].map((f, i) => (
              <Card key={f.title} className="card-lift border-none shadow-sm p-5" style={{ animationDelay: `${i * 80}ms` }}>
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${f.grad} text-white flex items-center justify-center shadow-md`}>
                  <f.icon size={20} />
                </div>
                <div className="mt-3 font-semibold text-foreground">{f.title}</div>
                <div className="mt-1 text-sm text-muted-foreground leading-relaxed">{f.desc}</div>
              </Card>
            ))}
          </div>
        </section>

        {/* 社区精选 */}
        <section className="w-full px-4 pb-20">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-foreground">社区精选</h2>
            <Link to="/community" className="text-sm text-primary hover:underline shrink-0">查看全部 →</Link>
          </div>
          <div className="grid md:grid-cols-3 xl:grid-cols-4 gap-4">
            {featured?.items?.map((p) => (
              <Link key={p.id} to={`/post/${p.id}`} className="card-lift block">
                <Card className="p-5 border-none shadow-sm">
                  <div className="font-semibold text-foreground truncate">{p.title}</div>
                  <div className="mt-2 text-sm text-muted-foreground line-clamp-3 leading-relaxed">{p.content_text}</div>
                  <div className="mt-3 text-xs text-muted-foreground/70">{p.author_name}</div>
                </Card>
              </Link>
            ))}
            {(!featured || featured.items.length === 0) && (
              <div className="md:col-span-3 text-center text-muted-foreground py-8">
                社区还没有帖子，登录后发布第一篇吧
              </div>
            )}
          </div>
        </section>

        {/* 页脚 */}
        <footer className="border-t border-border">
          <div className="max-w-6xl mx-auto px-4 py-6 text-center text-sm text-muted-foreground/70">
            StoryClaw · AI 辅助小说创作平台 · 本地版 / 商业版
          </div>
        </footer>
      </div>
    )
  }

  return (
    <div className="w-full animate-fade-up">
      {/* 欢迎横幅 */}
      <div className="relative mb-6 overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-600 via-purple-600 to-fuchsia-600 text-white px-6 py-6 flex items-center justify-between shadow-lg shadow-indigo-500/20">
        <div className="pointer-events-none absolute inset-0 animate-glow-pulse bg-[radial-gradient(30rem_12rem_at_20%_-20%,rgba(255,255,255,0.35),transparent_60%)]" />
        <div className="relative flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-white/20 border border-white/30 flex items-center justify-center text-xl font-bold">
            {user?.username?.[0]?.toUpperCase()}
          </div>
          <div>
            <div className="text-lg font-semibold">欢迎回来，{user?.username}</div>
            <div className="mt-1 flex items-center gap-2">
              <span className="bg-white/20 rounded-full px-2 py-0.5 text-xs">
                {isBusiness ? '商业版' : '本地版'}
              </span>
              {isBusiness && (
                <span className="text-xs text-indigo-100">剩余 {user?.credits_balance ?? 0} 积分</span>
              )}
            </div>
          </div>
        </div>
        <div className="relative hidden sm:flex gap-8 text-center">
          <div>
            <div className="text-2xl font-bold">{books?.length ?? 0}</div>
            <div className="text-xs text-indigo-100/80 mt-0.5">本书</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{(stats?.total_words ?? 0).toLocaleString()}</div>
            <div className="text-xs text-indigo-100/80 mt-0.5">累计字数</div>
          </div>
        </div>
      </div>

      {/* 统计卡 */}
      <div className="grid grid-cols-3 gap-3 mb-8">
        <StatCard label="今日字数" value={stats?.today_words ?? 0} icon={PenLine} grad="from-indigo-500 to-blue-500" />
        <StatCard label="当月字数" value={stats?.month_words ?? 0} icon={CalendarDays} grad="from-purple-500 to-fuchsia-500" />
        <StatCard label="已入库" value={stats?.total_words ?? 0} icon={Database} grad="from-emerald-500 to-teal-500" />
      </div>

      {/* 我的作品（书架） */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
          <BookIcon size={20} className="text-primary" /> 我的作品
        </h1>
        <Button
          onClick={() => setShowModal(true)}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 shadow-md shadow-indigo-500/20"
        >
          <Plus size={16} /> 新建书籍
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-5">
        {books?.map((b) => (
          <div key={b.id} onClick={() => openBook(b.id)} className="group cursor-pointer">
            <div className="relative aspect-[3/4] rounded-xl overflow-hidden shadow-sm group-hover:shadow-xl group-hover:-translate-y-1 transition-all duration-300 bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-950/60 dark:to-purple-950/60 flex items-center justify-center">
              {b.cover_url ? (
                <img src={b.cover_url} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center gap-2 text-indigo-400 group-hover:text-indigo-500 transition dark:text-indigo-300/70">
                  <BookIcon size={34} />
                  <span className="text-3xl font-bold text-indigo-300/90 dark:text-indigo-200/60">{b.title?.[0] ?? '书'}</span>
                </div>
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition" />
              {b.genre && (
                <span className="absolute top-2 left-2 text-[10px] px-1.5 py-0.5 rounded-full bg-black/40 text-white">
                  {b.genre}
                </span>
              )}
            </div>
            <div className="mt-2 font-medium text-foreground truncate">{b.title}</div>
            <div className="text-xs text-muted-foreground mt-0.5 flex justify-between">
              <span>{b.chapter_count} 章</span>
              <span>{b.total_words} 字</span>
            </div>
            {b.platforms.length > 0 && (
              <div className="text-[10px] text-muted-foreground/70 mt-0.5 truncate">{b.platforms.join(' / ')}</div>
            )}
          </div>
        ))}
        {books?.length === 0 && (
          <div className="col-span-full text-center py-16">
            <BookIcon size={44} className="mx-auto text-muted-foreground/40" />
            <div className="text-muted-foreground mt-3">还没有作品</div>
            <button
              onClick={() => setShowModal(true)}
              className="mt-4 px-5 py-2 text-sm border border-primary/40 text-primary rounded-xl hover:bg-primary/5 transition"
            >
              创建第一本书
            </button>
          </div>
        )}
      </div>

      {/* 社区精选 */}
      <section className="mt-12">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
            <BookOpen size={18} className="text-primary" /> 社区精选
          </h2>
          <Link to="/community" className="text-sm text-primary hover:underline shrink-0">查看全部 →</Link>
        </div>
        <div className="grid md:grid-cols-3 xl:grid-cols-4 gap-4">
          {featured?.items?.map((p) => (
            <Link key={p.id} to={`/post/${p.id}`} className="card-lift block">
              <Card className="p-5 border-none shadow-sm">
                <div className="font-semibold text-foreground truncate">{p.title}</div>
                <div className="mt-2 text-sm text-muted-foreground line-clamp-3 leading-relaxed">{p.content_text}</div>
                <div className="mt-3 text-xs text-muted-foreground/70">{p.author_name}</div>
              </Card>
            </Link>
          ))}
          {(!featured || featured.items.length === 0) && (
            <div className="md:col-span-3 text-center text-muted-foreground py-8">社区还没有帖子，来发布第一篇吧</div>
          )}
        </div>
      </section>

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>创建新书</DialogTitle>
            <DialogDescription>填写书籍信息，AI 将据此自动规划大纲与章节。</DialogDescription>
          </DialogHeader>
          <form onSubmit={submit} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="bk-title">书名 *</Label>
              <Input id="bk-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="我的小说" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="bk-intro">简介</Label>
              <Textarea id="bk-intro" rows={2} value={form.intro} onChange={(e) => setForm({ ...form, intro: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <Label>类型</Label>
              <Select value={form.genre ?? ''} onValueChange={(v) => setForm({ ...form, genre: v ?? '' })}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {GENRES.map((g) => (
                    <SelectItem key={g} value={g}>{g}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>发布平台</Label>
              <div className="flex flex-wrap gap-2">
                {PLATFORMS.map((p) => (
                  <Button
                    key={p}
                    type="button"
                    variant={form.platforms.includes(p) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => togglePlatform(p)}
                  >
                    {p}
                  </Button>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="space-y-1.5">
                <Label htmlFor="bk-chapters">预计章数</Label>
                <Input id="bk-chapters" type="number" value={form.target_chapters} onChange={(e) => recompute({ target_chapters: Number(e.target.value) || 1 })} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="bk-words">预计字数</Label>
                <Input id="bk-words" type="number" value={form.target_words} onChange={(e) => recompute({ target_words: Number(e.target.value) || 0 })} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="bk-per">每章字数</Label>
                <Input id="bk-per" type="number" className="bg-muted" value={form.per_chapter_words} readOnly />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1.5">
                <Label htmlFor="bk-pname">主角名</Label>
                <Input id="bk-pname" value={form.protagonist_name} onChange={(e) => setForm({ ...form, protagonist_name: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="bk-cover">封面 URL（可选）</Label>
                <Input id="bk-cover" value={form.cover_url} onChange={(e) => setForm({ ...form, cover_url: e.target.value })} placeholder="https://..." />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="bk-pintro">主角介绍</Label>
              <Textarea id="bk-pintro" rows={2} value={form.protagonist_intro} onChange={(e) => setForm({ ...form, protagonist_intro: e.target.value })} />
            </div>
            <div className="space-y-1.5 rounded-lg border bg-muted/40 p-3">
              <Label className="text-xs text-muted-foreground">创建后自动生成（后台进行，可在工作区查看）</Label>
              <div className="flex flex-wrap gap-4 pt-1">
                {([
                  ['generate_outline', '大纲', '按书名/主角/字数规划全书章节大纲'],
                  ['generate_plots', '情节', '基于大纲为每章规划情节点与伏笔'],
                  ['generate_characters', '角色', '为主角/配角/反派生成角色卡'],
                ] as const).map(([key, label, tip]) => (
                  <label key={key} className="flex items-start gap-2 cursor-pointer" title={tip}>
                    <input
                      type="checkbox"
                      className="accent-indigo-600 mt-0.5"
                      checked={!!form[key]}
                      onChange={(e) => setForm({ ...form, [key]: e.target.checked })}
                    />
                    <span className="text-sm leading-tight">
                      {label}
                      <span className="block text-[11px] text-muted-foreground">{tip}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowModal(false)}>取消</Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? '创建中…' : '创建并进入'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
