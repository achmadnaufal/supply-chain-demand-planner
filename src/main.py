"""
Supply chain demand planning for pharmaceutical and NbS project supply chains.

Provides demand forecasting using moving averages, trend detection, safety stock
calculation, and reorder point analysis for inventory planning.

Author: github.com/achmadnaufal
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List


class DemandPlanner:
    """
    Supply chain demand planning and forecasting.

    Supports moving average forecasting, trend analysis, safety stock
    calculation, and inventory replenishment recommendations.

    Args:
        config: Optional dict with keys:
            - ma_window: Moving average window (default 3 periods)
            - service_level_z: Z-score for service level (default 1.65 = 95%)
            - lead_time_periods: Supply lead time in periods (default 2)

    Example:
        >>> planner = DemandPlanner(config={"ma_window": 3, "service_level_z": 1.65})
        >>> df = planner.load_data("data/demand_history.csv")
        >>> forecast = planner.demand_forecast(df)
        >>> print(forecast)
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.ma_window = self.config.get("ma_window", 3)
        self.z_score = self.config.get("service_level_z", 1.65)  # 95% service level
        self.lead_time = self.config.get("lead_time_periods", 2)

    def load_data(self, filepath: str) -> pd.DataFrame:
        """
        Load demand history from CSV or Excel.

        Args:
            filepath: Path to file. Expected columns: sku_id, period,
                      demand_qty, unit_cost (optional).

        Returns:
            DataFrame with demand history.

        Raises:
            FileNotFoundError: If file does not exist.
        """
        p = Path(filepath)
        if not p.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        if p.suffix in (".xlsx", ".xls"):
            return pd.read_excel(filepath)
        return pd.read_csv(filepath)

    def validate(self, df: pd.DataFrame) -> bool:
        """
        Validate demand history data.

        Args:
            df: DataFrame to validate.

        Returns:
            True if valid.

        Raises:
            ValueError: If empty or missing required columns.
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty")
        df_cols = [c.lower().strip().replace(" ", "_") for c in df.columns]
        required = ["sku_id", "demand_qty"]
        missing = [c for c in required if c not in df_cols]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        return True

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and fill missing values."""
        df = df.copy()
        df.dropna(how="all", inplace=True)
        df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
        if "demand_qty" in df.columns:
            df["demand_qty"] = pd.to_numeric(df["demand_qty"], errors="coerce").fillna(0)
        return df

    def demand_forecast(
        self, df: pd.DataFrame, periods_ahead: int = 3
    ) -> pd.DataFrame:
        """
        Forecast demand using simple moving average with trend adjustment.

        For each SKU, computes rolling mean and trend (slope of recent demand)
        then projects forward for periods_ahead periods.

        Args:
            df: Demand history DataFrame with sku_id, period, demand_qty.
            periods_ahead: Number of periods to forecast (default 3).

        Returns:
            DataFrame with columns: sku_id, forecast_period, forecast_qty,
            ma_baseline, trend_adj, lower_bound, upper_bound.

        Raises:
            ValueError: If demand_qty column missing.
        """
        df = self.preprocess(df)
        if "demand_qty" not in df.columns:
            raise ValueError("Column 'demand_qty' required for forecasting")

        results = []
        sku_col = "sku_id" if "sku_id" in df.columns else df.columns[0]

        for sku, grp in df.groupby(sku_col):
            grp = grp.sort_values("period") if "period" in grp.columns else grp
            demand = grp["demand_qty"].values

            if len(demand) < 2:
                continue

            # Moving average baseline
            window = min(self.ma_window, len(demand))
            ma = float(demand[-window:].mean())

            # Trend: linear slope over last window periods
            x = np.arange(len(demand[-window:]))
            slope = np.polyfit(x, demand[-window:], 1)[0] if window > 1 else 0

            # Demand variability for bounds
            std_dev = float(demand[-window:].std()) if window > 1 else 0

            for i in range(1, periods_ahead + 1):
                forecast = max(0, ma + slope * i)
                results.append({
                    sku_col: sku,
                    "forecast_period": i,
                    "forecast_qty": round(forecast, 1),
                    "ma_baseline": round(ma, 1),
                    "trend_adj": round(slope * i, 2),
                    "lower_bound": round(max(0, forecast - std_dev), 1),
                    "upper_bound": round(forecast + std_dev, 1),
                })

        return pd.DataFrame(results)

    def safety_stock_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate safety stock and reorder points per SKU.

        Safety Stock = Z × σ_demand × √lead_time
        Reorder Point = (avg_demand × lead_time) + safety_stock

        Args:
            df: Demand history DataFrame.

        Returns:
            DataFrame with sku_id, avg_demand, std_demand, safety_stock,
            reorder_point, and recommended_order_qty.
        """
        df = self.preprocess(df)
        sku_col = "sku_id" if "sku_id" in df.columns else df.columns[0]

        results = []
        for sku, grp in df.groupby(sku_col):
            demand = grp["demand_qty"].values
            avg = float(demand.mean())
            std = float(demand.std()) if len(demand) > 1 else 0
            safety_stock = self.z_score * std * np.sqrt(self.lead_time)
            rop = avg * self.lead_time + safety_stock
            eoq = avg * self.ma_window  # simplified order quantity = avg × window

            results.append({
                sku_col: sku,
                "avg_demand_per_period": round(avg, 2),
                "std_demand": round(std, 2),
                "safety_stock": round(safety_stock, 1),
                "reorder_point": round(rop, 1),
                "recommended_order_qty": round(eoq, 1),
            })

        return pd.DataFrame(results)

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run descriptive analysis and return summary metrics."""
        df = self.preprocess(df)
        result = {
            "total_records": len(df),
            "columns": list(df.columns),
            "missing_pct": (df.isnull().sum() / len(df) * 100).round(1).to_dict(),
        }
        numeric_df = df.select_dtypes(include="number")
        if not numeric_df.empty:
            result["summary_stats"] = numeric_df.describe().round(3).to_dict()
            result["totals"] = numeric_df.sum().round(2).to_dict()
            result["means"] = numeric_df.mean().round(3).to_dict()
        return result

    def run(self, filepath: str) -> Dict[str, Any]:
        """Full pipeline: load → validate → analyze."""
        df = self.load_data(filepath)
        self.validate(df)
        return self.analyze(df)

    def to_dataframe(self, result: Dict) -> pd.DataFrame:
        """Convert result dict to flat DataFrame for export."""
        rows = []
        for k, v in result.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    rows.append({"metric": f"{k}.{kk}", "value": vv})
            else:
                rows.append({"metric": k, "value": v})
        return pd.DataFrame(rows)
