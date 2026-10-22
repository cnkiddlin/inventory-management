import { useState } from 'react'
import { DatePicker, Empty, Input, Select, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { Dayjs } from 'dayjs'
import dayjs from 'dayjs'
import { Search } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { PageHeader } from '../../components/PageHeader'
import { LoadError, LoadingState } from '../../components/DataState'
import { StatusTag } from '../../components/StatusTag'
import { useApi } from '../../hooks/useApi'
import { getWarehouseOptions } from '../../services/catalog'
import { getTransactions } from '../../services/inventory'
import type { InventoryTransaction } from '../../types'


const { RangePicker } = DatePicker

export function TransactionsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialProductId = Number(searchParams.get('product_id')) || undefined
  const initialWarehouseId = Number(searchParams.get('warehouse_id')) || undefined
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [warehouseId, setWarehouseId] = useState<number | undefined>(initialWarehouseId)
  const [transactionType, setTransactionType] = useState<string | undefined>()
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null)
  const [productId, setProductId] = useState<number | undefined>(initialProductId)

  const warehouses = useApi(() => getWarehouseOptions(), [])
  const transactions = useApi(
    () =>
      getTransactions({
        page,
        page_size: 20,
        search: search || undefined,
        product_id: productId,
        warehouse_id: warehouseId,
        transaction_type: transactionType,
        date_from: dateRange?.[0].format('YYYY-MM-DD'),
        date_to: dateRange?.[1].format('YYYY-MM-DD'),
      }),
    [page, search, productId, warehouseId, transactionType, dateRange],
  )

  const clearProductFilter = () => {
    setProductId(undefined)
    const next = new URLSearchParams(searchParams)
    next.delete('product_id')
    setSearchParams(next, { replace: true })
  }

  const columns: ColumnsType<InventoryTransaction> = [
    {
      title: '流水号',
      dataIndex: 'transaction_no',
      width: 185,
      fixed: 'left',
      render: (value) => <span className="font-mono text-[11px] text-slate-500">{value}</span>,
    },
    {
      title: '发生时间',
      dataIndex: 'created_at',
      width: 145,
      render: (value) => (
        <div>
          <div className="text-xs text-slate-600">{dayjs(value).format('YYYY-MM-DD')}</div>
          <div className="text-[11px] text-slate-400">{dayjs(value).format('HH:mm:ss')}</div>
        </div>
      ),
    },
    {
      title: '商品',
      dataIndex: 'product_name',
      width: 220,
      render: (_, record) => (
        <div>
          <div className="font-medium text-slate-800">{record.product_name}</div>
          <div className="font-mono text-[11px] text-slate-400">{record.sku}</div>
        </div>
      ),
    },
    { title: '仓库', dataIndex: 'warehouse_name', width: 140 },
    {
      title: '类型',
      dataIndex: 'transaction_type',
      width: 110,
      render: (value) => <StatusTag status={value} />,
    },
    {
      title: '数量变动',
      dataIndex: 'quantity_change',
      width: 105,
      align: 'right',
      render: (value) => (
        <span className={value > 0 ? 'font-semibold text-emerald-600' : 'font-semibold text-orange-600'}>
          {value > 0 ? '+' : ''}
          {value}
        </span>
      ),
    },
    {
      title: '变动后余额',
      dataIndex: 'balance_after',
      width: 115,
      align: 'right',
      render: (value) => <span className="font-medium text-slate-800">{value}</span>,
    },
    {
      title: '关联单据',
      dataIndex: 'reference_no',
      width: 180,
      render: (value) => <span className="font-mono text-[11px] text-slate-500">{value || '—'}</span>,
    },
    {
      title: '备注',
      dataIndex: 'notes',
      ellipsis: true,
      render: (value) => <span className="text-xs text-slate-400">{value || '—'}</span>,
    },
  ]

  return (
    <div>
      <PageHeader
        title="库存流水"
        description="完整记录每一次入库、出库与调拨产生的库存变化和变动后余额，用于审计与追溯。"
      />
      <div className="panel mb-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input
            allowClear
            placeholder="搜索流水号、单据号、SKU 或商品"
            prefix={<Search size={15} className="text-slate-400" />}
            className="w-full lg:w-[300px]"
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
            placeholder="全部仓库"
            className="w-full sm:w-[150px]"
            value={warehouseId}
            onChange={(value) => {
              setWarehouseId(value)
              setPage(1)
            }}
            options={warehouses.data?.map((item) => ({ value: item.id, label: item.name }))}
          />
          <Select
            allowClear
            placeholder="全部类型"
            className="w-full sm:w-[145px]"
            value={transactionType}
            onChange={(value) => {
              setTransactionType(value)
              setPage(1)
            }}
            options={[
              { value: 'INBOUND', label: '入库' },
              { value: 'OUTBOUND', label: '出库' },
              { value: 'TRANSFER_IN', label: '调拨入库' },
              { value: 'TRANSFER_OUT', label: '调拨出库' },
              { value: 'ADJUSTMENT', label: '库存调整' },
            ]}
          />
          <RangePicker
            className="w-full sm:w-[250px]"
            value={dateRange}
            onChange={(values) => {
              setDateRange(values as [Dayjs, Dayjs] | null)
              setPage(1)
            }}
          />
          {productId && (
            <Tag closable color="blue" className="m-0" onClose={clearProductFilter}>
              商品 #{productId}
            </Tag>
          )}
          <span className="ml-auto text-xs text-slate-400">共 {transactions.data?.total ?? 0} 条流水</span>
        </div>
      </div>

      {transactions.error ? (
        <LoadError message={transactions.error} onRetry={transactions.reload} />
      ) : transactions.loading && !transactions.data ? (
        <LoadingState />
      ) : (
        <div className="panel table-card overflow-hidden">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={transactions.data?.items}
            loading={transactions.loading}
            scroll={{ x: 1380 }}
            pagination={{
              current: page,
              pageSize: 20,
              total: transactions.data?.total ?? 0,
              showSizeChanger: false,
              showTotal: (total) => `共 ${total} 条`,
              onChange: setPage,
            }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有匹配的库存流水" /> }}
          />
        </div>
      )}
    </div>
  )
}
