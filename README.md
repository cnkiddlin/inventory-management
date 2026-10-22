# 库存管理系统

库存管理系统是一个可直接运行的企业级库存管理 Web 应用。项目包含 React 管理后台、FastAPI REST API、PostgreSQL 数据库、SQLAlchemy 模型、Alembic 迁移、演示数据以及核心业务流程自动化测试。

所有库存变更均由后端服务层在数据库事务中完成。AI 智能体后续应直接调用 `/api/v1` REST API，不应访问数据库。

## 在线环境

系统已部署到 OpenShift，前端页面和 API 使用同一个 Route：

- 应用地址：https://inventory-inventory-management.apps.itz-00k64z.infra01-lb.tok04.techzone.ibm.com
- Swagger UI：https://inventory-inventory-management.apps.itz-00k64z.infra01-lb.tok04.techzone.ibm.com/docs
- 健康检查：https://inventory-inventory-management.apps.itz-00k64z.infra01-lb.tok04.techzone.ibm.com/api/v1/health
- OpenShift 项目：`inventory-management`

## 功能

- Dashboard：库存总量、SKU 数、库存价值、低库存/缺货数、14 天趋势、分类分布和预警列表
- 商品与分类：新增、编辑、搜索、分类筛选、SKU、成本单价和安全库存
- 仓库管理：新增、编辑、搜索、容量利用率和仓库库存分布
- 库存查询：按商品、仓库、分类、状态筛选，查看可用库存和库存状态
- 入库管理：创建入库单、查看明细、确认入库并增加库存
- 出库管理：创建出库单、校验可用库存、确认出库并扣减库存
- 库存调拨：创建调拨单、完成调拨并同步更新两个仓库库存
- 库存预警：独立 API 返回当前库存、安全库存、缺口和建议补货量
- 库存流水：记录所有库存变更、变动后余额和关联单据，支持搜索与筛选
- API 管理：服务健康检查、Swagger UI、OpenAPI Schema 与核心端点入口

## 技术栈

- 前端：React 18、TypeScript、Vite 5、Tailwind CSS、Ant Design、Recharts
- 后端：Python、FastAPI、Pydantic、SQLAlchemy 2、Alembic
- 数据库：PostgreSQL
- 测试：Pytest、FastAPI TestClient

## 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+，且数据库用户拥有连接权限

本项目不需要 Docker Compose、消息队列或微服务。

## 环境变量

项目根目录的 `.env` 用于 PostgreSQL 连接。已有 `.env` 不会被初始化脚本覆盖。缺少配置时可参考 `.env.example`：

```dotenv
PG_HOST=localhost
PG_PORT=5432
PG_USERNAME=postgres
PG_PASSWORD=your-password
PG_DATABASE=stockpilot_db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

默认数据库名为 `stockpilot_db`。请不要把真实密码提交到版本库。

前端默认通过 Vite 将 `/api` 代理到 `http://localhost:8000`。如 API 部署在其他地址，可参考 `frontend/.env.example` 设置 `VITE_API_BASE_URL` 和 `VITE_BACKEND_URL`。

## 安装依赖

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
cd frontend && npm install && cd ..
```

## 初始化数据库与演示数据

确保 PostgreSQL 已启动、`.env` 可连接后执行：

```bash
.venv/bin/python scripts/init-db.py
```

脚本会依次完成：

1. 检查并创建 `stockpilot_db`（若用户无建库权限，会输出明确的管理员 SQL 解决方式）。
2. 在 `backend` 目录执行 `alembic upgrade head`。
3. 导入演示数据。种子脚本具有幂等保护：检测到已有商品后直接跳过，不会重复插入。

演示数据包含 5 个分类、30 个商品、3 个仓库、60 条商品-仓库库存记录、102 条库存流水，以及多张已确认入库/出库单、已完成调拨单和草稿单据。数据按真实操作顺序生成，库存余额由流水汇总得出。

不要用初始化脚本执行数据库重置。脚本不会删除已有数据。

## 启动项目

```bash
./scripts/start.sh
```

启动脚本会检查后端/前端依赖，然后同时启动 API 与 Vite 开发服务器。启动时不会重复初始化数据库。

- 前端应用：http://localhost:5173
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc
- OpenAPI JSON：http://localhost:8000/openapi.json
- 健康检查：http://localhost:8000/api/v1/health

也可分别启动：

```bash
cd backend && ../.venv/bin/uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## 测试与构建

```bash
cd backend && ../.venv/bin/pytest
cd frontend && npm run build
```

当前测试覆盖健康检查、Dashboard/预警读取、入库确认、出库扣减、调拨双仓更新、重复确认拦截和超卖拦截。测试使用唯一数据并在结束时清理，不影响演示数据。

## 目录结构

```text
backend/
  app/
    api/            # /api/v1 路由与端点
    core/           # 配置、数据库、异常、日志
    models/         # SQLAlchemy 业务模型
    schemas/        # Pydantic 请求/响应结构
    repositories/   # 数据访问与查询
    services/       # 业务规则、事务与库存计算
  alembic/          # 数据库迁移
  tests/            # 关键 API/业务流程测试
frontend/
  src/
    components/     # 通用 UI 组件
    layouts/        # 应用框架
    features/       # 按业务模块组织的页面
    services/       # 真实 REST API 客户端
    routes/         # 前端路由
    types/          # TypeScript 类型
scripts/
  init-db.py        # 建库、迁移、导入演示数据
  seed-demo-data.py # 幂等演示数据导入
  start.sh          # 前后端统一启动
docs/
  architecture.md
  api-guide.md
```

## 关键业务约束

- 所有库存操作必须通过后端 API，不允许前端或智能体直接写数据库。
- 入库确认、出库确认和调拨完成均使用数据库事务与行锁。
- 单据确认采用状态校验：只有 `DRAFT` 可确认，重复提交返回 `409`，不会重复变更库存。
- 出库和调拨会检查可用库存（账面库存减去预留库存），库存不会变成负数。
- 每次库存变更都会生成一条 `inventory_transactions` 记录，包含变动数量、变动后余额和关联单据。
- 该本地演示项目未接入身份认证。生产部署前应在 API 网关或应用层增加认证、授权和审计策略。

更多设计说明见 [docs/architecture.md](docs/architecture.md)，接口调用方式见 [docs/api-guide.md](docs/api-guide.md)。
