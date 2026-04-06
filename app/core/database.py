from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine("postgresql://{}:{}@{}:{}/{}".format(settings.db_user, settings.db_password, settings.db_host, settings.db_port, settings.db_name))

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine)