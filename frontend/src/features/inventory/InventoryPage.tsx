import { useState } from 'react'
import { Button, Empty, Input, Select, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { ArrowRight, Boxes, Search } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { PageHeader } from '../../components/PageHeader'
import { LoadError, LoadingState } from '../../components/DataState'
import { StatusTag } from '../../components/StatusTag'
import { useApi } from '../../hooks/useApi'
import { getCategories, getWarehouseOptions } from '../../services/catalog'
import { getInventory } from '../../services/inventory'
import type { InventoryRecord } from '../../types'


export function InventoryPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialProductId = Number(searchParams.get('product_id')) || undefined
  const initialWarehouseId = Number(searchParams.get('warehouse_id')) || undefined
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [warehouseId, setWarehouseId] = useState<number | undefined>(initialWarehouseId)
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [status, setStatus] = useState<string | undefined>()
  const [productId, setProductId] = useState<number | undefined>(initialProductId)

  const categories = useApi(() => getCategories({ page: 1, page_size: 100 }), [])
  const warehouses = useApi(() => getWarehouseOptions(), [])
  const inventory = useApi(
    () =>
      getInventory({
        page,
        page_size: 20,
        search: search || undefined,
        product_id: productId,
        warehouse_id: warehouseId,
        category_id: categoryId,
        status,
      }),
    [page, search, productId, warehouseId, categoryId, status],
  )

  const clearProductFilter = () => {
    setProductId(undefined)
    const next = new URLSearchParams(searchParams)
    next.delete('product_id')
    setSearchParams(next, { replace: true })
  }

  const columns: ColumnsType<InventoryRecord> = [
    {
      title: '商品',
      dataIndex: 'product_name',
      fixed: 'left',
      width: 250,
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
      title: '仓库',
      dataIndex: 'warehouse_name',
      width: 150,
      render: (_, record) => (
        <div>
          <div className="text-slate-700">{record.warehouse_name}</div>
          <div className="font-mono text-[11px] text-slate-400">{record.warehouse_code}</div>
        </div>
      ),
    },
    {
      title: '账面库存',
      dataIndex: 'quantity',
      width: 110,
      align: 'right',
      render: (value, record) => (
        <span className="font-semibold text-slate-800">
          {value} <span className="text-[11px] font-normal text-slate-400">{record.unit}</span>
        </span>
      ),
    },
    { title: '预留', dataIndex: 'reserved_quantity', width: 75, align: 'right' },
    {
      title: '可用库存',
      dataIndex: 'available_quantity',
      width: 105,
      align: 'right',
      render: (value) => <span className="font-medium text-blue-600">{value}</span>,
    },
    { title: '安全库存', dataIndex: 'safety_stock', width: 95, align: 'right' },
    {
      title: '状态',
      dataIndex: 'status',
      width: 105,
      render: (value) => <StatusTag status={value} />,
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          onClick={() => navigate(`/transactions?product_id=${record.product_id}&warehouse_id=${record.warehouse_id}`)}
        >
          流水 <ArrowRight size={13} />
        </Button>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="库存查询"
        description="按商品与仓库查看账面库存、可用库存、安全阈值和实时库存状态。"
        actions={
          <Button icon={<Boxes size={15} />} onClick={() => navigate('/alerts')}>
            查看库存预警
          </Button>
        }
      />

      <div className="panel mb-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input
            allowClear
            placeholder="搜索 SKU 或商品名称"
            prefix={<Search size={15} className="text-slate-400" />}
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
            className="w-full sm:w-[280px]"
          />
          <Select
            allowClear
            placeholder="全部仓库"
            className="w-full sm:w-[160px]"
            value={warehouseId}
            onChange={(value) => {
              setWarehouseId(value)
              setPage(1)
            }}
            options={warehouses.data?.map((item) => ({ value: item.id, label: item.name }))}
          />
          <Select
            allowClear
            placeholder="全部分类"
            className="w-full sm:w-[150px]"
            value={categoryId}
            onChange={(value) => {
              setCategoryId(value)
              setPage(1)
            }}
            options={categories.data?.items.map((item) => ({ value: item.id, label: item.name }))}
          />
          <Select
            allowClear
            placeholder="全部状态"
            className="w-full sm:w-[145px]"
            value={status}
            onChange={(value) => {
              setStatus(value)
              setPage(1)
            }}
            options={[
              { value: 'IN_STOCK', label: '库存正常' },
              { value: 'LOW_STOCK', label: '低库存' },
              { value: 'OUT_OF_STOCK', label: '缺货' },
            ]}
          />
          {productId && (
            <Tag closable onClose={clearProductFilter} color="blue" className="m-0">
              商品 #{productId}
            </Tag>
          )}
          <span className="ml-auto text-xs text-slate-400">共 {inventory.data?.total ?? 0} 条库存记录</span>
        </div>
      </div>

      {inventory.error ? (
        <LoadError message={inventory.error} onRetry={inventory.reload} />
      ) : inventory.loading && !inventory.data ? (
        <LoadingState />
      ) : (
        <div className="panel table-card overflow-hidden">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={inventory.data?.items}
            loading={inventory.loading}
            scroll={{ x: 1120 }}
            pagination={{
              current: page,
              pageSize: 20,
              total: inventory.data?.total ?? 0,
              showSizeChanger: false,
              showTotal: (total) => `共 ${total} 条`,
              onChange: setPage,
            }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有匹配的库存记录" /> }}
          />
        </div>
      )}
    </div>
  )
}
