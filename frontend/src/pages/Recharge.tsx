import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  listMemberships,
  purchaseMembership,
  getRechargeHistory,
  extractError,
} from '@/lib/api'
import type { Membership, RechargeHistory, PurchaseResult } from '@/types'
import {
  CreditCard,
  Check,
  Star,
  Crown,
  Gift,
  Clock,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'

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

function priceYuan(cents: number): string {
  return (cents / 100).toFixed(2)
}

const PERIOD_ICON: Record<string, React.ReactNode> = {
  month: <Star size={18} />,
  quarter: <Gift size={18} />,
  year: <Crown size={18} />,
}

const PERIOD_LABEL: Record<string, string> = {
  month: '月卡',
  quarter: '季卡',
  year: '年卡',
}

export default function Recharge() {
  const qc = useQueryClient()

  const { data: cfg, isFetching } = useQuery({
    queryKey: ['recharge-memberships'],
    queryFn: listMemberships,
  })

  const { data: history, isFetching: histLoading } = useQuery<RechargeHistory[]>({
    queryKey: ['recharge-history'],
    queryFn: getRechargeHistory,
  })

  const purchaseMut = useMutation({
    mutationFn: (id: string) => purchaseMembership(id),
    onSuccess: (res: PurchaseResult) => {
      toast.success(`购买成功：${res.membership}，新增积分 ${res.credits_added}，新余额 ${res.new_balance}（${res.payment_status}）`)
      qc.invalidateQueries({ queryKey: ['recharge-history'] })
    },
    onError: (err) => {
      toast.error(extractError(err, '购买失败'))
    },
  })

  const memberships: Membership[] = cfg?.memberships?.filter((m) => m.enabled) ?? []

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <CreditCard size={22} /> 充值会员
        </h1>
        <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
          模拟支付
        </Badge>
      </div>

      {/* 套餐卡片 */}
      {isFetching && !cfg ? (
        <div className="space-y-2">
          <Skeleton className="h-40 w-full" />
        </div>
      ) : memberships.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {memberships.map((m) => {
            const icon = PERIOD_ICON[m.period] ?? <CreditCard size={18} />
            const label = PERIOD_LABEL[m.period] ?? m.name
            const buying = purchaseMut.isPending && purchaseMut.variables === m.id
            return (
              <Card key={m.id} className="p-5 flex flex-col hover:shadow-md transition border-none shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <span className="w-9 h-9 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                    {icon}
                  </span>
                  <div>
                    <div className="font-bold">{m.name}</div>
                    <div className="text-xs text-muted-foreground">{label}</div>
                  </div>
                </div>
                <div className="mb-3">
                  <span className="text-3xl font-bold text-foreground">¥{priceYuan(m.price_cny)}</span>
                  <span className="text-sm text-muted-foreground ml-1">
                    / {m.duration_days} 天
                  </span>
                </div>
                <div className="text-sm text-muted-foreground mb-4 flex items-center gap-1">
                  <Gift size={14} className="text-amber-500" />
                  赠送 <span className="font-semibold text-amber-600">{m.bonus_credits}</span> 积分
                </div>
                <Button
                  onClick={() => purchaseMut.mutate(m.id)}
                  disabled={buying}
                  className="mt-auto w-full"
                >
                  {buying ? '处理中…' : (
                    <>
                      <CreditCard size={14} /> 立即购买
                    </>
                  )}
                </Button>
              </Card>
            )
          })}
        </div>
      ) : (
        <div className="text-center text-muted-foreground py-12 border rounded-xl bg-muted/30">
          暂无可用套餐
        </div>
      )}

      {/* 充值历史 */}
      <div className="mt-8">
        <h2 className="font-semibold flex items-center gap-2 mb-3">
          <Clock size={16} /> 充值历史
        </h2>
        {histLoading && !history ? (
          <div className="text-muted-foreground text-sm">加载中…</div>
        ) : history && history.length > 0 ? (
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead className="text-right">积分变动</TableHead>
                  <TableHead>说明</TableHead>
                  <TableHead>时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((h) => (
                  <TableRow key={h.id}>
                    <TableCell className="text-muted-foreground">{h.id}</TableCell>
                    <TableCell className={`text-right tabular-nums ${h.delta >= 0 ? 'text-emerald-600' : 'text-destructive'}`}>
                      {h.delta >= 0 ? '+' : ''}{h.delta}
                    </TableCell>
                    <TableCell>{h.reason}</TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(h.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        ) : (
          <div className="text-center text-muted-foreground py-8 border rounded-xl bg-muted/30">
            暂无充值记录
          </div>
        )}
      </div>
    </div>
  )
}
