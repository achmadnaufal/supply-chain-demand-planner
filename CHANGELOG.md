# Changelog

## [1.3.0] - 2026-03-15

### Added
- **Stockout Risk Assessor** — `calculate_stockout_risk()`: Scores each SKU 0–100 for stockout probability using days-of-supply, lead time, demand variability (CoV), and safety stock gap; outputs risk band and recommended action
- **Unit Tests** — 8 new tests in `tests/test_stockout_risk.py` covering high/low risk scenarios, sorting order, and validation
- **README** — Added stockout risk usage example

## [1.2.0] - 2026-03-06

### Added
- Add demand forecast accuracy metrics
- Enhanced README with getting started guide
- Comprehensive unit tests for core functions
- Real-world sample data and fixtures

### Improved
- Edge case handling for null/empty inputs
- Boundary condition validation

### Fixed
- Various edge cases and corner scenarios

---
