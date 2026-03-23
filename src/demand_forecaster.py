"""
Demand Forecasting Module for Pharmaceutical Supply Chain Planning.

Implements three statistical forecasting methods commonly used in pharma supply:

1. **Simple Moving Average (SMA)** — baseline, trend-insensitive
2. **Exponential Smoothing (ES / Holt's method)** — handles level + trend
3. **Seasonal Adjusted Forecast (SAS)** — decomposes seasonal patterns

These methods are designed for short-to-medium horizon forecasting of drug
sales volumes (units/packs) at SKU or market level, consistent with S&OP
(Sales and Operations Planning) processes in pharmaceutical companies.

Author: github.com/achmadnaufal
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple


def _validate_series(series: List[float], min_len: int = 2, name: str = "series") -> None:
    """Validate a time series input."""
    if not isinstance(series, list):
        raise TypeError(f"{name} must be a list, got {type(series).__name__}")
    if len(series) < min_len:
        raise ValueError(f"{name} must have at least {min_len} data points, got {len(series)}")
    if any(v < 0 for v in series):
        raise ValueError(f"{name} contains negative values — demand must be non-negative")


class SimpleMovingAverage:
    """
    Simple Moving Average (SMA) demand forecaster.

    Computes a rolling average over the last ``window`` periods as the
    forecast for the next period. Simple but effective as a naive baseline.

    Attributes:
        window (int): Number of periods used in each average calculation.
        history (list[float]): Historical demand series.
        sku (str): SKU identifier (informational).

    Example::

        sma = SimpleMovingAverage(window=3, sku="OSIMER-30MG-PK30")
        sma.fit([120, 135, 128, 142, 138, 150, 145, 162])
        print(sma.forecast(periods=3))
        # [152.3, 152.3, 152.3]  (constant SMA for 3 forward periods)
    """

    def __init__(self, window: int = 3, sku: str = "SKU") -> None:
        """
        Initialize SMA forecaster.

        Args:
            window: Look-back window in periods. Must be >= 1.
            sku: SKU code (for labelling only).

        Raises:
            ValueError: If window < 1.
        """
        if window < 1:
            raise ValueError("window must be >= 1")
        self.window = window
        self.sku = sku
        self.history: List[float] = []

    def fit(self, demand_series: List[float]) -> "SimpleMovingAverage":
        """
        Load historical demand for this SKU.

        Args:
            demand_series: Ordered list of observed demand values (most recent last).

        Returns:
            self (for chaining).

        Raises:
            ValueError: If series has fewer than ``window`` observations.
        """
        _validate_series(demand_series, min_len=self.window, name="demand_series")
        self.history = list(demand_series)
        return self

    def current_average(self) -> float:
        """Return the SMA of the last ``window`` periods."""
        if len(self.history) < self.window:
            raise RuntimeError("Call fit() with enough data before forecasting.")
        return round(sum(self.history[-self.window:]) / self.window, 2)

    def forecast(self, periods: int = 1) -> List[float]:
        """
        Generate ``periods`` forward forecasts.

        SMA forecasts are constant for all forward periods (no trend extrapolation).

        Args:
            periods: Number of periods to forecast ahead.

        Returns:
            List of forecasted demand values (all identical to current SMA).
        """
        if periods < 1:
            raise ValueError("periods must be >= 1")
        avg = self.current_average()
        return [avg] * periods

    def mae(self, actuals: List[float]) -> float:
        """
        Calculate Mean Absolute Error against a validation series.

        Args:
            actuals: Observed actuals to compare against SMA forecasts.

        Returns:
            Mean Absolute Error.
        """
        _validate_series(actuals, min_len=1, name="actuals")
        errors = [abs(self.current_average() - a) for a in actuals]
        return round(sum(errors) / len(errors), 3)

    def __repr__(self) -> str:
        return f"SimpleMovingAverage(sku={self.sku!r}, window={self.window}, n={len(self.history)})"


class ExponentialSmoothing:
    """
    Double Exponential Smoothing (Holt's Method) for trend-aware forecasting.

    Suitable for demand series with a clear upward or downward trend.
    Applies two smoothing parameters: alpha (level) and beta (trend).

    Attributes:
        alpha (float): Level smoothing parameter (0 < alpha < 1).
        beta (float): Trend smoothing parameter (0 < beta < 1).
        sku (str): SKU identifier.
        level_ (float): Last estimated level (set after fit).
        trend_ (float): Last estimated trend (set after fit).

    Example::

        es = ExponentialSmoothing(alpha=0.3, beta=0.1, sku="GEFITINIB-250MG")
        es.fit([200, 215, 230, 225, 245, 260, 255, 275])
        print(es.forecast(periods=4))
        print(f"MAPE: {es.mape([280, 285, 290, 295]):.1f}%")
    """

    def __init__(
        self, alpha: float = 0.2, beta: float = 0.1, sku: str = "SKU"
    ) -> None:
        """
        Initialize Holt's double exponential smoother.

        Args:
            alpha: Level smoothing factor. Higher = more weight on recent data.
            beta: Trend smoothing factor. Higher = faster trend adaptation.
            sku: SKU label.

        Raises:
            ValueError: If alpha or beta are not in (0, 1).
        """
        if not (0 < alpha < 1):
            raise ValueError("alpha must be in (0, 1)")
        if not (0 < beta < 1):
            raise ValueError("beta must be in (0, 1)")
        self.alpha = alpha
        self.beta = beta
        self.sku = sku
        self.level_: Optional[float] = None
        self.trend_: Optional[float] = None
        self.history: List[float] = []
        self.fitted_: List[float] = []

    def fit(self, demand_series: List[float]) -> "ExponentialSmoothing":
        """
        Fit the model on historical demand.

        Args:
            demand_series: At least 2 observations (oldest → newest).

        Returns:
            self (for chaining).
        """
        _validate_series(demand_series, min_len=2, name="demand_series")
        self.history = list(demand_series)

        # Initialise level and trend
        level = demand_series[0]
        trend = demand_series[1] - demand_series[0]
        fitted = []

        for obs in demand_series:
            prev_level = level
            level = self.alpha * obs + (1 - self.alpha) * (level + trend)
            trend = self.beta * (level - prev_level) + (1 - self.beta) * trend
            fitted.append(round(level + trend, 3))

        self.level_ = level
        self.trend_ = trend
        self.fitted_ = fitted
        return self

    def forecast(self, periods: int = 1) -> List[float]:
        """
        Generate forward demand forecasts.

        Args:
            periods: Number of periods ahead to forecast.

        Returns:
            List of forecasted values (with trend extrapolation).

        Raises:
            RuntimeError: If ``fit()`` has not been called.
        """
        if self.level_ is None:
            raise RuntimeError("Call fit() before forecast().")
        if periods < 1:
            raise ValueError("periods must be >= 1")
        return [
            round(max(0.0, self.level_ + h * self.trend_), 2)
            for h in range(1, periods + 1)
        ]

    def mape(self, actuals: List[float]) -> float:
        """
        Mean Absolute Percentage Error against validation actuals.

        Args:
            actuals: Observed values for the forecast horizon.

        Returns:
            MAPE as percentage (0–100). Returns nan if any actual is 0.
        """
        _validate_series(actuals, min_len=1, name="actuals")
        forecasts = self.forecast(len(actuals))
        pct_errors = []
        for f, a in zip(forecasts, actuals):
            if a == 0:
                return float("nan")
            pct_errors.append(abs(f - a) / a * 100)
        return round(sum(pct_errors) / len(pct_errors), 2)

    def __repr__(self) -> str:
        return (
            f"ExponentialSmoothing(sku={self.sku!r}, alpha={self.alpha}, "
            f"beta={self.beta}, level={self.level_}, trend={self.trend_})"
        )


class SafetyStockCalculator:
    """
    Calculate safety stock levels for pharmaceutical SKUs.

    Safety stock protects against demand variability and supply uncertainty.
    Uses the standard safety stock formula:

        SS = Z * σ_demand * √(lead_time)

    where Z is the service level z-score.

    Example::

        ss_calc = SafetyStockCalculator()
        result = ss_calc.calculate(
            demand_series=[120, 135, 128, 142, 138, 150],
            lead_time_days=14,
            service_level_pct=95.0,
            review_period_days=7,
        )
        print(f"Safety stock: {result['safety_stock_units']} units")
        print(f"Reorder point: {result['reorder_point_units']} units")
    """

    # Standard Normal z-scores for common service levels
    Z_SCORES = {
        90.0: 1.282,
        95.0: 1.645,
        97.0: 1.881,
        98.0: 2.054,
        99.0: 2.326,
        99.5: 2.576,
    }

    def calculate(
        self,
        demand_series: List[float],
        lead_time_days: int,
        service_level_pct: float = 95.0,
        review_period_days: int = 7,
    ) -> Dict:
        """
        Calculate safety stock and reorder point.

        Args:
            demand_series: Historical daily demand observations.
            lead_time_days: Supplier lead time in days.
            service_level_pct: Target service level (fill rate). Must be one of
                ``{90, 95, 97, 98, 99, 99.5}``.
            review_period_days: Inventory review cycle length in days.

        Returns:
            dict with:

            - ``avg_daily_demand`` – mean daily demand
            - ``demand_std`` – standard deviation of demand
            - ``z_score`` – z-score for target service level
            - ``safety_stock_units`` – calculated safety stock (ceiling)
            - ``reorder_point_units`` – reorder point = avg_demand_during_LT + SS
            - ``service_level_pct`` – target service level used

        Raises:
            ValueError: If service_level_pct is not a supported value or
                lead_time_days <= 0.
        """
        _validate_series(demand_series, min_len=2, name="demand_series")
        if service_level_pct not in self.Z_SCORES:
            raise ValueError(
                f"service_level_pct must be one of {sorted(self.Z_SCORES)}. "
                f"Got {service_level_pct}"
            )
        if lead_time_days <= 0:
            raise ValueError("lead_time_days must be > 0")

        n = len(demand_series)
        mean = sum(demand_series) / n
        variance = sum((x - mean) ** 2 for x in demand_series) / n
        std = math.sqrt(variance)

        z = self.Z_SCORES[service_level_pct]
        # Safety stock during lead time + review period
        cycle_days = lead_time_days + review_period_days
        safety_stock = z * std * math.sqrt(cycle_days)
        avg_during_lt = mean * lead_time_days
        reorder_point = avg_during_lt + safety_stock

        return {
            "avg_daily_demand": round(mean, 2),
            "demand_std": round(std, 3),
            "z_score": z,
            "safety_stock_units": math.ceil(safety_stock),
            "reorder_point_units": math.ceil(reorder_point),
            "service_level_pct": service_level_pct,
        }
