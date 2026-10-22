# 库存管理系统 API 指南

## 1. 基本信息

- Base URL：`http://localhost:8000/api/v1`
- Swagger UI：`http://localhost:8000/docs`
- OpenAPI Schema：`http://localhost:8000/openapi.json`
- 内容类型：`application/json`
- 本地演示环境未启用认证

## 2. 统一约定

### 分页

列表接口统一返回：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "pages": 0
}
```

常用查询参数：`page`、`page_size`、`search`。

### 错误响应

业务错误和校验错误统一为：

```json
{
  "error": {
    "code": "conflict",
    "message": "可用库存不足，出库单未确认",
    "details": [
      {
        "product_id": 1,
        "sku": "SP-EL-001",
        "requested": 99,
        "available": 3
      }
    ]
  }
}
```

常见状态码：

- `200`：查询或确认成功
- `201`：单据/主数据创建成功
- `404`：资源不存在
- `409`：状态冲突、重复确认或库存不足
- `422`：请求参数校验失败

## 3. 端点速览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | API 与数据库健康检查 |
| GET | `/dashboard` | Dashboard 聚合数据 |
| GET | `/categories` | 分类分页列表 |
| POST | `/categories` | 新增分类 |
| PATCH | `/categories/{id}` | 编辑分类 |
| GET | `/products` | 商品分页列表与筛选 |
| GET | `/products/options` | 商品下拉选项 |
| POST | `/products` | 新增商品 |
| PATCH | `/products/{id}` | 编辑商品 |
| GET | `/warehouses` | 仓库列表与库存统计 |
| GET | `/warehouses/options` | 仓库下拉选项 |
| POST | `/warehouses` | 新增仓库 |
| PATCH | `/warehouses/{id}` | 编辑仓库 |
| GET | `/inventory` | 库存列表 |
| GET | `/inventory/alerts` | 低库存与缺货预警 |
| GET | `/inventory/transactions` | 库存流水 |
| GET | `/inbound-orders` | 入库单列表 |
| POST | `/inbound-orders` | 创建入库单草稿 |
| GET | `/inbound-orders/{id}` | 入库单详情 |
| POST | `/inbound-orders/{id}/confirm` | 确认入库 |
| GET | `/outbound-orders` | 出库单列表 |
| POST | `/outbound-orders` | 创建出库单草稿 |
| GET | `/outbound-orders/{id}` | 出库单详情 |
| POST | `/outbound-orders/{id}/confirm` | 确认出库 |
| GET | `/stock-transfers` | 调拨单列表 |
| POST | `/stock-transfers` | 创建调拨单草稿 |
| GET | `/stock-transfers/{id}` | 调拨单详情 |
| POST | `/stock-transfers/{id}/complete` | 完成调拨 |

## 4. 查询示例

### Dashboard

```bash
curl -s http://localhost:8000/api/v1/dashboard
```

返回库存总量、SKU 数、库存价值、低库存/缺货数量、14 天入出库趋势、分类分布、低库存列表和最近流水。

### 商品查询

```bash
curl -s "http://localhost:8000/api/v1/products?page=1&page_size=20&search=交换机&status=ACTIVE"
```

### 库存查询

```bash
curl -s "http://localhost:8000/api/v1/inventory?warehouse_id=1&category_id=1&status=LOW_STOCK&page=1&page_size=20"
```

支持的商品筛选参数：`product_id`、`warehouse_id`、`category_id`、`status`、`search`。

### 库存预警

```bash
curl -s "http://localhost:8000/api/v1/inventory/alerts?status=OUT_OF_STOCK&page_size=20"
```

字段含义：

- `current_stock`：该商品所有仓库当前库存合计
- `safety_stock`：商品安全库存阈值
- `shortage`：`max(safety_stock - current_stock, 0)`
- `suggested_replenishment`：建议补货数量，当前等于 `shortage`
- `warehouse_stock`：各仓库库存明细

### 库存流水

```bash
curl -s "http://localhost:8000/api/v1/inventory/transactions?product_id=1&warehouse_id=1&transaction_type=INBOUND&page_size=50"
```

可选筛选：`product_id`、`warehouse_id`、`transaction_type`、`date_from`、`date_to`、`search`。

## 5. 入库流程

### 创建入库单草稿

```bash
curl -s -X POST http://localhost:8000/api/v1/inbound-orders \
  -H 'Content-Type: application/json' \
  -d '{
    "warehouse_id": 1,
    "supplier": "示例供应商",
    "created_by": "inventory-admin",
    "notes": "采购到货",
    "items": [
      {"product_id": 1, "quantity": 10, "unit_cost": 2200}
    ]
  }'
```

### 确认入库

```bash
curl -s -X POST http://localhost:8000/api/v1/inbound-orders/1/confirm
```

成功条件：单据存在且状态为 `DRAFT`。确认后：

- 对应仓库库存增加。
- 生成类型为 `INBOUND` 的库存流水。
- 单据状态变为 `CONFIRMED`。
- 再次确认返回 `409`。

## 6. 出库流程

### 创建出库单草稿

```bash
curl -s -X POST http://localhost:8000/api/v1/outbound-orders \
  -H 'Content-Type: application/json' \
  -d '{
    "warehouse_id": 1,
    "customer": "示例客户",
    "created_by": "inventory-admin",
    "items": [
      {"product_id": 1, "quantity": 5, "unit_price": 2899}
    ]
  }'
```

### 确认出库

```bash
curl -s -X POST http://localhost:8000/api/v1/outbound-orders/1/confirm
```

如果可用库存不足，返回 `409`，库存不会发生任何变化，`details` 中包含每一项的请求量与可用量。

## 7. 调拨流程

```bash
curl -s -X POST http://localhost:8000/api/v1/stock-transfers \
  -H 'Content-Type: application/json' \
  -d '{
    "from_warehouse_id": 1,
    "to_warehouse_id": 2,
    "created_by": "inventory-admin",
    "notes": "华南仓补货",
    "items": [
      {"product_id": 1, "quantity": 3}
    ]
  }'
```

```bash
curl -s -X POST http://localhost:8000/api/v1/stock-transfers/1/complete
```

完成调拨后：

- 调出仓库存扣减。
- 调入仓库存增加。
- 生成 `TRANSFER_OUT` 和 `TRANSFER_IN` 两条流水。
- 单据状态变为 `COMPLETED`。

## 8. 智能体调用建议

推荐将 API 包装为明确意图的工具：

1. `get_inventory_alerts`：先读取补货风险。
2. `get_product_options` / `get_warehouse_options`：获取合法 ID。
3. `create_inbound_order`：创建草稿并等待用户确认。
4. `confirm_inbound_order`：执行真实库存变更。
5. `get_inventory_transactions`：核对变更结果和余额。

不要让模型直接访问 PostgreSQL，也不要让模型拼接 SQL。所有库存一致性保证都在 API 服务层。
