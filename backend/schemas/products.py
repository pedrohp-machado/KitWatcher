from pydantic import BaseModel, ConfigDict
from typing import Optional, List  
from datetime import datetime
from decimal import Decimal

# Schemas para validação de dados de produtos e histórico de preços

# dados mínimos necessários para cada produto
class ProductBase(BaseModel):
    name: str
    url: str
    store: str
    image_url: Optional[str] = None

# dados que a API retorna sobre o histórico de preços de um produto
class PriceHistoryOut(BaseModel):
    id: int
    price: Decimal
    old_price: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    collected_at: datetime 
    available: bool

    model_config = ConfigDict(from_attributes=True) # permite conversão para json 

# dados completos do produto
class ProductOut(ProductBase):
    id: int
    active: bool
    created_at: datetime
    prices: List[PriceHistoryOut] = [] # inclui o historico de preços

    model_config = ConfigDict(from_attributes=True)

