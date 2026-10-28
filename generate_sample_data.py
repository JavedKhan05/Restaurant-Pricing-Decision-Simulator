"""Regenerate the explicitly synthetic demonstration dataset. No external data is used."""
from datetime import date, timedelta
import math
import random
from pathlib import Path
import pandas as pd

random.seed(23)
stores = [
    ("S001", "City Centre", 1.15),
    ("S002", "Residential North", 0.95),
    ("S003", "Transit Hub", 1.28),
    ("S004", "University District", 1.05),
]
products = [
    ("P001", "Classic Burger", 220.0, 105.0, 2.0),
    ("P002", "Veggie Wrap", 160.0, 72.0, 1.5),
    ("P003", "Cold Coffee", 130.0, 48.0, 2.4),
]
start = date(2026, 1, 1)
rows = []
for day_idx in range(120):
    d = start + timedelta(days=day_idx)
    weekend = d.weekday() >= 5
    seasonal = 1 + 0.10 * math.sin(day_idx / 11.0)
    for sid, sname, store_factor in stores:
        for pid, pname, price, cost, base in products:
            promo = (day_idx % 17 in (0, 1)) and (pid != "P003")
            disc = 10.0 if promo else (5.0 if (day_idx % 29 == 0 and pid == "P003") else 0.0)
            effective = price * (1 - disc / 100)
            competitor = price * (0.95 + (int(sid[-1]) * 0.018))
            expected = 38 * base * store_factor * seasonal * (1.18 if weekend else 1.0) * (1.15 if promo else 1.0)
            units = max(0, int(round(expected + random.gauss(0, max(2, expected * 0.10)))))
            rows.append({
                "date": d.isoformat(), "store_id": sid, "store_name": sname,
                "product_id": pid, "product_name": pname, "list_price": round(price, 2),
                "discount_pct": disc, "effective_price": round(effective, 2),
                "units_sold": units, "unit_variable_cost": round(cost, 2),
                "competitor_price": round(competitor, 2), "promotion_flag": int(promo or disc > 0),
                "day_of_week": d.strftime("%A"), "weekend_flag": int(weekend),
                "data_type": "SYNTHETIC_DEMO_ONLY"
            })

out = Path(__file__).with_name("synthetic_sales.csv")
pd.DataFrame(rows).to_csv(out, index=False)
print(f"Wrote {len(rows)} synthetic rows to {out}")
