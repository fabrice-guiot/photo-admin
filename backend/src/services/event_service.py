"""
Event service for managing calendar events.

Provides business logic for listing, retrieving, creating, updating, and
deleting calendar events with support for event series.

Design:
- Events can be standalone or part of a series
- Series events inherit properties from EventSeries
- Soft delete preserves event history
- Date range queries support calendar views
"""

from typing import List, Optional
from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_

from backend.src.models import Event, EventSeries, Category
from backend.src.utils.logging_config import get_logger
from backend.src.services.exceptions import NotFoundError, ValidationError
from backend.src.services.guid import GuidService


logger = get_logger("services")


class EventService:
    """
    Service for managing calendar events.

    Handles CRUD operations for events with support for:
    - Date range queries for calendar views
    - Event series (multi-day events)
    - Filtering by category, status, attendance
    - Soft delete

    Usage:
        >>> service = EventService(db_session)
        >>> events = service.list(
        ...     start_date=date(2026, 1, 1),
        ...     end_date=date(2026, 1, 31)
        ... )
    """

    def __init__(self, db: Session):
        """
        Initialize event service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_guid(self, guid: str, include_deleted: bool = False) -> Event:
        """
        Get an event by GUID.

        Args:
            guid: Event GUID (evt_xxx format)
            include_deleted: If True, include soft-deleted events

        Returns:
            Event instance with relationships loaded

        Raises:
            NotFoundError: If event not found
        """
        # Validate GUID format
        if not GuidService.validate_guid(guid, "evt"):
            raise NotFoundError("Event", guid)

        # Extract UUID from GUID
        try:
            uuid_value = GuidService.parse_guid(guid, "evt")
        except ValueError:
            raise NotFoundError("Event", guid)

        query = (
            self.db.query(Event)
            .options(
                joinedload(Event.category),
                joinedload(Event.series),
                joinedload(Event.location),
                joinedload(Event.organizer),
            )
            .filter(Event.uuid == uuid_value)
        )

        if not include_deleted:
            query = query.filter(Event.deleted_at.is_(None))

        event = query.first()
        if not event:
            raise NotFoundError("Event", guid)

        return event

    def get_by_id(self, event_id: int, include_deleted: bool = False) -> Event:
        """
        Get an event by internal ID.

        Args:
            event_id: Internal database ID
            include_deleted: If True, include soft-deleted events

        Returns:
            Event instance

        Raises:
            NotFoundError: If event not found
        """
        query = self.db.query(Event).filter(Event.id == event_id)

        if not include_deleted:
            query = query.filter(Event.deleted_at.is_(None))

        event = query.first()
        if not event:
            raise NotFoundError("Event", event_id)

        return event

    def list(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_guid: Optional[str] = None,
        status: Optional[str] = None,
        attendance: Optional[str] = None,
        include_deleted: bool = False,
    ) -> List[Event]:
        """
        List events with optional filtering.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            category_guid: Filter by category GUID
            status: Filter by event status
            attendance: Filter by attendance status
            include_deleted: If True, include soft-deleted events

        Returns:
            List of Event instances ordered by date
        """
        query = self.db.query(Event).options(
            joinedload(Event.category),
            joinedload(Event.series),
        )

        # Exclude soft-deleted unless requested
        if not include_deleted:
            query = query.filter(Event.deleted_at.is_(None))

        # Date range filter
        if start_date:
            query = query.filter(Event.event_date >= start_date)
        if end_date:
            query = query.filter(Event.event_date <= end_date)

        # Category filter
        if category_guid:
            if not GuidService.validate_guid(category_guid, "cat"):
                raise ValidationError(f"Invalid category GUID: {category_guid}", field="category_guid")
            try:
                cat_uuid = GuidService.parse_guid(category_guid, "cat")
                category = (
                    self.db.query(Category)
                    .filter(Category.uuid == cat_uuid)
                    .first()
                )
                if category:
                    # Include events directly in category OR in series with that category
                    query = query.outerjoin(Event.series).filter(
                        or_(
                            Event.category_id == category.id,
                            and_(
                                Event.category_id.is_(None),
                                EventSeries.category_id == category.id,
                            ),
                        )
                    )
            except ValueError:
                pass  # Invalid GUID, will return no results

        # Status filter
        if status:
            query = query.filter(Event.status == status)

        # Attendance filter
        if attendance:
            query = query.filter(Event.attendance == attendance)

        # Order by date, then by start time
        query = query.order_by(Event.event_date.asc(), Event.start_time.asc())

        return query.all()

    def list_by_month(self, year: int, month: int, include_deleted: bool = False) -> List[Event]:
        """
        List events for a specific month.

        Convenience method for calendar views.

        Args:
            year: Year (e.g., 2026)
            month: Month (1-12)
            include_deleted: If True, include soft-deleted events

        Returns:
            List of Event instances for the month
        """
        # Calculate first and last day of month
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1)
        else:
            last_day = date(year, month + 1, 1)

        # Subtract one day to get actual last day of month
        from datetime import timedelta
        last_day = last_day - timedelta(days=1)

        return self.list(
            start_date=first_day,
            end_date=last_day,
            include_deleted=include_deleted,
        )

    def get_stats(self) -> dict:
        """
        Get event statistics for KPIs.

        Returns:
            Dictionary with event statistics:
            - total_count: Total non-deleted events
            - upcoming_count: Events with status 'future' or 'confirmed'
            - this_month_count: Events in current month
            - attended_count: Events with attendance 'attended'
        """
        today = date.today()
        first_of_month = date(today.year, today.month, 1)
        if today.month == 12:
            first_of_next_month = date(today.year + 1, 1, 1)
        else:
            first_of_next_month = date(today.year, today.month + 1, 1)

        # Base query for non-deleted events
        base_query = self.db.query(func.count(Event.id)).filter(
            Event.deleted_at.is_(None)
        )

        total = base_query.scalar()

        upcoming = (
            base_query.filter(
                Event.event_date >= today,
                Event.status.in_(["future", "confirmed"]),
            ).scalar()
        )

        this_month = (
            base_query.filter(
                Event.event_date >= first_of_month,
                Event.event_date < first_of_next_month,
            ).scalar()
        )

        attended = (
            base_query.filter(Event.attendance == "attended").scalar()
        )

        return {
            "total_count": total or 0,
            "upcoming_count": upcoming or 0,
            "this_month_count": this_month or 0,
            "attended_count": attended or 0,
        }

    def get_series_by_guid(self, guid: str) -> EventSeries:
        """
        Get an event series by GUID.

        Args:
            guid: Series GUID (ser_xxx format)

        Returns:
            EventSeries instance with events loaded

        Raises:
            NotFoundError: If series not found
        """
        if not GuidService.validate_guid(guid, "ser"):
            raise NotFoundError("EventSeries", guid)

        try:
            uuid_value = GuidService.parse_guid(guid, "ser")
        except ValueError:
            raise NotFoundError("EventSeries", guid)

        series = (
            self.db.query(EventSeries)
            .options(joinedload(EventSeries.category))
            .filter(EventSeries.uuid == uuid_value)
            .first()
        )

        if not series:
            raise NotFoundError("EventSeries", guid)

        return series

    def build_event_response(self, event: Event) -> dict:
        """
        Build a response dictionary for an event.

        Computes effective fields (title, category) and includes
        series information.

        Args:
            event: Event instance with relationships loaded

        Returns:
            Dictionary suitable for EventResponse schema
        """
        # Get effective category (from event or series)
        category = event.category
        if not category and event.series:
            category = event.series.category

        category_data = None
        if category:
            category_data = {
                "guid": category.guid,
                "name": category.name,
                "icon": category.icon,
                "color": category.color,
            }

        response = {
            "guid": event.guid,
            "title": event.effective_title,
            "event_date": event.event_date,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "is_all_day": event.is_all_day,
            "input_timezone": event.input_timezone,
            "status": event.status,
            "attendance": event.attendance,
            "category": category_data,
            "series_guid": event.series.guid if event.series else None,
            "sequence_number": event.sequence_number,
            "series_total": event.series.total_events if event.series else None,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }

        return response

    def build_event_detail_response(self, event: Event) -> dict:
        """
        Build a detailed response dictionary for an event.

        Includes all event fields plus related entities.

        Args:
            event: Event instance with relationships loaded

        Returns:
            Dictionary suitable for EventDetailResponse schema
        """
        response = self.build_event_response(event)

        # Add description
        response["description"] = event.description

        # Add location
        if event.location:
            response["location"] = {
                "guid": event.location.guid,
                "name": event.location.name,
                "city": event.location.city,
                "country": event.location.country,
                "timezone": event.location.timezone,
            }
        else:
            response["location"] = None

        # Add organizer
        if event.organizer:
            response["organizer"] = {
                "guid": event.organizer.guid,
                "name": event.organizer.name,
            }
        else:
            response["organizer"] = None

        # Add performers
        performers = []
        for ep in event.event_performers:
            if ep.performer:
                performers.append({
                    "guid": ep.performer.guid,
                    "name": ep.performer.name,
                })
        response["performers"] = performers

        # Add series details
        if event.series:
            response["series"] = {
                "guid": event.series.guid,
                "title": event.series.title,
                "total_events": event.series.total_events,
            }
        else:
            response["series"] = None

        # Add logistics
        response["ticket_required"] = event.ticket_required
        response["ticket_status"] = event.ticket_status
        response["ticket_purchase_date"] = event.ticket_purchase_date
        response["timeoff_required"] = event.timeoff_required
        response["timeoff_status"] = event.timeoff_status
        response["timeoff_booking_date"] = event.timeoff_booking_date
        response["travel_required"] = event.travel_required
        response["travel_status"] = event.travel_status
        response["travel_booking_date"] = event.travel_booking_date
        response["deadline_date"] = event.deadline_date

        # Add soft delete
        response["deleted_at"] = event.deleted_at

        return response
