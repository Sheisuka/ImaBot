import datetime
from .db_session import SqlAlchemyBase
from sqlalchemy import String, Integer, DateTime, Column


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True, unique=True)
    photos_count = Column(Integer, nullable=True, default=0)
    created_date = Column(DateTime, default=datetime.datetime.today().strftime("%m/%d/%Y"))
    lang = Column(String, default='ru')
