# WebSocket Protocol: Real-Time Analysis Progress

**Feature**: 004-remote-photos-persistence
**Date**: 2025-12-29
**Protocol Version**: 1.0.0

## Overview

This document defines the WebSocket protocol for real-time progress updates during analysis tool execution (PhotoStats, Photo Pairing, Pipeline Validation). The protocol enables clients to receive live updates about files scanned, issues found, and execution stage without polling REST endpoints.

**Key Features**:
- Real-time progress streaming (files scanned, issues found, stage, percent complete)
- Queue position updates for pending jobs
- Completion/error notifications
- Graceful reconnection handling
- Background job continuation on disconnect

**Implementation** (from research.md Task 6):
- FastAPI WebSocket endpoint
- JSON event protocol with structured messages
- Backend polls job progress every 1 second and pushes to WebSocket
- Client disconnect doesn't stop job execution

---

## WebSocket Endpoint

### Connection URL

```
ws://localhost:8000/api/tools/progress/{job_id}
```

**Parameters**:
- `job_id` (path): UUID of the analysis job (returned from POST /api/tools/photostats, /api/tools/photo_pairing, /api/tools/pipeline_validation)

**Authentication**: None (localhost deployment for v1)

### Connection Example

```javascript
// JavaScript client
const jobId = "a3f8d5c2-1234-5678-90ab-cdef12345678";
const ws = new WebSocket(`ws://localhost:8000/api/tools/progress/${jobId}`);

ws.onopen = () => {
  console.log("WebSocket connected");
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("Received:", message);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("WebSocket closed");
};
```

```python
# Python client (using websockets library)
import asyncio
import websockets
import json

async def monitor_progress(job_id: str):
    uri = f"ws://localhost:8000/api/tools/progress/{job_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")

            if data["event"] in ["complete", "error", "cancelled"]:
                break
```

---

## Message Protocol

All messages are JSON objects with the following structure:

```json
{
  "event": "<event_type>",
  "data": { ... }
}
```

**Event Types**:
- `status`: Initial job status (sent immediately on connect)
- `progress`: Periodic progress updates (every 1 second during execution)
- `complete`: Job completed successfully
- `error`: Job failed with error
- `cancelled`: Job cancelled by user

---

## Event Schemas

### 1. Status Event (Initial)

Sent immediately after WebSocket connection established.

```json
{
  "event": "status",
  "data": {
    "job_id": "a3f8d5c2-1234-5678-90ab-cdef12345678",
    "status": "queued",
    "position": 2,
    "estimated_start_minutes": 10
  }
}
```

**Data Fields**:
- `job_id` (string): Job UUID
- `status` (string): Current job status (`queued` | `running` | `completed` | `failed` | `cancelled`)
- `position` (integer | null): Queue position (1-indexed, null if running/completed)
- `estimated_start_minutes` (integer | null): Estimated minutes until job starts (null if running/completed)

**Use Case**: Client displays initial status to user ("Your job is queued. Position: 2. Estimated start: 10 minutes")

---

### 2. Progress Event (Periodic)

Sent every 1 second while job is running (or when queue position changes for queued jobs).

```json
{
  "event": "progress",
  "data": {
    "status": "running",
    "progress": {
      "files_scanned": 1500,
      "issues_found": 12,
      "stage": "Scanning photos",
      "percent_complete": 30
    },
    "position": null
  }
}
```

**Data Fields**:
- `status` (string): Current job status (`queued` | `running`)
- `progress` (object | null): Progress details (null for queued jobs)
  - `files_scanned` (integer): Number of files processed
  - `issues_found` (integer): Number of issues detected (tool-specific: orphaned files, validation errors, etc.)
  - `stage` (string): Human-readable current stage (e.g., "Scanning photos", "Validating pipelines", "Generating report")
  - `percent_complete` (integer): Percentage complete (0-100)
- `position` (integer | null): Queue position (non-null only if status=queued)

**Use Case**: Client updates progress bar, displays file count and current stage

**Progress Fields by Tool**:

#### PhotoStats Progress
```json
{
  "files_scanned": 1500,
  "issues_found": 12,
  "stage": "Scanning photos",
  "percent_complete": 30
}
```

#### Photo Pairing Progress
```json
{
  "files_scanned": 2000,
  "camera_groups_found": 2,
  "stage": "Analyzing camera usage",
  "percent_complete": 50
}
```

#### Pipeline Validation Progress
```json
{
  "files_scanned": 3000,
  "image_groups_validated": 500,
  "consistent_count": 450,
  "partial_count": 40,
  "inconsistent_count": 10,
  "stage": "Validating image groups",
  "percent_complete": 75
}
```

---

### 3. Complete Event (Success)

Sent when job completes successfully.

```json
{
  "event": "complete",
  "data": {
    "result_id": 123,
    "message": "Analysis completed successfully"
  }
}
```

**Data Fields**:
- `result_id` (integer): ID of stored AnalysisResult record (for fetching full report via GET /api/results/{id})
- `message` (string): Success message

**Use Case**: Client navigates to result page or displays "View Report" link

**After Receiving**: WebSocket connection closes automatically.

---

### 4. Error Event (Failure)

Sent when job fails due to error.

```json
{
  "event": "error",
  "data": {
    "message": "Collection inaccessible: Network timeout after 30s"
  }
}
```

**Data Fields**:
- `message` (string): Human-readable error description (actionable guidance)

**Example Error Messages** (from research.md Task 2):
- `"Collection inaccessible: Invalid credentials (decryption failed)"`
- `"Collection inaccessible: Network timeout after 30s"`
- `"Analysis failed: Insufficient disk space for report generation"`
- `"Collection path not found: /photos/collection does not exist"`

**Use Case**: Client displays error with retry/fix instructions

**After Receiving**: WebSocket connection closes automatically.

---

### 5. Cancelled Event

Sent when job is cancelled by user (before execution starts).

```json
{
  "event": "cancelled",
  "data": {
    "message": "Job was cancelled by user"
  }
}
```

**Data Fields**:
- `message` (string): Cancellation reason

**Use Case**: Client displays cancellation notification

**After Receiving**: WebSocket connection closes automatically.

**Note**: Running jobs cannot be cancelled in v1 (only queued jobs). See research.md Task 4 for details.

---

## Connection Lifecycle

### 1. Connection Establishment

```text
Client                              Server
  |                                    |
  |--- WS Connect /api/tools/progress/{job_id} ---|
  |                                    |
  |<----------- WS Accept ------------|
  |                                    |
  |<-------- status event ------------|  (Immediate)
  |                                    |
