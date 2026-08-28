import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'sonner'
import {
  listAdminUsers,
  getCreditsReport,
  getAdminPricing,
  updateAdminPricing,
  getAdminMembership,
  updateAdminMembership,
  extractError,
} from '@/lib/api'
import type { AdminUser, CreditsReport } from '@/types'
import { Users, BarChart3, DollarSign, Settings, Save, RefreshCw } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'

type Tab = 'users' | 'report' | 'pricing' | 'membership'

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

function isForbidden(err: unknown): boolean {
  return axios.isAxiosError(err) && err.response?.status === 403
}

function ForbiddenNotice() {
  return (
    <div className="text-center text-muted-foreground py-12 border rounded-xl bg-muted/30">
      需要管理员权限
    </div>
  )
}

function ErrorOrForbidden({ err }: { err: unknown }) {
  if (isForbidden(err)) return <ForbiddenNotice />
  return (
    <div className="text-center text-destructive py-12 border rounded-xl bg-destructive/5">
      {extractError(err, '加载失败')}
    </div>
  )
}

function Loading() {
  return (
    <div className="space-y-2">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
    </div>
  )
}

export default function Admin() {
  const [tab, setTab] = useState<Tab>('users')

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">后台管理</h1>
        <Badge variant="secondary">管理员控制台</Badge>
      </div>

      <Tabs value={tab} onValueChange={(v) => v && setTab(v as Tab)}>
        <TabsList variant="line" className="w-full justify-start h-10 gap-1 mb-4">
          <TabsTrigger value="users"><Users size={16} /> 用户管理</TabsTrigger>
          <TabsTrigger value="report"><BarChart3 size={16} /> 积分报表</TabsTrigger>
          <TabsTrigger value="pricing"><DollarSign size={16} /> 定价配置</TabsTrigger>
          <TabsTrigger value="membership"><Settings size={16} /> 会员配置</TabsTrigger>
        </TabsList>

        <div className="flex-1 min-h-0">
          <TabsContent value="users"><UsersPanel /></TabsContent>
          <TabsContent value="report"><ReportPanel /></TabsContent>
          <TabsContent value="pricing"><ConfigPanel kind="pricing" /></TabsContent>
          <TabsContent value="membership"><ConfigPanel kind="membership" /></TabsContent>
        </div>
      </Tabs>
    </div>
  )
}

function UsersPanel() {
  const { data, isFetching, error, refetch } = useQuery<AdminUser[]>({
    queryKey: ['admin-users'],
    queryFn: listAdminUsers,
    retry: false,
  })

  if (isFetching && !data) return <Loading />
  if (error) return <ErrorOrForbidden err={error} />
  if (!data) return null

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>用户管理</CardTitle>
          <CardDescription className="mt-1">共 {data.length} 个用户</CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw size={14} /> 刷新
        </Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>用户名</TableHead>
              <TableHead>版本</TableHead>
              <TableHead className="text-right">积分余额</TableHead>
              <TableHead className="text-center">管理员</TableHead>
              <TableHead>创建时间</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((u) => (
              <TableRow key={u.id}>
                <TableCell className="text-muted-foreground">{u.id}</TableCell>
                <TableCell className="font-medium">{u.username}</TableCell>
                <TableCell>
                  <Badge variant={u.version === 'business' ? 'default' : 'secondary'}>
                    {u.version}
                  </Badge>
                </TableCell>
                <TableCell className="text-right tabular-nums font-medium">{u.credits_balance}</TableCell>
                <TableCell className="text-center">
                  {u.is_admin ? (
                    <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                      管理员
                    </Badge>
                  ) : (
                    <span className="text-muted-foreground/40">—</span>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground">{formatDate(u.created_at)}</TableCell>
              </TableRow>
            ))}
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                  暂无用户
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

function ReportPanel() {
  const { data, isFetching, error, refetch } = useQuery<CreditsReport>({
    queryKey: ['admin-credits-report'],
    queryFn: getCreditsReport,
    retry: false,
  })

  if (isFetching && !data) return <Loading />
  if (error) return <ErrorOrForbidden err={error} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="flex items-center gap-1.5"><BarChart3 size={16} /> 积分报表</CardTitle>
            <CardDescription className="mt-1">积分流水按维度聚合统计</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={14} /> 刷新
          </Button>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">按用户聚合</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>用户 ID</TableHead>
                <TableHead className="text-right">总积分变动</TableHead>
                <TableHead className="text-right">交易数</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.by_user.map((r) => (
                <TableRow key={r.user_id}>
                  <TableCell>{r.user_id}</TableCell>
                  <TableCell className="text-right tabular-nums">{r.total_delta}</TableCell>
                  <TableCell className="text-right tabular-nums">{r.tx_count}</TableCell>
                </TableRow>
              ))}
              {data.by_user.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground py-6">
                    暂无数据
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">按模型聚合</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>模型</TableHead>
                <TableHead className="text-right">总积分变动</TableHead>
                <TableHead className="text-right">交易数</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.by_model.map((r) => (
                <TableRow key={r.model}>
                  <TableCell className="font-mono text-xs">{r.model}</TableCell>
                  <TableCell className="text-right tabular-nums">{r.total_delta}</TableCell>
                  <TableCell className="text-right tabular-nums">{r.tx_count}</TableCell>
                </TableRow>
              ))}
              {data.by_model.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground py-6">
                    暂无数据
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

function ConfigPanel({ kind }: { kind: 'pricing' | 'membership' }) {
  const queryKey = ['admin-config', kind]
  const fetcher = kind === 'pricing' ? getAdminPricing : getAdminMembership
  const saver = kind === 'pricing' ? updateAdminPricing : updateAdminMembership
  const qc = useQueryClient()

  const { data, isFetching, error } = useQuery<Record<string, unknown>>({
    queryKey,
    queryFn: fetcher,
    retry: false,
  })

  const [text, setText] = useState('')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (data) {
      setText(JSON.stringify(data, null, 2))
      setLoaded(true)
    }
  }, [data])

  const saveMut = useMutation({
    mutationFn: (body: Record<string, unknown>) => saver(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey })
      toast.success('保存成功')
    },
    onError: (err) => toast.error(extractError(err, '保存失败')),
  })

  const handleSave = () => {
    let parsed: unknown
    try {
      parsed = JSON.parse(text)
    } catch (e) {
      toast.error('JSON 解析失败：' + (e as Error).message)
      return
    }
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      toast.error('配置必须是 JSON 对象')
      return
    }
    saveMut.mutate(parsed as Record<string, unknown>)
  }

  if (isFetching && !loaded) return <Loading />
  if (error) return <ErrorOrForbidden err={error} />

  return (
    <Card className="flex flex-col h-full min-h-[420px]">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="flex items-center gap-1.5">
            {kind === 'pricing' ? <DollarSign size={16} /> : <Settings size={16} />}
            {kind === 'pricing' ? '定价配置' : '会员配置'}
          </CardTitle>
          <CardDescription className="mt-1">
            {kind === 'pricing'
              ? '模型与积分换算关系（YAML 加载，JSON 编辑）'
              : '月度/季度/年度会员金额与赠送积分'}
          </CardDescription>
        </div>
        <Button onClick={handleSave} disabled={saveMut.isPending}>
          <Save size={14} /> {saveMut.isPending ? '保存中…' : '保存'}
        </Button>
      </CardHeader>
      <CardContent className="flex-1 min-h-0">
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          spellCheck={false}
          className="flex-1 w-full h-full min-h-[320px] font-mono text-xs resize-none"
          placeholder="编辑 JSON 配置…"
        />
      </CardContent>
    </Card>
  )
}
