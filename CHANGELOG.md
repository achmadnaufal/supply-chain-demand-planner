# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.2.0] - 2026-03-04
### Added
- `demand_forecast()`: moving average + trend forecasting with confidence bounds per SKU
- `safety_stock_analysis()`: Z-score safety stock and reorder point calculation
- NbS project supply chain sample data (seeds, fertilizer, planting tools)
- 13 unit tests covering forecast accuracy, safety stock math, and edge cases
### Fixed
- `validate()` checks for sku_id and demand_qty columns
- Forecast lower bound clamped at 0 (no negative demand)
## [1.1.0] - 2026-03-02
### Added
- Add demand sensing ML integration and S&OP templates
- Improved unit test coverage
- Enhanced documentation with realistic examples
