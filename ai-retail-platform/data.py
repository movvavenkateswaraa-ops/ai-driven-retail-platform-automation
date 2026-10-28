"""Synthetic retail data: products, daily sales history and customer baskets."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

PRODUCTS = pd.DataFrame(
    [
        # id, name, category, price, cost, stock, lead_time_days, base_daily_demand
        (1, "Basmati Rice 5kg", "Grocery", 620.0, 480.0, 120, 3, 14),
        (2, "Sunflower Oil 1L", "Grocery", 160.0, 125.0, 60, 2, 20),
        (3, "Wireless Mouse", "Electronics", 799.0, 520.0, 25, 7, 4),
        (4, "USB-C Cable", "Electronics", 349.0, 180.0, 300, 5, 6),
        (5, "Cotton T-Shirt", "Apparel", 499.0, 260.0, 80, 6, 5),
        (6, "Running Shoes", "Apparel", 2499.0, 1500.0, 18, 10, 2),
        (7, "Green Tea 100g", "Grocery", 210.0, 140.0, 45, 2, 9),
        (8, "Notebook A4", "Stationery", 90.0, 55.0, 500, 4, 15),
    ],
    columns=["product_id", "name", "category", "price", "cost",
             "stock", "lead_time_days", "base_demand"],
)


def generate_sales(days: int = 120) -> pd.DataFrame:
    """Daily units sold per product with weekly seasonality, trend and noise."""
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days)
    rows = []
    for _, p in PRODUCTS.iterrows():
        for i, d in enumerate(dates):
            weekend_boost = 1.3 if d.dayofweek >= 5 else 1.0
            trend = 1 + 0.002 * i
            units = rng.poisson(p.base_demand * weekend_boost * trend)
            rows.append((d, int(p.product_id), int(units)))
    return pd.DataFrame(rows, columns=["date", "product_id", "units"])


def generate_baskets(n: int = 800) -> list[list[int]]:
    """Customer baskets with a few built-in affinities (e.g. rice + oil)."""
    affinities = {1: [2, 7], 3: [4], 5: [6], 8: [3]}
    ids = PRODUCTS.product_id.tolist()
    baskets = []
    for _ in range(n):
        first = int(rng.choice(ids))
        basket = {first}
        for other in affinities.get(first, []):
            if rng.random() < 0.6:
                basket.add(other)
        if rng.random() < 0.3:
            basket.add(int(rng.choice(ids)))
        baskets.append(sorted(basket))
    return baskets
