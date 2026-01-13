# PRD: Cloud Drive Connectors - Microsoft OneDrive and Google Drive

**Issue**: #TBD
**Status**: Draft
**Created**: 2026-01-13
**Last Updated**: 2026-01-13
**Related Features**:
- 004-remote-photos-persistence (Connector architecture)
- 007-remote-photos-completion (Tool execution)

---

## Executive Summary

This PRD proposes extending the photo-admin connector architecture to support Microsoft OneDrive and Google Drive as remote storage backends. These consumer-focused cloud storage services are popular among photographers for personal photo backup and sharing. Adding support for these platforms enables users to analyze photo collections stored in their personal or business cloud drives without manual download.

### Current State

**Existing Connectors:**
- ✅ **AWS S3** - Enterprise object storage
- ✅ **Google Cloud Storage (GCS)** - Enterprise object storage (service account auth)
- ✅ **SMB/CIFS** - Network-attached storage shares

**Architecture Foundation:**
- `StorageAdapter` abstract base class with `list_files()` and `test_connection()` methods
- `ConnectorType` enum for storage type identification
- Encrypted credential storage with Fernet encryption
- GUID-based external identification (con_xxx format)
- Connection testing with exponential backoff retry

### What This PRD Delivers

- **OneDrive Connector**: Access Microsoft OneDrive personal and business storage via Microsoft Graph API
- **Google Drive Connector**: Access Google Drive personal and workspace storage via Google Drive API
- OAuth2 authentication flows for both platforms
- Token refresh and persistence mechanisms
- Unified file listing matching existing adapter patterns

---

## Background

### Problem Statement

Many photographers store photos in consumer cloud services for convenience:

1. **Automatic Phone Backup**: iOS/Android devices auto-upload to OneDrive/Google Drive
2. **Cross-Platform Access**: Easy sharing across devices without NAS infrastructure
3. **Storage Pricing**: Consumer plans often cheaper than enterprise storage for personal use
4. **Existing Workflows**: Users already have large collections in these services

Currently, users must:
1. Manually download entire photo libraries (often 100GB+)
2. Run photo-admin tools locally
3. Manage sync/versioning between local copies and cloud originals

### Strategic Value

Adding cloud drive support:
- Reduces barrier to entry for casual users
- Enables in-place analysis without download overhead
- Completes the "any storage, anywhere" vision for photo-admin
- Positions photo-admin for potential mobile/web client expansion

### Technical Challenges

Unlike S3/GCS/SMB which use straightforward credential-based access:

| Aspect | S3/GCS/SMB | OneDrive/Google Drive |
|--------|------------|----------------------|
| **Authentication** | API keys, service accounts, username/password | OAuth2 with user consent |
| **Token Lifecycle** | Static credentials | Access tokens expire (typically 1 hour) |
| **User Interaction** | One-time credential entry | Periodic re-authentication required |
| **Rate Limits** | Generally high | Stricter per-user quotas |
| **File Structure** | Flat namespace with paths | Hierarchical with folder IDs |

---

## Goals

### Primary Goals

1. **OneDrive Integration**: List and access photos in Microsoft OneDrive (personal/business)
2. **Google Drive Integration**: List and access photos in Google Drive (personal/workspace)
3. **OAuth2 Flow**: Implement secure browser-based authentication flow
4. **Token Management**: Handle token refresh and re-authentication gracefully
5. **Adapter Consistency**: Match existing `StorageAdapter` interface patterns

### Secondary Goals

1. **Incremental Sync**: Leverage change detection APIs for efficient re-scans
2. **Folder Selection**: Allow users to specify specific folders (not entire drive)
3. **Shared Drive Support**: Access team/shared drives in business accounts

### Non-Goals (v1)

1. **Write Operations**: No upload, rename, or delete functionality
2. **Real-Time Sync**: No continuous synchronization (on-demand analysis only)
3. **Mobile OAuth**: Browser-based auth only (no mobile app deep links)
4. **Local Caching**: No local file cache (stream on demand for analysis)

