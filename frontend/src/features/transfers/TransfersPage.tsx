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
import { ArrowLeftRight, CheckCircle2, Eye, Plus } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { LoadError, LoadingState } from '../../components/DataState'
import { LineItemsEditor } from '../../components/LineItemsEditor'
import { StatusTag } from '../../components/StatusTag'
import { useApi } from '../../hooks/useApi'
import { getProductOptions, getWarehouseOptions } from '../../services/catalog'
import { completeTransfer, createTransfer, getTransfers } from '../../services/orders'
import type { StockTransfer, TransferItem } from '../../types'


interface TransferFormValues {
  from_warehouse_id: number
  to_warehouse_id: number
  notes?: string
  created_by: string
  items: Array<{ product_id: number; quantity: number }>
}

const itemColumns: ColumnsType<TransferItem> = [
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
  {
    title: '调拨数量',
    dataIndex: 'quantity',
    width: 130,
    align: 'right',
    render: (value, record) => `${value} ${record.unit}`,
  },
]

export function TransfersPage() {
  const [form] = Form.useForm<TransferFormValues>()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string | undefined>()
  const [warehouseId, setWarehouseId] = useState<number | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [selected, setSelected] = useState<StockTransfer | null>(null)
  const [completing, setCompleting] = useState(false)

  const warehouses = useApi(() => getWarehouseOptions(), [])
  const products = useApi(() => getProductOptions(), [])
  const transfers = useApi(
    () =>
      getTransfers({
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

  const submit = async (values: TransferFormValues) => {
    setSaving(true)
    try {
      await createTransfer(values)
      message.success('调拨单已创建，完成时将同步更新两个仓库库存')
      setCreateOpen(false)
      await transfers.reload()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '创建调拨单失败')
    } finally {
      setSaving(false)
    }
  }

  const finishTransfer = async (transfer: StockTransfer) => {
    setCompleting(true)
    try {
      const updated = await completeTransfer(transfer.id)
      message.success(`调拨单 ${updated.transfer_no} 已完成`)
      setSelected(updated)
      await transfers.reload()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '完成调拨失败')
    } finally {
      setCompleting(false)
    }
  }

  const columns: ColumnsType<StockTransfer> = [
    {
      title: '调拨单号',
      dataIndex: 'transfer_no',
      width: 190,
      fixed: 'left',
      render: (value) => <span className="font-mono text-[11px] font-medium text-blue-700">{value}</span>,
    },
    {
      title: '调拨路径',
      key: 'route',
      width: 320,
      render: (_, record) => (
        <div className="flex items-center gap-2 text-sm">
          <span className="font-medium text-slate-700">{record.from_warehouse_name}</span>
          <ArrowLeftRight size={14} className="text-blue-500" />
          <span className="font-medium text-slate-700">{record.to_warehouse_name}</span>
        </div>
      ),
    },
    { title: '明细', dataIndex: 'item_count', width: 75, align: 'right', render: (value) => `${value} 项` },
    { title: '调拨数量', dataIndex: 'total_quantity', width: 100, align: 'right' },
    { title: '状态', dataIndex: 'status', width: 95, render: (value) => <StatusTag status={value} /> },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 140,
      render: (value) => <span className="text-xs text-slate-500">{dayjs(value).format('YYYY-MM-DD HH:mm')}</span>,
    },
    {
      title: '备注',
      dataIndex: 'notes',
      ellipsis: true,
      render: (value) => <span className="text-xs text-slate-400">{value || '—'}</span>,
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
              title="完成调拨？"
              description="系统将同时扣减调出仓并增加调入仓库存。"
              onConfirm={() => finishTransfer(record)}
              okText="完成调拨"
              cancelText="取消"
            >
              <Button type="link" size="small" icon={<CheckCircle2 size={14} />} loading={completing}>
                完成
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
        title="库存调拨"
        description="在仓库之间转移库存。完成调拨会在同一事务中扣减调出仓、增加调入仓，并生成两条库存流水。"
        actions={
          <Button type="primary" icon={<Plus size={16} />} onClick={openCreate}>
            创建调拨单
          </Button>
        }
      />
      <div className="panel mb-4 flex flex-wrap items-center gap-3 p-4">
        <Input.Search
          allowClear
          placeholder="搜索调拨单号或备注"
          className="w-full sm:w-[280px]"
          onSearch={(value) => {
            setSearch(value.trim())
            setPage(1)
          }}
        />
        <Select
          allowClear
          placeholder="涉及仓库"
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
            { value: 'COMPLETED', label: '已完成' },
          ]}
        />
        <span className="ml-auto flex items-center gap-1.5 text-xs text-slate-400">
          <ArrowLeftRight size={14} /> {transfers.data?.total ?? 0} 张调拨单
        </span>
      </div>

      {transfers.error ? (
        <LoadError message={transfers.error} onRetry={transfers.reload} />
      ) : transfers.loading && !transfers.data ? (
        <LoadingState />
      ) : (
        <div className="panel table-card overflow-hidden">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={transfers.data?.items}
            loading={transfers.loading}
            scroll={{ x: 1200 }}
            pagination={{
              current: page,
              pageSize: 20,
              total: transfers.data?.total ?? 0,
              showSizeChanger: false,
              onChange: setPage,
            }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无调拨单" /> }}
          />
        </div>
      )}

      <Modal
        title="创建库存调拨单"
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
            <Form.Item name="from_warehouse_id" label="调出仓库" rules={[{ required: true, message: '请选择调出仓库' }]}>
              <Select
                placeholder="调出仓库"
                options={warehouses.data?.map((item) => ({ value: item.id, label: `${item.code} · ${item.name}` }))}
              />
            </Form.Item>
            <Form.Item name="to_warehouse_id" label="调入仓库" rules={[{ required: true, message: '请选择调入仓库' }]}>
              <Select
                placeholder="调入仓库"
                options={warehouses.data?.map((item) => ({ value: item.id, label: `${item.code} · ${item.name}` }))}
              />
            </Form.Item>
            <Form.Item name="created_by" label="制单人" rules={[{ required: true }]}>
              <Input placeholder="制单人" />
            </Form.Item>
          </div>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={2} placeholder="例如：华南仓低库存补货" maxLength={1000} />
          </Form.Item>
          <LineItemsEditor form={form} products={products.data ?? []} showStock />
        </Form>
      </Modal>

      <Drawer
        title={selected ? `调拨单 ${selected.transfer_no}` : '调拨单详情'}
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        width={760}
        extra={
          selected?.status === 'DRAFT' ? (
            <Popconfirm
              title="完成调拨？"
              description="确认后将同步更新两个仓库库存。"
              onConfirm={() => finishTransfer(selected)}
              okText="完成调拨"
            >
              <Button type="primary" icon={<CheckCircle2 size={15} />} loading={completing}>
                完成调拨
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
              <Descriptions.Item label="调出仓库">{selected.from_warehouse_name}</Descriptions.Item>
              <Descriptions.Item label="调入仓库">{selected.to_warehouse_name}</Descriptions.Item>
              <Descriptions.Item label="状态"><StatusTag status={selected.status} /></Descriptions.Item>
              <Descriptions.Item label="制单人">{selected.created_by}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{dayjs(selected.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
              <Descriptions.Item label="完成时间">
                {selected.completed_at ? dayjs(selected.completed_at).format('YYYY-MM-DD HH:mm:ss') : '—'}
              </Descriptions.Item>
              <Descriptions.Item label="备注" span={2}>{selected.notes || '—'}</Descriptions.Item>
            </Descriptions>
            <Table rowKey="id" columns={itemColumns} dataSource={selected.items} pagination={false} size="small" />
          </>
        )}
      </Drawer>
    </div>
  )
}
