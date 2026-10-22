import { useState } from 'react'
import {
  Button,
  Col,
  Drawer,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Progress,
  Row,
  Select,
  Space,
  Table,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Boxes, Eye, MapPin, Pencil, Plus } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { LoadError, LoadingState } from '../../components/DataState'
import { StatusTag } from '../../components/StatusTag'
import { useApi } from '../../hooks/useApi'
import { getInventory } from '../../services/inventory'
import { createWarehouse, getWarehouses, updateWarehouse } from '../../services/catalog'
import type { InventoryRecord, Warehouse } from '../../types'


const currency = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  maximumFractionDigits: 0,
})

interface WarehouseValues {
  code: string
  name: string
  location: string
  manager_name?: string
  phone?: string
  capacity: number
  status: 'ACTIVE' | 'INACTIVE'
}

const inventoryColumns: ColumnsType<InventoryRecord> = [
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
    title: '库存',
    dataIndex: 'quantity',
    align: 'right',
    width: 90,
    render: (value, record) => `${value} ${record.unit}`,
  },
  { title: '可用', dataIndex: 'available_quantity', align: 'right', width: 75 },
  { title: '安全库存', dataIndex: 'safety_stock', align: 'right', width: 90 },
  {
    title: '状态',
    dataIndex: 'status',
    width: 100,
    render: (value) => <StatusTag status={value} />,
  },
]

