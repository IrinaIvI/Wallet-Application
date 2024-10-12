from sqlalchemy import Column, Float, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Wallet(Base):
    __tablename__ = 'wallet'

    id = Column(String, primary_key=True)
    balance = Column(Float, default=0.0)