---

## User Personas

### Primary: Casual Photo Enthusiast (Sam)
- **Storage**: 50,000+ photos in Google Photos/Drive from phone backups
- **Current Pain**: Cannot analyze photo organization without downloading entire library
- **Desired Outcome**: Run PhotoStats directly on Google Drive without local copies
- **This PRD Delivers**: Google Drive connector with OAuth login

### Secondary: Microsoft 365 Business User (Pat)
- **Storage**: Work and personal photos in OneDrive for Business
- **Current Pain**: Must export OneDrive to local drive, run tools, manage sync
- **Desired Outcome**: Point photo-admin at OneDrive folder, get analysis
- **This PRD Delivers**: OneDrive connector supporting personal and business accounts

### Tertiary: Family Photographer (Jordan)
- **Storage**: Shared family photos in Google Workspace shared drive
- **Current Pain**: No way to analyze shared family archive quality
- **Desired Outcome**: Run Photo Pairing on shared Google Drive folder
- **This PRD Delivers**: Google Drive connector with shared drive support

---

## User Stories

### User Story 1: Connect Google Drive Account (Priority: P1) 🎯 MVP

**As** a photographer with photos in Google Drive
**I want to** connect my Google Drive account to photo-admin
**So that** I can analyze my cloud photo collection without downloading

**Acceptance Criteria:**
- Click "Add Connector" and select "Google Drive"
- Browser opens Google OAuth consent screen
- After authorization, connector appears in connector list
- Connector shows account email and available storage quota
- Connection test succeeds and shows accessible folders

**Independent Test:** Connect Google Drive, run PhotoStats on a Drive folder, view results without any local file copies

---

### User Story 2: Connect Microsoft OneDrive Account (Priority: P1) 🎯 MVP

**As** a photographer with photos in OneDrive
**I want to** connect my OneDrive account (personal or business) to photo-admin
**So that** I can analyze my cloud photo collection without downloading

**Acceptance Criteria:**
- Click "Add Connector" and select "OneDrive"
- Browser opens Microsoft OAuth consent screen
- After authorization, connector appears in connector list
- Connector shows account email and storage quota
- Connection test succeeds and shows accessible folders
- Works with both personal Microsoft accounts and Microsoft 365 business accounts

**Independent Test:** Connect OneDrive, run PhotoStats on a OneDrive folder, view results without any local file copies

---

### User Story 3: Handle Token Expiration Gracefully (Priority: P1)

**As** a user with a connected cloud drive
**I want to** be notified when my authorization expires
**So that** I can re-authorize without losing my connector configuration

**Acceptance Criteria:**
- When access token expires and refresh fails, connector shows "Re-authorization required" status
- User can click "Re-authorize" to repeat OAuth flow
- Existing connector settings (name, metadata) preserved after re-auth
- Clear error message if re-authorization fails
- Collections using the connector remain intact (paused, not deleted)

**Independent Test:** Wait for token expiration (or revoke manually), attempt tool execution, verify re-auth flow

---

### User Story 4: Select Specific Folders for Analysis (Priority: P2)

**As** a user with large cloud storage
**I want to** select specific folders for analysis
**So that** I don't analyze my entire drive (which includes documents, etc.)

**Acceptance Criteria:**
- When creating a collection from cloud drive connector, show folder picker
- Folder picker displays hierarchical folder structure
- Selected folder path stored with collection
- Tool execution scopes to selected folder only
- Support both regular folders and (for Google) shared drives

**Independent Test:** Create collection pointing to specific folder, verify only that folder's contents are analyzed

---

## Requirements

### Functional Requirements

#### Core Connector Support

