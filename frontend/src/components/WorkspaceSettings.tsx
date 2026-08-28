import type { LLMConfig } from '@/types'
import { Timer, Database, Sparkles, ArrowRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface Props {
  autoSaveMs: number
  setAutoSaveMs: (ms: number) => void
  llmReady: boolean
  embeddingReady: boolean
  llmConfigs: LLMConfig[]
  onGoConfig: () => void
}

const PRESETS = [
  { label: '关闭', ms: 0 },
  { label: '5 秒', ms: 5000 },
  { label: '10 秒', ms: 10000 },
  { label: '30 秒', ms: 30000 },
]

export default function WorkspaceSettings({
  autoSaveMs, setAutoSaveMs, llmReady, embeddingReady, llmConfigs, onGoConfig,
}: Props) {
  const defaultCfg = llmConfigs.find((c) => c.is_default) || llmConfigs[0]

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto space-y-4">
        <h2 className="text-lg font-semibold">设置</h2>

        {/* 模型配置状态 */}
        <Card className="border-none shadow-sm">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-sm font-medium">
                <Sparkles size={14} /> 模型配置
              </div>
              <Button variant="outline" size="sm" onClick={onGoConfig}>
                去模型配置 <ArrowRight size={12} className="ml-1" />
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className={`rounded-lg border p-3 ${llmReady ? 'border-emerald-500/30 bg-emerald-50/50 dark:bg-emerald-950/20' : 'border-amber-500/30 bg-amber-50/50 dark:bg-amber-950/20'}`}>
                <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                  <Sparkles size={11} /> 对话模型（写作 / Ask）
                </div>
                {llmReady
                  ? <div className="font-medium flex items-center gap-1.5">{defaultCfg?.model ?? '已配置'} <Badge className="text-[10px] h-4 bg-emerald-500/10 text-emerald-600 border-emerald-500/30">就绪</Badge></div>
                  : <div className="text-amber-600 dark:text-amber-400 text-xs">未配置，写作/Ask 不可用</div>}
              </div>
              <div className={`rounded-lg border p-3 ${embeddingReady ? 'border-emerald-500/30 bg-emerald-50/50 dark:bg-emerald-950/20' : 'border-amber-500/30 bg-amber-50/50 dark:bg-amber-950/20'}`}>
                <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                  <Database size={11} /> 向量模型（章节入库 / RAG）
                </div>
                {embeddingReady
                  ? <div className="font-medium flex items-center gap-1.5">{defaultCfg?.embedding_model ?? '已配置'} <Badge className="text-[10px] h-4 bg-emerald-500/10 text-emerald-600 border-emerald-500/30">就绪</Badge></div>
                  : <div className="text-amber-600 dark:text-amber-400 text-xs">未配置，数据库页不可用</div>}
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              使用写作、Ask、章节入库（RAG）前，请在模型配置页将两个模型都配置完整。
            </p>
          </CardContent>
        </Card>

        {/* 自动保存 */}
        <Card className="border-none shadow-sm">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-1.5 text-sm font-medium">
              <Timer size={14} /> 自动保存
            </div>
            <p className="text-xs text-muted-foreground">
              编辑器内容变化后，经过设定的延时自动保存章节；也可随时点右上角「保存」手动保存。
            </p>
            <div className="flex flex-wrap gap-1.5">
              {PRESETS.map((p) => (
                <button
                  key={p.ms}
                  type="button"
                  onClick={() => setAutoSaveMs(p.ms)}
                  className={`px-3 py-1.5 rounded-full text-xs border transition ${autoSaveMs === p.ms ? 'bg-primary text-primary-foreground border-primary' : 'border-input text-muted-foreground hover:border-primary/50'}`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 阅读设置说明 */}
        <Card className="border-none shadow-sm">
          <CardContent className="p-4 space-y-2">
            <div className="text-sm font-medium">阅读设置</div>
            <p className="text-xs text-muted-foreground">
              字体大小、边距、背景色、字体颜色、亮度等阅读参数，请在「阅读」标签页右上角调整并保存。
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
