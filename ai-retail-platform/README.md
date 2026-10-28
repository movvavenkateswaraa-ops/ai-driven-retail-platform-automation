# AI-Driven Retail Platform Automation

A simple base project showing how AI can automate core retail operations.

## Features
| Module | What it does | Method |
|---|---|---|
| Demand forecasting | Predicts daily units per product | Ridge regression (trend + day-of-week) |
| Auto-replenishment | Raises purchase orders when stock hits the reorder point | Forecast x lead time + safety stock |
| Dynamic pricing | Suggests discounts/increases from days-of-cover | Rule-based, with a margin floor |
| Recommendations | "Frequently bought together" | Basket co-occurrence / lift |

Data is synthetic (see `data.py`); swap in your own sales and inventory tables.

## Run
```bash
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000 for the dashboard.

## API
- `GET  /api/inventory`
- `GET  /api/forecast/<product_id>?days=14`
- `GET  /api/reorders` : suggestions only
- `POST /api/automate` : creates purchase orders
- `GET  /api/purchase-orders`
- `POST /api/purchase-orders/<id>/receive` : adds stock
- `GET  /api/pricing`
- `GET  /api/recommend/<product_id>`
- `POST /api/sale` with `{"product_id": 1, "qty": 2}`

## Structure
```
app.py            Flask API + dashboard
engine.py         Forecasting, reorder, pricing, recommender
data.py           Synthetic data generator
requirements.txt
```

## Ideas to extend
Replace Ridge with Prophet/XGBoost, add a database (SQLite/Postgres), authentication, supplier integrations, and an LLM chat assistant for store managers.