- **FR-001**: Add `ONEDRIVE` and `GOOGLE_DRIVE` values to `ConnectorType` enum
- **FR-002**: Implement `OneDriveAdapter` extending `StorageAdapter` base class
- **FR-003**: Implement `GoogleDriveAdapter` extending `StorageAdapter` base class
- **FR-004**: Both adapters MUST implement `list_files(location)` returning list of file paths
- **FR-005**: Both adapters MUST implement `test_connection()` returning (success, message) tuple
- **FR-006**: Both adapters MUST follow existing retry pattern (3 attempts with exponential backoff)

#### OAuth2 Authentication

- **FR-010**: Implement OAuth2 authorization code flow for Google Drive
- **FR-011**: Implement OAuth2 authorization code flow for Microsoft OneDrive
- **FR-012**: Store encrypted OAuth tokens (access_token, refresh_token, expiry) in connector credentials
- **FR-013**: Implement automatic token refresh before expiration
- **FR-014**: Handle refresh token revocation with clear user feedback
- **FR-015**: Provide `/api/connectors/oauth/{provider}/authorize` endpoint returning auth URL
- **FR-016**: Provide `/api/connectors/oauth/{provider}/callback` endpoint handling OAuth callback

#### Credential Schemas

- **FR-020**: Create `OneDriveCredentials` Pydantic schema for OneDrive token storage
- **FR-021**: Create `GoogleDriveCredentials` Pydantic schema for Google Drive token storage
- **FR-022**: Both schemas MUST validate required OAuth response fields
- **FR-023**: Token refresh MUST update stored credentials atomically

#### API Integration

- **FR-030**: OneDrive adapter MUST use Microsoft Graph API (`graph.microsoft.com`)
- **FR-031**: Google Drive adapter MUST use Google Drive API v3
- **FR-032**: Both adapters MUST handle API rate limiting with appropriate backoff
- **FR-033**: File listing MUST handle pagination for large directories (1000+ files)

#### Frontend OAuth Flow

- **FR-040**: Add "OneDrive" and "Google Drive" options to connector type selector
- **FR-041**: Connector creation form MUST trigger OAuth flow instead of credential form
- **FR-042**: Display OAuth callback success/failure status
- **FR-043**: Show "Re-authorize" button when token refresh fails
- **FR-044**: Display connected account email/name in connector details

### Non-Functional Requirements

#### Security

- **NFR-001**: OAuth client secrets MUST be stored in environment variables (not codebase)
- **NFR-002**: All tokens MUST be encrypted at rest using existing Fernet encryption
- **NFR-003**: OAuth state parameter MUST be validated to prevent CSRF attacks
- **NFR-004**: Redirect URIs MUST be validated against whitelist
- **NFR-005**: Audit logging for OAuth operations (authorize, token refresh, revoke)

#### Performance

- **NFR-010**: Token refresh MUST complete within 5 seconds
- **NFR-011**: Initial folder listing MUST complete within 30 seconds for 10,000 files
- **NFR-012**: Adapter MUST cache folder structure for 5 minutes during active operations
- **NFR-013**: Connection test MUST complete within 10 seconds

#### Reliability

- **NFR-020**: Token refresh MUST retry 3 times before failing
- **NFR-021**: API calls MUST retry on 429 (rate limit) and 5xx errors
- **NFR-022**: Failed token refresh MUST NOT delete connector (only mark as needs re-auth)
- **NFR-023**: Connector status MUST reflect actual authorization state

#### Testing

- **NFR-030**: Backend test coverage MUST exceed 80% for new adapter code
- **NFR-031**: OAuth flow MUST have integration tests with mocked provider responses
- **NFR-032**: Token refresh logic MUST have dedicated unit tests
- **NFR-033**: Rate limit handling MUST have dedicated unit tests

---

## Technical Approach

### Architecture Extension

