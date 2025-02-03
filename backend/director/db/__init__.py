import os
from director.constants import DBType
from .base import BaseDB
from .sqlite.db import SQLiteDB
from .postgres.db import PostgresDB

db_types = {
    DBType.SQLITE: SQLiteDB,
    DBType.POSTGRES: PostgresDB,
}

def load_db(db_type: str = None) -> BaseDB:
    if db_type is None:
        db_type = os.getenv("DB_TYPE", "sqlite").lower()
    if db_type not in db_types:
        raise ValueError(
            f"Unknown DB type: {db_type}, Valid db types are: {[db_type.value for db_type in db_types]}"
        )
    return db_types[DBType(db_type)]()
