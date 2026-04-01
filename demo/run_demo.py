#!/usr/bin/env python3
"""
Supply Chain Demand Planner — Demo
Demonstrates demand forecasting, safety stock analysis, and stockout risk.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import DemandPlanner
import pandas as pd


def main():
    print("=" * 62)
    print("  Supply Chain Demand Planner — Demo")
    print("  NbS Field Supply: Seed · Fertilizer · Planting Tools")
    print("=" * 62)
    print()

    planner = DemandPlanner(config={
        "ma_window": 3,
        "service_level_z": 1.65,   # 95% service level
        "lead_time_periods": 4,    # 4-week lead time
    })

    # Load historical demand
    data_path = Path(__file__).parent.parent / "sample_data" / "demand_history.csv"
    df = planner.load_data(str(data_path))
    planner.validate(df)

    print(f"✓ Loaded {len(df)} demand records from demand_history.csv")
    print(f"  SKUs    : {df['sku_id'].nunique()} ({', '.join(df['sku_id'].unique())})")
    print(f"  Periods : {df['period'].min()} → {df['period'].max()}")
    print()

    # Demand Forecast
    forecast = planner.demand_forecast(df, periods_ahead=3)
    print("✓ Demand Forecast (next 3 periods, 3-period MA + trend):")
    print(f"  {'SKU':<15} {'Period':>8} {'Forecast':>10} {'Lower':>8} {'Upper':>8}")
    print("  " + "-" * 54)
    for _, row in forecast.iterrows():
        print(
            f"  {row['sku_id']:<15} {row['forecast_period']:>8} "
            f"{row['forecast_qty']:>10.1f} {row['lower_bound']:>8.1f} {row['upper_bound']:>8.1f}"
        )
    print()

    # Safety Stock Analysis
    safety = planner.safety_stock_analysis(df)
    print("✓ Safety Stock & Reorder Points:")
    print(f"  {'SKU':<15} {'Avg Demand':>10} {'Std Dev':>8} {'Safety Stock':>13} {'Reorder Point':>14}")
    print("  " + "-" * 64)
    for _, row in safety.iterrows():
        print(
            f"  {row['sku_id']:<15} {row['avg_demand_per_period']:>10.1f} "
            f"{row['std_demand']:>8.1f} {row['safety_stock']:>13.1f} {row['reorder_point']:>14.1f}"
        )
    print()

    # Stockout Risk
    # Build current stock snapshot for demo
    stock_df = pd.DataFrame([
        {"sku_id": "SKU-SEED-01", "period": "2025-06", "demand_qty": 520, "current_stock": 350},
        {"sku_id": "SKU-FERT-02", "period": "2025-06", "demand_qty": 16,  "current_stock": 5},
        {"sku_id": "SKU-TOOL-03", "period": "2025-06", "demand_qty": 32,  "current_stock": 120},
    ])
    risks = planner.calculate_stockout_risk(
        stock_df, sku_col="sku_id", demand_col="demand_qty", stock_col="current_stock"
    )
    print("✓ Stockout Risk Assessment:")
    print(f"  {'SKU':<15} {'Stock':>7} {'Avg Demand':>10} {'Days Supply':>12} {'Risk Score':>11} {'Band':<10} {'Action'}")
    print("  " + "-" * 90)
    for _, row in risks.iterrows():
        days = f"{row['days_of_supply']:.1f}" if row['days_of_supply'] is not None else "∞"
        print(
            f"  {row['sku_id']:<15} {int(row['current_stock']):>7} {row['avg_demand_per_period']:>10.1f} "
            f"{days:>12} {row['stockout_risk_score']:>11.1f} {row['risk_band']:<10} {row['recommended_action']}"
        )
    print()
    print("=" * 62)
    print("  ✅ Demo complete")
    print("=" * 62)


if __name__ == "__main__":
    main()