```
┌────────────────────────────────────────────────────────────────────┐
│                    StorageAdapter (Abstract Base)                   │
│  - list_files(location) → List[str]                                │
│  - test_connection() → Tuple[bool, str]                            │
└─────────────────────────────────┬──────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│  S3Adapter    │        │  GCSAdapter   │        │  SMBAdapter   │
│  (boto3)      │        │(google-cloud) │        │(smbprotocol)  │
└───────────────┘        └───────────────┘        └───────────────┘
                                  │
        ┌─────────────────────────┴─────────────────────────┐
        │                                                   │
        ▼                                                   ▼
┌─────────────────────┐                         ┌─────────────────────┐
│  GoogleDriveAdapter │                         │   OneDriveAdapter   │
│  (NEW)              │                         │   (NEW)             │
│                     │                         │                     │
│  Library:           │                         │  Library:           │
│  google-api-python- │                         │  msal +             │
│  client + google-   │                         │  msgraph-sdk-python │
│  auth-oauthlib      │                         │                     │
└─────────────────────┘                         └─────────────────────┘
```

### OAuth2 Flow Architecture

```
┌──────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Frontend │     │ Backend API  │     │ OAuth Provider  │     │   Database   │
│          │     │              │     │ (Google/MSFT)   │     │              │
└────┬─────┘     └──────┬───────┘     └────────┬────────┘     └──────┬───────┘
     │                  │                      │                     │
     │ 1. Create Connector (type=GOOGLE_DRIVE) │                     │
     │─────────────────►│                      │                     │
     │                  │                      │                     │
     │ 2. Return auth_url + state              │                     │
     │◄─────────────────│                      │                     │
     │                  │                      │                     │
     │ 3. Open auth_url in browser             │                     │
     │─────────────────────────────────────────►                     │
     │                  │                      │                     │
     │ 4. User grants consent                  │                     │
     │◄─────────────────────────────────────────                     │
     │                  │                      │                     │
     │ 5. Redirect to callback with code       │                     │
     │─────────────────►│                      │                     │
     │                  │                      │                     │
     │                  │ 6. Exchange code for tokens                │
     │                  │─────────────────────►│                     │
     │                  │◄─────────────────────│                     │
     │                  │                      │                     │
     │                  │ 7. Encrypt and store tokens                │
     │                  │────────────────────────────────────────────►
     │                  │                      │                     │
     │ 8. Connector created successfully       │                     │
     │◄─────────────────│                      │                     │
     │                  │                      │                     │
```

### Recommended Python Libraries

#### Google Drive

| Library | Purpose | Justification |
|---------|---------|---------------|
| `google-api-python-client` (2.x) | Google Drive API v3 client | Official Google SDK, well-maintained, comprehensive documentation |
| `google-auth` (2.x) | Authentication primitives | Required dependency, handles credential management |
| `google-auth-oauthlib` (1.x) | OAuth2 flow helpers | Simplifies OAuth2 authorization code flow for installed apps |

**Alternative Considered:** `pydrive2` - simpler API but less maintained, abstracts away too much control for our needs.

**Installation:**
```bash
pip install google-api-python-client google-auth-oauthlib
```

**Credential Storage Format (encrypted):**
```json
{
  "access_token": "ya29.a0AfH6SMB...",
  "refresh_token": "1//0e...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "xxx.apps.googleusercontent.com",
  "client_secret": "GOCSPX-xxx",
  "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
  "expiry": "2026-01-13T15:30:00Z",
  "account_email": "user@gmail.com"
}
```

**Required OAuth Scopes:**
- `https://www.googleapis.com/auth/drive.readonly` - Read-only access to files
- `https://www.googleapis.com/auth/drive.metadata.readonly` - Read-only access to file metadata

#### Microsoft OneDrive

| Library | Purpose | Justification |
|---------|---------|---------------|
| `msal` (1.x) | Microsoft Authentication Library | Official Microsoft auth library, handles OAuth2 + token refresh |
| `msgraph-sdk-python` (1.x) | Microsoft Graph API client | Official SDK for Graph API, type-safe, async support |

**Alternative Considered:** `O365` library - comprehensive but heavier weight, more opinionated about data models.

**Installation:**
```bash
pip install msal msgraph-sdk-python
```

