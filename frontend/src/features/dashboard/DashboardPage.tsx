import { Button, Card, Empty, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  AlertTriangle,
  ArrowRight,
  Boxes,
  CircleDollarSign,
  PackageSearch,
  TriangleAlert,
  Warehouse,
} from 'lucide-react'
import dayjs from 'dayjs'
import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../components/PageHeader'
import { StatCard } from '../../components/StatCard'
import { StatusTag } from '../../components/StatusTag'
import { LoadError, LoadingState } from '../../components/DataState'
import { useApi } from '../../hooks/useApi'
import { getDashboard } from '../../services/dashboard'
import type { InventoryAlert, InventoryTransaction } from '../../types'


const pieColors = ['#2563eb', '#0ea5e9', '#14b8a6', '#f59e0b', '#8b5cf6']

const numberFormat = new Intl.NumberFormat('zh-CN')
const currencyFormat = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  maximumFractionDigits: 0,
})

const alertColumns: ColumnsType<InventoryAlert> = [
  {
    title: '商品',
    dataIndex: 'product_name',
    render: (_, record) => (
      <div>
        <div className="font-medium text-slate-800">{record.product_name}</div>
        <div className="mt-0.5 text-[11px] text-slate-400">{record.sku}</div>
      </div>
    ),
  },
  { title: '分类', dataIndex: 'category_name', width: 120 },
  {
    title: '当前库存',
    dataIndex: 'current_stock',
    width: 100,
    render: (value, record) => (
      <span className="font-semibold text-slate-900">
        {value} {record.unit}
      </span>
    ),
  },
  { title: '安全库存', dataIndex: 'safety_stock', width: 100 },
  {
    title: '缺口',
    dataIndex: 'shortage',
    width: 90,
    render: (value) => <span className="font-medium text-rose-600">{value}</span>,
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 100,
    render: (value) => <StatusTag status={value} />,
  },
]

const transactionColumns: ColumnsType<InventoryTransaction> = [
  {
    title: '流水号',
    dataIndex: 'transaction_no',
    width: 165,
    render: (value) => <span className="font-mono text-[11px] text-slate-500">{value}</span>,
  },
  {
    title: '商品',
    dataIndex: 'product_name',
    render: (_, record) => (
      <div>
        <div className="text-slate-800">{record.product_name}</div>
        <div className="text-[11px] text-slate-400">{record.warehouse_name}</div>
      </div>
    ),
  },
  {
    title: '类型',
    dataIndex: 'transaction_type',
    width: 105,
    render: (value) => <StatusTag status={value} />,
  },
  {
    title: '变动',
    dataIndex: 'quantity_change',
    width: 80,
    align: 'right',
    render: (value: number) => (
      <span className={value > 0 ? 'font-semibold text-emerald-600' : 'font-semibold text-orange-600'}>
        {value > 0 ? '+' : ''}
        {value}
      </span>
    ),
  },
  {
    title: '结存',
    dataIndex: 'balance_after',
    width: 75,
    align: 'right',
  },
  {
    title: '时间',
    dataIndex: 'created_at',
    width: 120,
    render: (value) => <span className="text-xs text-slate-400">{dayjs(value).format('MM-DD HH:mm')}</span>,
  },
]

