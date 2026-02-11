"""Supply chain risk assessment and mitigation strategies."""

from typing import Dict, List, Optional


class SupplyChainRiskAssessor:
    """
    Assess and mitigate supply chain disruption risks.
    
    Evaluates:
    - Supplier concentration risk
    - Geographic concentration risk
    - Lead time buffer adequacy
    - Demand volatility risks
    """
    
    RISK_LEVELS = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }
    
    def __init__(self):
        """Initialize risk assessor."""
        self.suppliers = {}
        self.products = {}
        self.risks = []
    
    def assess_supplier_concentration(
        self,
        suppliers: Dict[str, Dict],  # {supplier_id: {volume_pct, locations, lead_days}}
        critical_threshold_pct: float = 30.0
    ) -> Dict:
        """
        Assess concentration risk from key suppliers.
        
        Args:
            suppliers: Supplier volume and characteristics
            critical_threshold_pct: Single supplier >X% is critical
        
        Returns:
            Concentration risk analysis
        """
        if not suppliers:
            raise ValueError("suppliers dict required")
        if not (10 <= critical_threshold_pct <= 100):
            raise ValueError("critical_threshold_pct must be 10-100")
        
        total_volume = sum(s.get('volume_pct', 0) for s in suppliers.values())
        
        critical_suppliers = []
        high_risk_suppliers = []
        
        for supplier_id, profile in suppliers.items():
            volume_pct = profile.get('volume_pct', 0)
            
            if volume_pct >= critical_threshold_pct:
                critical_suppliers.append((supplier_id, volume_pct))
            elif volume_pct >= critical_threshold_pct * 0.6:
                high_risk_suppliers.append((supplier_id, volume_pct))
        
        # Calculate HHI for concentration index
        hhi = sum((vol ** 2) for supplier_id, vol in suppliers.items() for vol in [suppliers[supplier_id].get('volume_pct', 0)])
        
        risk_level = "critical" if critical_suppliers else ("high" if high_risk_suppliers else "medium")
        
        return {
            "total_suppliers": len(suppliers),
            "critical_supplier_count": len(critical_suppliers),
            "critical_suppliers": critical_suppliers,
            "high_risk_suppliers": high_risk_suppliers,
            "hhi_concentration_index": round(hhi, 1),
            "risk_level": risk_level,
            "mitigation": self._get_concentration_mitigation(critical_suppliers),
        }
    
    def _get_concentration_mitigation(self, critical: List[tuple]) -> List[str]:
        """Generate mitigation strategies."""
        if not critical:
            return ["Monitor supplier performance regularly"]
        
        strategies = [
            "Diversify supplier base immediately",
            "Establish backup suppliers for critical items",
            "Increase safety stock for critical SKUs",
            "Negotiate multi-year contracts to reduce risk",
        ]
        
        if len(critical) > 1:
            strategies.append("Implement supplier redundancy program")
        
        return strategies
    
    def assess_lead_time_adequacy(
        self,
        product_id: str,
        average_demand: float,
        demand_std_dev: float,
        lead_time_days: int,
        current_inventory_days: int
    ) -> Dict:
        """
        Assess if lead time and inventory buffers are adequate.
        
        Args:
            product_id: Product identifier
            average_demand: Average daily demand (units)
            demand_std_dev: Demand standard deviation
            lead_time_days: Supplier lead time
            current_inventory_days: Current days-of-inventory
        
        Returns:
            Lead time risk analysis and safety stock recommendations
        """
        if lead_time_days <= 0 or average_demand <= 0:
            raise ValueError("lead_time_days and average_demand must be positive")
        
        # Calculate safety stock using service level 95% (1.65 sigma)
        safety_stock_units = 1.65 * demand_std_dev * (lead_time_days ** 0.5)
        min_inventory_days = lead_time_days + (safety_stock_units / average_demand)
        
        adequacy_pct = (current_inventory_days / min_inventory_days * 100) if min_inventory_days > 0 else 100
        
        if adequacy_pct >= 100:
            risk = "low"
        elif adequacy_pct >= 80:
            risk = "medium"
        else:
            risk = "high"
        
        return {
            "product_id": product_id,
            "lead_time_days": lead_time_days,
            "average_demand": round(average_demand, 2),
            "demand_volatility": round(demand_std_dev, 2),
            "current_inventory_days": current_inventory_days,
            "recommended_safety_stock_units": round(safety_stock_units, 0),
            "minimum_inventory_days": round(min_inventory_days, 1),
            "adequacy_percentage": round(adequacy_pct, 1),
            "risk_level": risk,
            "action": "Increase inventory" if adequacy_pct < 100 else "Current levels adequate",
        }
    
    def assess_geographic_concentration(
        self,
        suppliers: Dict[str, Dict]  # {supplier_id: {locations: [country, ...]}}
    ) -> Dict:
        """
        Assess geographic concentration and geopolitical risks.
        
        Args:
            suppliers: Supplier geographic locations
        
        Returns:
            Geographic risk analysis
        """
        location_counts = {}
        supplier_locations = {}
        
        for supplier_id, profile in suppliers.items():
            locations = profile.get('locations', [])
            supplier_locations[supplier_id] = locations
            
            for location in locations:
                location_counts[location] = location_counts.get(location, 0) + 1
        
        # Identify concentrated regions
        concentrated_regions = [
            (region, count) for region, count in location_counts.items()
            if count >= len(suppliers) * 0.4  # >40% of suppliers in one region
        ]
        
        risk_level = "high" if concentrated_regions else "medium"
        
        return {
            "total_unique_locations": len(location_counts),
            "suppliers_per_location": location_counts,
            "concentrated_regions": concentrated_regions,
            "geographic_risk_level": risk_level,
            "recommendations": [
                f"Expand suppliers beyond {r[0]}" for r, c in concentrated_regions
            ] if concentrated_regions else ["Geographic distribution is adequate"],
        }
    
    def create_supply_chain_risk_scorecard(
        self,
        suppliers: Dict[str, Dict],
        products: Dict[str, Dict]
    ) -> Dict:
        """
        Create comprehensive supply chain risk scorecard.
        
        Args:
            suppliers: All suppliers data
            products: All products data
        
        Returns:
            Risk scorecard with overall health and priority mitigations
        """
        if not suppliers or not products:
            return {"error": "suppliers and products data required"}
        
        concentration = self.assess_supplier_concentration(suppliers)
        geographic = self.assess_geographic_concentration(suppliers)
        
        # Calculate overall risk score (0-100, higher = more risky)
        concentration_score = self.RISK_LEVELS.get(concentration["risk_level"], 2) * 25
        geographic_score = self.RISK_LEVELS.get(geographic["geographic_risk_level"], 2) * 25
        
        overall_score = (concentration_score + geographic_score) / 2
        
        overall_risk = "critical" if overall_score >= 75 else ("high" if overall_score >= 50 else "medium")
        
        return {
            "overall_risk_score": round(overall_score, 1),
            "overall_risk_level": overall_risk,
            "supplier_concentration_risk": concentration["risk_level"],
            "geographic_concentration_risk": geographic["geographic_risk_level"],
            "key_mitigations": self._prioritize_mitigations(
                concentration, geographic
            ),
            "monitoring_frequency": "daily" if overall_risk == "critical" else ("weekly" if overall_risk == "high" else "monthly"),
        }
    
    def _prioritize_mitigations(self, concentration: Dict, geographic: Dict) -> List[str]:
        """Prioritize mitigation actions."""
        mitigations = []
        
        if concentration["risk_level"] == "critical":
            mitigations.extend(concentration["mitigation"][:2])
        
        if geographic["geographic_risk_level"] == "high":
            mitigations.extend(geographic["recommendations"][:2])
        
        return mitigations or ["Continue current risk monitoring"]
