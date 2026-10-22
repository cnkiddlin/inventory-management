import { useState } from 'react'
import {
  Button,
  Col,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Table,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { PackagePlus, Pencil, Search } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { LoadError, LoadingState } from '../../components/DataState'
import { StatusTag } from '../../components/StatusTag'
import { useApi } from '../../hooks/useApi'
import { createProduct, getCategories, getProducts, updateProduct } from '../../services/catalog'
import type { Product } from '../../types'


const currency = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  maximumFractionDigits: 2,
})

interface ProductFormValues {
  sku: string
  name: string
  description?: string
  category_id: number
  cost_price: number
  selling_price: number
  unit: string
  safety_stock: number
  status: 'ACTIVE' | 'INACTIVE'
}

export function ProductsPage() {
  const [form] = Form.useForm<ProductFormValues>()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [status, setStatus] = useState<string | undefined>()
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Product | null>(null)
  const [saving, setSaving] = useState(false)

  const categories = useApi(() => getCategories({ page: 1, page_size: 100 }), [])
  const products = useApi(
    () =>
      getProducts({
        page,
        page_size: 20,
        search: search || undefined,
        category_id: categoryId,
        status,
      }),
    [page, search, categoryId, status],
  )

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ unit: '件', safety_stock: 20, status: 'ACTIVE', cost_price: 0, selling_price: 0 })
    setModalOpen(true)
  }

  const openEdit = (record: Product) => {
    setEditing(record)
    form.setFieldsValue({
      sku: record.sku,
      name: record.name,
      description: record.description ?? undefined,
      category_id: record.category_id,
      cost_price: record.cost_price,
      selling_price: record.selling_price,
      unit: record.unit,
      safety_stock: record.safety_stock,
      status: record.status,
    })
    setModalOpen(true)
  }

  const submit = async (values: ProductFormValues) => {
    setSaving(true)
    try {
      if (editing) {
        await updateProduct(editing.id, values)
        message.success('商品信息已更新')
      } else {
        await createProduct(values)
        message.success('商品已创建')
      }
      setModalOpen(false)
      await products.reload()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const columns: ColumnsType<Product> = [
    {
      title: '商品',
      dataIndex: 'name',
      fixed: 'left',
      width: 240,
      render: (_, record) => (
        <div>
          <div className="font-medium text-slate-800">{record.name}</div>
          <div className="mt-0.5 font-mono text-[11px] text-slate-400">{record.sku}</div>
        </div>
      ),
    },
    { title: '分类', dataIndex: 'category_name', width: 120 },
    {
      title: '成本单价',
      dataIndex: 'cost_price',
      width: 120,
      align: 'right',
      render: (value) => currency.format(value),
    },
    {
      title: '销售单价',
      dataIndex: 'selling_price',
      width: 120,
      align: 'right',
      render: (value) => currency.format(value),
    },
    {
      title: '当前库存',
      dataIndex: 'current_stock',
      width: 120,
      align: 'right',
      render: (value, record) => (
        <span className={value <= record.safety_stock ? 'font-semibold text-rose-600' : 'font-medium text-slate-700'}>
          {value} {record.unit}
        </span>
      ),
    },
    { title: '安全库存', dataIndex: 'safety_stock', width: 100, align: 'right' },
    {
      title: '库存价值',
      dataIndex: 'inventory_value',
      width: 135,
      align: 'right',
      render: (value) => <span className="font-medium text-slate-800">{currency.format(value)}</span>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (value) => <StatusTag status={value} />,
    },
    {
      title: '操作',
      key: 'actions',
      width: 90,
      fixed: 'right',
      render: (_, record) => (
        <Button type="link" size="small" icon={<Pencil size={14} />} onClick={() => openEdit(record)}>
          编辑
        </Button>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="商品管理"
        description="维护 SKU、分类、成本价格与安全库存阈值。库存余额由入库、出库与调拨业务实时计算。"
        actions={
          <Button type="primary" icon={<PackagePlus size={16} />} onClick={openCreate}>
            新增商品
          </Button>
        }
      />

      <div className="panel mb-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input.Search
            allowClear
            placeholder="搜索 SKU 或商品名称"
            prefix={<Search size={15} className="text-slate-400" />}
            onSearch={(value) => {
              setSearch(value.trim())
              setPage(1)
            }}
            className="w-full sm:w-[300px]"
          />
          <Select
            allowClear
            placeholder="全部分类"
            className="w-full sm:w-[170px]"
            value={categoryId}
            onChange={(value) => {
              setCategoryId(value)
              setPage(1)
            }}
            options={categories.data?.items.map((item) => ({ value: item.id, label: item.name }))}
            loading={categories.loading}
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
            options={[
              { value: 'ACTIVE', label: '启用' },
              { value: 'INACTIVE', label: '停用' },
            ]}
          />
          <span className="ml-auto text-xs text-slate-400">共 {products.data?.total ?? 0} 个 SKU</span>
        </div>
      </div>

      {products.error ? (
        <LoadError message={products.error} onRetry={products.reload} />
      ) : products.loading && !products.data ? (
        <LoadingState />
      ) : (
        <div className="panel table-card overflow-hidden">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={products.data?.items}
            loading={products.loading}
            scroll={{ x: 1120 }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无商品" /> }}
            pagination={{
              current: page,
              pageSize: 20,
              total: products.data?.total ?? 0,
              showSizeChanger: false,
              showTotal: (total) => `共 ${total} 条`,
              onChange: setPage,
            }}
          />
        </div>
      )}

      <Modal
        title={editing ? '编辑商品' : '新增商品'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={saving}
        width={700}
        destroyOnClose
        okText={editing ? '保存修改' : '创建商品'}
      >
        <Form form={form} layout="vertical" onFinish={submit} className="mt-4" requiredMark="optional">
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item name="sku" label="SKU 编码" rules={[{ required: true, message: '请输入 SKU' }]}>
                <Input placeholder="例如 SP-EL-031" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="name" label="商品名称" rules={[{ required: true, message: '请输入商品名称' }]}>
                <Input placeholder="商品名称" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="category_id" label="商品分类" rules={[{ required: true, message: '请选择分类' }]}>
                <Select
                  placeholder="选择分类"
                  options={categories.data?.items.map((item) => ({ value: item.id, label: item.name }))}
                />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="unit" label="计量单位" rules={[{ required: true, message: '请输入单位' }]}>
                <Input placeholder="件 / 台 / 箱" />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="status" label="状态" rules={[{ required: true }]}>
                <Select options={[{ value: 'ACTIVE', label: '启用' }, { value: 'INACTIVE', label: '停用' }]} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item name="cost_price" label="成本单价" rules={[{ required: true, message: '请输入成本单价' }]}>
                <InputNumber min={0} precision={2} prefix="¥" className="w-full" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item name="selling_price" label="销售单价" rules={[{ required: true, message: '请输入销售单价' }]}>
                <InputNumber min={0} precision={2} prefix="¥" className="w-full" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item name="safety_stock" label="安全库存" rules={[{ required: true, message: '请输入安全库存' }]}>
                <InputNumber min={0} precision={0} className="w-full" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item name="description" label="商品描述">
                <Input.TextArea rows={3} maxLength={2000} showCount placeholder="可选：规格、用途或供应商信息" />
              </Form.Item>
            </Col>
          </Row>
          <Space className="text-xs text-slate-400">
            新商品创建后可通过入库单建立首个仓库库存。
          </Space>
        </Form>
      </Modal>
    </div>
  )
}
