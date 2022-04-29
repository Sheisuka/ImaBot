from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg2

DATABASE = {
    'drivername': 'postgresql+psycopg2',
    'host': '192.168.1.101',
    'port': '5432',
    'username': 'superuser',
    'password': 'superpass',
    'database': 'imagiro'
}
engine = create_engine(URL(**DATABASE))
DeclarativeBase = declarative_base()

class Post(DeclarativeBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column('name', String, unique=True)
    def __repr__(self):
        return ''.format(self.code)

def run_db():
    engine = create_engine(URL(**DATABASE))
    DeclarativeBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()