export function WarehousesPage() {
  const [form] = Form.useForm<WarehouseValues>()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string | undefined>()
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Warehouse | null>(null)
  const [saving, setSaving] = useState(false)
  const [selected, setSelected] = useState<Warehouse | null>(null)

  const warehouses = useApi(
    () => getWarehouses({ page, page_size: 20, search: search || undefined, status }),
    [page, search, status],
  )
  const warehouseInventory = useApi(
    () =>
      selected
        ? getInventory({ warehouse_id: selected.id, page: 1, page_size: 100 })
        : Promise.resolve(null),
    [selected?.id],
  )

  const openEditor = (record?: Warehouse) => {
    setEditing(record ?? null)
    form.resetFields()
    if (record) {
      form.setFieldsValue({
        code: record.code,
        name: record.name,
        location: record.location,
        manager_name: record.manager_name ?? undefined,
        phone: record.phone ?? undefined,
        capacity: record.capacity,
        status: record.status,
      })
    } else {
      form.setFieldsValue({ status: 'ACTIVE', capacity: 10000 })
    }
    setOpen(true)
  }

  const submit = async (values: WarehouseValues) => {
    setSaving(true)
    try {
      if (editing) {
        await updateWarehouse(editing.id, values)
        message.success('仓库信息已更新')
      } else {
        await createWarehouse(values)
        message.success('仓库已创建')
      }
      setOpen(false)
      await warehouses.reload()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const columns: ColumnsType<Warehouse> = [
    {
      title: '仓库',
      dataIndex: 'name',
      width: 220,
      render: (_, record) => (
        <div>
          <div className="font-medium text-slate-800">{record.name}</div>
          <div className="font-mono text-[11px] text-slate-400">{record.code}</div>
        </div>
      ),
    },
    {
      title: '地址',
      dataIndex: 'location',
      render: (value) => (
        <span className="flex items-center gap-1.5 text-slate-500">
          <MapPin size={13} className="shrink-0" /> {value}
        </span>
      ),
    },
    { title: '负责人', dataIndex: 'manager_name', width: 100, render: (value) => value || '—' },
    { title: 'SKU', dataIndex: 'sku_count', width: 75, align: 'right' },
    {
      title: '库存量',
      dataIndex: 'total_units',
      width: 100,
      align: 'right',
      render: (value) => `${Number(value).toLocaleString('zh-CN')} 件`,
    },
    {
      title: '库存价值',
      dataIndex: 'total_value',
      width: 130,
      align: 'right',
      render: (value) => currency.format(value),
    },
    {
      title: '容量利用',
      dataIndex: 'utilization_percent',
      width: 150,
      render: (value) => (
        <Progress
          percent={Math.min(value, 100)}
          size="small"
          strokeColor={value > 90 ? '#dc2626' : value > 70 ? '#d97706' : '#2563eb'}
          format={() => `${value}%`}
        />
      ),
    },
    { title: '状态', dataIndex: 'status', width: 85, render: (value) => <StatusTag status={value} /> },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space size={0}>
          <Button type="link" size="small" icon={<Eye size={14} />} onClick={() => setSelected(record)}>
            库存
          </Button>
          <Button type="link" size="small" icon={<Pencil size={14} />} onClick={() => openEditor(record)}>
            编辑
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="仓库管理"
        description="维护仓库档案与容量信息，并查看各仓库的实时库存分布与资金占用。"
        actions={
          <Button type="primary" icon={<Plus size={16} />} onClick={() => openEditor()}>
            新增仓库
          </Button>
        }
      />
      <div className="panel mb-4 flex flex-wrap items-center gap-3 p-4">
        <Input.Search
          allowClear
          placeholder="搜索仓库编码、名称或地址"
          className="w-full sm:w-[320px]"
          onSearch={(value) => {
            setSearch(value.trim())
            setPage(1)
          }}
        />
        <Select
          allowClear
          placeholder="全部状态"
          className="w-full sm:w-[140px]"
          value={status}
          onChange={(value) => {
            setStatus(value)
            setPage(1)
          }}
          options={[{ value: 'ACTIVE', label: '启用' }, { value: 'INACTIVE', label: '停用' }]}
        />
        <span className="ml-auto flex items-center gap-1.5 text-xs text-slate-400">
          <Boxes size={14} /> {warehouses.data?.total ?? 0} 个仓库
        </span>
      </div>

      {warehouses.error ? (
        <LoadError message={warehouses.error} onRetry={warehouses.reload} />
      ) : warehouses.loading && !warehouses.data ? (
        <LoadingState />
      ) : (
        <div className="panel table-card overflow-hidden">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={warehouses.data?.items}
            loading={warehouses.loading}
            scroll={{ x: 1200 }}
            pagination={{
              current: page,
              pageSize: 20,
              total: warehouses.data?.total ?? 0,
              showSizeChanger: false,
              onChange: setPage,
            }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无仓库" /> }}
          />
        </div>
      )}

      <Modal
        title={editing ? '编辑仓库' : '新增仓库'}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={saving}
        width={680}
        okText="保存"
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={submit} className="mt-4">
          <Row gutter={16}>
            <Col xs={24} sm={10}>
              <Form.Item name="code" label="仓库编码" rules={[{ required: true, message: '请输入仓库编码' }]}>
                <Input placeholder="WH-BJ" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={14}>
              <Form.Item name="name" label="仓库名称" rules={[{ required: true, message: '请输入仓库名称' }]}>
                <Input placeholder="北京华北仓" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item name="location" label="仓库地址" rules={[{ required: true, message: '请输入仓库地址' }]}>
                <Input placeholder="省市区与详细地址" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="manager_name" label="负责人">
                <Input placeholder="负责人姓名" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="phone" label="联系电话">
                <Input placeholder="联系电话" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="capacity" label="设计容量（件）" rules={[{ required: true }]}>
                <InputNumber min={0} precision={0} className="w-full" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="status" label="状态" rules={[{ required: true }]}>
                <Select options={[{ value: 'ACTIVE', label: '启用' }, { value: 'INACTIVE', label: '停用' }]} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      <Drawer
        title={selected ? `${selected.name} · 库存分布` : '仓库库存'}
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        width={760}
        extra={selected ? <StatusTag status={selected.status} /> : null}
      >
        {warehouseInventory.loading ? (
          <LoadingState label="正在读取仓库库存..." />
        ) : warehouseInventory.error ? (
          <LoadError message={warehouseInventory.error} onRetry={warehouseInventory.reload} />
        ) : (
          <Table
            rowKey="id"
            columns={inventoryColumns}
            dataSource={warehouseInventory.data?.items}
            pagination={false}
            size="small"
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="该仓库暂无库存" /> }}
          />
        )}
      </Drawer>
    </div>
  )
}
