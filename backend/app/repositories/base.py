from typing import TypeVar

from sqlalchemy.orm import Session


ModelT = TypeVar("ModelT")


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, instance: ModelT) -> ModelT:
        self.db.add(instance)
        self.db.flush()
        return instance

