import { useState } from 'react'
import {
  Button,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { ArrowUpFromLine, CheckCircle2, Eye, Plus } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { LoadError, LoadingState } from '../../components/DataState'
import { LineItemsEditor } from '../../components/LineItemsEditor'
import { StatusTag } from '../../components/StatusTag'
import { useApi } from '../../hooks/useApi'
import { getProductOptions, getWarehouseOptions } from '../../services/catalog'
import {
  confirmOutboundOrder,
  createOutboundOrder,
  getOutboundOrders,
} from '../../services/orders'
import type { OutboundItem, OutboundOrder } from '../../types'


const currency = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  maximumFractionDigits: 2,
})

interface OutboundFormValues {
  warehouse_id: number
  customer: string
  notes?: string
  created_by: string
  items: Array<{ product_id: number; quantity: number; unit_price?: number }>
}

const itemColumns: ColumnsType<OutboundItem> = [
  {
    title: '商品',
    dataIndex: 'product_name',
    render: (_, record) => (
      <div>
        <div className="font-medium text-slate-800">{record.product_name}</div>
        <div className="font-mono text-[11px] text-slate-400">{record.sku}</div>
      </div>
    ),
  },
  { title: '数量', dataIndex: 'quantity', width: 90, align: 'right', render: (value, record) => `${value} ${record.unit}` },
  { title: '销售单价', dataIndex: 'unit_price', width: 120, align: 'right', render: (value) => currency.format(value) },
  { title: '金额', dataIndex: 'line_total', width: 130, align: 'right', render: (value) => currency.format(value) },
]

