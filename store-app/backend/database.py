"""
Database setup for the STORE app.

Everything lives in ONE SQLite file (store.db) right next to this script.
Two tables:
  - Product : the catalog + how much stock is left   (what we sell)
  - Order   : a record of every sale                 (the receipt)

SQLite is the simplest possible database: just a single file, no server to
install. `echo=True` prints every SQL command so you can watch it work.
"""

import os

from sqlalchemy import event
from sqlmodel import SQLModel, Field, create_engine, Session, select


# ---- One row in the "product" table ----
class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # auto-numbered
    name: str          # product name, e.g. "Coffee Mug"
    price: float       # price per unit
    quantity: int      # how many are in stock right now


# ---- One row in the "order" table ----
class Order(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # auto-numbered
    product_id: int        # which product was sold
    product_name: str      # copied in so the receipt reads nicely on its own
    quantity: int          # how many units were sold
    unit_price: float      # the price at the moment of sale
    total: float           # quantity * unit_price
    created_at: str        # when the sale happened (ISO text)


# The database file. Locally it's store.db right next to this script.
# In Docker we set STORE_DB_DIR=/app/data (a mounted volume) so the data
# survives restarts and redeploys instead of being baked into the image.
_db_dir = os.getenv("STORE_DB_DIR")
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)
    _db_path = os.path.join(_db_dir, "store.db")
else:
    _db_path = "store.db"

engine = create_engine(
    f"sqlite:///{_db_path}",
    echo=True,
    connect_args={"check_same_thread": False, "timeout": 30},
)


@event.listens_for(engine, "connect")
def _sqlite_settings(dbapi_connection, _record):
    """WAL mode so reads never block a write — fixes 'database is locked'."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


def init_db() -> None:
    """Create the tables, then add a few starter products if the shop is empty."""
    SQLModel.metadata.create_all(engine)
    _seed_products()


def _seed_products() -> None:
    """Put some demo products in the catalog the very first time we run."""
    with Session(engine) as session:
        already = session.exec(select(Product)).first()
        if already:
            return  # already have products, don't add duplicates
        starter = [
            Product(name="Coffee Mug", price=8.50, quantity=25),
            Product(name="Notebook", price=4.00, quantity=40),
            Product(name="Ballpoint Pen", price=1.50, quantity=100),
            Product(name="Water Bottle", price=12.00, quantity=15),
            Product(name="Backpack", price=45.00, quantity=8),
        ]
        session.add_all(starter)
        session.commit()


def get_session():
    """Hand a short-lived database connection to each request."""
    with Session(engine) as session:
        yield session
