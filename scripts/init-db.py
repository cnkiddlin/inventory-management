#!/usr/bin/env python3
"""Create the StockPilot database, run Alembic migrations and seed demo data."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

try:
    import psycopg
    from psycopg import sql
except ImportError:
    print("缺少后端依赖。请先运行：.venv/bin/pip install -r backend/requirements-dev.txt")
    raise SystemExit(1)

from app.core.config import settings  # noqa: E402


def create_database_if_needed() -> None:
    try:
        with psycopg.connect(
            host=settings.pg_host,
            port=settings.pg_port,
            user=settings.pg_username,
            password=settings.pg_password,
            dbname="postgres",
            autocommit=True,
            connect_timeout=5,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.pg_database,))
                if cursor.fetchone() is None:
                    cursor.execute(
                        sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.pg_database))
                    )
                    print(f"已创建数据库 {settings.pg_database}")
                else:
                    print(f"数据库 {settings.pg_database} 已存在")
    except psycopg.errors.InsufficientPrivilege as exc:
        print("当前 PostgreSQL 用户没有创建数据库的权限。")
        print("最简单的解决方式：让管理员执行以下 SQL，然后重新运行本脚本：")
        print(f"  CREATE DATABASE {settings.pg_database} OWNER {settings.pg_username};")
        raise SystemExit(1) from exc
    except psycopg.OperationalError as exc:
        print("无法连接 PostgreSQL，请检查 .env 中的 PG_HOST / PG_PORT / PG_USERNAME / PG_PASSWORD。")
        raise SystemExit(1) from exc


def run(command: list[str], cwd: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND)
    result = subprocess.run(command, cwd=cwd, env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    create_database_if_needed()
    print("正在执行数据库迁移...")
    run([sys.executable, "-m", "alembic", "upgrade", "head"], BACKEND)
    print("正在导入演示数据（如已存在会自动跳过）...")
    run([sys.executable, str(ROOT / "scripts" / "seed-demo-data.py")], ROOT)
    print("初始化完成。")


if __name__ == "__main__":
    main()