export function DashboardPage() {
  const navigate = useNavigate()
  const { data, loading, error, reload } = useApi(getDashboard, [])

  if (loading && !data) return <LoadingState label="正在汇总库存运营数据..." />
  if (error && !data) return <LoadError message={error} onRetry={reload} />
  if (!data) return null

  const summary = data.summary
  const trendData = data.trend.map((item) => ({
    ...item,
    label: dayjs(item.date).format('MM/DD'),
  }))
  const categoryData = data.category_distribution.map((item, index) => ({
    ...item,
    color: pieColors[index % pieColors.length],
  }))

  return (
    <div>
      <PageHeader
        title="库存运营总览"
        description="掌握实时库存、资金占用与补货风险。所有指标直接来自 PostgreSQL 中的业务数据。"
        actions={
          <>
            <Button icon={<AlertTriangle size={15} />} onClick={() => navigate('/alerts')}>
              查看预警
            </Button>
            <Button type="primary" icon={<PackageSearch size={15} />} onClick={() => navigate('/inventory')}>
              查询库存
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-5 xl:gap-4">
        <StatCard
          label="库存总量"
          value={`${numberFormat.format(summary.total_units)} 件`}
          helper={`${summary.warehouse_count} 个运营仓库`}
          icon={<Boxes size={21} />}
          tone="blue"
        />
        <StatCard
          label="在售 SKU"
          value={numberFormat.format(summary.total_sku)}
          helper="启用状态的商品"
          icon={<PackageSearch size={21} />}
          tone="slate"
        />
        <StatCard
          label="库存价值"
          value={currencyFormat.format(summary.inventory_value)}
          helper="按商品成本单价计算"
          icon={<CircleDollarSign size={21} />}
          tone="green"
        />
        <StatCard
          label="低库存"
          value={numberFormat.format(summary.low_stock_count)}
          helper="已低于安全库存"
          icon={<TriangleAlert size={21} />}
          tone="amber"
        />
        <StatCard
          label="缺货商品"
          value={numberFormat.format(summary.out_of_stock_count)}
          helper="需要优先补货"
          icon={<AlertTriangle size={21} />}
          tone="red"
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card
          className="panel xl:col-span-2"
          styles={{ body: { padding: 20 } }}
          title={
            <div>
              <div className="font-semibold text-slate-900">近 14 天库存变化</div>
              <div className="mt-0.5 text-xs font-normal text-slate-400">入库与出库数量趋势</div>
            </div>
          }
          extra={<Tag bordered={false} color="blue">实时数据</Tag>}
        >
          <div className="h-[286px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid stroke="#eef2f7" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ borderRadius: 10, borderColor: '#e2e8f0', fontSize: 12 }}
                  labelStyle={{ color: '#475569', marginBottom: 4 }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
                <Line
                  type="monotone"
                  dataKey="inbound_quantity"
                  name="入库"
                  stroke="#2563eb"
                  strokeWidth={2.2}
                  dot={false}
                  activeDot={{ r: 4 }}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="outbound_quantity"
                  name="出库"
                  stroke="#f97316"
                  strokeWidth={2.2}
                  dot={false}
                  activeDot={{ r: 4 }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card
          className="panel"
          styles={{ body: { padding: 20 } }}
          title={
            <div>
              <div className="font-semibold text-slate-900">库存分类分布</div>
              <div className="mt-0.5 text-xs font-normal text-slate-400">各分类库存单位占比</div>
            </div>
          }
        >
          {categoryData.length ? (
            <>
              <div className="h-[210px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categoryData}
                      dataKey="units"
                      nameKey="category_name"
                      innerRadius={54}
                      outerRadius={82}
                      paddingAngle={3}
                      stroke="none"
                      isAnimationActive={false}
                    >
                      {categoryData.map((item) => (
                        <Cell key={item.category_id} fill={item.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number) => [`${numberFormat.format(value)} 件`, '库存']}
                      contentStyle={{ borderRadius: 10, borderColor: '#e2e8f0', fontSize: 12 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="-mt-2 space-y-2">
                {categoryData.map((item) => (
                  <div key={item.category_id} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-2 text-slate-600">
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
                      {item.category_name}
                    </span>
                    <span className="font-medium text-slate-800">{numberFormat.format(item.units)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无分类库存数据" />
          )}
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-5">
        <Card
          className="panel table-card xl:col-span-3"
          styles={{ body: { padding: 0 } }}
          title={
            <div>
              <div className="font-semibold text-slate-900">低库存与缺货</div>
              <div className="mt-0.5 text-xs font-normal text-slate-400">按当前总库存低于安全阈值排序</div>
            </div>
          }
          extra={
            <Button type="link" size="small" onClick={() => navigate('/alerts')}>
              全部预警 <ArrowRight size={13} />
            </Button>
          }
        >
          <Table
            rowKey="product_id"
            columns={alertColumns}
            dataSource={data.low_stock}
            pagination={false}
            size="small"
            scroll={{ x: 620 }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="库存状态良好" /> }}
          />
        </Card>

        <Card
          className="panel table-card xl:col-span-2"
          styles={{ body: { padding: 0 } }}
          title={
            <div>
              <div className="font-semibold text-slate-900">最近库存流水</div>
              <div className="mt-0.5 text-xs font-normal text-slate-400">最新 8 条库存变更</div>
            </div>
          }
          extra={
            <Button type="link" size="small" onClick={() => navigate('/transactions')}>
              查看全部 <ArrowRight size={13} />
            </Button>
          }
        >
          <Table
            rowKey="id"
            columns={transactionColumns.slice(1)}
            dataSource={data.recent_transactions}
            pagination={false}
            size="small"
            scroll={{ x: 420 }}
          />
        </Card>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-400">
        <span className="flex items-center gap-2">
          <Warehouse size={14} /> 数据生成时间：{dayjs(data.generated_at).format('YYYY-MM-DD HH:mm:ss')}
        </span>
        <span>库存价值 = Σ（仓库库存 × 商品成本单价）</span>
      </div>
    </div>
  )
}
