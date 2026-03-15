# supply-chain-demand-planner

**Domain:** Utility

## Features
- Add demand forecast accuracy metrics
- Comprehensive documentation and examples

## Getting Started

### Installation
```bash
pip install -r requirements.txt
```

### Quick Example
```python
# See examples/ directory for complete examples
```

## Configuration
Detailed configuration options in `config/` directory.

## Testing
```bash
pytest tests/ -v
```

## Edge Cases Handled
- Null/empty input validation
- Boundary condition testing
- Type safety checks

## Contributing
See CONTRIBUTING.md for guidelines.

## License
MIT


## Usage Examples

### Stockout Risk Assessment

```python
from src.main import SupplyChainDemandPlanner
import pandas as pd

planner = SupplyChainDemandPlanner(lead_time=14, z_score=1.65)

demand_data = pd.read_csv("data/demand_history.csv")
# Columns: sku, demand_qty, current_stock

risks = planner.calculate_stockout_risk(demand_data)
print(risks[["sku", "days_of_supply", "stockout_risk_score", "risk_band", "recommended_action"]])
#    sku  days_of_supply  stockout_risk_score risk_band                   recommended_action
# 0  SKU-B         0.7             88.5   Critical      Expedite order immediately
# 1  SKU-A        50.0             12.0      Low         Monitor per standard schedule
```