**Credential Storage Format (encrypted):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1Q...",
  "refresh_token": "0.ARoAv4j5cvG...",
  "token_type": "Bearer",
  "expires_at": 1705159800,
  "scope": "Files.Read.All User.Read offline_access",
  "client_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "account_email": "user@outlook.com",
  "account_name": "John Doe"
}
```

**Required OAuth Scopes:**
- `Files.Read.All` - Read all files user can access
- `User.Read` - Read user profile (for account identification)
- `offline_access` - Obtain refresh token for long-lived access

### API Endpoints (New)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/connectors/oauth/google/authorize` | GET | Generate Google OAuth authorization URL |
| `/api/connectors/oauth/google/callback` | GET | Handle Google OAuth callback, store tokens |
| `/api/connectors/oauth/onedrive/authorize` | GET | Generate OneDrive OAuth authorization URL |
| `/api/connectors/oauth/onedrive/callback` | GET | Handle OneDrive OAuth callback, store tokens |
| `/api/connectors/{guid}/reauthorize` | POST | Trigger re-authorization for expired tokens |

### Credential Schema Additions

```python
class GoogleDriveCredentials(BaseModel):
    """Google Drive OAuth2 credentials."""
    access_token: str = Field(..., min_length=20)
    refresh_token: str = Field(..., min_length=20)
    token_uri: str = Field(default="https://oauth2.googleapis.com/token")
    client_id: str = Field(..., pattern=r".*\.apps\.googleusercontent\.com$")
    client_secret: str = Field(..., min_length=10)
    scopes: List[str] = Field(...)
    expiry: datetime = Field(...)
    account_email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")


class OneDriveCredentials(BaseModel):
    """Microsoft OneDrive OAuth2 credentials."""
    access_token: str = Field(..., min_length=20)
    refresh_token: str = Field(..., min_length=20)
    token_type: str = Field(default="Bearer")
    expires_at: int = Field(...)  # Unix timestamp
    scope: str = Field(...)
    client_id: str = Field(..., pattern=r"^[a-f0-9-]{36}$")
    account_email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    account_name: Optional[str] = Field(default=None)
```

### Environment Variables (New)

```bash
# Google Drive OAuth (from Google Cloud Console)
GOOGLE_DRIVE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_DRIVE_CLIENT_SECRET=GOCSPX-xxx

# Microsoft OneDrive OAuth (from Azure Portal)
ONEDRIVE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ONEDRIVE_CLIENT_SECRET=xxx~xxx

# OAuth callback base URL (for redirect URI construction)
OAUTH_REDIRECT_BASE_URL=http://localhost:8000
```

### Data Model Changes

#### ConnectorType Enum Extension

```python
class ConnectorType(enum.Enum):
    S3 = "s3"
    GCS = "gcs"
    SMB = "smb"
    GOOGLE_DRIVE = "google_drive"  # NEW
    ONEDRIVE = "onedrive"          # NEW
```

#### Collection Type Enum Extension

```python
class CollectionType(enum.Enum):
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    SMB = "smb"
    GOOGLE_DRIVE = "google_drive"  # NEW
    ONEDRIVE = "onedrive"          # NEW
```

#### GUID Prefix (Already Reserved)

Per `docs/domain-model.md`, connector GUIDs use `con_` prefix - no change needed.

### New Files

```
backend/src/
├── services/
│   ├── oauth/
│   │   ├── __init__.py
│   │   ├── google_oauth.py      # Google OAuth2 flow handler
│   │   └── microsoft_oauth.py   # Microsoft OAuth2 flow handler
│   └── remote/
│       ├── google_drive_adapter.py  # GoogleDriveAdapter
│       └── onedrive_adapter.py      # OneDriveAdapter
├── api/
│   └── oauth.py                 # OAuth endpoints router
└── schemas/
    └── oauth.py                 # OAuth-specific Pydantic schemas
```

---

## Implementation Plan

### Phase 1: Google Drive Connector (Priority: P1) 🎯 MVP

