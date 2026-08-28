import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import api, { extractError } from '@/lib/api'
import type { LLMConfig, LLMFormat, LLMConfigInput } from '@/types'
import { Plus, Trash2, X, Database } from 'lucide-react'
import type { FormEvent } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'

const FORMATS: LLMFormat[] = ['openai_chat', 'anthropic', 'openai_responses']

interface FormState {
  name: string
  format: LLMFormat
  base_url: string
  model: string
  api_key: string
  temperature: string
  max_tokens: string
  is_default: boolean
  // embedding（向量化）配置
  embedding_model: string
  embedding_base_url: string
  embedding_api_key: string
}

const emptyForm: FormState = {
  name: '',
  format: 'openai_chat',
  base_url: '',
  model: '',
  api_key: '',
  temperature: '0.7',
  max_tokens: '2048',
  is_default: false,
  embedding_model: '',
  embedding_base_url: '',
  embedding_api_key: '',
}

export default function LLMConfigs() {
  const qc = useQueryClient()
  const { data: configs, isLoading } = useQuery({
    queryKey: ['llm-configs'],
    queryFn: async () => (await api.get<LLMConfig[]>('/llm-configs')).data,
  })
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(emptyForm)
  const [mode, setMode] = useState<'new' | 'edit'>('new')
  const [error, setError] = useState('')

  const selected = configs?.find((c) => c.id === selectedId) || null

  useEffect(() => {
    if (mode === 'edit' && selected) {
      setForm({
        name: selected.name,
        format: selected.format,
        base_url: selected.base_url,
        model: selected.model,
        api_key: '',
        temperature: String(selected.temperature),
        max_tokens: String(selected.max_tokens),
        is_default: selected.is_default,
        embedding_model: selected.embedding_model ?? '',
        embedding_base_url: selected.embedding_base_url ?? '',
        embedding_api_key: '',
      })
    }
  }, [mode, selected])

  const startNew = () => {
    setMode('new')
    setSelectedId(null)
    setForm(emptyForm)
    setError('')
  }

  const startEdit = (id: string) => {
    setSelectedId(id)
    setMode('edit')
    setError('')
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload: LLMConfigInput = {
        name: form.name,
        format: form.format,
        base_url: form.base_url,
        model: form.model,
        temperature: Number(form.temperature),
        max_tokens: Number(form.max_tokens),
        is_default: form.is_default,
      }
      if (form.api_key) payload.api_key = form.api_key
      if (form.embedding_model || form.embedding_base_url) {
        payload.embedding_model = form.embedding_model
        payload.embedding_base_url = form.embedding_base_url
        if (form.embedding_api_key) payload.embedding_api_key = form.embedding_api_key
      }
      if (mode === 'new') {
        payload.api_key = form.api_key
        const res = await api.post<LLMConfig>('/llm-configs', payload)
        return res.data
      } else if (selectedId) {
        const res = await api.put<LLMConfig>(`/llm-configs/${selectedId}`, payload)
        return res.data
      }
      throw new Error('未选中配置')
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['llm-configs'] })
      toast.success('已保存')
      setError('')
      if (mode === 'new') startNew()
    },
    onError: (err) => setError(extractError(err, '保存失败')),
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/llm-configs/${id}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['llm-configs'] })
      toast.success('已删除')
      startNew()
    },
    onError: (err) => toast.error(extractError(err, '删除失败')),
  })

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!form.name || !form.model) {
      setError('请填写名称和模型')
      return
    }
    if (mode === 'new' && !form.api_key) {
      setError('新建配置时必须填写 API Key')
      return
    }
    setError('')
    saveMutation.mutate()
  }

  return (
    <div className="flex flex-col md:flex-row gap-4 flex-1 min-h-0">
      {/* 左侧配置列表 */}
      <Card className="w-full md:w-1/3 flex flex-col border-none shadow-sm min-h-0">
        <CardContent className="p-0 flex flex-col flex-1 min-h-0">
          <div className="px-3 py-2.5 border-b flex items-center justify-between">
            <span className="font-medium text-sm">配置列表</span>
            <Button variant="ghost" size="sm" onClick={startNew}>
              <Plus size={14} /> 新建
            </Button>
          </div>
          <div className="divide-y overflow-y-auto flex-1 min-h-0">
            {isLoading && (
              <div className="p-3 space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            )}
            {!isLoading && configs?.length === 0 && (
              <div className="px-3 py-3 text-sm text-muted-foreground">暂无配置</div>
            )}
            {configs?.map((c) => (
              <div
                key={c.id}
                className={`px-3 py-2 cursor-pointer hover:bg-muted flex items-center justify-between ${
                  selectedId === c.id ? 'bg-primary/10' : ''
                }`}
                onClick={() => startEdit(c.id)}
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate flex items-center gap-1">
                    {c.name}
                    {c.is_default && (
                      <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4">默认</Badge>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground truncate">
                    {c.format} · {c.model}
                    {c.has_embedding_key && c.embedding_model
                      ? <span className="text-emerald-600/80"> · 向量✓ {c.embedding_model}</span>
                      : <span className="text-amber-600/80"> · 未配向量模型</span>}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-destructive ml-2 h-7 w-7"
                  title="删除"
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteMutation.mutate(c.id)
                  }}
                >
                  <Trash2 size={15} />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 右侧编辑表单 */}
      <Card className="flex-1 border-none shadow-sm min-h-0 overflow-y-auto">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-medium">
              {mode === 'new' ? '新建配置' : `编辑：${selected?.name ?? ''}`}
            </h2>
            {mode === 'edit' && (
              <Button variant="ghost" size="sm" onClick={startNew}>
                <X size={14} /> 取消编辑
              </Button>
            )}
          </div>
          <form onSubmit={submit} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="llm-name">名称</Label>
              <Input id="llm-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="My OpenAI" />
            </div>
            <div className="space-y-1.5">
              <Label>格式</Label>
              <Select value={form.format} onValueChange={(v) => setForm({ ...form, format: (v ?? 'openai_chat') as LLMFormat })}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FORMATS.map((f) => (
                    <SelectItem key={f} value={f}>{f}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="llm-base">Base URL</Label>
              <Input id="llm-base" value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} placeholder="https://api.openai.com/v1" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="llm-model">模型</Label>
              <Input id="llm-model" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} placeholder="gpt-4o-mini" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="llm-key">API Key</Label>
              <Input
                id="llm-key"
                type="password"
                value={form.api_key}
                onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                placeholder={mode === 'edit' && selected?.has_key ? '已配置（留空则不改）' : 'sk-...'}
              />
            </div>
            {/* ===== 向量化（Embedding）配置 ===== */}
            <div className="pt-2 mt-1 border-t">
              <div className="flex items-center gap-1.5 text-sm font-medium text-foreground mb-1">
                <Database size={14} className="text-indigo-500" />
                向量化模型（Embedding）
              </div>
              <p className="text-xs text-muted-foreground mb-2">
                用于「数据库」页的章节入库与 RAG 检索。若对话端点同时提供 embeddings 接口，只需填写「向量模型」即可复用上方 Base URL 与 API Key；留空则不启用向量化（RAG 不可用）。
              </p>
              <div className="space-y-1.5">
                <Label htmlFor="emb-model">向量模型</Label>
                <Input id="emb-model" value={form.embedding_model} onChange={(e) => setForm({ ...form, embedding_model: e.target.value })} placeholder="text-embedding-v3 / bge-m3" />
              </div>
              <div className="space-y-1.5 mt-1.5">
                <Label htmlFor="emb-url">Embedding Base URL</Label>
                <Input id="emb-url" value={form.embedding_base_url} onChange={(e) => setForm({ ...form, embedding_base_url: e.target.value })} placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1" />
              </div>
              <div className="space-y-1.5 mt-1.5">
                <Label htmlFor="emb-key">Embedding API Key</Label>
                <Input
                  id="emb-key"
                  type="password"
                  value={form.embedding_api_key}
                  onChange={(e) => setForm({ ...form, embedding_api_key: e.target.value })}
                  placeholder={mode === 'edit' && selected?.has_embedding_key ? '已配置（留空则不改）' : 'sk-...'}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <div className="space-y-1.5 flex-1">
                <Label htmlFor="llm-temp">Temperature</Label>
                <Input id="llm-temp" value={form.temperature} onChange={(e) => setForm({ ...form, temperature: e.target.value })} />
              </div>
              <div className="space-y-1.5 flex-1">
                <Label htmlFor="llm-max">Max Tokens</Label>
                <Input id="llm-max" value={form.max_tokens} onChange={(e) => setForm({ ...form, max_tokens: e.target.value })} />
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                className="accent-indigo-600"
                checked={form.is_default}
                onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
              />
              设为默认
            </label>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? '保存中…' : '保存'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
