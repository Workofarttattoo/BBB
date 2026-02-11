import pytest
import asyncio
from src.blank_business_builder.all_features_implementation import ComplianceManager, ComplianceFramework

class TestComplianceManager:
    """Test the ComplianceManager class."""

    def test_initialization(self):
        """Test initial state of frameworks."""
        manager = ComplianceManager()
        assert ComplianceFramework.SOC2_TYPE_II in manager.frameworks
        assert ComplianceFramework.GDPR in manager.frameworks
        assert len(manager.frameworks) == 2

    def test_run_compliance_audit_soc2(self):
        """Test running compliance audit for SOC2 Type II."""
        manager = ComplianceManager()
        result = asyncio.run(manager.run_compliance_audit(ComplianceFramework.SOC2_TYPE_II))

        assert result["framework"] == ComplianceFramework.SOC2_TYPE_II.value
        assert result["controls_total"] == 64
        assert result["controls_implemented"] == 58
        assert result["compliance_score"] == 58 / 64
        assert result["status"] == "in_progress"
        assert len(result["recommendations"]) == 3
        assert "Complete access control logging" in result["recommendations"]

    def test_run_compliance_audit_gdpr(self):
        """Test running compliance audit for GDPR."""
        manager = ComplianceManager()
        result = asyncio.run(manager.run_compliance_audit(ComplianceFramework.GDPR))

        assert result["framework"] == ComplianceFramework.GDPR.value
        assert result["controls_total"] == 32
        assert result["controls_implemented"] == 32
        assert result["compliance_score"] == 1.0
        assert result["status"] == "compliant"
        assert len(result["recommendations"]) == 3
        assert "Ensure data portability" in result["recommendations"]

    def test_run_compliance_audit_unimplemented_framework(self):
        """Test running compliance audit for unimplemented frameworks (HIPAA, PCI_DSS)."""
        manager = ComplianceManager()

        # Test for HIPAA
        result_hipaa = asyncio.run(manager.run_compliance_audit(ComplianceFramework.HIPAA))
        assert result_hipaa["framework"] == ComplianceFramework.HIPAA.value
        assert result_hipaa["controls_total"] == 0
        assert result_hipaa["controls_implemented"] == 0
        assert result_hipaa["compliance_score"] == 0.0
        assert result_hipaa["status"] == "unknown"
        assert result_hipaa["recommendations"] == []

        # Test for PCI_DSS
        result_pci = asyncio.run(manager.run_compliance_audit(ComplianceFramework.PCI_DSS))
        assert result_pci["framework"] == ComplianceFramework.PCI_DSS.value
        assert result_pci["controls_total"] == 0
        assert result_pci["controls_implemented"] == 0
        assert result_pci["compliance_score"] == 0.0
        assert result_pci["status"] == "unknown"
        assert result_pci["recommendations"] == []

    def test_get_recommendations(self):
        """Test getting recommendations directly."""
        manager = ComplianceManager()

        soc2_recs = manager._get_recommendations(ComplianceFramework.SOC2_TYPE_II)
        assert len(soc2_recs) == 3
        assert "Implement change management process" in soc2_recs

        gdpr_recs = manager._get_recommendations(ComplianceFramework.GDPR)
        assert len(gdpr_recs) == 3
        assert "Maintain consent records" in gdpr_recs

        hipaa_recs = manager._get_recommendations(ComplianceFramework.HIPAA)
        assert hipaa_recs == []
