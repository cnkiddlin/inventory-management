import { useState } from 'react'
import { Button, Empty, Form, Input, Modal, Table, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Pencil, Plus, Tags } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { LoadError, LoadingState } from '../../components/DataState'
import { useApi } from '../../hooks/useApi'
import { createCategory, getCategories, updateCategory } from '../../services/catalog'
import type { Category } from '../../types'


interface CategoryValues {
  name: string
  description?: string
}

export function CategoriesPage() {
  const [form] = Form.useForm<CategoryValues>()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Category | null>(null)
  const [saving, setSaving] = useState(false)
  const categories = useApi(
    () => getCategories({ page, page_size: 20, search: search || undefined }),
    [page, search],
  )

  const openEditor = (record?: Category) => {
    setEditing(record ?? null)
    form.resetFields()
    if (record) form.setFieldsValue({ name: record.name, description: record.description ?? undefined })
    setOpen(true)
  }

  const submit = async (values: CategoryValues) => {
    setSaving(true)
    try {
      if (editing) {
        await updateCategory(editing.id, values)
        message.success('分类已更新')
      } else {
        await createCategory(values)
        message.success('分类已创建')
      }
      setOpen(false)
      await categories.reload()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const columns: ColumnsType<Category> = [
    {
      title: '分类名称',
      dataIndex: 'name',
      render: (value) => (
        <span className="flex items-center gap-2 font-medium text-slate-800">
          <Tags size={15} className="text-blue-500" /> {value}
        </span>
      ),
    },
    {
      title: '分类描述',
      dataIndex: 'description',
      render: (value) => <span className="text-slate-500">{value || '—'}</span>,
    },
    {
      title: '商品数量',
      dataIndex: 'product_count',
      width: 120,
      align: 'right',
      render: (value) => <span className="font-medium text-slate-700">{value} 个</span>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button type="link" size="small" icon={<Pencil size={14} />} onClick={() => openEditor(record)}>
          编辑
        </Button>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="商品分类"
        description="分类用于商品组织和 Dashboard 库存结构分析。删除操作默认关闭，避免影响历史单据。"
        actions={
          <Button type="primary" icon={<Plus size={16} />} onClick={() => openEditor()}>
            新增分类
          </Button>
        }
      />
      <div className="panel mb-4 p-4">
        <Input.Search
          allowClear
          placeholder="搜索分类名称"
          className="w-full sm:w-[300px]"
          onSearch={(value) => {
            setSearch(value.trim())
            setPage(1)
          }}
        />
      </div>
      {categories.error ? (
        <LoadError message={categories.error} onRetry={categories.reload} />
      ) : categories.loading && !categories.data ? (
        <LoadingState />
      ) : (
        <div className="panel table-card overflow-hidden">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={categories.data?.items}
            loading={categories.loading}
            pagination={{
              current: page,
              pageSize: 20,
              total: categories.data?.total ?? 0,
              showSizeChanger: false,
              onChange: setPage,
            }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无分类" /> }}
          />
        </div>
      )}
      <Modal
        title={editing ? '编辑分类' : '新增分类'}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={saving}
        okText="保存"
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={submit} className="mt-4">
          <Form.Item name="name" label="分类名称" rules={[{ required: true, message: '请输入分类名称' }]}>
            <Input placeholder="例如：电子设备" maxLength={80} />
          </Form.Item>
          <Form.Item name="description" label="分类描述">
            <Input.TextArea rows={3} maxLength={1000} showCount placeholder="分类用途说明" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
