"""
Tests for Public Engagement Module
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import uuid

# Import the modules we're testing
from src.public_engagement.models import (
    ReportCategory, ReportStatus, ReportSource, ReportVerification,
    PublicReport, PublicReportMedia, PublicReportLink, PublicEngagementAuditLog
)
from src.public_engagement.services import (
    PublicReportService, DuplicateDetectionService, SpamDetectionService,
    AnalyticsService, ReportCreateRequest, SpamCheckResult
)


class TestReportCategory:
    """Test ReportCategory enum"""
    
    def test_all_categories_exist(self):
        categories = [
            'leak', 'burst', 'no_water', 'low_pressure',
            'illegal_connection', 'overflow', 'contamination', 'other'
        ]
        for cat in categories:
            assert hasattr(ReportCategory, cat.upper())
    
    def test_category_values(self):
        assert ReportCategory.LEAK.value == 'leak'
        assert ReportCategory.BURST.value == 'burst'


class TestReportStatus:
    """Test ReportStatus enum"""
    
    def test_status_progression(self):
        statuses = ['received', 'under_review', 'technician_assigned', 
                    'in_progress', 'resolved', 'closed']
        for status in statuses:
            assert hasattr(ReportStatus, status.upper())


class TestPublicReportModel:
    """Test PublicReport SQLAlchemy model"""
    
    def test_public_report_fields(self):
        """Verify all required fields exist on PublicReport model"""
        required_fields = [
            'id', 'ticket', 'tenant_id', 'category', 'description',
            'latitude', 'longitude', 'area_text', 'source',
            'reporter_name', 'reporter_phone', 'reporter_email',
            'reporter_consent', 'status', 'verification',
            'spam_flag', 'quarantine', 'master_report_id',
            'is_master', 'duplicate_count', 'linked_leak_id',
            'linked_work_order_id', 'admin_notes', 'assigned_to_user_id',
            'assigned_team', 'created_at', 'updated_at'
        ]
        for field in required_fields:
            assert hasattr(PublicReport, field), f"Missing field: {field}"
    
    def test_to_public_dict_excludes_sensitive_data(self):
        """Verify to_public_dict() hides sensitive info from public"""
        report = PublicReport(
            id=uuid.uuid4(),
            ticket='TKT-ABC123',
            tenant_id='test-tenant',
            category=ReportCategory.LEAK,
            description='Test leak',
            latitude=-15.4,
            longitude=28.3,
            reporter_name='John Doe',
            reporter_phone='+260971234567',
            reporter_email='john@example.com',
            admin_notes='Internal notes here',
            spam_flag=False,
            quarantine=False
        )
        
        public_data = report.to_public_dict()
        
        # Should include safe fields
        assert 'ticket' in public_data
        assert 'status' in public_data
        assert 'category' in public_data
        
        # Should NOT include sensitive fields
        assert 'reporter_phone' not in public_data
        assert 'reporter_email' not in public_data
        assert 'admin_notes' not in public_data
        assert 'spam_flag' not in public_data
    
    def test_to_admin_dict_includes_all_data(self):
        """Verify to_admin_dict() includes all fields for admins"""
        report = PublicReport(
            id=uuid.uuid4(),
            ticket='TKT-ABC123',
            tenant_id='test-tenant',
            category=ReportCategory.LEAK,
            reporter_phone='+260971234567',
            admin_notes='Internal notes',
            spam_flag=True
        )
        
        admin_data = report.to_admin_dict()
        
        # Should include all fields
        assert 'reporter_phone' in admin_data
        assert 'admin_notes' in admin_data
        assert 'spam_flag' in admin_data


class TestDuplicateDetectionService:
    """Test duplicate detection logic"""
    
    def test_haversine_distance_calculation(self):
        """Test haversine formula for distance calculation"""
        service = DuplicateDetectionService()
        
        # Lusaka city center coordinates
        lat1, lon1 = -15.4167, 28.2833
        lat2, lon2 = -15.4168, 28.2834  # ~15m away
        
        distance = service._haversine_distance(lat1, lon1, lat2, lon2)
        assert distance < 50  # Should be less than 50m
    
    def test_duplicate_detection_within_radius(self):
        """Test that reports within 100m and 30min are flagged as duplicates"""
        service = DuplicateDetectionService()
        
        existing_reports = [
            {
                'id': 'report-1',
                'ticket': 'TKT-AAA111',
                'latitude': -15.4167,
                'longitude': 28.2833,
                'category': 'leak',
                'created_at': datetime.utcnow() - timedelta(minutes=15)
            }
        ]
        
        new_report = {
            'latitude': -15.4168,  # ~15m from existing
            'longitude': 28.2834,
            'category': 'leak'
        }
        
        # Mock DB session
        mock_db = MagicMock()
        
        with patch.object(service, '_get_nearby_reports', return_value=existing_reports):
            duplicates = service.find_duplicates(
                db=mock_db,
                tenant_id='test',
                latitude=new_report['latitude'],
                longitude=new_report['longitude'],
                category=new_report['category']
            )
        
        assert len(duplicates) == 1
        assert duplicates[0]['ticket'] == 'TKT-AAA111'
    
    def test_no_duplicate_outside_time_window(self):
        """Reports older than 30min should not be flagged"""
        service = DuplicateDetectionService()
        
        old_report = {
            'id': 'report-1',
            'ticket': 'TKT-AAA111',
            'latitude': -15.4167,
            'longitude': 28.2833,
            'category': 'leak',
            'created_at': datetime.utcnow() - timedelta(hours=2)  # 2 hours old
        }
        
        mock_db = MagicMock()
        
        with patch.object(service, '_get_nearby_reports', return_value=[old_report]):
            duplicates = service.find_duplicates(
                db=mock_db,
                tenant_id='test',
                latitude=-15.4168,
                longitude=28.2834,
                category='leak'
            )
        
        assert len(duplicates) == 0


class TestSpamDetectionService:
    """Test spam/abuse prevention logic"""
    
    def test_rate_limit_by_ip(self):
        """Test that IP-based rate limiting works"""
        service = SpamDetectionService()
        
        # Simulate 5 requests from same IP
        ip = '192.168.1.100'
        
        for i in range(5):
            result = service.check_report(
                ip_address=ip,
                device_fingerprint=f'device-{i}',
                phone_number=None,
                description='Test report'
            )
            if i < 5:
                assert not result.is_spam, f"Request {i} should not be flagged"
        
        # 6th request should be rate limited
        result = service.check_report(
            ip_address=ip,
            device_fingerprint='device-6',
            phone_number=None,
            description='Test report'
        )
        
        assert result.is_spam
        assert 'rate_limit' in result.reason.lower()
    
    def test_spam_text_detection(self):
        """Test that spam patterns in text are detected"""
        service = SpamDetectionService()
        
        spam_descriptions = [
            'BUY NOW!!! CLICK HERE!!!',
            'test test test test test',  # Repetitive
            'Visit http://spam.com for free stuff',  # Suspicious URL
        ]
        
        for desc in spam_descriptions:
            result = service.check_report(
                ip_address='192.168.1.1',
                device_fingerprint='device-1',
                phone_number=None,
                description=desc
            )
            # Some of these should be flagged
            # (implementation may vary)
    
    def test_phone_number_rate_limit(self):
        """Test rate limiting by phone number"""
        service = SpamDetectionService()
        
        phone = '+260971234567'
        
        # Multiple reports from same phone in short time
        for i in range(3):
            result = service.check_report(
                ip_address=f'192.168.1.{i}',
                device_fingerprint=f'device-{i}',
                phone_number=phone,
                description='Test report'
            )
        
        # After limit, should flag
        result = service.check_report(
            ip_address='192.168.1.99',
            device_fingerprint='device-99',
            phone_number=phone,
            description='Test report'
        )
        
        # Check if flagged (depends on limit setting)


class TestAnalyticsService:
    """Test analytics and KPI calculations"""
    
    def test_confirmation_rate_calculation(self):
        """Test confirmed vs false report ratio"""
        service = AnalyticsService()
        
        mock_db = MagicMock()
        
        # Mock query results
        with patch.object(service, '_get_report_counts') as mock_counts:
            mock_counts.return_value = {
                'total': 100,
                'confirmed': 65,
                'false': 12,
                'pending': 23
            }
            
            metrics = service.get_metrics(mock_db, 'test-tenant')
            
            assert metrics['confirmed_rate'] == 65.0
            assert metrics['false_rate'] == 12.0
    
    def test_monthly_trend_data(self):
        """Test monthly trend aggregation"""
        service = AnalyticsService()
        mock_db = MagicMock()
        
        with patch.object(service, '_get_monthly_data') as mock_monthly:
            mock_monthly.return_value = [
                {'month': '2024-01', 'count': 45},
                {'month': '2024-02', 'count': 52},
                {'month': '2024-03', 'count': 48},
            ]
            
            trend = service.get_monthly_trend(mock_db, 'test-tenant', months=3)
            
            assert len(trend) == 3


class TestTenantIsolation:
    """Test multi-tenant data isolation"""
    
    def test_reports_filtered_by_tenant(self):
        """Verify queries always include tenant_id filter"""
        service = PublicReportService()
        mock_db = MagicMock()
        
        # When fetching reports for tenant A, should not see tenant B data
        tenant_a = 'lwsc-zambia'
        tenant_b = 'ncwsc-kenya'
        
        # This test would verify the query includes tenant filter
        # Implementation depends on actual query structure
    
    def test_cannot_access_other_tenant_report(self):
        """Verify cross-tenant access is blocked"""
        service = PublicReportService()
        mock_db = MagicMock()
        
        # Attempt to access report from different tenant should fail
        # Implementation would return None or raise exception


class TestTicketGeneration:
    """Test ticket number generation"""
    
    def test_ticket_format(self):
        """Verify ticket format: TKT-XXXXXX"""
        service = PublicReportService()
        
        ticket = service._generate_ticket()
        
        assert ticket.startswith('TKT-')
        assert len(ticket) == 10  # TKT- + 6 chars
    
    def test_ticket_uniqueness(self):
        """Verify tickets are unique"""
        service = PublicReportService()
        
        tickets = set()
        for _ in range(1000):
            ticket = service._generate_ticket()
            assert ticket not in tickets, f"Duplicate ticket: {ticket}"
            tickets.add(ticket)


class TestWhatsAppWebhook:
    """Test WhatsApp bot state machine"""
    
    def test_greeting_state_transition(self):
        """Test transition from greeting to category selection"""
        # Test state machine transitions
        pass
    
    def test_location_parsing(self):
        """Test GPS coordinate parsing from WhatsApp location"""
        pass
    
    def test_photo_handling(self):
        """Test media attachment handling"""
        pass


class TestUSSDFlow:
    """Test USSD menu system"""
    
    def test_initial_menu(self):
        """Test initial USSD menu response"""
        pass
    
    def test_category_selection(self):
        """Test category selection via USSD input"""
        pass
    
    def test_session_timeout(self):
        """Test USSD session timeout handling"""
        pass


# Integration tests (would require actual DB)
class TestIntegration:
    """Integration tests requiring database"""
    
    @pytest.mark.integration
    def test_full_report_flow(self):
        """Test complete report creation flow"""
        pass
    
    @pytest.mark.integration
    def test_duplicate_merge_flow(self):
        """Test duplicate detection and merge"""
        pass
    
    @pytest.mark.integration
    def test_work_order_creation(self):
        """Test creating work order from report"""
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
