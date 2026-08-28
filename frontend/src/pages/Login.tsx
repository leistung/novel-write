import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'
import api, { extractError } from '@/lib/api'
import type { AuthResponse } from '@/types'
import type { FormEvent } from 'react'
import { User, Lock, Feather, Sparkles, BookOpen, PenLine, Wand2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

// 演示账号（快速体验用）
const DEMO_ACCOUNTS = [
  { label: '本地版', username: 'local_17c707', password: 'test123456' },
  { label: '商业版', username: 'biz_17c707', password: 'test123456' },
]

export default function Login() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!username || !password) {
      setError('请输入用户名和密码')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await api.post<AuthResponse>('/auth/login', {
        username,
        password,
      })
      setAuth(res.data.user, res.data.token)
      const from = params.get('from')
      // 登录后默认进入书籍主页（/），而非对话页
      navigate(from ? decodeURIComponent(from) : '/')
    } catch (err) {
      setError(extractError(err, '登录失败'))
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = (u: string, p: string) => {
    setUsername(u)
    setPassword(p)
    setError('')
  }

  return (
    <div className="min-h-full flex items-center justify-center relative overflow-hidden bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 px-4">
      {/* 背景装饰光晕 */}
      <div className="pointer-events-none absolute -top-32 -left-32 w-96 h-96 rounded-full bg-indigo-500/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-24 w-[28rem] h-[28rem] rounded-full bg-purple-500/20 blur-3xl" />
      <div className="pointer-events-none absolute top-1/3 right-1/4 w-64 h-64 rounded-full bg-sky-500/10 blur-3xl" />

      <div className="relative w-full max-w-4xl grid lg:grid-cols-2 gap-8 items-center">
        {/* 左侧品牌区 */}
        <div className="hidden lg:block text-white">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Feather size={24} />
            </div>
            <span className="text-3xl font-bold tracking-tight">StoryClaw</span>
          </div>
          <h1 className="mt-8 text-4xl font-bold leading-tight">
            AI 辅助小说创作
            <br />
            一站式工作台
          </h1>
          <p className="mt-4 text-indigo-200/80 leading-relaxed">
            大纲规划 · 章节写作 · 角色场景设定 · 向量+图谱记忆
            <br />
            登录后管理你的全部作品。
          </p>
          <div className="mt-10 space-y-4">
            {[
              { icon: BookOpen, title: '作品管理', desc: '创建书籍、自动规划章节，一眼看到进度' },
              { icon: Wand2, title: 'AI 创作', desc: 'Ask 助手 + 写作 Skill，向量/图谱 RAG 加持' },
              { icon: PenLine, title: '完整工作区', desc: '创作 / 阅读 / 角色 / 场景 / 情节 / 大纲 / 数据库' },
            ].map((f) => (
              <div key={f.title} className="flex items-start gap-3">
                <div className="mt-0.5 w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center shrink-0">
                  <f.icon size={18} />
                </div>
                <div>
                  <div className="font-medium">{f.title}</div>
                  <div className="text-sm text-indigo-200/60">{f.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 右侧登录卡片 */}
        <div className="w-full max-w-sm mx-auto bg-white/95 backdrop-blur rounded-2xl shadow-2xl p-7">
          <div className="flex items-center gap-2 lg:hidden mb-6">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white">
              <Feather size={18} />
            </div>
            <span className="text-xl font-bold">StoryClaw</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">欢迎回来</h2>
          <p className="text-sm text-gray-500 mt-1">登录你的创作工作台</p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="login-username">用户名</Label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="login-username"
                  className="pl-9 h-10"
                  placeholder="请输入用户名"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="login-password">密码</Label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="login-password"
                  type="password"
                  className="pl-9 h-10"
                  placeholder="请输入密码"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>
            </div>

            {error && (
              <p className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <Button type="submit" disabled={loading} size="lg" className="w-full h-10.5 text-[15px]">
              {loading ? '登录中…' : '登录'}
            </Button>
          </form>

          {/* 演示账号快捷填充 */}
          <div className="mt-5 pt-5 border-t border-gray-100">
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <Sparkles size={12} /> 演示账号，点击自动填充
            </div>
            <div className="mt-2 flex gap-2">
              {DEMO_ACCOUNTS.map((a) => (
                <Button
                  key={a.label}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => fillDemo(a.username, a.password)}
                  className="flex-1"
                >
                  {a.label}
                </Button>
              ))}
            </div>
          </div>

          <p className="mt-6 text-sm text-gray-500 text-center">
            还没有账号？
            <Link to="/register" className="text-primary font-medium ml-1 hover:underline">
              去注册
            </Link>
          </p>
          <div className="mt-3 text-center">
            <Link to="/" className="text-xs text-gray-400 hover:text-gray-600 transition">
              ← 返回主页
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
