import { Button, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { BookOpen, Braces, CheckCircle2, ExternalLink, RefreshCw, Server, Terminal } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { LoadError, LoadingState } from '../../components/DataState'
import { useApi } from '../../hooks/useApi'
import { API_BASE_URL, BACKEND_URL } from '../../services/api'
import { getHealth } from '../../services/dashboard'


interface EndpointRow {
  method: string
  path: string
  description: string
  group: string
}

const endpoints: EndpointRow[] = [
  { method: 'GET', path: '/api/v1/dashboard', description: '库存看板汇总、趋势、分类与预警', group: 'Dashboard' },
  { method: 'GET', path: '/api/v1/products', description: '商品分页、关键词与分类筛选', group: 'Catalog' },
  { method: 'POST', path: '/api/v1/products', description: '创建商品', group: 'Catalog' },
  { method: 'GET', path: '/api/v1/categories', description: '商品分类列表', group: 'Catalog' },
  { method: 'GET', path: '/api/v1/warehouses', description: '仓库列表与库存统计', group: 'Catalog' },
  { method: 'GET', path: '/api/v1/inventory', description: '按商品、仓库、分类与状态查询库存', group: 'Inventory' },
  { method: 'GET', path: '/api/v1/inventory/alerts', description: '低库存与缺货预警', group: 'Inventory' },
  { method: 'GET', path: '/api/v1/inventory/transactions', description: '库存流水查询与筛选', group: 'Inventory' },
  { method: 'GET', path: '/api/v1/inbound-orders', description: '入库单列表', group: 'Inbound' },
  { method: 'POST', path: '/api/v1/inbound-orders/{id}/confirm', description: '确认入库并增加库存', group: 'Inbound' },
  { method: 'GET', path: '/api/v1/outbound-orders', description: '出库单列表', group: 'Outbound' },
  { method: 'POST', path: '/api/v1/outbound-orders/{id}/confirm', description: '确认出库并校验可用库存', group: 'Outbound' },
  { method: 'GET', path: '/api/v1/stock-transfers', description: '调拨单列表', group: 'Transfer' },
  { method: 'POST', path: '/api/v1/stock-transfers/{id}/complete', description: '完成仓间调拨', group: 'Transfer' },
  { method: 'GET', path: '/api/v1/health', description: 'API 与数据库健康检查', group: 'System' },
]

const methodColor: Record<string, string> = {
  GET: 'blue',
  POST: 'green',
  PATCH: 'gold',
}

const columns: ColumnsType<EndpointRow> = [
  {
    title: '方法',
    dataIndex: 'method',
    width: 85,
    render: (value) => (
      <Tag color={methodColor[value]} bordered={false} className="m-0 font-mono text-[11px]">
        {value}
      </Tag>
    ),
  },
  {
    title: '路径',
    dataIndex: 'path',
    width: 330,
    render: (value) => <span className="font-mono text-xs text-slate-700">{value}</span>,
  },
  { title: '说明', dataIndex: 'description' },
  {
    title: '模块',
    dataIndex: 'group',
    width: 110,
    render: (value) => <span className="text-xs text-slate-400">{value}</span>,
  },
]

const curlExample = [
  'curl -s http://localhost:8000/api/v1/health',
  '',
  'curl -s "http://localhost:8000/api/v1/inventory/alerts?page_size=20"',
  '',
  'curl -s -X POST \\',
  '  http://localhost:8000/api/v1/inbound-orders/1/confirm',
].join('\n')

export function ApiManagementPage() {
  const health = useApi(getHealth, [])

  return (
    <div>
      <PageHeader
        title="API 管理"
        description="库存管理系统的业务能力以 REST API 暴露。AI 智能体应通过 API 调用业务服务，不应直接访问数据库。"
        actions={
          <>
            <Button icon={<RefreshCw size={15} />} onClick={health.reload} loading={health.loading}>
              检查服务
            </Button>
            <Button type="primary" icon={<BookOpen size={15} />} href={`${BACKEND_URL}/docs`} target="_blank">
              打开 Swagger UI
            </Button>
          </>
        }
      />

      {health.error && !health.data ? (
        <LoadError message={health.error} onRetry={health.reload} />
      ) : health.loading && !health.data ? (
        <LoadingState label="正在检查 API 服务状态..." />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="panel p-5">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-500"><Server size={15} /> API 状态</div>
            <div className="mt-3 flex items-center gap-2 text-lg font-semibold text-emerald-600">
              <CheckCircle2 size={20} /> {health.data?.status === 'ok' ? '运行正常' : health.data?.status}
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-500"><Braces size={15} /> 数据库</div>
            <div className="mt-3 text-lg font-semibold text-slate-900">PostgreSQL</div>
            <div className="mt-1 text-xs text-emerald-600">连接正常 · stockpilot_db</div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-500"><Terminal size={15} /> API 版本</div>
            <div className="mt-3 text-lg font-semibold text-slate-900">v{health.data?.version}</div>
            <div className="mt-1 text-xs text-slate-400">REST · OpenAPI 3</div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-500"><RefreshCw size={15} /> 最近检查</div>
            <div className="mt-3 text-lg font-semibold text-slate-900">
              {health.data ? dayjs(health.data.timestamp).format('HH:mm:ss') : '—'}
            </div>
            <div className="mt-1 text-xs text-slate-400">健康检查实时响应</div>
          </div>
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="panel p-5 xl:col-span-2">
          <h2 className="m-0 text-base font-semibold text-slate-900">接入信息</h2>
          <p className="mt-1 text-xs text-slate-400">前端默认通过 Vite 代理访问 API；外部智能体可使用后端完整地址。</p>
          <div className="mt-4 space-y-3">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="text-[11px] font-medium text-slate-400">API Base URL</div>
              <div className="mt-1 font-mono text-sm text-slate-800">{API_BASE_URL}</div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="text-[11px] font-medium text-slate-400">OpenAPI Schema</div>
              <a className="mt-1 flex items-center gap-1 font-mono text-sm text-blue-600" href={`${BACKEND_URL}/openapi.json`} target="_blank" rel="noreferrer">
                {BACKEND_URL}/openapi.json <ExternalLink size={13} />
              </a>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="text-[11px] font-medium text-slate-400">Swagger UI</div>
              <a className="mt-1 flex items-center gap-1 font-mono text-sm text-blue-600" href={`${BACKEND_URL}/docs`} target="_blank" rel="noreferrer">
                {BACKEND_URL}/docs <ExternalLink size={13} />
              </a>
            </div>
          </div>
        </div>

        <div className="panel bg-slate-950 p-5 text-slate-200">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400"><Terminal size={15} /> 调用示例</div>
          <pre className="mt-4 overflow-x-auto whitespace-pre-wrap break-all rounded-lg border border-white/10 bg-[#020617] p-4 font-mono text-xs font-medium leading-6 text-sky-100">
            {curlExample}
          </pre>
          <div className="mt-3 text-[11px] leading-5 text-slate-400">
            所有确认类接口具备状态幂等保护：重复提交会返回 409，不会重复增减库存。
          </div>
        </div>
      </div>

      <div className="panel table-card mt-4 overflow-hidden">
        <div className="border-b border-slate-100 px-5 py-4">
          <h2 className="m-0 text-base font-semibold text-slate-900">核心端点</h2>
          <p className="mt-1 text-xs text-slate-400">完整参数、请求体与响应模型请查看 Swagger UI。</p>
        </div>
        <Table rowKey="path" columns={columns} dataSource={endpoints} pagination={false} scroll={{ x: 850 }} />
      </div>
    </div>
  )
}
