# 库存管理系统架构说明

## 1. 设计目标

库存管理系统的首要目标不是静态展示，而是提供一套真实可调用的库存业务系统：

- 前端所有数据来自 PostgreSQL。
- 所有库存数量变更由后端服务层执行。
- 库存流水、单据状态与库存余额保持事务一致。
- API 结构稳定、响应可预测，便于后续构建库存管理 AI 智能体。

## 2. 运行时结构

```text
React SPA (:5173)
      │  /api/v1 (Vite dev proxy)
      ▼
FastAPI (:8000)
      │
      ├─ api/v1: HTTP 路由、参数校验、依赖注入
      ├─ services: 业务规则、事务边界、状态机
      ├─ repositories: SQLAlchemy 查询与数据访问
      ├─ models: 数据库表映射
      └─ schemas: Pydantic 请求/响应契约
      │
      ▼
PostgreSQL / stockpilot_db
```

本地运行只有一个 API 进程和一个 Vite 进程，不引入微服务、消息队列或额外基础设施。

## 3. 后端分层

| 层 | 职责 | 关键位置 |
|---|---|---|
| API | 路由、查询参数、依赖注入、HTTP 状态码 | `backend/app/api/v1/endpoints` |
| Schemas | 请求校验、分页与响应结构 | `backend/app/schemas` |
| Services | 业务规则、状态机、事务、库存增减 | `backend/app/services` |
| Repositories | SQL 查询、行锁、聚合统计、分页 | `backend/app/repositories` |
| Models | 表、外键、唯一约束、检查约束 | `backend/app/models` |
| Core | 配置、数据库会话、异常、日志 | `backend/app/core` |

业务规则集中在服务层，路由不直接操作模型。AI 智能体只需要理解 API，不需要了解数据库结构。

## 4. 数据模型

核心表：

- `categories`：商品分类；与商品一对多。
- `products`：SKU、名称、OEM 件号、分类、成本/销售价格、安全库存和状态。
- `warehouses`：仓库编码、名称、地址、负责人、容量和状态。
- `inventory`：商品与仓库的唯一组合，保存账面库存和预留库存。
- `inbound_orders` / `inbound_order_items`：入库单及明细。
- `outbound_orders` / `outbound_order_items`：出库单及明细。
- `stock_transfers` / `stock_transfer_items`：仓间调拨单及明细。
- `inventory_transactions`：不可变库存流水，记录每次增减的余额结果。

关键约束：

- `inventory(product_id, warehouse_id)` 唯一。
- 库存、预留库存、安全库存和明细数量均有非负或正值检查约束。
- 调拨单的调出仓与调入仓不能相同。
- 金额使用 PostgreSQL `NUMERIC(12, 2)`，API 输出为 JSON 数值。

## 5. 库存状态与预警

单个商品-仓库库存状态：

- `OUT_OF_STOCK`：账面库存为 0。
- `LOW_STOCK`：账面库存大于 0 且小于等于商品安全库存。
- `IN_STOCK`：账面库存大于安全库存。

预警 API 按商品汇总所有仓库的库存后再与商品安全库存比较：

- `current_stock = Σ inventory.quantity`
- `shortage = max(safety_stock - current_stock, 0)`
- `suggested_replenishment = shortage`
- 当前总库存为 0 时为缺货，否则为低库存。

这样可避免同一商品在多个仓库分别比较阈值造成误报。

## 6. 事务与并发控制

### 入库确认

1. `SELECT ... FOR UPDATE` 锁定入库单。
2. 校验单据状态必须为 `DRAFT`。
3. 逐项锁定或创建库存记录。
4. 增加库存，写入 `INBOUND` 流水。
5. 单据置为 `CONFIRMED`。
6. 一次提交；异常则整体回滚。

### 出库确认

1. 锁定出库单并校验状态。
2. 锁定涉及的库存记录。
3. 按 `quantity - reserved_quantity` 检查可用库存。
4. 任一明细不足则回滚并返回 `409`，附带缺口详情。
5. 全部满足后扣减库存、写入 `OUTBOUND` 流水并确认单据。

### 调拨完成

1. 锁定调拨单并校验状态。
2. 同时锁定调出仓和调入仓库存记录。
3. 校验调出仓可用库存。
4. 扣减调出仓、增加调入仓。
5. 分别写入 `TRANSFER_OUT` 和 `TRANSFER_IN` 两条流水。

### 幂等保护

确认接口不是基于“请求是否到达”判断，而是基于数据库中的单据状态：

- 第一次确认：`DRAFT → CONFIRMED/COMPLETED`。
- 第二次确认：在行锁下读到非 `DRAFT`，返回 `409 Conflict`。

因此网络重试或智能体重复调用不会重复增减库存。

## 7. 演示数据一致性

种子脚本不直接写入一组“看起来合理”的最终库存数字。它按照时间顺序回放：

1. 60 条初始入库明细，覆盖 30 个商品 × 2 个仓库。
2. 24 条历史出库明细。
3. 9 条调拨明细，每条产生 2 条流水。

每条流水记录变动后余额，最终 `inventory.quantity` 等于该商品-仓库全部流水变动之和。种子数据还确保：

- 至少 5 个低库存商品。
- 至少 1 个商品总库存为 0。
- 多家仓库、多张历史单据和草稿单据可用于页面演示。

种子脚本默认幂等跳过，不会在每次启动时重复插入。

## 8. 前端结构

前端使用 React Router 管理页面，使用原生 `fetch` 封装 API 客户端，未引入复杂全局状态库：

- 页面级数据通过 `useApi` 自定义钩子加载。
- 表格统一使用 Ant Design Table，支持分页、筛选与加载态。
- 表单与弹窗统一使用 Ant Design Form/Modal。
- Tailwind CSS 负责布局、间距、卡片和响应式栅格。
- Recharts 仅用于 Dashboard 趋势与分类统计。

前端不模拟库存增减，只提交真实单据请求，并在确认后重新读取 API 数据。

## 9. AI 智能体接入建议

推荐将 API 按业务意图封装为工具，而不是让模型生成 SQL：

- 查询：`GET /dashboard`、`GET /inventory`、`GET /inventory/alerts`、`GET /inventory/transactions`
- 查询商品：`GET /products`、`GET /products/options`、`GET /categories`
- 查询仓库：`GET /warehouses`、`GET /warehouses/options`
- 创建单据：`POST /inbound-orders`、`POST /outbound-orders`、`POST /stock-transfers`
- 执行变更：`POST /inbound-orders/{id}/confirm`、`POST /outbound-orders/{id}/confirm`、`POST /stock-transfers/{id}/complete`

智能体应在创建单据后向用户确认，再调用确认接口。后端保留库存检查、状态机和事务保护，即使智能体重试也不会重复变更库存。

## 10. 生产化扩展点

当前版本聚焦本地业务闭环，生产部署前建议补充：

- OAuth2/OIDC 身份认证与基于角色的权限控制。
- 操作人审计、审批流与单据取消/冲销策略。
- 预留库存与订单占用工作流。
- 库存批次、序列号、有效期与多组织隔离。
- 结构化日志、指标监控和告警。
- 在生产环境中限制 CORS、启用 HTTPS 并使用密钥管理服务。
