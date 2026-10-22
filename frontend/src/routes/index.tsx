import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../layouts/AppShell'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { ProductsPage } from '../features/products/ProductsPage'
import { CategoriesPage } from '../features/categories/CategoriesPage'
import { WarehousesPage } from '../features/warehouses/WarehousesPage'
import { InventoryPage } from '../features/inventory/InventoryPage'
import { AlertsPage } from '../features/alerts/AlertsPage'
import { TransactionsPage } from '../features/transactions/TransactionsPage'
import { InboundPage } from '../features/inbound/InboundPage'
import { OutboundPage } from '../features/outbound/OutboundPage'
import { TransfersPage } from '../features/transfers/TransfersPage'
import { ApiManagementPage } from '../features/api-management/ApiManagementPage'


export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/categories" element={<CategoriesPage />} />
        <Route path="/warehouses" element={<WarehousesPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/inbound" element={<InboundPage />} />
        <Route path="/outbound" element={<OutboundPage />} />
        <Route path="/transfers" element={<TransfersPage />} />
        <Route path="/api-management" element={<ApiManagementPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}

