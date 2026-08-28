import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api, { extractError } from '@/lib/api'
import type { Outline, OutlineVolume } from '@/types'
import { Sparkles, Save, Plus, Trash2, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'

export default function OutlinePanel({ bookId }: { bookId: number }) {
  const qc = useQueryClient()
  const [volumes, setVolumes] = useState<OutlineVolume[]>([])
  const [error, setError] = useState('')
  const [synced, setSynced] = useState(false)

  const { data: outline, isFetching } = useQuery({
    queryKey: ['outline', bookId],
    queryFn: async () => {
      try {
        return (await api.get<Outline>(`/books/${bookId}/outline`)).data
      } catch {
        return null
      }
    },
  })

  useEffect(() => {
    if (outline && !synced) {
      const vols = (outline.content as { volumes?: OutlineVolume[] }).volumes || []
      setVolumes(vols)
      setSynced(true)
      setError(outline.error || '')
    }
  }, [outline, synced])

  const generateMutation = useMutation({
    mutationFn: async () => (await api.post<Outline>(`/books/${bookId}/outline/generate`)).data,
    onSuccess: (o) => {
      setVolumes((o.content as { volumes?: OutlineVolume[] }).volumes || [])
      setError(o.error || '')
      qc.invalidateQueries({ queryKey: ['outline', bookId] })
    },
    onError: (e) => setError(extractError(e, '生成失败')),
  })

  const saveMutation = useMutation({
    mutationFn: async () => (await api.put<Outline>(`/books/${bookId}/outline`, { content: { volumes } })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['outline', bookId] }),
    onError: (e) => setError(extractError(e, '保存失败')),
  })

  const updateVolName = (vi: number, name: string) => {
    setVolumes((prev) => prev.map((v, i) => (i === vi ? { ...v, name } : v)))
  }
  const updateChapter = (vi: number, ci: number, field: 'title' | 'summary', value: string) => {
    setVolumes((prev) => prev.map((v, i) =>
      i === vi ? { ...v, chapters: v.chapters.map((c, j) => (j === ci ? { ...c, [field]: value } : c)) } : v
    ))
  }
  const addChapter = (vi: number) => {
    setVolumes((prev) => prev.map((v, i) => {
      if (i !== vi) return v
      const nextNum = (v.chapters[v.chapters.length - 1]?.number ?? 0) + 1
      return { ...v, chapters: [...v.chapters, { number: nextNum, title: `第${nextNum}章 待定`, summary: '' }] }
    }))
  }
  const delChapter = (vi: number, ci: number) => {
    setVolumes((prev) => prev.map((v, i) => (i === vi ? { ...v, chapters: v.chapters.filter((_, j) => j !== ci) } : v)))
  }
  const addVolume = () => {
    setVolumes((prev) => [...prev, { name: `第${prev.length + 1}卷`, chapters: [] }])
  }

  const hasData = volumes.length > 0

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="px-6 py-3 border-b flex items-center gap-2">
        <h2 className="font-bold">大纲规划</h2>
        <Button size="sm" className="bg-purple-600 hover:bg-purple-700 text-white" onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
          <Sparkles size={14} /> {generateMutation.isPending ? '生成中…' : '生成大纲'}
        </Button>
        {hasData && (
          <Button size="sm" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
            <Save size={14} /> {saveMutation.isPending ? '保存中' : '保存'}
          </Button>
        )}
        <span className="ml-auto text-xs text-muted-foreground">
          {generateMutation.isPending ? 'Agent 规划中…' : isFetching ? '加载中…' : hasData ? `${volumes.length} 卷` : ''}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        {error && (
          <div className="mb-3 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
            {error}
          </div>
        )}
        {!hasData && !generateMutation.isPending && (
          <div className="text-center text-muted-foreground py-16">
            <Sparkles size={40} className="mx-auto mb-3 text-muted-foreground/40" />
            <p className="mb-3">点击「生成大纲」，AI 将根据书籍设定生成完整章节规划</p>
            <Button className="bg-purple-600 hover:bg-purple-700 text-white" onClick={() => generateMutation.mutate()}>
              <Sparkles size={16} /> 立即生成
            </Button>
          </div>
        )}
        {generateMutation.isPending && !hasData && (
          <div className="text-center text-muted-foreground py-16">大纲规划中，请稍候…</div>
        )}
        {hasData && (
          <div className="space-y-4 max-w-3xl">
            {volumes.map((v, vi) => (
              <Card key={vi} className="p-3 border-none shadow-sm">
                <Input className="font-bold text-lg outline-none w-full bg-transparent border-b border-transparent focus:border-primary px-0 shadow-none"
                  value={v.name} onChange={(e) => updateVolName(vi, e.target.value)} />
                <div className="mt-2 space-y-2">
                  {v.chapters.map((c, ci) => (
                    <div key={ci} className="flex gap-2 items-start group">
                      <span className="text-xs text-muted-foreground mt-2 w-6 shrink-0">{c.number}</span>
                      <Input className="flex-1 border-b px-1 py-1 text-sm shadow-none" value={c.title} onChange={(e) => updateChapter(vi, ci, 'title', e.target.value)} />
                      <Input className="flex-[2] border-b px-1 py-1 text-xs text-muted-foreground shadow-none" value={c.summary} onChange={(e) => updateChapter(vi, ci, 'summary', e.target.value)} placeholder="梗概" />
                      <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 h-7 w-7" title="删除" onClick={() => delChapter(vi, ci)}>
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  ))}
                </div>
                <Button variant="ghost" size="sm" className="mt-2 text-primary h-7" onClick={() => addChapter(vi)}>
                  <Plus size={12} /> 新增章节
                </Button>
              </Card>
            ))}
            <Button variant="ghost" className="text-sm text-primary w-full justify-center border-t pt-3 border-dashed rounded-none h-10" onClick={addVolume}>
              <Plus size={14} /> 新增卷
            </Button>
          </div>
        )}
      </div>

      {error && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-destructive text-white text-sm px-4 py-2 rounded-lg shadow z-50 flex items-center gap-2">
          {error}
          <button onClick={() => setError('')}><RotateCcw size={12} /></button>
        </div>
      )}
    </div>
  )
}
