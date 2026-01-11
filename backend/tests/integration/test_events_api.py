"""
Integration tests for Events API endpoints.

Tests end-to-end flows for event management:
- Listing events with date range filtering
- Getting event details by GUID
- Statistics endpoint

Issue #39 - Calendar Events feature (Phase 4)
"""

import pytest
from datetime import date, time

from backend.src.models import Category, Event, EventSeries


class TestEventsAPI:
    """Integration tests for Events API endpoints."""

    @pytest.fixture
    def test_category(self, test_db_session):
        """Create a test category."""
        category = Category(
            name="Test Airshow",
            icon="plane",
            color="#3B82F6",
            is_active=True,
            display_order=0,
        )
        test_db_session.add(category)
        test_db_session.commit()
        test_db_session.refresh(category)
        return category

    @pytest.fixture
    def test_events(self, test_db_session, test_category):
        """Create test events."""
        events = []

        # Create standalone events
        for i in range(3):
            event = Event(
                title=f"Test Event {i + 1}",
                event_date=date(2026, 3, 10 + i),
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_all_day=False,
                status="future",
                attendance="planned",
                category_id=test_category.id,
            )
            test_db_session.add(event)
            events.append(event)

        test_db_session.commit()
        for event in events:
            test_db_session.refresh(event)

        return events

    @pytest.fixture
    def test_series(self, test_db_session, test_category):
        """Create a test event series with events."""
        series = EventSeries(
            title="Multi-Day Airshow",
            category_id=test_category.id,
            total_events=3,
            ticket_required=True,
            travel_required=True,
            timeoff_required=False,
        )
        test_db_session.add(series)
        test_db_session.commit()
        test_db_session.refresh(series)

        events = []
        for i in range(3):
            event = Event(
                series_id=series.id,
                sequence_number=i + 1,
                event_date=date(2026, 7, 27 + i),
                start_time=time(8, 0),
                end_time=time(18, 0),
                is_all_day=False,
                status="future",
                attendance="planned",
            )
            test_db_session.add(event)
            events.append(event)

        test_db_session.commit()
        for event in events:
            test_db_session.refresh(event)

        return series, events

    def test_list_events_empty(self, test_client):
        """Test listing events when none exist."""
        response = test_client.get("/api/events")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_events(self, test_client, test_events):
        """Test listing all events."""
        response = test_client.get("/api/events")
        assert response.status_code == 200

        events = response.json()
        assert len(events) >= 3

        # Verify event structure
        event = events[0]
        assert "guid" in event
        assert event["guid"].startswith("evt_")
        assert "title" in event
        assert "event_date" in event
        assert "status" in event
        assert "attendance" in event
        assert "category" in event

    def test_list_events_with_date_range(self, test_client, test_events):
        """Test listing events with date range filter."""
        # Filter to specific dates
        response = test_client.get(
            "/api/events",
            params={
                "start_date": "2026-03-10",
                "end_date": "2026-03-11",
            },
        )
        assert response.status_code == 200

        events = response.json()
        # Should only get events within the date range
        for event in events:
            event_date = event["event_date"]
            assert "2026-03-10" <= event_date <= "2026-03-11"

    def test_list_events_with_category_filter(self, test_client, test_events, test_category):
        """Test listing events filtered by category."""
        response = test_client.get(
            "/api/events",
            params={"category_guid": test_category.guid},
        )
        assert response.status_code == 200

        events = response.json()
        assert len(events) >= 3

        # All events should have the test category
        for event in events:
            if event["category"]:
                assert event["category"]["guid"] == test_category.guid

    def test_list_events_with_status_filter(self, test_client, test_events):
        """Test listing events filtered by status."""
        response = test_client.get(
            "/api/events",
            params={"status": "future"},
        )
        assert response.status_code == 200

        events = response.json()
        for event in events:
            assert event["status"] == "future"

    def test_list_events_with_attendance_filter(self, test_client, test_events):
        """Test listing events filtered by attendance."""
        response = test_client.get(
            "/api/events",
            params={"attendance": "planned"},
        )
        assert response.status_code == 200

        events = response.json()
        for event in events:
            assert event["attendance"] == "planned"

    def test_list_events_ordered_by_date(self, test_client, test_events):
        """Test that events are returned ordered by date."""
        response = test_client.get("/api/events")
        assert response.status_code == 200

        events = response.json()
        if len(events) > 1:
            dates = [event["event_date"] for event in events]
            assert dates == sorted(dates)

    def test_get_event_by_guid(self, test_client, test_events):
        """Test getting event details by GUID."""
        event = test_events[0]

        response = test_client.get(f"/api/events/{event.guid}")
        assert response.status_code == 200

        data = response.json()
        assert data["guid"] == event.guid
        assert data["title"] == event.title
        assert data["event_date"] == str(event.event_date)
        assert data["status"] == event.status
        assert data["attendance"] == event.attendance

        # Detail response should include additional fields
        assert "description" in data
        assert "location" in data
        assert "organizer" in data
        assert "performers" in data
        assert "ticket_required" in data
        assert "travel_required" in data

    def test_get_event_not_found(self, test_client):
        """Test getting non-existent event."""
        response = test_client.get("/api/events/evt_00000000000000000000000001")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_event_invalid_guid(self, test_client):
        """Test getting event with invalid GUID format."""
        response = test_client.get("/api/events/invalid-guid")
        assert response.status_code == 404

    def test_list_series_events(self, test_client, test_series):
        """Test that series events are listed with series info."""
        series, events = test_series

        response = test_client.get("/api/events")
        assert response.status_code == 200

        result = response.json()

        # Find series events
        series_events = [e for e in result if e.get("series_guid")]
        assert len(series_events) >= 3

        for event in series_events:
            assert event["series_guid"] == series.guid
            assert event["sequence_number"] is not None
            assert event["series_total"] == 3
            # Series events should have title from series
            assert event["title"] == "Multi-Day Airshow"

    def test_get_series_event_details(self, test_client, test_series):
        """Test getting details for a series event."""
        series, events = test_series
        event = events[0]

        response = test_client.get(f"/api/events/{event.guid}")
        assert response.status_code == 200

        data = response.json()
        assert data["series_guid"] == series.guid
        assert data["sequence_number"] == 1
        assert data["series_total"] == 3
        assert data["title"] == "Multi-Day Airshow"

        # Should include series details
        assert "series" in data
        assert data["series"]["guid"] == series.guid
        assert data["series"]["title"] == "Multi-Day Airshow"
        assert data["series"]["total_events"] == 3

    def test_get_event_stats(self, test_client, test_events):
        """Test getting event statistics."""
        response = test_client.get("/api/events/stats")
        assert response.status_code == 200

        stats = response.json()
        assert "total_count" in stats
        assert "upcoming_count" in stats
        assert "this_month_count" in stats
        assert "attended_count" in stats

        # With test events, should have at least 3
        assert stats["total_count"] >= 3

    def test_get_event_stats_empty(self, test_client):
        """Test getting stats when no events exist."""
        response = test_client.get("/api/events/stats")
        assert response.status_code == 200

        stats = response.json()
        assert stats["total_count"] == 0
        assert stats["upcoming_count"] == 0
        assert stats["this_month_count"] == 0
        assert stats["attended_count"] == 0