```

### 2. Active Job Monitoring

```text
Client                              Server
  |                                    |
  |<-------- progress event ----------|  (Every 1 second)
  |                                    |
  |<-------- progress event ----------|
  |                                    |
  |<-------- progress event ----------|
  |                                    |
  |         ... continues until job finishes ...
  |                                    |
  |<-------- complete event ----------|  (Job done)
  |                                    |
  |<----------- WS Close -------------|
```

### 3. Queued Job Monitoring

```text
Client                              Server
  |                                    |
  |<-- progress event (position: 2) --|  (Every 1 second)
  |                                    |
  |<-- progress event (position: 1) --|  (Queue advanced)
  |                                    |
  |<-- progress event (status: running) --|  (Job started)
  |                                    |
  |         ... continues with file progress ...
  |                                    |
  |<-------- complete event ----------|
  |                                    |
  |<----------- WS Close -------------|
```

### 4. Client Disconnect (Job Continues)

```text
Client                              Server
  |                                    |
  |<-------- progress event ----------|
  |                                    |
  |----------- WS Close ------------->|  (Client disconnects)
  |                                    |
                                       |
                        [Job continues in background]
                                       |

  |                                    |
  |--- WS Connect /api/tools/progress/{same_job_id} ---|  (Reconnect)
  |                                    |
  |<-------- status event ------------|  (Current progress)
  |                                    |
  |<-------- progress event ----------|
  |                                    |
