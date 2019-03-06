from sqlalchemy import *
from sqlalchemy.pool import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import config
import datetime

DB_HOST = config.get("database.host")
DB_USER = config.get("database.username")
DB_PASS = config.get("database.password")
DB_SCHEMA = config.get("database.schema")
DB_TYPE = config.get("database.type")


if DB_TYPE == "sqlite":
    DB_UUID_TYPE = Integer
    DB_STRING_ID_TYPE = Text
    DB_PATH_STRING = "{type}:///{schema}.db"
    DB_TEXT_TYPE = Text
elif DB_TYPE == "mysql":
    from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT
    DB_UUID_TYPE = BIGINT(unsigned=True)
    DB_STRING_ID_TYPE = VARCHAR(length=160)
    DB_PATH_STRING = "{type}://{user}:{pass}@{host}/{schema}?charset=utf8mb4"
    DB_TEXT_TYPE = LONGTEXT
elif DB_TYPE == "memory":
    DB_UUID_TYPE = Integer
    DB_STRING_ID_TYPE = Text
    DB_PATH_STRING = "sqlite://"
    DB_TEXT_TYPE = Text
else:
    print("Not supported db type %s" % DB_TYPE)
    exit(1)

Base = declarative_base()


class CommitDiff(Base):
    __tablename__ = "commit_diff"
    child = Column(DB_STRING_ID_TYPE, primary_key=True)
    parent = Column(DB_STRING_ID_TYPE, primary_key=True)
    message = Column(DB_TEXT_TYPE, nullable=False)
    diff = Column(DB_TEXT_TYPE, nullable=True)
    insertions = Column(DB_UUID_TYPE, nullable=False)
    deletions = Column(DB_UUID_TYPE, nullable=False)
    create_at = Column(DateTime, nullable=False, index=True)

    def __init__(self, child_id: str, parent_id: str, message: str, diff: str, insertions: int, deletions: int, create_at: datetime.datetime):
        self.child = child_id
        self.parent = parent_id
        self.message = message
        self.diff = diff
        self.insertions = insertions
        self.deletions = deletions
        self.create_at = create_at


_session = None


def get_session() -> Session:
    return _session()


def init_database():
    params = {"type": DB_TYPE, "user": DB_USER, "pass":DB_PASS, "host":DB_HOST, "schema": DB_SCHEMA}
    engine = create_engine(DB_PATH_STRING.format(**params), encoding="utf8",
                           pool_size=16, max_overflow=-1,
                           poolclass=QueuePool, pool_recycle=3600)

    Base.metadata.create_all(engine)
    global _session
    _session = sessionmaker(bind=engine, autocommit=True, autoflush=True)
    return True