class TestEventsSoftDelete:
    """Tests for soft-deleted events."""

    @pytest.fixture
    def deleted_event(self, test_db_session):
        """Create a soft-deleted event."""
        category = Category(
            name="Deleted Test Category",
            is_active=True,
            display_order=0,
        )
        test_db_session.add(category)
        test_db_session.commit()

        from datetime import datetime

        event = Event(
            title="Deleted Event",
            event_date=date(2026, 5, 15),
            status="cancelled",
            attendance="skipped",
            category_id=category.id,
            deleted_at=datetime.utcnow(),
        )
        test_db_session.add(event)
        test_db_session.commit()
        test_db_session.refresh(event)
        return event

    def test_list_events_excludes_deleted(self, test_client, deleted_event):
        """Test that soft-deleted events are excluded by default."""
        response = test_client.get("/api/events")
        assert response.status_code == 200

        events = response.json()
        guids = [e["guid"] for e in events]
        assert deleted_event.guid not in guids

    def test_list_events_includes_deleted(self, test_client, deleted_event):
        """Test that soft-deleted events can be included."""
        response = test_client.get(
            "/api/events",
            params={"include_deleted": True},
        )
        assert response.status_code == 200

        events = response.json()
        guids = [e["guid"] for e in events]
        assert deleted_event.guid in guids

    def test_get_deleted_event_excluded(self, test_client, deleted_event):
        """Test that soft-deleted event returns 404 by default."""
        response = test_client.get(f"/api/events/{deleted_event.guid}")
        assert response.status_code == 404

    def test_get_deleted_event_included(self, test_client, deleted_event):
        """Test that soft-deleted event can be retrieved."""
        response = test_client.get(
            f"/api/events/{deleted_event.guid}",
            params={"include_deleted": True},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["guid"] == deleted_event.guid
        assert data["deleted_at"] is not None
