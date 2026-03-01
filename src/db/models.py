from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    monthly_budget = Column(Float, default=0.0) # Добавляем поле для бюджета
    
    expenses = relationship("Expense", back_populates="user")

class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    item = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String)
    currency = Column(String, default="RUB")
    date = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="expenses")

class ErrorLog(Base):
    __tablename__ = 'error_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    request_text = Column(String)
    output_text = Column(String)
    error_trace = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