**Estimated Tasks: ~45**

**Backend (25 tasks):**
1. Add `GOOGLE_DRIVE` to `ConnectorType` and `CollectionType` enums
2. Create `GoogleDriveCredentials` Pydantic schema
3. Implement `GoogleOAuthService` with authorization URL generation
4. Implement OAuth callback handling with token exchange
5. Implement token refresh logic
6. Create `GoogleDriveAdapter` extending `StorageAdapter`
7. Implement `list_files()` with pagination via Drive API
8. Implement `test_connection()` verifying token validity
9. Add retry logic matching existing adapter patterns
10. Handle Google API rate limiting (429 responses)
11. Integrate with `ConnectorService` for adapter selection
12. Add OAuth endpoints to API router
13. Comprehensive unit tests (adapters, OAuth flow)
14. Integration tests with mocked Google API responses

**Frontend (15 tasks):**
1. Add "Google Drive" to connector type selector
2. Implement OAuth redirect flow (open auth URL)
3. Handle OAuth callback success page
4. Display connected Google account info
5. Add "Re-authorize" button for expired tokens
6. Update connector form for OAuth-based types
7. Component tests for OAuth flow UI

**Testing (5 tasks):**
1. Mock Google OAuth token exchange
2. Mock Drive API file listing responses
3. Test token refresh scenarios
4. Test rate limit handling
5. E2E test: OAuth → Connector → Collection → Tool execution

**Checkpoint:** Users can connect Google Drive and run PhotoStats on Drive folders.

---

### Phase 2: Microsoft OneDrive Connector (Priority: P1)

**Estimated Tasks: ~45**

**Backend (25 tasks):**
1. Add `ONEDRIVE` to `ConnectorType` and `CollectionType` enums
2. Create `OneDriveCredentials` Pydantic schema
3. Implement `MicrosoftOAuthService` with MSAL integration
4. Implement OAuth callback handling for Microsoft identity platform
5. Implement token refresh logic using MSAL
6. Create `OneDriveAdapter` extending `StorageAdapter`
7. Implement `list_files()` using Microsoft Graph API
8. Implement `test_connection()` verifying token validity
9. Add retry logic matching existing adapter patterns
10. Handle Graph API throttling (429 responses)
11. Support both personal and work/school accounts
12. Integrate with `ConnectorService`
13. Comprehensive unit tests
14. Integration tests with mocked Graph API responses

**Frontend (15 tasks):**
1. Add "OneDrive" to connector type selector
2. Implement OAuth redirect flow
3. Handle OAuth callback
4. Display connected Microsoft account info
5. Add "Re-authorize" button
6. Support account type indicator (personal vs business)
7. Component tests

**Testing (5 tasks):**
1. Mock MSAL token operations
2. Mock Graph API responses
3. Test personal vs business account handling
4. Test rate limit handling
5. E2E test: OAuth → Connector → Collection → Tool execution

**Checkpoint:** Users can connect OneDrive and run PhotoStats on OneDrive folders.

---

### Phase 3: Shared/Team Drive Support (Priority: P2)

**Estimated Tasks: ~20**

**Google Shared Drives (10 tasks):**
1. Extend `list_files()` to support shared drives
2. Add shared drive enumeration endpoint
3. UI for selecting shared drive vs personal drive
4. Update folder picker to show shared drives
5. Tests for shared drive access

**OneDrive Shared Libraries (10 tasks):**
1. Extend adapter for SharePoint document libraries
2. Add shared library enumeration endpoint
3. UI for selecting shared library
4. Update folder picker
5. Tests for shared library access

**Checkpoint:** Users can access team/shared drives in addition to personal drives.

---

### Phase 4: Incremental Sync Optimization (Priority: P3)

**Estimated Tasks: ~15**

**Change Detection (15 tasks):**
1. Implement Google Drive changes API integration
2. Implement Microsoft Graph delta queries
3. Store change tokens per collection
4. Skip unchanged files during re-analysis
5. UI indicator for "unchanged since last scan"
6. Tests for incremental sync logic

