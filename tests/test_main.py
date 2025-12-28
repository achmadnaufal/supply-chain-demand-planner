"""Unit tests for DemandPlanner."""
import pytest
import pandas as pd
import sys
sys.path.insert(0, "/Users/johndoe/projects/supply-chain-demand-planner")
from src.main import DemandPlanner


@pytest.fixture
def demand_df():
    skus = ["SKU-A"] * 6 + ["SKU-B"] * 6
    periods = list(range(1, 7)) * 2
    demand = [120, 135, 128, 142, 138, 150, 45, 50, 48, 55, 52, 58]
    return pd.DataFrame({"sku_id": skus, "period": periods, "demand_qty": demand})


@pytest.fixture
def planner():
    return DemandPlanner(config={"ma_window": 3, "service_level_z": 1.65, "lead_time_periods": 2})


class TestValidation:
    def test_empty_raises(self, planner):
        with pytest.raises(ValueError, match="empty"):
            planner.validate(pd.DataFrame())

    def test_missing_columns_raises(self, planner):
        df = pd.DataFrame({"sku_id": ["A"], "period": [1]})
        with pytest.raises(ValueError, match="Missing required columns"):
            planner.validate(df)

    def test_valid_passes(self, planner, demand_df):
        assert planner.validate(demand_df) is True


class TestDemandForecast:
    def test_returns_dataframe(self, planner, demand_df):
        result = planner.demand_forecast(demand_df)
        assert isinstance(result, pd.DataFrame)

    def test_forecast_qty_positive(self, planner, demand_df):
        result = planner.demand_forecast(demand_df)
        assert (result["forecast_qty"] >= 0).all()

    def test_correct_periods_ahead(self, planner, demand_df):
        result = planner.demand_forecast(demand_df, periods_ahead=3)
        for sku, grp in result.groupby("sku_id"):
            assert len(grp) == 3

    def test_bounds_make_sense(self, planner, demand_df):
        result = planner.demand_forecast(demand_df)
        assert (result["upper_bound"] >= result["forecast_qty"]).all()
        assert (result["forecast_qty"] >= result["lower_bound"]).all()

    def test_missing_demand_qty_raises(self, planner):
        df = pd.DataFrame({"sku_id": ["A"], "period": [1], "volume": [100]})
        with pytest.raises(ValueError, match="demand_qty"):
            planner.demand_forecast(df)


class TestSafetyStockAnalysis:
    def test_returns_dataframe(self, planner, demand_df):
        result = planner.safety_stock_analysis(demand_df)
        assert isinstance(result, pd.DataFrame)

    def test_safety_stock_positive(self, planner, demand_df):
        result = planner.safety_stock_analysis(demand_df)
        assert (result["safety_stock"] >= 0).all()

    def test_reorder_point_above_safety_stock(self, planner, demand_df):
        result = planner.safety_stock_analysis(demand_df)
        assert (result["reorder_point"] >= result["safety_stock"]).all()

    def test_two_skus_in_result(self, planner, demand_df):
        result = planner.safety_stock_analysis(demand_df)
        assert len(result) == 2

    def test_higher_demand_higher_rop(self, planner, demand_df):
        result = planner.safety_stock_analysis(demand_df)
        rop_a = result[result["sku_id"] == "SKU-A"]["reorder_point"].values[0]
        rop_b = result[result["sku_id"] == "SKU-B"]["reorder_point"].values[0]
        assert rop_a > rop_b
