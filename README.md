# Supply Chain Demand Planner

Demand planning and inventory optimization tools for pharma supply chains

## Features
- Data ingestion from CSV/Excel input files
- Automated analysis and KPI calculation
- Summary statistics and trend reporting
- Sample data generator for testing and development

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from src.main import DemandPlanner

analyzer = DemandPlanner()
df = analyzer.load_data("data/sample.csv")
result = analyzer.analyze(df)
print(result)
```

## Data Format

Expected CSV columns: `sku, month, actuals_units, forecast_units, safety_stock, reorder_point, fill_rate_pct`

## Project Structure

```
supply-chain-demand-planner/
├── src/
│   ├── main.py          # Core analysis logic
│   └── data_generator.py # Sample data generator
├── data/                # Data directory (gitignored for real data)
├── examples/            # Usage examples
├── requirements.txt
└── README.md
```

## License

MIT License — free to use, modify, and distribute.

## 🚀 New Features (2026-03-02)
- Add demand sensing ML integration and S&OP templates
- Enhanced error handling and edge case coverage
- Comprehensive unit tests and integration examples