export function OutboundPage() {
  const [form] = Form.useForm<OutboundFormValues>()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string | undefined>()
  const [warehouseId, setWarehouseId] = useState<number | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [selected, setSelected] = useState<OutboundOrder | null>(null)
  const [confirming, setConfirming] = useState(false)

  const warehouses = useApi(() => getWarehouseOptions(), [])
  const products = useApi(() => getProductOptions(), [])
  const orders = useApi(
    () =>
      getOutboundOrders({
        page,
        page_size: 20,
        search: search || undefined,
        status,
        warehouse_id: warehouseId,
      }),
    [page, search, status, warehouseId],
  )

  const openCreate = () => {
    form.resetFields()
    form.setFieldsValue({ created_by: 'inventory-admin', items: [{ quantity: 1 }] })
    setCreateOpen(true)
  }

  const submit = async (values: OutboundFormValues) => {
    setSaving(true)
    try {
      await createOutboundOrder(values)
      message.success('出库单已创建，确认时将校验可用库存')
      setCreateOpen(false)
      await orders.reload()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '创建出库单失败')
    } finally {
      setSaving(false)
    }
  }

  const confirmOrder = async (order: OutboundOrder) => {
    setConfirming(true)
    try {
      const updated = await confirmOutboundOrder(order.id)
      message.success(`出库单 ${updated.order_no} 已确认，库存已扣减`)
      setSelected(updated)
      await orders.reload()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '确认出库失败')
    } finally {
      setConfirming(false)
    }
  }

  const columns: ColumnsType<OutboundOrder> = [
    {
      title: '出库单号',
      dataIndex: 'order_no',
      width: 190,
      fixed: 'left',
      render: (value) => <span className="font-mono text-[11px] font-medium text-blue-700">{value}</span>,
    },
    { title: '出库仓库', dataIndex: 'warehouse_name', width: 140 },
    { title: '客户', dataIndex: 'customer', width: 190 },
    { title: '明细', dataIndex: 'item_count', width: 75, align: 'right', render: (value) => `${value} 项` },
    { title: '总数量', dataIndex: 'total_quantity', width: 90, align: 'right' },
    {
      title: '销售金额',
      dataIndex: 'total_value',
      width: 125,
      align: 'right',
      render: (value) => currency.format(value),
    },
    { title: '状态', dataIndex: 'status', width: 95, render: (value) => <StatusTag status={value} /> },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 135,
      render: (value) => <span className="text-xs text-slate-500">{dayjs(value).format('YYYY-MM-DD HH:mm')}</span>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 185,
      fixed: 'right',
      render: (_, record) => (
        <Space size={0}>
          <Button type="link" size="small" icon={<Eye size={14} />} onClick={() => setSelected(record)}>
            查看
          </Button>
          {record.status === 'DRAFT' && (
            <Popconfirm
              title="确认出库？"
              description="系统将校验可用库存，扣减后不可超出库存。"
              onConfirm={() => confirmOrder(record)}
              okText="确认出库"
              cancelText="取消"
            >
              <Button type="link" size="small" icon={<CheckCircle2 size={14} />} loading={confirming}>
                确认
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="出库管理"
        description="创建出库单并确认发货。后端会锁定库存、校验可用量并阻止任何负库存产生。"
        actions={
          <Button type="primary" icon={<Plus size={16} />} onClick={openCreate}>
            创建出库单
          </Button>
        }
      />
      <div className="panel mb-4 flex flex-wrap items-center gap-3 p-4">
        <Input.Search
          allowClear
          placeholder="搜索出库单号或客户"
          className="w-full sm:w-[280px]"
          onSearch={(value) => {
            setSearch(value.trim())
            setPage(1)
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
          placeholder="全部状态"
          className="w-full sm:w-[130px]"
          value={status}
          onChange={(value) => {
            setStatus(value)
            setPage(1)
          }}
          options={[
            { value: 'DRAFT', label: '草稿' },
            { value: 'CONFIRMED', label: '已确认' },
          ]}
        />
        <span className="ml-auto flex items-center gap-1.5 text-xs text-slate-400">
          <ArrowUpFromLine size={14} /> {orders.data?.total ?? 0} 张出库单
        </span>
      </div>

      {orders.error ? (
        <LoadError message={orders.error} onRetry={orders.reload} />
      ) : orders.loading && !orders.data ? (
        <LoadingState />
      ) : (
        <div className="panel table-card overflow-hidden">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={orders.data?.items}
            loading={orders.loading}
            scroll={{ x: 1220 }}
            pagination={{
              current: page,
              pageSize: 20,
              total: orders.data?.total ?? 0,
              showSizeChanger: false,
              onChange: setPage,
            }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无出库单" /> }}
          />
        </div>
      )}

      <Modal
        title="创建出库单"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={saving}
        width={920}
        okText="创建草稿"
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={submit} className="mt-4">
          <div className="grid grid-cols-1 gap-x-4 sm:grid-cols-3">
            <Form.Item name="warehouse_id" label="出库仓库" rules={[{ required: true, message: '请选择仓库' }]}>
              <Select
                placeholder="选择仓库"
                options={warehouses.data?.map((item) => ({ value: item.id, label: `${item.code} · ${item.name}` }))}
              />
            </Form.Item>
            <Form.Item name="customer" label="客户" rules={[{ required: true, message: '请输入客户名称' }]}>
              <Input placeholder="客户名称" />
            </Form.Item>
            <Form.Item name="created_by" label="制单人" rules={[{ required: true }]}>
              <Input placeholder="制单人" />
            </Form.Item>
          </div>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={2} placeholder="可选：订单号、配送说明" maxLength={1000} />
          </Form.Item>
          <LineItemsEditor form={form} products={products.data ?? []} priceField="unit_price" priceLabel="销售单价" showStock />
        </Form>
      </Modal>

      <Drawer
        title={selected ? `出库单 ${selected.order_no}` : '出库单详情'}
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        width={820}
        extra={
          selected?.status === 'DRAFT' ? (
            <Popconfirm
              title="确认出库？"
              description="确认后将扣减可用库存并生成流水。"
              onConfirm={() => confirmOrder(selected)}
              okText="确认出库"
            >
              <Button type="primary" icon={<CheckCircle2 size={15} />} loading={confirming}>
                确认出库
              </Button>
            </Popconfirm>
          ) : (
            selected && <StatusTag status={selected.status} />
          )
        }
      >
        {selected && (
          <>
            <Descriptions bordered size="small" column={2} className="mb-5">
              <Descriptions.Item label="出库仓库">{selected.warehouse_name}</Descriptions.Item>
              <Descriptions.Item label="客户">{selected.customer}</Descriptions.Item>
              <Descriptions.Item label="状态"><StatusTag status={selected.status} /></Descriptions.Item>
              <Descriptions.Item label="制单人">{selected.created_by}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{dayjs(selected.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
              <Descriptions.Item label="确认时间">
                {selected.confirmed_at ? dayjs(selected.confirmed_at).format('YYYY-MM-DD HH:mm:ss') : '—'}
              </Descriptions.Item>
              <Descriptions.Item label="备注" span={2}>{selected.notes || '—'}</Descriptions.Item>
            </Descriptions>
            <Table
              rowKey="id"
              columns={itemColumns}
              dataSource={selected.items}
              pagination={false}
              size="small"
              summary={() => (
                <Table.Summary.Row>
                  <Table.Summary.Cell index={0} colSpan={2}><span className="font-medium">合计</span></Table.Summary.Cell>
                  <Table.Summary.Cell index={1} />
                  <Table.Summary.Cell index={2} align="right">
                    <span className="font-semibold">{currency.format(selected.total_value)}</span>
                  </Table.Summary.Cell>
                </Table.Summary.Row>
              )}
            />
          </>
        )}
      </Drawer>
    </div>
  )
}
