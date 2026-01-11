"""
Events API endpoints for managing calendar events.

Provides endpoints for:
- Listing events with date range and filtering
- Getting event details
- Event statistics for KPIs

Phase 4 (MVP): List and get operations
Phase 5: Create, update, delete operations

Design:
- Uses dependency injection for services
- Comprehensive error handling with meaningful HTTP status codes
- All endpoints use GUID format (evt_xxx) for identifiers
- Date range queries support calendar views

Issue #39 - Calendar Events feature
"""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.schemas.event import (
    EventResponse,
    EventDetailResponse,
    EventStatsResponse,
    EventStatus,
    AttendanceStatus,
)
from backend.src.services.event_service import EventService
from backend.src.services.exceptions import NotFoundError, ValidationError
from backend.src.utils.logging_config import get_logger


logger = get_logger("api")

router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


# ============================================================================
# Dependencies
# ============================================================================


def get_event_service(db: Session = Depends(get_db)) -> EventService:
    """Create EventService instance with database session."""
    return EventService(db=db)


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/stats",
    response_model=EventStatsResponse,
    summary="Get event statistics",
    description="Get aggregated statistics for all events",
)
async def get_event_stats(
    event_service: EventService = Depends(get_event_service),
) -> EventStatsResponse:
    """
    Get aggregated statistics for all events.

    Returns:
        EventStatsResponse with:
        - total_count: Total non-deleted events
        - upcoming_count: Future events
        - this_month_count: Events this month
        - attended_count: Events marked as attended

    Example:
        GET /api/events/stats

        Response:
        {
          "total_count": 42,
          "upcoming_count": 15,
          "this_month_count": 3,
          "attended_count": 27
        }
    """
    try:
        stats = event_service.get_stats()

        logger.info(
            "Retrieved event stats",
            extra={"total_count": stats["total_count"]},
        )

        return EventStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting event stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event statistics",
        )


@router.get(
    "",
    response_model=List[EventResponse],
    summary="List events",
    description="List events with optional date range and filtering",
)
async def list_events(
    start_date: Optional[date] = Query(
        default=None,
        description="Start of date range (inclusive)",
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="End of date range (inclusive)",
    ),
    category_guid: Optional[str] = Query(
        default=None,
        description="Filter by category GUID",
    ),
    status: Optional[EventStatus] = Query(
        default=None,
        description="Filter by event status",
    ),
    attendance: Optional[AttendanceStatus] = Query(
        default=None,
        description="Filter by attendance status",
    ),
    include_deleted: bool = Query(
        default=False,
        description="Include soft-deleted events",
    ),
    event_service: EventService = Depends(get_event_service),
) -> List[EventResponse]:
    """
    List events with optional filtering.

    Query Parameters:
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        category_guid: Filter by category GUID
        status: Filter by event status (future, confirmed, completed, cancelled)
        attendance: Filter by attendance (planned, attended, skipped)
        include_deleted: Include soft-deleted events

    Returns:
        List of events ordered by date

    Example:
        GET /api/events?start_date=2026-01-01&end_date=2026-01-31

        Response:
        [
          {
            "guid": "evt_xxx",
            "title": "Airshow Day 1",
            "event_date": "2026-01-15",
            ...
          }
        ]
    """
    try:
        events = event_service.list(
            start_date=start_date,
            end_date=end_date,
            category_guid=category_guid,
            status=status.value if status else None,
            attendance=attendance.value if attendance else None,
            include_deleted=include_deleted,
        )

        logger.info(
            "Listed events",
            extra={
                "count": len(events),
                "start_date": str(start_date) if start_date else None,
                "end_date": str(end_date) if end_date else None,
            },
        )

        # Build response objects
        return [
            EventResponse(**event_service.build_event_response(event))
            for event in events
        ]

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Error listing events: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list events",
        )


@router.get(
    "/{guid}",
    response_model=EventDetailResponse,
    summary="Get event by GUID",
    description="Get detailed information about a specific event",
)
async def get_event(
    guid: str,
    include_deleted: bool = Query(
        default=False,
        description="Include soft-deleted event",
    ),
    event_service: EventService = Depends(get_event_service),
) -> EventDetailResponse:
    """
    Get event details by GUID.

    Path Parameters:
        guid: Event GUID (evt_xxx format)

    Query Parameters:
        include_deleted: Include soft-deleted event

    Returns:
        Full event details including related entities

    Raises:
        404: Event not found

    Example:
        GET /api/events/evt_01hgw2bbg0000000000000001

        Response:
        {
          "guid": "evt_01hgw2bbg0000000000000001",
          "title": "Oshkosh Airshow 2026",
          "description": "Annual EAA AirVenture",
          "event_date": "2026-07-27",
          ...
        }
    """
    try:
        event = event_service.get_by_guid(guid, include_deleted=include_deleted)

        logger.info(f"Retrieved event: {guid}")

        return EventDetailResponse(
            **event_service.build_event_detail_response(event)
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {guid} not found",
        )

    except Exception as e:
        logger.error(f"Error getting event {guid}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event",
        )
