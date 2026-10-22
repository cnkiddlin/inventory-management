import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import 'antd/dist/reset.css'
import './index.css'
import App from './App'


dayjs.locale('zh-cn')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#2563eb',
          colorInfo: '#2563eb',
          colorSuccess: '#16a34a',
          colorWarning: '#d97706',
          colorError: '#dc2626',
          borderRadius: 10,
          borderRadiusLG: 14,
          colorBgLayout: '#f4f6fa',
          colorText: '#0f172a',
          colorTextSecondary: '#64748b',
          fontFamily:
            'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif',
        },
        components: {
          Layout: { headerBg: '#ffffff', siderBg: '#0f172a' },
          Table: { headerBg: '#f8fafc', rowHoverBg: '#f8fbff' },
          Menu: {
            darkItemBg: '#0f172a',
            darkSubMenuItemBg: '#0f172a',
            darkItemSelectedBg: 'rgba(37, 99, 235, 0.24)',
          },
          Button: { controlHeight: 36 },
          Input: { controlHeight: 36 },
          Select: { controlHeight: 36 },
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)

