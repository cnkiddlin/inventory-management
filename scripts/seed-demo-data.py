#!/usr/bin/env python3
"""Seed StockPilot with a deterministic, transaction-consistent demo dataset."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import func, select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Category,
    InboundOrder,
    InboundOrderItem,
    Inventory,
    InventoryTransaction,
    OutboundOrder,
    OutboundOrderItem,
    Product,
    StockTransfer,
    StockTransferItem,
    Warehouse,
)


CATEGORIES = [
    ("电子设备", "工业计算、显示与数据采集设备"),
    ("办公用品", "日常办公与文档处理耗材"),
    ("网络设备", "企业网络连接与机房基础设施"),
    ("仓储配件", "仓储周转、包装与作业防护用品"),
    ("设施用品", "仓库照明、安全与存储设施"),
]

WAREHOUSES = [
    {
        "code": "WH-SH",
        "name": "上海中心仓",
        "location": "上海市浦东新区临港物流园 A3",
        "manager_name": "陈思远",
        "phone": "021-5888-1201",
        "capacity": 18000,
    },
    {
        "code": "WH-GZ",
        "name": "广州华南仓",
        "location": "广州市黄埔区综合保税区 B8",
        "manager_name": "梁晓晴",
        "phone": "020-6688-3302",
        "capacity": 14000,
    },
    {
        "code": "WH-CD",
        "name": "成都西部仓",
        "location": "成都市双流区空港物流大道 66 号",
        "manager_name": "周明宇",
        "phone": "028-8555-7603",
        "capacity": 12000,
    },
]

# sku, name, category index, cost, selling, unit, safety stock
PRODUCTS = [
    ("SP-EL-001", "工业级平板电脑", 0, 2200, 2899, "台", 30),
    ("SP-EL-002", "4K 专业显示器", 0, 1350, 1799, "台", 30),
    ("SP-EL-003", "无线条码扫描器", 0, 420, 599, "台", 24),
    ("SP-EL-004", "工业标签打印机", 0, 980, 1299, "台", 36),
    ("SP-EL-005", "智能温湿度传感器", 0, 160, 249, "个", 40),
    ("SP-EL-006", "便携式储能电源", 0, 1890, 2599, "台", 45),
    ("SP-OF-007", "A4 复印纸（5包/箱）", 1, 118, 159, "箱", 57),
    ("SP-OF-008", "中性签字笔（50支）", 1, 32, 49, "盒", 19),
    ("SP-OF-009", "桌面文件收纳架", 1, 45, 69, "个", 26),
    ("SP-OF-010", "三层文件柜", 1, 340, 459, "个", 33),
    ("SP-OF-011", "磁性白板 1200×900", 1, 260, 359, "块", 40),
    ("SP-OF-012", "商用碎纸机", 1, 560, 799, "台", 47),
    ("SP-NE-013", "8口千兆交换机", 2, 310, 449, "台", 54),
    ("SP-NE-014", "24口 PoE 交换机", 2, 1580, 2099, "台", 16),
    ("SP-NE-015", "企业级无线路由器", 2, 760, 999, "台", 23),
    ("SP-NE-016", "双频无线 AP", 2, 480, 649, "台", 30),
    ("SP-NE-017", "千兆光纤收发器", 2, 210, 299, "对", 37),
    ("SP-NE-018", "24口网络配线架", 2, 180, 259, "个", 44),
    ("SP-WA-019", "塑料周转箱 600×400", 3, 68, 99, "个", 51),
    ("SP-WA-020", "川字型塑料托盘", 3, 145, 199, "个", 13),
    ("SP-WA-021", "热敏条码标签（1000张）", 3, 28, 39, "卷", 20),
    ("SP-WA-022", "透明打包胶带（6卷）", 3, 21, 32, "组", 27),
    ("SP-WA-023", "工业防护手套（12双）", 3, 46, 69, "包", 34),
    ("SP-WA-024", "手持终端备用电池", 3, 190, 269, "块", 41),
    ("SP-FA-025", "LED 工矿灯 100W", 4, 165, 229, "盏", 48),
    ("SP-FA-026", "消防应急照明灯", 4, 75, 109, "盏", 55),
    ("SP-FA-027", "防静电地垫 1.2m", 4, 230, 319, "卷", 17),
    ("SP-FA-028", "重型货架层板", 4, 480, 659, "块", 24),
    ("SP-FA-029", "电动堆高车电瓶", 4, 1860, 2499, "组", 31),
    ("SP-FA-030", "仓库安全标识套装", 4, 55, 79, "套", 38),
]


def warehouse_indexes_for_product(index: int) -> tuple[int, int]:
    return {0: (0, 1), 1: (0, 2), 2: (1, 2)}[index % 3]


def initial_quantity(index: int, warehouse_index: int) -> int:
    if index == 0:
        return 24
    if index <= 5:
        return 12
    return 42 + ((index * 11 + warehouse_index * 7) % 35)


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(func.count(Product.id))) or 0
        if existing:
            print(f"检测到已有 {existing} 个商品，演示数据已存在，跳过导入。")
            return

        now = datetime.now(timezone.utc).replace(microsecond=0)
        categories = [Category(name=name, description=description) for name, description in CATEGORIES]
        warehouses = [Warehouse(**warehouse) for warehouse in WAREHOUSES]
        db.add_all(categories + warehouses)
        db.flush()

        products = []
        for sku, name, category_index, cost, selling, unit, safety in PRODUCTS:
            products.append(
                Product(
                    sku=sku,
                    name=name,
                    description=f"{name}，用于企业库存管理演示数据。",
                    category_id=categories[category_index].id,
                    cost_price=Decimal(str(cost)),
                    selling_price=Decimal(str(selling)),
                    unit=unit,
                    safety_stock=safety,
                    status="ACTIVE",
                )
            )
        db.add_all(products)
        db.flush()

        inventory_rows: dict[tuple[int, int], Inventory] = {}
        balances: dict[tuple[int, int], int] = {}
        for index, product in enumerate(products):
            for warehouse_index in warehouse_indexes_for_product(index):
                key = (product.id, warehouses[warehouse_index].id)
                inventory_rows[key] = Inventory(
                    product_id=product.id,
                    warehouse_id=warehouses[warehouse_index].id,
                    quantity=0,
                    reserved_quantity=0,
                )
                balances[key] = 0
        db.add_all(inventory_rows.values())
        db.flush()

        tx_sequence = 0

        def apply_transaction(
            product_index: int,
            warehouse_index: int,
            transaction_type: str,
            quantity_change: int,
            when: datetime,
            reference_type: str,
            reference_id: int,
            reference_no: str,
            notes: str,
        ) -> None:
            nonlocal tx_sequence
            product = products[product_index]
            warehouse = warehouses[warehouse_index]
            key = (product.id, warehouse.id)
            new_balance = balances[key] + quantity_change
            if new_balance < 0:
                raise RuntimeError(f"演示数据库存为负: {product.sku} / {warehouse.code}")
            balances[key] = new_balance
            tx_sequence += 1
            db.add(
                InventoryTransaction(
                    transaction_no=f"TX-DEMO-{tx_sequence:04d}",
                    product_id=product.id,
                    warehouse_id=warehouse.id,
                    transaction_type=transaction_type,
                    quantity_change=quantity_change,
                    balance_after=new_balance,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    reference_no=reference_no,
                    notes=notes,
                    created_at=when,
                )
            )

        inbound_sequence = 0
        inbound_times = [28, 24, 20, 16, 12, 8]
        time_index = 0
        suppliers = ["华东工业供应链", "南方办公集采中心", "西部网络设备供应商"]
        for warehouse_index in range(3):
            warehouse_products = [
                index
                for index in range(len(products))
                if warehouse_index in warehouse_indexes_for_product(index)
            ]
            for chunk_index in range(2):
                chunk = warehouse_products[chunk_index * 10 : (chunk_index + 1) * 10]
                inbound_sequence += 1
                when = now - timedelta(days=inbound_times[time_index], hours=warehouse_index)
                time_index += 1
                order = InboundOrder(
                    order_no=f"IN-DEMO-{inbound_sequence:03d}",
                    warehouse_id=warehouses[warehouse_index].id,
                    supplier=suppliers[warehouse_index],
                    status="CONFIRMED",
                    notes="演示历史入库单",
                    created_by="demo-seed",
                    confirmed_at=when,
                    created_at=when - timedelta(hours=2),
                    updated_at=when,
                )
                db.add(order)
                db.flush()
                for product_index in chunk:
                    quantity = initial_quantity(product_index, warehouse_index)
                    order.items.append(
                        InboundOrderItem(
                            product_id=products[product_index].id,
                            quantity=quantity,
                            unit_cost=products[product_index].cost_price,
                        )
                    )
                    apply_transaction(
                        product_index,
                        warehouse_index,
                        "INBOUND",
                        quantity,
                        when,
                        "INBOUND_ORDER",
                        order.id,
                        order.order_no,
                        f"入库单 {order.order_no} 确认入库",
                    )

        outbound_plan = [
            (0, [(0, 24), (1, 2), (10, 10)], "上海智联科技有限公司"),
            (1, [(0, 24), (2, 2), (14, 10)], "广州新锐电子有限公司"),
            (2, [(2, 2), (4, 3), (19, 8)], "成都蓉创自动化有限公司"),
            (0, [(3, 6), (6, 8), (9, 10)], "苏州精工制造有限公司"),
            (1, [(5, 4), (8, 6), (17, 9)], "深圳云网科技股份有限公司"),
            (2, [(7, 8), (11, 7), (22, 12)], "重庆恒达商贸有限公司"),
            (1, [(12, 10), (15, 8), (18, 12)], "杭州启明信息技术有限公司"),
            (2, [(20, 9), (23, 7), (26, 10)], "西安航天设备有限公司"),
        ]
        outbound_times = [10, 8, 6, 4, 2, 1, 6, 3]
        for sequence, (warehouse_index, items, customer) in enumerate(outbound_plan, start=1):
            when = now - timedelta(days=outbound_times[sequence - 1], hours=2)
            order = OutboundOrder(
                order_no=f"OUT-DEMO-{sequence:03d}",
                warehouse_id=warehouses[warehouse_index].id,
                customer=customer,
                status="CONFIRMED",
                notes="演示历史出库单",
                created_by="demo-seed",
                confirmed_at=when,
                created_at=when - timedelta(hours=3),
                updated_at=when,
            )
            db.add(order)
            db.flush()
            for product_index, quantity in items:
                order.items.append(
                    OutboundOrderItem(
                        product_id=products[product_index].id,
                        quantity=quantity,
                        unit_price=products[product_index].selling_price,
                    )
                )
                apply_transaction(
                    product_index,
                    warehouse_index,
                    "OUTBOUND",
                    -quantity,
                    when,
                    "OUTBOUND_ORDER",
                    order.id,
                    order.order_no,
                    f"出库单 {order.order_no} 确认出库",
                )

        transfer_plan = [
            (0, 1, [(3, 5), (6, 8), (9, 10)], 5),
            (1, 2, [(2, 4), (5, 5), (8, 6)], 3),
            (0, 2, [(1, 3), (4, 5), (7, 6)], 1),
        ]
        for sequence, (from_index, to_index, items, days_ago) in enumerate(transfer_plan, start=1):
            when = now - timedelta(days=days_ago, hours=1)
            transfer = StockTransfer(
                transfer_no=f"TR-DEMO-{sequence:03d}",
                from_warehouse_id=warehouses[from_index].id,
                to_warehouse_id=warehouses[to_index].id,
                status="COMPLETED",
                notes="演示仓间补货调拨",
                created_by="demo-seed",
                completed_at=when,
                created_at=when - timedelta(hours=4),
                updated_at=when,
            )
            db.add(transfer)
            db.flush()
            for product_index, quantity in items:
                transfer.items.append(
                    StockTransferItem(
                        product_id=products[product_index].id,
                        quantity=quantity,
                    )
                )
                apply_transaction(
                    product_index,
                    from_index,
                    "TRANSFER_OUT",
                    -quantity,
                    when,
                    "STOCK_TRANSFER",
                    transfer.id,
                    transfer.transfer_no,
                    f"调拨单 {transfer.transfer_no} 调出",
                )
                apply_transaction(
                    product_index,
                    to_index,
                    "TRANSFER_IN",
                    quantity,
                    when,
                    "STOCK_TRANSFER",
                    transfer.id,
                    transfer.transfer_no,
                    f"调拨单 {transfer.transfer_no} 调入",
                )

        draft_inbound = InboundOrder(
            order_no="IN-DEMO-007",
            warehouse_id=warehouses[0].id,
            supplier="华东工业供应链",
            status="DRAFT",
            notes="待到货后确认，演示草稿单据",
            created_by="demo-seed",
            created_at=now - timedelta(hours=8),
            updated_at=now - timedelta(hours=8),
        )
        draft_inbound.items.extend(
            [
                InboundOrderItem(
                    product_id=products[16].id,
                    quantity=8,
                    unit_cost=products[16].cost_price,
                ),
                InboundOrderItem(
                    product_id=products[17].id,
                    quantity=6,
                    unit_cost=products[17].cost_price,
                ),
            ]
        )
        draft_outbound = OutboundOrder(
            order_no="OUT-DEMO-009",
            warehouse_id=warehouses[1].id,
            customer="佛山智造装备有限公司",
            status="DRAFT",
            notes="待客户确认后出库，演示草稿单据",
            created_by="demo-seed",
            created_at=now - timedelta(hours=6),
            updated_at=now - timedelta(hours=6),
        )
        draft_outbound.items.extend(
            [
                OutboundOrderItem(
                    product_id=products[11].id,
                    quantity=2,
                    unit_price=products[11].selling_price,
                )
            ]
        )
        db.add_all([draft_inbound, draft_outbound])

        for key, inventory in inventory_rows.items():
            inventory.quantity = balances[key]
            inventory.updated_at = now

        db.commit()

        product_count = db.scalar(select(func.count(Product.id))) or 0
        inventory_count = db.scalar(select(func.count(Inventory.id))) or 0
        transaction_count = db.scalar(select(func.count(InventoryTransaction.id))) or 0
        inbound_count = db.scalar(select(func.count(InboundOrder.id))) or 0
        outbound_count = db.scalar(select(func.count(OutboundOrder.id))) or 0
        transfer_count = db.scalar(select(func.count(StockTransfer.id))) or 0
        print("库存管理系统演示数据导入完成：")
        print(f"  分类 {len(categories)} / 商品 {product_count} / 仓库 {len(warehouses)}")
        print(f"  库存记录 {inventory_count} / 库存流水 {transaction_count}")
        print(f"  入库单 {inbound_count} / 出库单 {outbound_count} / 调拨单 {transfer_count}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
