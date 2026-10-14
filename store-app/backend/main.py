"""
STORE — Backend API (self-contained)

A simple shop in ONE app: it owns its products, its stock, and its orders,
all in a single SQLite database (store.db). No other app is needed.

What it does:
  - GET  /catalog              -> list products for sale
  - POST /checkout             -> sell a product (reduce stock + record the sale)
  - GET  /orders               -> every sale we've made, newest first
  - POST /products             -> add a new product to the catalog
  - POST /products/{id}/restock-> add more stock to an existing product

Run it with:   uvicorn main:app --reload --port 8001
Then open:     http://localhost:8001/docs   (a live page to test every endpoint)
"""

from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

from database import Product, Order, init_db, get_session

app = FastAPI(title="Store API")

# Allow the React frontend (on a different port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # fine for local learning; lock this down in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- What incoming data looks like ----
class CheckoutIn(BaseModel):
    product_id: int
    quantity: int = 1


class ProductIn(BaseModel):
    name: str
    price: float
    quantity: int = 0


class RestockIn(BaseModel):
    amount: int


# ---------------- Endpoints ----------------

@app.get("/catalog")
def catalog(session: Session = Depends(get_session)):
    """List every product in the shop."""
    return session.exec(select(Product).order_by(Product.id)).all()


@app.get("/orders")
def list_orders(session: Session = Depends(get_session)):
    """Return every sale this store has made, newest first."""
    return session.exec(select(Order).order_by(Order.id.desc())).all()


@app.post("/checkout")
def checkout(data: CheckoutIn, session: Session = Depends(get_session)):
    """
    Sell a product. This is the heart of the Store:
      1. Look the product up in our own database.
      2. Check there's enough stock, then reduce it.
      3. Record the sale in the orders table.
    """
    if data.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    # 1. Look up the product.
    product = session.get(Product, data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 2. Check stock, then reduce it.
    if product.quantity < data.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")
    product.quantity -= data.quantity
    session.add(product)

    # 3. Record the sale.
    order = Order(
        product_id=product.id,
        product_name=product.name,
        quantity=data.quantity,
        unit_price=product.price,
        total=round(product.price * data.quantity, 2),
        created_at=datetime.now().isoformat(timespec="seconds"),
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@app.post("/products")
def add_product(data: ProductIn, session: Session = Depends(get_session)):
    """Add a brand-new product to the catalog."""
    if data.price < 0 or data.quantity < 0:
        raise HTTPException(status_code=400, detail="Price and quantity cannot be negative")
    product = Product(name=data.name, price=data.price, quantity=data.quantity)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@app.post("/products/{product_id}/restock")
def restock(product_id: int, data: RestockIn, session: Session = Depends(get_session)):
    """Add more stock to an existing product."""
    if data.amount < 1:
        raise HTTPException(status_code=400, detail="Amount must be at least 1")
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.quantity += data.amount
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


# ---------------- Startup: create tables + seed demo products ----------------

init_db()
