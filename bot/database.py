import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)


@dataclass
class UserRecord:
    user_id: int
    username: str | None
    generations_balance: int
    created_at: str


class Database:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._init_schema()
        logger.info("Database connected: %s", self._path)

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def _init_schema(self) -> None:
        assert self._conn is not None
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                generations_balance INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target TEXT NOT NULL,
                context TEXT NOT NULL,
                details TEXT NOT NULL,
                length_type TEXT NOT NULL,
                result_text TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                telegram_payment_charge_id TEXT UNIQUE,
                pack_payload TEXT NOT NULL,
                stars_amount INTEGER NOT NULL,
                generations_added INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            """
        )
        await self._conn.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def get_or_create_user(
        self, user_id: int, username: str | None, free_generations: int
    ) -> tuple[UserRecord, bool]:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT user_id, username, generations_balance, created_at FROM users WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            return (
                UserRecord(
                    user_id=row["user_id"],
                    username=row["username"],
                    generations_balance=row["generations_balance"],
                    created_at=row["created_at"],
                ),
                False,
            )

        created_at = self._now()
        await self._conn.execute(
            "INSERT INTO users (user_id, username, generations_balance, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, free_generations, created_at),
        )
        await self._conn.commit()
        logger.info("New user registered: %s with %s free generations", user_id, free_generations)
        return (
            UserRecord(
                user_id=user_id,
                username=username,
                generations_balance=free_generations,
                created_at=created_at,
            ),
            True,
        )

    async def update_username(self, user_id: int, username: str | None) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE users SET username = ? WHERE user_id = ?",
            (username, user_id),
        )
        await self._conn.commit()

    async def get_user(self, user_id: int) -> UserRecord | None:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT user_id, username, generations_balance, created_at FROM users WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
        if not row:
            return None
        return UserRecord(
            user_id=row["user_id"],
            username=row["username"],
            generations_balance=row["generations_balance"],
            created_at=row["created_at"],
        )

    async def get_balance(self, user_id: int) -> int:
        user = await self.get_user(user_id)
        return user.generations_balance if user else 0

    async def spend_generation(self, user_id: int) -> bool:
        """Atomically spend one generation. Returns False if balance is zero."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            UPDATE users
            SET generations_balance = generations_balance - 1
            WHERE user_id = ? AND generations_balance >= 1
            """,
            (user_id,),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def add_generations(self, user_id: int, amount: int) -> int:
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE users SET generations_balance = generations_balance + ? WHERE user_id = ?",
            (amount, user_id),
        )
        await self._conn.commit()
        return await self.get_balance(user_id)

    async def save_generation_history(
        self,
        user_id: int,
        target: str,
        context: str,
        details: str,
        length_type: str,
        result_text: str,
    ) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO generation_history
            (user_id, target, context, details, length_type, result_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, target, context, details, length_type, result_text, self._now()),
        )
        await self._conn.commit()

    async def refund_generation(self, user_id: int) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE users SET generations_balance = generations_balance + 1 WHERE user_id = ?",
            (user_id,),
        )
        await self._conn.commit()

    async def is_payment_processed(self, charge_id: str) -> bool:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT 1 FROM payments WHERE telegram_payment_charge_id = ?",
            (charge_id,),
        ) as cursor:
            return await cursor.fetchone() is not None

    async def record_payment(
        self,
        user_id: int,
        charge_id: str,
        pack_payload: str,
        stars_amount: int,
        generations_added: int,
    ) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO payments
            (user_id, telegram_payment_charge_id, pack_payload, stars_amount, generations_added, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, charge_id, pack_payload, stars_amount, generations_added, self._now()),
        )
        await self._conn.commit()
