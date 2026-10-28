"""AI engine: demand forecasting, auto-reorder, dynamic pricing, recommendations."""
from collections import defaultdict
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

import data


class RetailEngine:
    def __init__(self):
        self.products = data.PRODUCTS.copy().set_index("product_id")
        self.sales = data.generate_sales()
        self.baskets = data.generate_baskets()
        self.purchase_orders: list[dict] = []
        self._build_recommender()

    # ---------------- Demand forecasting ----------------
    @staticmethod
    def _features(dates: pd.DatetimeIndex, start: pd.Timestamp) -> np.ndarray:
        t = (dates - start).days.values.reshape(-1, 1)
        dow = np.eye(7)[dates.dayofweek.values]  # day-of-week one-hot
        return np.hstack([t, dow])

    def forecast(self, product_id: int, horizon: int = 14) -> pd.DataFrame:
        hist = self.sales[self.sales.product_id == product_id].sort_values("date")
        start = hist.date.min()
        model = Ridge(alpha=1.0).fit(self._features(pd.DatetimeIndex(hist.date), start),
                                     hist.units.values)
        future = pd.date_range(hist.date.max() + pd.Timedelta(days=1), periods=horizon)
        pred = np.clip(model.predict(self._features(future, start)), 0, None)
        return pd.DataFrame({"date": future.strftime("%Y-%m-%d"),
                             "predicted_units": pred.round(1)})

    # ---------------- Automated replenishment ----------------
    def reorder_suggestions(self, cover_days: int = 14, safety_days: int = 2) -> list[dict]:
        out = []
        for pid, p in self.products.iterrows():
            fc = self.forecast(pid, horizon=cover_days + int(p.lead_time_days))
            daily = fc.predicted_units.mean()
            reorder_point = daily * (p.lead_time_days + safety_days)
            if p.stock <= reorder_point:
                target = fc.predicted_units.sum() + daily * safety_days
                qty = int(np.ceil(max(target - p.stock, 0)))
                out.append({"product_id": int(pid), "name": p["name"], "stock": int(p.stock),
                            "avg_daily_demand": round(float(daily), 1),
                            "reorder_point": round(float(reorder_point), 1),
                            "order_qty": qty})
        return out

    def run_automation(self) -> list[dict]:
        """Create purchase orders for everything below its reorder point."""
        placed = []
        for s in self.reorder_suggestions():
            po = {"po_id": len(self.purchase_orders) + 1, **s,
                  "created": pd.Timestamp.now().isoformat(timespec="seconds"),
                  "status": "PLACED"}
            self.purchase_orders.append(po)
            placed.append(po)
        return placed

    def receive_stock(self, product_id: int, qty: int):
        self.products.loc[product_id, "stock"] += qty

    def record_sale(self, product_id: int, qty: int) -> bool:
        if self.products.loc[product_id, "stock"] < qty:
            return False
        self.products.loc[product_id, "stock"] -= qty
        return True

    # ---------------- Dynamic pricing ----------------
    def pricing_suggestions(self) -> list[dict]:
        out = []
        for pid, p in self.products.iterrows():
            daily = self.forecast(pid, 14).predicted_units.mean()
            days_cover = p.stock / daily if daily > 0 else 999
            if days_cover > 30:
                factor, reason = 0.90, "Overstocked: discount 10% to clear stock"
            elif days_cover < 5:
                factor, reason = 1.05, "Low stock: raise price 5%"
            else:
                factor, reason = 1.0, "Healthy stock: keep price"
            new_price = max(round(p.price * factor, 2), round(p.cost * 1.05, 2))  # margin floor
            out.append({"product_id": int(pid), "name": p["name"], "stock": int(p.stock),
                        "days_of_cover": round(float(days_cover), 1),
                        "current_price": p.price, "suggested_price": new_price,
                        "reason": reason})
        return out

    # ---------------- Recommendations ----------------
    def _build_recommender(self):
        self.pair_counts = defaultdict(int)
        self.item_counts = defaultdict(int)
        for b in self.baskets:
            for i in b:
                self.item_counts[i] += 1
            for a, c in combinations(b, 2):
                self.pair_counts[(a, c)] += 1
                self.pair_counts[(c, a)] += 1

    def recommend(self, product_id: int, k: int = 3) -> list[dict]:
        scores = []
        for other in self.products.index:
            if other == product_id:
                continue
            both = self.pair_counts.get((product_id, other), 0)
            if both:
                # confidence-style score, dampened by item popularity (lift-like)
                score = both / self.item_counts[product_id] / (self.item_counts[other] / len(self.baskets))
                scores.append((other, score))
        scores.sort(key=lambda x: -x[1])
        return [{"product_id": int(i), "name": self.products.loc[i, "name"],
                 "score": round(float(s), 2)} for i, s in scores[:k]]

    def inventory(self) -> list[dict]:
        df = self.products.reset_index()
        return df.to_dict(orient="records")
