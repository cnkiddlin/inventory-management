import { Alert, Button, Spin } from 'antd'
import { RefreshCw } from 'lucide-react'


export function LoadingState({ label = '正在加载数据...' }: { label?: string }) {
  return (
    <div className="panel flex min-h-64 flex-col items-center justify-center gap-3 p-8 text-slate-500">
      <Spin size="large" />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function LoadError({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Alert
      type="error"
      showIcon
      message="数据加载失败"
      description={message}
      action={
        onRetry ? (
          <Button size="small" icon={<RefreshCw size={14} />} onClick={onRetry}>
            重试
          </Button>
        ) : undefined
      }
      className="rounded-xl"
    />
  )
}

