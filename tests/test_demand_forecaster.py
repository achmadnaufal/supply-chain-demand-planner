"""Unit tests for demand forecasting module."""
import math
import pytest
from src.demand_forecaster import (
    SimpleMovingAverage, ExponentialSmoothing, SafetyStockCalculator, _validate_series
)

SERIES_8 = [120.0, 135.0, 128.0, 142.0, 138.0, 150.0, 145.0, 162.0]
TREND_SERIES = [200.0, 215.0, 230.0, 225.0, 245.0, 260.0, 255.0, 275.0]


# --- _validate_series ---

def test_validate_non_list():
    with pytest.raises(TypeError):
        _validate_series((1, 2, 3))

def test_validate_too_short():
    with pytest.raises(ValueError, match="at least 3"):
        _validate_series([1.0, 2.0], min_len=3)

def test_validate_negative():
    with pytest.raises(ValueError, match="negative"):
        _validate_series([10.0, -5.0, 8.0])


# --- SMA ---

class TestSimpleMovingAverage:
    def test_window_1_invalid(self):
        # window=1 is valid, window=0 is not
        with pytest.raises(ValueError):
            SimpleMovingAverage(window=0)

    def test_fit_requires_enough_data(self):
        sma = SimpleMovingAverage(window=5)
        with pytest.raises(ValueError):
            sma.fit([1.0, 2.0, 3.0])

    def test_current_average_window3(self):
        sma = SimpleMovingAverage(window=3)
        sma.fit(SERIES_8)
        # last 3: [150, 145, 162] → mean = 152.33
        assert abs(sma.current_average() - 152.33) < 0.01

    def test_forecast_length(self):
        sma = SimpleMovingAverage(window=3)
        sma.fit(SERIES_8)
        assert len(sma.forecast(5)) == 5

    def test_forecast_constant(self):
        sma = SimpleMovingAverage(window=3)
        sma.fit(SERIES_8)
        forecasts = sma.forecast(4)
        # All forecasts should be equal (SMA is constant)
        assert len(set(forecasts)) == 1

    def test_forecast_invalid_periods(self):
        sma = SimpleMovingAverage(window=3)
        sma.fit(SERIES_8)
        with pytest.raises(ValueError):
            sma.forecast(0)

    def test_mae_positive(self):
        sma = SimpleMovingAverage(window=3)
        sma.fit(SERIES_8)
        mae = sma.mae([155.0, 165.0, 170.0])
        assert mae >= 0

    def test_repr(self):
        sma = SimpleMovingAverage(window=4, sku="DRUG-A")
        sma.fit(SERIES_8)
        assert "DRUG-A" in repr(sma)


# --- Exponential Smoothing ---

class TestExponentialSmoothing:
    def test_invalid_alpha(self):
        with pytest.raises(ValueError, match="alpha"):
            ExponentialSmoothing(alpha=1.5)

    def test_invalid_beta(self):
        with pytest.raises(ValueError, match="beta"):
            ExponentialSmoothing(beta=0.0)

    def test_fit_sets_level_and_trend(self):
        es = ExponentialSmoothing(alpha=0.3, beta=0.1)
        es.fit(TREND_SERIES)
        assert es.level_ is not None
        assert es.trend_ is not None

    def test_trend_is_positive_for_upward_series(self):
        es = ExponentialSmoothing(alpha=0.4, beta=0.2)
        es.fit(TREND_SERIES)
        assert es.trend_ > 0

    def test_forecast_length(self):
        es = ExponentialSmoothing(alpha=0.3, beta=0.1)
        es.fit(TREND_SERIES)
        assert len(es.forecast(6)) == 6

    def test_forecast_increasing_with_positive_trend(self):
        es = ExponentialSmoothing(alpha=0.4, beta=0.2)
        es.fit(TREND_SERIES)
        forecasts = es.forecast(4)
        assert forecasts[3] > forecasts[0]

    def test_forecast_non_negative(self):
        # Even with declining series, forecasts shouldn't go below 0
        es = ExponentialSmoothing(alpha=0.5, beta=0.1)
        es.fit([100.0, 50.0, 10.0, 5.0, 2.0])
        for f in es.forecast(5):
            assert f >= 0

    def test_forecast_without_fit_raises(self):
        es = ExponentialSmoothing()
        with pytest.raises(RuntimeError, match="fit"):
            es.forecast(3)

    def test_forecast_invalid_periods(self):
        es = ExponentialSmoothing()
        es.fit(TREND_SERIES)
        with pytest.raises(ValueError):
            es.forecast(0)

    def test_mape_reasonable(self):
        es = ExponentialSmoothing(alpha=0.3, beta=0.1)
        es.fit(TREND_SERIES)
        mape = es.mape([280.0, 285.0, 290.0])
        assert 0 <= mape < 50  # should be reasonably close

    def test_mape_with_zero_actual_returns_nan(self):
        es = ExponentialSmoothing()
        es.fit([100.0, 110.0, 120.0])
        result = es.mape([0.0])
        assert math.isnan(result)

    def test_repr(self):
        es = ExponentialSmoothing(alpha=0.3, beta=0.1, sku="GEFITINIB")
        es.fit(TREND_SERIES)
        assert "GEFITINIB" in repr(es)


# --- Safety Stock Calculator ---

class TestSafetyStockCalculator:
    def test_basic_calculation(self):
        calc = SafetyStockCalculator()
        result = calc.calculate(
            demand_series=[100.0, 110.0, 95.0, 120.0, 105.0, 115.0],
            lead_time_days=7,
            service_level_pct=95.0,
        )
        assert result["safety_stock_units"] > 0
        assert result["reorder_point_units"] >= result["safety_stock_units"]

    def test_higher_service_level_more_ss(self):
        calc = SafetyStockCalculator()
        series = [100.0, 120.0, 95.0, 130.0, 105.0, 118.0, 108.0]
        r95 = calc.calculate(series, lead_time_days=7, service_level_pct=95.0)
        r99 = calc.calculate(series, lead_time_days=7, service_level_pct=99.0)
        assert r99["safety_stock_units"] > r95["safety_stock_units"]

    def test_longer_lead_time_more_reorder_point(self):
        calc = SafetyStockCalculator()
        series = [100.0] * 10
        r7 = calc.calculate(series, lead_time_days=7)
        r14 = calc.calculate(series, lead_time_days=14)
        assert r14["reorder_point_units"] > r7["reorder_point_units"]

    def test_invalid_service_level(self):
        calc = SafetyStockCalculator()
        with pytest.raises(ValueError, match="service_level_pct"):
            calc.calculate([100.0, 110.0], lead_time_days=7, service_level_pct=93.0)

    def test_invalid_lead_time(self):
        calc = SafetyStockCalculator()
        with pytest.raises(ValueError, match="lead_time_days"):
            calc.calculate([100.0, 110.0], lead_time_days=0)

    def test_constant_demand_low_ss(self):
        # Zero variance → very low safety stock
        calc = SafetyStockCalculator()
        result = calc.calculate([100.0] * 10, lead_time_days=7)
        assert result["safety_stock_units"] == 0  # std=0

    def test_result_keys(self):
        calc = SafetyStockCalculator()
        result = calc.calculate([100.0, 110.0, 95.0], lead_time_days=7)
        for key in ["avg_daily_demand", "demand_std", "z_score",
                    "safety_stock_units", "reorder_point_units"]:
            assert key in result
