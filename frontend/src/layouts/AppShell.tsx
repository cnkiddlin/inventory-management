import { useState } from 'react'
import { Avatar, Button, Layout, Menu, Tooltip } from 'antd'
import type { MenuProps } from 'antd'
import {
  AlertTriangle,
  ArrowDownToLine,
  ArrowLeftRight,
  ArrowUpFromLine,
  Boxes,
  ChevronLeft,
  LayoutDashboard,
  Menu as MenuIcon,
  Package,
  PlugZap,
  Repeat2,
  Tags,
  Warehouse,
} from 'lucide-react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'


const { Header, Sider, Content } = Layout

const routeTitles: Record<string, string> = {
  '/dashboard': '运营总览',
  '/products': '商品管理',
  '/categories': '商品分类',
  '/warehouses': '仓库管理',
  '/inventory': '库存查询',
  '/alerts': '库存预警',
  '/transactions': '库存流水',
  '/inbound': '入库管理',
  '/outbound': '出库管理',
  '/transfers': '库存调拨',
  '/api-management': 'API 管理',
}

const menuItems: MenuProps['items'] = [
  {
    type: 'group',
    label: '运营',
    children: [
      { key: '/dashboard', icon: <LayoutDashboard size={16} />, label: '运营总览' },
      { key: '/inventory', icon: <Boxes size={16} />, label: '库存查询' },
      { key: '/alerts', icon: <AlertTriangle size={16} />, label: '库存预警' },
      { key: '/transactions', icon: <Repeat2 size={16} />, label: '库存流水' },
    ],
  },
  {
    type: 'group',
    label: '主数据',
    children: [
      { key: '/products', icon: <Package size={16} />, label: '商品管理' },
      { key: '/categories', icon: <Tags size={16} />, label: '商品分类' },
      { key: '/warehouses', icon: <Warehouse size={16} />, label: '仓库管理' },
    ],
  },
  {
    type: 'group',
    label: '库存单据',
    children: [
      { key: '/inbound', icon: <ArrowDownToLine size={16} />, label: '入库管理' },
      { key: '/outbound', icon: <ArrowUpFromLine size={16} />, label: '出库管理' },
      { key: '/transfers', icon: <ArrowLeftRight size={16} />, label: '库存调拨' },
    ],
  },
  {
    type: 'group',
    label: '系统',
    children: [{ key: '/api-management', icon: <PlugZap size={16} />, label: 'API 管理' }],
  },
]

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const pageTitle = routeTitles[location.pathname] ?? '库存管理系统'

  return (
    <Layout className="min-h-screen bg-canvas">
      <Sider
        width={238}
        collapsedWidth={0}
        collapsed={collapsed}
        trigger={null}
        breakpoint="lg"
        onBreakpoint={(broken) => setCollapsed(broken)}
        className="sticky top-0 h-screen overflow-hidden bg-[#0f172a]"
        theme="dark"
      >
        <div className="flex h-16 items-center gap-3 border-b border-white/10 px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500 text-white shadow-lg shadow-blue-500/20">
            <Package size={19} strokeWidth={2.3} />
          </div>
          <div>
            <div className="text-[17px] font-semibold leading-tight tracking-tight text-white">库存管理系统</div>
          </div>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => {
            navigate(key)
            if (window.innerWidth < 1024) setCollapsed(true)
          }}
          className="border-none bg-[#0f172a] px-2 py-3 [&_.ant-menu-item]:my-0.5 [&_.ant-menu-item]:rounded-lg [&_.ant-menu-item-group-title]:px-3 [&_.ant-menu-item-group-title]:pb-1 [&_.ant-menu-item-group-title]:pt-4 [&_.ant-menu-item-group-title]:text-[10px] [&_.ant-menu-item-group-title]:uppercase [&_.ant-menu-item-group-title]:tracking-[0.16em] [&_.ant-menu-item-group-title]:text-slate-500"
        />
        <div className="absolute bottom-0 left-0 right-0 border-t border-white/10 p-4 text-[11px] text-slate-500">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_0_3px_rgba(52,211,153,0.12)]" />
            API 服务已连接
          </div>
          <div className="mt-1 pl-4">库存管理系统 v1.0.0</div>
        </div>
      </Sider>

      <Layout className="min-w-0 bg-canvas">
        <Header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200/80 bg-white/95 px-4 backdrop-blur md:px-7">
          <div className="flex min-w-0 items-center gap-3">
            <Button
              type="text"
              icon={collapsed ? <MenuIcon size={19} /> : <ChevronLeft size={19} />}
              onClick={() => setCollapsed((value) => !value)}
              aria-label="切换导航栏"
            />
            <div className="truncate text-sm font-medium text-slate-700">{pageTitle}</div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-slate-400 md:inline">库存运营工作台</span>
            <Tooltip title="当前用户：库存管理员">
              <Avatar size={32} className="bg-slate-900 text-xs">管</Avatar>
            </Tooltip>
          </div>
        </Header>
        <Content className="mx-auto w-full max-w-[1560px] p-4 md:p-7">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
