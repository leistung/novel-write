import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'
import api, { extractError } from '@/lib/api'
import type { AuthResponse, UserVersion } from '@/types'
import type { FormEvent } from 'react'
import { User, Lock, Feather, Laptop, Store, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function Register() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [version, setVersion] = useState<UserVersion>('local')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!username || !password) {
      setError('请输入用户名和密码')
      return
    }
    setLoading(true)
    setError('')
    setNotice('')
    try {
      const res = await api.post<AuthResponse>('/auth/register', {
        username,
        password,
        version,
      })
      setAuth(res.data.user, res.data.token)
      if (version === 'local') {
        setNotice('注册成功，记得先配置 LLM')
        setTimeout(() => navigate('/llm-configs'), 900)
      } else {
        // 商业版注册后进书籍主页
        navigate('/')
      }
    } catch (err) {
      setError(extractError(err, '注册失败'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-full flex items-center justify-center relative overflow-hidden bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 px-4">
      {/* 背景装饰光晕 */}
      <div className="pointer-events-none absolute -top-32 -right-32 w-96 h-96 rounded-full bg-purple-500/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -left-24 w-[28rem] h-[28rem] rounded-full bg-indigo-500/20 blur-3xl" />

      <div className="relative w-full max-w-md mx-auto">
        <div className="w-full bg-white/95 backdrop-blur rounded-2xl shadow-2xl p-7">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white">
              <Feather size={18} />
            </div>
            <span className="text-xl font-bold">StoryClaw</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mt-4">创建账号</h2>
          <p className="text-sm text-gray-500 mt-1">选择你的版本开始创作</p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="reg-username">用户名</Label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="reg-username"
                  className="pl-9 h-10"
                  placeholder="请输入用户名"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="reg-password">密码</Label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="reg-password"
                  type="password"
                  className="pl-9 h-10"
                  placeholder="请输入密码"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                />
              </div>
            </div>

            {/* 版本选择卡片 */}
            <div className="space-y-2">
              <label
                className={`flex items-start gap-3 border rounded-xl p-3 cursor-pointer transition ${
                  version === 'local' ? 'border-indigo-500 bg-indigo-50/60 ring-1 ring-indigo-500' : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input type="radio" className="hidden" checked={version === 'local'} onChange={() => setVersion('local')} />
                <div className={`mt-0.5 w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${version === 'local' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-500'}`}>
                  <Laptop size={18} />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 flex items-center gap-1">
                    本地版
                    {version === 'local' && <Check size={14} className="text-indigo-600" />}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    自带 LLM 配置（OpenAI / Anthropic 等），按 token 自负
                  </div>
                </div>
              </label>
              <label
                className={`flex items-start gap-3 border rounded-xl p-3 cursor-pointer transition ${
                  version === 'business' ? 'border-indigo-500 bg-indigo-50/60 ring-1 ring-indigo-500' : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input type="radio" className="hidden" checked={version === 'business'} onChange={() => setVersion('business')} />
                <div className={`mt-0.5 w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${version === 'business' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-500'}`}>
                  <Store size={18} />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 flex items-center gap-1">
                    商业版
                    {version === 'business' && <Check size={14} className="text-indigo-600" />}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    使用平台模型，按积分计费，支持充值
                  </div>
                </div>
              </label>
            </div>

            {error && (
              <p className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">{error}</p>
            )}
            {notice && (
              <p className="text-sm text-emerald-600 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">{notice}</p>
            )}

            <Button type="submit" disabled={loading} size="lg" className="w-full h-10.5 text-[15px]">
              {loading ? '注册中…' : '注册'}
            </Button>
          </form>

          <p className="mt-6 text-sm text-gray-500 text-center">
            已有账号？
            <Link to="/login" className="text-indigo-600 font-medium ml-1 hover:underline">
              去登录
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
