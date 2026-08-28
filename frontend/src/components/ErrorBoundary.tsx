import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  message: string
}

/** 全局错误边界：任何页面运行时崩溃时显示友好提示，而非白屏。 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' }

  static getDerivedStateFromError(error: unknown): State {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : String(error),
    }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // 保留完整堆栈便于排查（可在上报系统接入处替换）
    console.error('[StoryClaw] 页面渲染异常:', error, info.componentStack)
  }

  private handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-background p-6">
          <div className="w-full max-w-md rounded-xl border bg-card p-8 text-center shadow-sm">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10 text-3xl">
              ⚠️
            </div>
            <h2 className="mb-2 text-lg font-semibold text-foreground">页面出错了</h2>
            <p className="mb-1 text-sm text-muted-foreground">
              发生了一个意外错误，已中止当前渲染。
            </p>
            <p className="mb-6 truncate rounded bg-muted px-2 py-1 text-xs text-muted-foreground">
              {this.state.message || '未知错误'}
            </p>
            <div className="flex justify-center gap-2">
              <Button variant="outline" size="sm" onClick={() => window.history.back()}>
                返回上一页
              </Button>
              <Button size="sm" onClick={this.handleReload}>
                重新加载
              </Button>
            </div>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
