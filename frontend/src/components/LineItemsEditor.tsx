import { Button, Form, InputNumber, Select, Space, Typography } from 'antd'
import type { FormInstance } from 'antd'
import { Plus, Trash2 } from 'lucide-react'
import type { Product } from '../types'


interface LineItemsEditorProps {
  form: FormInstance
  products: Product[]
  priceField?: 'unit_cost' | 'unit_price'
  priceLabel?: string
  showStock?: boolean
}

export function LineItemsEditor({
  form,
  products,
  priceField,
  priceLabel = '单价',
  showStock = false,
}: LineItemsEditorProps) {
  return (
    <Form.List
      name="items"
      rules={[
        {
          validator: async (_, value) => {
            if (!value || value.length === 0) {
              throw new Error('请至少添加一条商品明细')
            }
          },
        },
      ]}
    >
      {(fields, { add, remove }, { errors }) => (
        <div>
          <div className="mb-2 flex items-center justify-between">
            <Typography.Text strong>商品明细</Typography.Text>
            <Button
              size="small"
              icon={<Plus size={14} />}
              onClick={() => add({ quantity: 1 })}
              type="dashed"
            >
              添加商品
            </Button>
          </div>
          <Space direction="vertical" size={8} className="w-full">
            {fields.map((field) => {
              const selectedId = form.getFieldValue(['items', field.name, 'product_id'])
              const selected = products.find((product) => product.id === selectedId)
              return (
                <div
                  key={field.key}
                  className="grid grid-cols-1 items-start gap-2 rounded-lg border border-slate-200 bg-slate-50/60 p-2 lg:grid-cols-[minmax(180px,1fr)_100px_120px_36px]"
                >
                  <Form.Item
                    name={[field.name, 'product_id']}
                    className="mb-0"
                    rules={[{ required: true, message: '请选择商品' }]}
                  >
                    <Select
                      showSearch
                      placeholder="选择商品"
                      optionFilterProp="label"
                      onChange={(productId: number) => {
                        const product = products.find((item) => item.id === productId)
                        if (priceField && product) {
                          form.setFieldValue(
                            ['items', field.name, priceField],
                            priceField === 'unit_cost' ? product.cost_price : product.selling_price,
                          )
                        }
                      }}
                      options={products.map((product) => ({
                        value: product.id,
                        label: `${product.sku} · ${product.name}${showStock ? ` · 库存 ${product.current_stock}${product.unit}` : ''}`,
                      }))}
                    />
                  </Form.Item>
                  <Form.Item
                    name={[field.name, 'quantity']}
                    className="mb-0"
                    rules={[{ required: true, message: '数量必填' }]}
                  >
                    <InputNumber min={1} precision={0} placeholder="数量" className="w-full" />
                  </Form.Item>
                  {priceField ? (
                    <Form.Item name={[field.name, priceField]} className="mb-0">
                      <InputNumber
                        min={0}
                        precision={2}
                        placeholder={priceLabel}
                        prefix="¥"
                        className="w-full"
                      />
                    </Form.Item>
                  ) : (
                    <div className="flex h-8 items-center truncate text-xs text-slate-500">
                      {selected ? `${selected.unit} · 安全库存 ${selected.safety_stock}` : '不含金额'}
                    </div>
                  )}
                  <Button
                    danger
                    type="text"
                    icon={<Trash2 size={15} />}
                    onClick={() => remove(field.name)}
                    aria-label="删除明细"
                  />
                </div>
              )
            })}
          </Space>
          <Form.ErrorList errors={errors} />
        </div>
      )}
    </Form.List>
  )
}
