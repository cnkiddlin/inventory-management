from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.repositories.inventory import InventoryRepository
from app.schemas.dashboard import (
    CategoryDistribution,
    DashboardRead,
    DashboardSummary,
    TrendPoint,
)
from app.services.inventory import InventoryService, serialize_transaction


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.repo = InventoryRepository(db)
        self.inventory_service = InventoryService(db)

    def get_dashboard(self) -> DashboardRead:
        total_units, inventory_value = self.repo.inventory_summary()
        low_stock_count, out_of_stock_count = self.repo.alert_counts()
        alerts = self.inventory_service.list_alerts(
            page=1, page_size=8, search=None, status=None
        ).items

        trend_rows = self.repo.trend(days=14)
        end_day = datetime.now(timezone.utc).date()
        start_day = end_day - timedelta(days=13)
        by_day: dict[str, dict[str, int]] = {}
        for day, transaction_type, quantity in trend_rows:
            key = day.isoformat()
            by_day.setdefault(key, {"INBOUND": 0, "OUTBOUND": 0})
            by_day[key][transaction_type] += quantity

        trend = []
        for offset in range(14):
            day = start_day + timedelta(days=offset)
            values = by_day.get(day.isoformat(), {"INBOUND": 0, "OUTBOUND": 0})
            trend.append(
                TrendPoint(
                    date=day.isoformat(),
                    inbound_quantity=values["INBOUND"],
                    outbound_quantity=values["OUTBOUND"],
                    net_change=values["INBOUND"] - values["OUTBOUND"],
                )
            )

        categories = [
            CategoryDistribution(
                category_id=category_id,
                category_name=name,
                units=units,
                value=value,
                product_count=product_count,
            )
            for category_id, name, units, value, product_count in self.repo.category_distribution()
        ]

        return DashboardRead(
            generated_at=datetime.now(timezone.utc),
            summary=DashboardSummary(
                total_units=total_units,
                total_sku=self.repo.active_product_count(),
                inventory_value=inventory_value,
                low_stock_count=low_stock_count,
                out_of_stock_count=out_of_stock_count,
                warehouse_count=self.repo.active_warehouse_count(),
            ),
            trend=trend,
            category_distribution=categories,
            low_stock=alerts,
            recent_transactions=[
                serialize_transaction(transaction)
                for transaction in self.repo.recent_transactions(limit=8)
            ],
        )