**Checkpoint:** Re-scans are faster when few files have changed.

---

## Risks and Mitigation

### Risk 1: OAuth Token Revocation
- **Impact**: High - User loses access, tool execution fails
- **Probability**: Medium (users may revoke in provider settings)
- **Mitigation**: Clear "re-authorize" flow; connector remains but paused; preserve settings on re-auth

### Risk 2: API Rate Limiting
- **Impact**: Medium - Slow listing, failed operations during high usage
- **Probability**: Medium (especially for large collections)
- **Mitigation**: Exponential backoff; pagination; request throttling; user notification of limits

### Risk 3: OAuth Client Secret Exposure
- **Impact**: Critical - Security breach
- **Probability**: Low (with proper practices)
- **Mitigation**: Environment variables only; never in code; secret scanning in CI; rotation procedure

### Risk 4: Provider API Changes
- **Impact**: Medium - Adapter breakage
- **Probability**: Low (stable APIs)
- **Mitigation**: Use official SDKs; version-pin dependencies; monitor deprecation notices

### Risk 5: Complex OAuth State Management
- **Impact**: Low - Confusing UX for re-auth
- **Probability**: Medium
- **Mitigation**: Clear connector status indicators; proactive token refresh before expiry

---

## Security Considerations

### OAuth Security Best Practices

1. **State Parameter**: Generate cryptographically random state, validate on callback
2. **PKCE**: Use PKCE (Proof Key for Code Exchange) for authorization code flow
3. **Secure Storage**: All tokens encrypted with Fernet before database storage
4. **Minimal Scopes**: Request only read-only access (no write permissions)
5. **Token Refresh**: Refresh proactively before expiry (5 min buffer)
6. **Audit Logging**: Log all OAuth operations with timestamps

### Provider Application Registration

**Google Cloud Console:**
1. Create OAuth2 client (Web application type)
2. Configure authorized redirect URIs
3. Enable Google Drive API
4. Set up OAuth consent screen (external or internal)

**Azure Portal (Microsoft Entra ID):**
1. Register application in App registrations
2. Configure redirect URIs (Web platform)
3. Add API permissions (Microsoft Graph: Files.Read.All, User.Read, offline_access)
4. Create client secret
5. Support both "Accounts in any organizational directory and personal Microsoft accounts"

---

## Open Questions

1. **Offline Support**: Should we support service-account style access for Google (via domain-wide delegation)?
2. **Folder Picker UX**: Modal with full folder tree, or simplified path input with validation?
3. **Multi-Account**: Allow multiple connectors of same type (e.g., two Google accounts)?
4. **Photo-Specific APIs**: Should Google Photos API be used instead of/alongside Drive API?
5. **Token Sharing**: Should one OAuth token be usable across multiple collections?

---

## Success Metrics

### Adoption Metrics
- **M1**: 50% of new connectors created are cloud drive types within 3 months
- **M2**: 80% of OAuth flows complete successfully on first attempt
- **M3**: <5% of connectors require re-authorization per month

### Performance Metrics
- **M4**: OAuth flow completes within 30 seconds
- **M5**: File listing for 10,000 files completes within 60 seconds
- **M6**: Token refresh completes within 5 seconds

### Reliability Metrics
- **M7**: 99% of token refreshes succeed without user intervention
- **M8**: Zero OAuth token leaks in logs or error messages
- **M9**: <1% of tool executions fail due to cloud drive issues

---

## Dependencies

### External Dependencies
- Google Cloud Console account for OAuth client registration
- Azure Portal account for Microsoft app registration
- OAuth redirect endpoint accessible during development

### Internal Dependencies
- ✅ Connector architecture (StorageAdapter, ConnectorType, encrypted credentials)
- ✅ Fernet encryption infrastructure
- ✅ GUID-based external identification
- ✅ Frontend connector management UI