```

**Key Behavior**: Job execution is **not interrupted** when client disconnects. Client can reconnect using same `job_id` to resume monitoring.

---

## Error Handling

### Invalid Job ID

```json
{
  "event": "error",
  "data": {
    "message": "Job not found"
  }
}
```

**After Receiving**: WebSocket closes with code 1000 (normal closure).

### Job Already Completed

If client connects to a job that finished before connection:

```json
{
  "event": "complete",
  "data": {
    "result_id": 123,
    "message": "Analysis completed (job finished before connection)"
  }
}
```

**After Receiving**: WebSocket closes immediately.

### Server Error

If server encounters internal error during progress streaming:

```json
{
  "event": "error",
  "data": {
    "message": "Internal server error: Failed to fetch progress"
  }
}
```

**After Receiving**: WebSocket closes with code 1011 (server error).

---

## Reconnection Strategy

### Client-Side Reconnection Logic

```javascript
class ProgressMonitor {
  constructor(jobId) {
    this.jobId = jobId;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    this.ws = new WebSocket(`ws://localhost:8000/api/tools/progress/${this.jobId}`);

    this.ws.onopen = () => {
      console.log("WebSocket connected");
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    this.ws.onclose = (event) => {
      console.log("WebSocket closed:", event.code, event.reason);

      // Attempt reconnection if job still running
      if (this.shouldReconnect(event.code) && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        setTimeout(() => this.connect(), delay);
      }
    };
  }

  shouldReconnect(closeCode) {
    // Don't reconnect on normal closure (job finished) or client-initiated close
    return closeCode !== 1000 && closeCode !== 1001;
  }

  handleMessage(message) {
    switch (message.event) {
      case 'status':
      case 'progress':
        this.updateUI(message.data);
        break;

      case 'complete':
        this.showSuccess(message.data);
        break;

      case 'error':
        this.showError(message.data);
        break;

      case 'cancelled':
        this.showCancellation(message.data);
        break;
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
    }
  }
}

// Usage
const monitor = new ProgressMonitor(jobId);
monitor.connect();
```

**Reconnection Strategy**:
- Exponential backoff: 2s, 4s, 8s, 10s (capped at 10s)
- Maximum 5 reconnection attempts
- Don't reconnect if job finished (close code 1000)

---

## Performance Considerations

### Server-Side

- **Polling Interval**: Backend polls job.progress every 1 second
  - Balance: Real-time updates vs CPU overhead
  - Configurable via environment variable (default 1s)
- **Concurrent Connections**: One WebSocket per active job
  - For localhost deployment (single user), acceptable
  - If 100+ concurrent jobs needed, consider connection pooling
- **Memory**: WebSocket connections held in memory (FastAPI async)
  - Lightweight: ~10KB per connection

### Client-Side

- **Message Frequency**: Client receives ~1 message/second during job execution
  - Manageable for UI updates (React state updates)
- **Backpressure**: If client slow, server continues sending (no backpressure handling in v1)
- **Battery Impact**: Continuous WebSocket connection drains battery on mobile
  - v1 targets desktop browsers (Chrome, Firefox, Safari, Edge)

---

## Security Considerations

### v1 (Localhost Deployment)

- **No Authentication**: WebSocket connections are unauthenticated
  - Acceptable for localhost-only deployment (Assumption #10)
  - Job IDs are UUIDs (hard to guess)
- **No Encryption**: WebSocket uses `ws://` (not `wss://`)
  - Localhost traffic not encrypted (not a concern for v1)

### v2 (Remote Deployment)

- **JWT Authentication**: Include JWT token in WebSocket connection handshake
  ```javascript
  const ws = new WebSocket(`wss://example.com/api/tools/progress/${jobId}?token=${jwt_token}`);
  ```
- **WSS Encryption**: Use `wss://` for encrypted WebSocket connections
- **Rate Limiting**: Limit WebSocket connection attempts per IP

---

## Testing WebSocket Protocol

### Manual Testing (wscat)

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c "ws://localhost:8000/api/tools/progress/a3f8d5c2-1234-5678-90ab-cdef12345678"

# Expected output:
# Connected (press CTRL+C to quit)
# < {"event":"status","data":{"job_id":"a3f8d5c2-...","status":"queued","position":2}}
# < {"event":"progress","data":{"status":"running","progress":{...},"position":null}}
# < {"event":"complete","data":{"result_id":123,"message":"Analysis completed"}}
# Disconnected
```

### Automated Testing (pytest + websockets)

```python
# tests/integration/test_websocket.py

import pytest
import asyncio
import websockets
import json

@pytest.mark.asyncio
async def test_websocket_progress_updates(create_job):
    """Test WebSocket sends progress updates during job execution"""
    job_id = create_job(tool="photostats", collection_id=1)

    uri = f"ws://localhost:8000/api/tools/progress/{job_id}"
    async with websockets.connect(uri) as websocket:
        # Receive status event
        message = json.loads(await websocket.recv())
        assert message["event"] == "status"
        assert message["data"]["job_id"] == job_id

        # Receive progress events
        progress_count = 0
        while progress_count < 3:
            message = json.loads(await websocket.recv())
            if message["event"] == "progress":
                progress_count += 1
                assert "files_scanned" in message["data"]["progress"]

        # Receive complete event
        message = json.loads(await websocket.recv())
        assert message["event"] == "complete"
        assert "result_id" in message["data"]

@pytest.mark.asyncio
async def test_websocket_invalid_job_id():
    """Test WebSocket handles invalid job ID gracefully"""
    uri = "ws://localhost:8000/api/tools/progress/invalid-uuid"
    async with websockets.connect(uri) as websocket:
        message = json.loads(await websocket.recv())
        assert message["event"] == "error"
        assert "Job not found" in message["data"]["message"]
```

---

## Future Enhancements (v2)

### Bidirectional Commands

Allow client to send commands to server (pause, resume, cancel running jobs):

```json
// Client → Server
{
  "command": "pause"
}

// Server → Client
{
  "event": "paused",
  "data": {
    "message": "Job paused at 50% completion"
  }
}
```

### Multiple Job Monitoring

Single WebSocket connection for monitoring multiple jobs:

```
ws://localhost:8000/api/tools/progress?jobs=job1,job2,job3
```

### Batch Updates

Reduce message frequency by batching progress updates:

```json
{
  "event": "progress_batch",
  "data": [
    {"timestamp": "2025-12-29T10:00:01Z", "files_scanned": 1000},
    {"timestamp": "2025-12-29T10:00:02Z", "files_scanned": 1100},
    {"timestamp": "2025-12-29T10:00:03Z", "files_scanned": 1200}
  ]
}
```

---

## Summary

This WebSocket protocol provides:

- **Real-time updates**: 1-second polling interval for live progress
- **Graceful reconnection**: Client can reconnect to same job after disconnect
- **Background execution**: Jobs continue even if client disconnects
- **Clear event schema**: Structured JSON messages with type-safe fields
- **Error handling**: Actionable error messages for user guidance

**Next Steps**:
1. Implement FastAPI WebSocket endpoint (backend/src/api/tools.py)
2. Create React useAnalysisProgress hook (frontend/src/hooks/useAnalysisProgress.js)
3. Add WebSocket tests (pytest + websockets library)
4. Document reconnection strategy in quickstart.md
