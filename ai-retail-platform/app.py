"""Flask API + tiny dashboard for the AI-Driven Retail Platform Automation project."""
from flask import Flask, jsonify, request, render_template_string

from engine import RetailEngine

app = Flask(__name__)
engine = RetailEngine()

DASHBOARD = """
<!doctype html>
<title>AI Retail Platform</title>
<style>
  body{font-family:system-ui,sans-serif;margin:2rem auto;max-width:960px;padding:0 1rem;color:#222}
  h1{margin-bottom:0} section{margin:2rem 0}
  table{border-collapse:collapse;width:100%} th,td{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left}
  button{padding:8px 14px;border:0;border-radius:6px;background:#2563eb;color:#fff;cursor:pointer}
  .low{color:#b91c1c;font-weight:600}
</style>
<h1>AI-Driven Retail Platform</h1>
<p>Forecasting, auto-replenishment, dynamic pricing and recommendations.</p>

<section><h2>Inventory</h2><table id="inv"></table></section>
<section><h2>Dynamic pricing</h2><table id="price"></table></section>
<section>
  <h2>Automated restocking</h2>
  <button onclick="runAuto()">Run automation</button>
  <table id="po"></table>
</section>

<script>
const rows = (id, cols, data, cls) => {
  const t = document.getElementById(id);
  t.innerHTML = '<tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr>' +
    data.map(r => '<tr>' + cols.map(c => `<td>${r[c] ?? ''}</td>`).join('') + '</tr>').join('');
};
async function load(){
  rows('inv', ['product_id','name','category','price','stock','lead_time_days'], await (await fetch('/api/inventory')).json());
  rows('price', ['name','stock','days_of_cover','current_price','suggested_price','reason'], await (await fetch('/api/pricing')).json());
}
async function runAuto(){
  const r = await (await fetch('/api/automate', {method:'POST'})).json();
  rows('po', ['po_id','name','stock','reorder_point','order_qty','status'], r.purchase_orders);
  load();
}
load();
</script>
"""


@app.get("/")
def home():
    return render_template_string(DASHBOARD)


@app.get("/api/inventory")
def inventory():
    return jsonify(engine.inventory())


@app.get("/api/forecast/<int:pid>")
def forecast(pid):
    if pid not in engine.products.index:
        return jsonify(error="unknown product"), 404
    horizon = request.args.get("days", 14, type=int)
    return jsonify(engine.forecast(pid, horizon).to_dict(orient="records"))


@app.get("/api/reorders")
def reorders():
    return jsonify(engine.reorder_suggestions())


@app.post("/api/automate")
def automate():
    return jsonify(purchase_orders=engine.run_automation())


@app.get("/api/purchase-orders")
def purchase_orders():
    return jsonify(engine.purchase_orders)


@app.post("/api/purchase-orders/<int:po_id>/receive")
def receive(po_id):
    for po in engine.purchase_orders:
        if po["po_id"] == po_id and po["status"] == "PLACED":
            engine.receive_stock(po["product_id"], po["order_qty"])
            po["status"] = "RECEIVED"
            return jsonify(po)
    return jsonify(error="PO not found or already received"), 404


@app.get("/api/pricing")
def pricing():
    return jsonify(engine.pricing_suggestions())


@app.get("/api/recommend/<int:pid>")
def recommend(pid):
    if pid not in engine.products.index:
        return jsonify(error="unknown product"), 404
    return jsonify(engine.recommend(pid))


@app.post("/api/sale")
def sale():
    body = request.get_json(force=True)
    pid, qty = int(body["product_id"]), int(body.get("qty", 1))
    if pid not in engine.products.index:
        return jsonify(error="unknown product"), 404
    if not engine.record_sale(pid, qty):
        return jsonify(error="insufficient stock"), 409
    return jsonify(ok=True, stock=int(engine.products.loc[pid, "stock"]))


if __name__ == "__main__":
    app.run(debug=True)
