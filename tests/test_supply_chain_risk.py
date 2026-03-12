"""Tests for supply chain risk assessment."""

import pytest
from src.supply_chain_risk import SupplyChainRiskAssessor


class TestSupplyChainRisk:
    """Test supply chain risk assessment."""
    
    @pytest.fixture
    def assessor(self):
        return SupplyChainRiskAssessor()
    
    def test_supplier_concentration(self, assessor):
        """Test supplier concentration risk."""
        suppliers = {
            "S001": {"volume_pct": 45, "locations": ["China"]},
            "S002": {"volume_pct": 30, "locations": ["India"]},
            "S003": {"volume_pct": 25, "locations": ["Vietnam"]},
        }
        
        result = assessor.assess_supplier_concentration(suppliers)
        
        assert result["total_suppliers"] == 3
        assert "S001" in [s[0] for s in result["critical_suppliers"]]
        assert result["risk_level"] == "critical"
    
    def test_lead_time_adequacy(self, assessor):
        """Test lead time buffer assessment."""
        result = assessor.assess_lead_time_adequacy(
            product_id="PROD_001",
            average_demand=100,
            demand_std_dev=20,
            lead_time_days=14,
            current_inventory_days=30
        )
        
        assert result["product_id"] == "PROD_001"
        assert result["adequacy_percentage"] >= 0
    
    def test_geographic_concentration(self, assessor):
        """Test geographic risk."""
        suppliers = {
            "S001": {"locations": ["China", "Taiwan"]},
            "S002": {"locations": ["China"]},
            "S003": {"locations": ["Vietnam"]},
        }
        
        result = assessor.assess_geographic_concentration(suppliers)
        
        assert result["total_unique_locations"] >= 2
        assert "China" in result["suppliers_per_location"]
    
    def test_risk_scorecard(self, assessor):
        """Test overall risk scorecard."""
        suppliers = {
            "S001": {"volume_pct": 60, "locations": ["China"]},
            "S002": {"volume_pct": 40, "locations": ["China"]},
        }
        products = {"P001": {"demand": 1000}}
        
        result = assessor.create_supply_chain_risk_scorecard(suppliers, products)
        
        assert "overall_risk_score" in result
        assert result["overall_risk_level"] in ["critical", "high", "medium"]
