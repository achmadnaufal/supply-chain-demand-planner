# Supply Chain Demand Planner

Demand forecasting and inventory planning for NbS project supply chains and pharma distribution.

## Features
- **Moving average forecast**: trend-adjusted with confidence bounds per SKU
- **Safety stock**: Z-score based with configurable service level (95% default)
- **Reorder point**: demand × lead_time + safety stock
- **NbS sample data**: tree planting supply chain (seeds, fertilizer, tools)

## Quick Start

```python
from src.main import DemandPlanner

planner = DemandPlanner(config={
    "ma_window": 3,
    "service_level_z": 1.65,  # 95% service level
    "lead_time_periods": 2,
})

df = planner.load_data("sample_data/demand_history.csv")
planner.validate(df)

# 3-period demand forecast
forecast = planner.demand_forecast(df, periods_ahead=3)
print(forecast[["sku_id", "forecast_period", "forecast_qty", "lower_bound", "upper_bound"]])

# Safety stock and reorder points
stock = planner.safety_stock_analysis(df)
print(stock[["sku_id", "safety_stock", "reorder_point", "recommended_order_qty"]])
```

## Running Tests
```bash
pytest tests/ -v
```