### New Dependencies (to add to requirements.txt)
```
# Google Drive
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0

# Microsoft OneDrive
msal>=1.24.0
msgraph-sdk-python>=1.0.0
```

---

## Appendix

### A. Library Comparison Matrix

#### Google Drive Libraries

| Library | Stars | Last Update | Pros | Cons |
|---------|-------|-------------|------|------|
| `google-api-python-client` | 7k+ | Active | Official, comprehensive | Verbose, generic |
| `pydrive2` | 500+ | Maintained | Simple API, high-level | Less control, community-maintained |
| Direct REST | N/A | N/A | Full control | More code, handle auth manually |

**Recommendation:** `google-api-python-client` - Official support, well-documented, production-proven.

#### Microsoft OneDrive Libraries

| Library | Stars | Last Update | Pros | Cons |
|---------|-------|-------------|------|------|
| `msal` + `msgraph-sdk-python` | 800+/500+ | Active | Official, type-safe | Two libraries to manage |
| `O365` | 1.5k+ | Active | All-in-one, simple | Heavier, opinionated |
| Direct REST | N/A | N/A | Full control | Handle auth, pagination manually |

**Recommendation:** `msal` + `msgraph-sdk-python` - Official Microsoft support, clean separation of concerns.

### B. Sample Adapter Implementation (GoogleDriveAdapter)

```python
"""Google Drive storage adapter (implementation sketch)."""

from typing import List, Tuple, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.src.services.remote.base import StorageAdapter


class GoogleDriveAdapter(StorageAdapter):
    """Google Drive storage adapter using Google Drive API v3."""

    MAX_RETRIES = 3
    PAGE_SIZE = 1000

    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)

        # Build credentials object from stored tokens
        creds = Credentials(
            token=credentials["access_token"],
            refresh_token=credentials["refresh_token"],
            token_uri=credentials["token_uri"],
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            scopes=credentials["scopes"]
        )

        # Build Drive API service
        self.service = build('drive', 'v3', credentials=creds)

    def list_files(self, location: str) -> List[str]:
        """List files in specified folder."""
        # location = folder ID or 'root' for top-level
        folder_id = location if location else 'root'

        files = []
        page_token = None

        while True:
            query = f"'{folder_id}' in parents and trashed = false"
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType)',
                pageToken=page_token,
                pageSize=self.PAGE_SIZE
            ).execute()

            for file in response.get('files', []):
                if file['mimeType'] != 'application/vnd.google-apps.folder':
                    files.append(file['name'])

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return files

    def test_connection(self) -> Tuple[bool, str]:
        """Test connection by fetching about info."""
        try:
            about = self.service.about().get(fields='user').execute()
            email = about['user']['emailAddress']
            return True, f"Connected as {email}"
        except HttpError as e:
            return False, f"Connection failed: {e.reason}"
```

### C. OAuth State Flow Example

```python
"""OAuth state management (implementation sketch)."""

import secrets
from datetime import datetime, timedelta

class OAuthStateManager:
    """Manage OAuth state tokens with expiration."""

    def __init__(self):
        self._states = {}  # In production, use Redis or database

    def generate_state(self, connector_name: str) -> str:
        """Generate and store OAuth state."""
        state = secrets.token_urlsafe(32)
        self._states[state] = {
            'connector_name': connector_name,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=10)
        }
        return state

    def validate_state(self, state: str) -> dict | None:
        """Validate state and return associated data."""
        if state not in self._states:
            return None
        data = self._states[state]
        if datetime.utcnow() > data['expires_at']:
            del self._states[state]
            return None
        del self._states[state]  # Single-use
        return data
```

---

## Revision History

- **2026-01-13 (v1.0)**: Initial draft
  - Defined OneDrive and Google Drive connector requirements
  - Analyzed existing connector architecture
  - Recommended Python libraries (google-api-python-client, msal, msgraph-sdk-python)
  - Designed OAuth2 flow architecture
  - Created phased implementation plan
