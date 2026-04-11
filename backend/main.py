from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.products import Product, PriceHistory
from backend.schemas.products import ProductOut, PriceHistoryOut
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="KitWatcher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/products", response_model=List[ProductOut])
def get_products(db: Session = Depends(get_db)):
    """
    Endpoint para obter a lista de todos os produtos
     - **db**: Sessão do banco de dados, injetada automaticamente pelo FastAPI.
     - **response_model**: Especifica o modelo de resposta para validação e documentação         automática
     - Retorna uma lista de produtos monitorados
     - O FastAPI cuida da serialização dos objetos SQLAlchemy para o formato JSON
    """
    products = db.query(Product).all()
    return products

@app.get("/products/{product_id}/price-history", response_model=List[PriceHistoryOut])
def get_price_history(product_id: int, db: Session = Depends(get_db)):

    """
    Endpoint para obter a lista de histórico de preços de um produto específico
     - Retorna uma lista de preços históricos para o produto especificado
    """

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    price_history = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).order_by(PriceHistory.collected_at.desc()).all()

    return price_history

