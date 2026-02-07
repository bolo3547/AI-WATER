"""
Tests for Community Reporting Portal - Tracking Code Generation
"""

import pytest
from src.community.reporting_portal import (
    CommunityPortalService,
    CommunityReport,
    ReportType,
    ReportStatus,
)


class TestTrackingCodeGeneration:
    """Test tracking code generation in community reports."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = CommunityPortalService()
        self.service.register_user(
            phone="+260971234567",
            name="Test User",
            language="en",
            area="Lusaka",
        )
        # Get user_id from the registered user
        self.user = self.service.get_user_by_phone("+260971234567")
        self.user_id = self.user.user_id

    def test_tracking_code_format(self):
        """Verify tracking code format: TRK-XXXXXX."""
        code = self.service._generate_tracking_code()
        assert code.startswith("TRK-")
        assert len(code) == 10  # TRK- + 6 chars

    def test_tracking_code_uniqueness(self):
        """Verify tracking codes are unique across many generations."""
        codes = set()
        for _ in range(1000):
            code = self.service._generate_tracking_code()
            assert code not in codes, f"Duplicate tracking code: {code}"
            codes.add(code)

    def test_submit_report_generates_tracking_code(self):
        """Verify that submitting a report generates a tracking code."""
        report = self.service.submit_report(
            user_id=self.user_id,
            report_type=ReportType.LEAK,
            latitude=-15.4167,
            longitude=28.2833,
            description="Water leaking from pipe",
        )
        assert report.tracking_code != ""
        assert report.tracking_code.startswith("TRK-")
        assert len(report.tracking_code) == 10

    def test_to_dict_includes_tracking_code(self):
        """Verify to_dict() includes tracking_code and tracking_url."""
        report = self.service.submit_report(
            user_id=self.user_id,
            report_type=ReportType.LEAK,
            latitude=-15.4167,
            longitude=28.2833,
            description="Water leaking from pipe",
        )
        report_dict = report.to_dict()
        assert "tracking_code" in report_dict
        assert "tracking_url" in report_dict
        assert report_dict["tracking_code"] == report.tracking_code
        assert report_dict["tracking_url"] == f"/track/{report.tracking_code}"

    def test_to_dict_tracking_url_none_when_no_code(self):
        """Verify tracking_url is None if tracking_code is empty."""
        report = CommunityReport(
            report_id="test-001",
            user_id="user-001",
            report_type=ReportType.LEAK,
            status=ReportStatus.SUBMITTED,
            latitude=-15.4167,
            longitude=28.2833,
        )
        report_dict = report.to_dict()
        assert report_dict["tracking_code"] == ""
        assert report_dict["tracking_url"] is None

    def test_multiple_reports_get_different_tracking_codes(self):
        """Verify each report gets a unique tracking code."""
        report1 = self.service.submit_report(
            user_id=self.user_id,
            report_type=ReportType.LEAK,
            latitude=-15.4167,
            longitude=28.2833,
        )
        report2 = self.service.submit_report(
            user_id=self.user_id,
            report_type=ReportType.BURST,
            latitude=-15.4200,
            longitude=28.2900,
        )
        assert report1.tracking_code != report2.tracking_code
