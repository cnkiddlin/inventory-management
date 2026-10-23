import { useState } from 'react'
import { Button, Empty, Input, Select, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { RefreshCw, Search, ShoppingCart } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { LoadError, LoadingState } from '../../components/DataState'
import { StatusTag } from '../../components/StatusTag'
import { useApi } from '../../hooks/useApi'
import { getAlerts } from '../../services/inventory'
import type { InventoryAlert } from '../../types'


export function AlertsPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string | undefined>()
  const alerts = useApi(
    () => getAlerts({ page, page_size: 20, search: search || undefined, status }),
    [page, search, status],
  )

  const columns: ColumnsType<InventoryAlert> = [
    {
      title: '商品',
      dataIndex: 'product_name',
      width: 260,
      render: (_, record) => (
        <div>
          <div className="font-medium text-slate-800">{record.product_name}</div>
          <div className="mt-0.5 font-mono text-[11px] text-slate-400">{record.sku}</div>
          {record.model && (
            <div className="font-mono text-[11px] text-slate-400">OEM {record.model}</div>
          )}
        </div>
      ),
    },
    { title: '分类', dataIndex: 'category_name', width: 110 },
    {
      title: '当前库存',
      dataIndex: 'current_stock',
      width: 120,
      align: 'right',
      render: (value, record) => (
        <span className={value === 0 ? 'font-semibold text-rose-600' : 'font-semibold text-amber-600'}>
          {value} {record.unit}
        </span>
      ),
    },
    { title: '安全库存', dataIndex: 'safety_stock', width: 105, align: 'right' },
    {
      title: '库存缺口',
      dataIndex: 'shortage',
      width: 105,
      align: 'right',
      render: (value) => <span className="font-semibold text-rose-600">-{value}</span>,
    },
    {
      title: '建议补货',
      dataIndex: 'suggested_replenishment',
      width: 130,
      align: 'right',
      render: (value, record) => (
        <Tag bordered={false} color="blue" className="m-0 font-medium">
          {value} {record.unit}
        </Tag>
      ),
    },
    {
      title: '涉及仓库',
      dataIndex: 'warehouse_count',
      width: 95,
      align: 'right',
      render: (value) => `${value} 个`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (value) => <StatusTag status={value} />,
    },
  ]

  return (
    <div>
      <PageHeader
        title="库存预警"
        description="按商品汇总所有仓库库存，与安全库存阈值实时比较，给出缺口与建议补货数量。"
        actions={
          <Button icon={<RefreshCw size={15} />} onClick={alerts.reload} loading={alerts.loading}>
            刷新预警
          </Button>
        }
      />

      <div className="panel mb-4 flex flex-wrap items-center gap-3 p-4">
        <Input
          allowClear
          placeholder="搜索 SKU 或商品名称"
          prefix={<Search size={15} className="text-slate-400" />}
          className="w-full sm:w-[300px]"
          onPressEnter={(event) => {
            setSearch(event.currentTarget.value.trim())
            setPage(1)
          }}
          onChange={(event) => {
            if (!event.target.value) {
              setSearch('')
              setPage(1)
            }
          }}
        />
        <Select
          allowClear
          placeholder="全部预警"
          className="w-full sm:w-[160px]"
          value={status}
          onChange={(value) => {
            setStatus(value)
            setPage(1)
          }}
          options={[
            { value: 'LOW_STOCK', label: '低库存' },
            { value: 'OUT_OF_STOCK', label: '缺货' },
          ]}
        />
        <span className="ml-auto flex items-center gap-1.5 text-xs text-slate-400">
          <ShoppingCart size={14} /> {alerts.data?.total ?? 0} 个商品需要关注
        </span>
      </div>

      {alerts.error ? (
        <LoadError message={alerts.error} onRetry={alerts.reload} />
      ) : alerts.loading && !alerts.data ? (
        <LoadingState label="正在计算库存预警..." />
      ) : (
        <div className="panel table-card overflow-hidden">
          <Table
            rowKey="product_id"
            columns={columns}
            dataSource={alerts.data?.items}
            loading={alerts.loading}
            scroll={{ x: 1080 }}
            expandable={{
              expandedRowRender: (record) => (
                <div className="px-2 py-1">
                  <div className="mb-2 text-xs font-medium text-slate-500">各仓库库存分布</div>
                  <div className="flex flex-wrap gap-2">
                    {record.warehouse_stock.map((stock) => (
                      <span
                        key={stock.warehouse_id}
                        className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600"
                      >
                        <span className="font-mono text-[10px] text-slate-400">{stock.warehouse_code}</span>{' '}
                        {stock.warehouse_name} · <span className="font-semibold text-slate-800">{stock.quantity}</span>{' '}
                        {record.unit}
                      </span>
                    ))}
                  </div>
                </div>
              ),
            }}
            pagination={{
              current: page,
              pageSize: 20,
              total: alerts.data?.total ?? 0,
              showSizeChanger: false,
              showTotal: (total) => `共 ${total} 条预警`,
              onChange: setPage,
            }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无库存预警，库存状态良好" /> }}
          />
        </div>
      )}
    </div>
  )
}
