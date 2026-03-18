from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Numeric, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import datetime 

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    store = Column(String(50), nullable=False)
    image_url = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prices = relationship("PriceHistory", back_populates="product", cascade="all, delete")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(BigInteger, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    old_price = Column(Numeric(10, 2))
    discount = Column(Numeric(5, 2))
    available = Column(Boolean, default=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="prices"   )


