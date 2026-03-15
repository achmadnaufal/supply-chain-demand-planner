"""
Unit tests for stockout risk assessment.
"""
import math
import pytest
import pandas as pd
from src.main import SupplyChainDemandPlanner


@pytest.fixture
def planner():
    return SupplyChainDemandPlanner(lead_time=14, z_score=1.65)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "sku": ["SKU-A"] * 4 + ["SKU-B"] * 4 + ["SKU-C"] * 4,
        "demand_qty": [100, 110, 95, 105,
                       200, 210, 190, 205,
                       50, 48, 52, 51],
        "current_stock": [500, 500, 500, 500,
                          150, 150, 150, 150,
                          2000, 2000, 2000, 2000],
    })


class TestCalculateStockoutRisk:

    def test_returns_one_row_per_sku(self, planner, sample_df):
        result = planner.calculate_stockout_risk(sample_df)
        assert len(result) == 3

    def test_high_stock_low_risk(self, planner, sample_df):
        """SKU-C has 2000 units, avg demand ~50 → very low risk."""
        result = planner.calculate_stockout_risk(sample_df)
        sku_c = result[result["sku"] == "SKU-C"].iloc[0]
        assert sku_c["risk_band"] == "Low"
        assert sku_c["stockout_risk_score"] < 20

    def test_low_stock_high_risk(self, planner, sample_df):
        """SKU-B has 150 units, avg demand ~201 → Critical or High."""
        result = planner.calculate_stockout_risk(sample_df)
        sku_b = result[result["sku"] == "SKU-B"].iloc[0]
        assert sku_b["risk_band"] in ("Critical", "High")
        assert sku_b["stockout_risk_score"] >= 40

    def test_risk_score_0_to_100(self, planner, sample_df):
        result = planner.calculate_stockout_risk(sample_df)
        assert (result["stockout_risk_score"] >= 0).all()
        assert (result["stockout_risk_score"] <= 100).all()

    def test_empty_dataframe_raises(self, planner):
        with pytest.raises(ValueError, match="DataFrame cannot be empty"):
            planner.calculate_stockout_risk(pd.DataFrame())

    def test_missing_column_raises(self, planner, sample_df):
        bad_df = sample_df.drop(columns=["current_stock"])
        with pytest.raises(ValueError, match="Missing required columns"):
            planner.calculate_stockout_risk(bad_df)

    def test_sorted_by_risk_descending(self, planner, sample_df):
        result = planner.calculate_stockout_risk(sample_df)
        scores = result["stockout_risk_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_below_reorder_point_flag(self, planner, sample_df):
        """SKU-B with very low stock should be flagged below reorder point."""
        result = planner.calculate_stockout_risk(sample_df)
        sku_b = result[result["sku"] == "SKU-B"].iloc[0]
        assert sku_b["below_reorder_point"] is True
