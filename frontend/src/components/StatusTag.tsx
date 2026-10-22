import { Tag } from 'antd'


const statusMeta: Record<string, { color: string; label: string }> = {
  ACTIVE: { color: 'green', label: '启用' },
  INACTIVE: { color: 'default', label: '停用' },
  IN_STOCK: { color: 'green', label: '库存正常' },
  LOW_STOCK: { color: 'gold', label: '低库存' },
  OUT_OF_STOCK: { color: 'red', label: '缺货' },
  DRAFT: { color: 'default', label: '草稿' },
  CONFIRMED: { color: 'blue', label: '已确认' },
  COMPLETED: { color: 'green', label: '已完成' },
  CANCELLED: { color: 'red', label: '已取消' },
  INBOUND: { color: 'green', label: '入库' },
  OUTBOUND: { color: 'orange', label: '出库' },
  TRANSFER_IN: { color: 'cyan', label: '调拨入库' },
  TRANSFER_OUT: { color: 'purple', label: '调拨出库' },
  ADJUSTMENT: { color: 'default', label: '调整' },
}

export function StatusTag({ status }: { status: string }) {
  const meta = statusMeta[status] ?? { color: 'default', label: status }
  return (
    <Tag color={meta.color} bordered={false} className="m-0 rounded-md px-2 py-0.5 text-xs">
      {meta.label}
    </Tag>
  )
}

