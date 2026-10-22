from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models import (
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


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def _inventory_quantity(client: TestClient, product_id: int, warehouse_id: int) -> int:
    response = client.get(
        "/api/v1/inventory",
        params={"product_id": product_id, "warehouse_id": warehouse_id, "page_size": 10},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    return items[0]["quantity"]


def _cleanup(sku: str, warehouse_codes: list[str], category_name: str) -> None:
    db = SessionLocal()
    try:
        product = db.scalar(select(Product).where(Product.sku == sku))
        warehouses = list(db.scalars(select(Warehouse).where(Warehouse.code.in_(warehouse_codes))).all())
        category = db.scalar(select(Category).where(Category.name == category_name))
        warehouse_ids = [warehouse.id for warehouse in warehouses]

        if product:
            transfer_ids = list(
                db.scalars(
                    select(StockTransferItem.transfer_id).where(
                        StockTransferItem.product_id == product.id
                    )
                ).all()
            )
            outbound_ids = list(
                db.scalars(
                    select(OutboundOrderItem.order_id).where(
                        OutboundOrderItem.product_id == product.id
                    )
                ).all()
            )
            inbound_ids = list(
                db.scalars(
                    select(InboundOrderItem.order_id).where(
                        InboundOrderItem.product_id == product.id
                    )
                ).all()
            )
            db.execute(delete(InventoryTransaction).where(InventoryTransaction.product_id == product.id))
            db.execute(delete(StockTransferItem).where(StockTransferItem.product_id == product.id))
            if transfer_ids:
                db.execute(delete(StockTransfer).where(StockTransfer.id.in_(transfer_ids)))
            db.execute(delete(OutboundOrderItem).where(OutboundOrderItem.product_id == product.id))
            if outbound_ids:
                db.execute(delete(OutboundOrder).where(OutboundOrder.id.in_(outbound_ids)))
            db.execute(delete(InboundOrderItem).where(InboundOrderItem.product_id == product.id))
            if inbound_ids:
                db.execute(delete(InboundOrder).where(InboundOrder.id.in_(inbound_ids)))
            db.execute(delete(Inventory).where(Inventory.product_id == product.id))
            db.delete(product)

        if warehouse_ids:
            db.execute(
                delete(InventoryTransaction).where(
                    InventoryTransaction.warehouse_id.in_(warehouse_ids)
                )
            )
            db.execute(delete(Inventory).where(Inventory.warehouse_id.in_(warehouse_ids)))
            db.execute(delete(Warehouse).where(Warehouse.id.in_(warehouse_ids)))
        if category:
            db.delete(category)
        db.commit()
    finally:
        db.close()


def test_health_and_dashboard_have_real_data(client: TestClient) -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["database"] == "connected"

    dashboard = client.get("/api/v1/dashboard")
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["summary"]["total_sku"] >= 30
    assert len(payload["trend"]) == 14
    assert len(payload["category_distribution"]) >= 5

    alerts = client.get("/api/v1/inventory/alerts", params={"page_size": 100})
    assert alerts.status_code == 200
    assert alerts.json()["total"] >= 1
    assert all(item["shortage"] == item["suggested_replenishment"] for item in alerts.json()["items"])


def test_inventory_business_flow_and_guardrails(client: TestClient) -> None:
    suffix = uuid4().hex[:8].upper()
    category_name = f"测试分类-{suffix}"
    sku = f"PYTEST-{suffix}"
    warehouse_codes = [f"T-A-{suffix}", f"T-B-{suffix}"]

    try:
        category_response = client.post(
            "/api/v1/categories",
            json={"name": category_name, "description": "自动化测试分类"},
        )
        assert category_response.status_code == 201, category_response.text
        category_id = category_response.json()["id"]

        product_response = client.post(
            "/api/v1/products",
            json={
                "sku": sku,
                "name": f"自动化测试商品 {suffix}",
                "category_id": category_id,
                "cost_price": 10,
                "selling_price": 15,
                "unit": "件",
                "safety_stock": 5,
                "status": "ACTIVE",
            },
        )
        assert product_response.status_code == 201, product_response.text
        product_id = product_response.json()["id"]

        warehouse_ids = []
        for index, code in enumerate(warehouse_codes, start=1):
            warehouse_response = client.post(
                "/api/v1/warehouses",
                json={
                    "code": code,
                    "name": f"测试仓库 {index} {suffix}",
                    "location": "测试地址",
                    "capacity": 1000,
                    "status": "ACTIVE",
                },
            )
            assert warehouse_response.status_code == 201, warehouse_response.text
            warehouse_ids.append(warehouse_response.json()["id"])

        inbound = client.post(
            "/api/v1/inbound-orders",
            json={
                "warehouse_id": warehouse_ids[0],
                "supplier": "测试供应商",
                "created_by": "pytest",
                "items": [{"product_id": product_id, "quantity": 15, "unit_cost": 10}],
            },
        )
        assert inbound.status_code == 201, inbound.text
        inbound_id = inbound.json()["id"]
        confirmed_inbound = client.post(f"/api/v1/inbound-orders/{inbound_id}/confirm")
        assert confirmed_inbound.status_code == 200, confirmed_inbound.text
        assert confirmed_inbound.json()["status"] == "CONFIRMED"
        assert _inventory_quantity(client, product_id, warehouse_ids[0]) == 15

        duplicate_confirm = client.post(f"/api/v1/inbound-orders/{inbound_id}/confirm")
        assert duplicate_confirm.status_code == 409
        assert _inventory_quantity(client, product_id, warehouse_ids[0]) == 15

        outbound = client.post(
            "/api/v1/outbound-orders",
            json={
                "warehouse_id": warehouse_ids[0],
                "customer": "测试客户",
                "created_by": "pytest",
                "items": [{"product_id": product_id, "quantity": 5, "unit_price": 15}],
            },
        )
        assert outbound.status_code == 201, outbound.text
        outbound_id = outbound.json()["id"]
        confirmed_outbound = client.post(f"/api/v1/outbound-orders/{outbound_id}/confirm")
        assert confirmed_outbound.status_code == 200, confirmed_outbound.text
        assert _inventory_quantity(client, product_id, warehouse_ids[0]) == 10

        transfer = client.post(
            "/api/v1/stock-transfers",
            json={
                "from_warehouse_id": warehouse_ids[0],
                "to_warehouse_id": warehouse_ids[1],
                "created_by": "pytest",
                "items": [{"product_id": product_id, "quantity": 3}],
            },
        )
        assert transfer.status_code == 201, transfer.text
        transfer_id = transfer.json()["id"]
        completed = client.post(f"/api/v1/stock-transfers/{transfer_id}/complete")
        assert completed.status_code == 200, completed.text
        assert completed.json()["status"] == "COMPLETED"
        assert _inventory_quantity(client, product_id, warehouse_ids[0]) == 7
        assert _inventory_quantity(client, product_id, warehouse_ids[1]) == 3

        duplicate_transfer = client.post(f"/api/v1/stock-transfers/{transfer_id}/complete")
        assert duplicate_transfer.status_code == 409

        oversell = client.post(
            "/api/v1/outbound-orders",
            json={
                "warehouse_id": warehouse_ids[0],
                "customer": "超卖测试客户",
                "created_by": "pytest",
                "items": [{"product_id": product_id, "quantity": 999, "unit_price": 15}],
            },
        )
        assert oversell.status_code == 201, oversell.text
        oversell_confirm = client.post(
            f"/api/v1/outbound-orders/{oversell.json()['id']}/confirm"
        )
        assert oversell_confirm.status_code == 409
        assert "可用库存不足" in oversell_confirm.json()["error"]["message"]
        assert _inventory_quantity(client, product_id, warehouse_ids[0]) == 7

        transactions = client.get(
            "/api/v1/inventory/transactions",
            params={"product_id": product_id, "page_size": 100},
        )
        assert transactions.status_code == 200
        assert transactions.json()["total"] == 4
    finally:
        _cleanup(sku, warehouse_codes, category_name)

