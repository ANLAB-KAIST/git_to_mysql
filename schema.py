from sqlalchemy import *
from sqlalchemy.pool import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
import config

DB_HOST = config.get("database.host")
DB_USER = config.get("database.username")
DB_PASS = config.get("database.password")
DB_SCHEMA = config.get("database.schema")
DB_TYPE = config.get("database.type")


if DB_TYPE == "sqlite":
    DB_UUID_TYPE = Integer
    DB_STRING_ID_TYPE = Text
    DB_PATH_STRING = "{type}:///{schema}.db"
elif DB_TYPE == "mysql":
    from sqlalchemy.dialects.mysql import BIGINT
    DB_UUID_TYPE = BIGINT(unsigned=True)
    DB_STRING_ID_TYPE = VARCHAR(length=160)
    DB_PATH_STRING = "{type}://{user}:{pass}@{host}/{schema}?charset=utf8mb4"
elif DB_TYPE == "memory":
    DB_UUID_TYPE = Integer
    DB_STRING_ID_TYPE = Text
    DB_PATH_STRING = "sqlite://"
else:
    print("Not supported db type %s" % DB_TYPE)
    exit(1)

Base = declarative_base()
