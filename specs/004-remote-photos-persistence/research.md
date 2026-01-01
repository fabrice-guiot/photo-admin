# Research: Remote Photo Collections and Analysis Persistence

**Feature**: 004-remote-photos-persistence
**Date**: 2025-12-29
**Status**: Complete

## Overview

This document captures technical research and decisions for the 8 research tasks identified in Phase 0 of the implementation plan. Each task resolves specific technical unknowns before proceeding to design and implementation phases.

All decisions prioritize v1 simplicity, align with Constitution principles (YAGNI, clear error messages, no over-engineering), and meet performance constraints (<2s collection listing, <1s queries, 80% cache reduction).

---

## Research Task 1: Database Schema Design for JSONB Analysis Results

### Question

How to structure JSONB columns for PhotoStats, Photo Pairing, and Pipeline Validation results with different schemas while supporting efficient queries and schema evolution?

### Decision

**Use PostgreSQL with JSONB columns for analysis results, storing full tool output as schema-versioned JSON documents.**

Schema structure:
```sql
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES collections(id),
    tool VARCHAR(50) NOT NULL,  -- 'photostats', 'photo_pairing', 'pipeline_validation'
    pipeline_id INTEGER REFERENCES pipelines(id),  -- NULL for non-pipeline tools
    executed_at TIMESTAMP DEFAULT NOW(),
    results JSONB NOT NULL,  -- Full analysis output with schema_version field
    report_html TEXT,  -- Pre-generated HTML report
    status VARCHAR(50) NOT NULL,  -- 'completed', 'failed', 'running'
    error_message TEXT,
    schema_version VARCHAR(20) NOT NULL  -- e.g., "1.0.0" for version tracking
);

-- Indexes for query performance
CREATE INDEX idx_analysis_collection ON analysis_results(collection_id);
CREATE INDEX idx_analysis_tool ON analysis_results(tool);
CREATE INDEX idx_analysis_executed ON analysis_results(executed_at DESC);
CREATE INDEX idx_analysis_status ON analysis_results(status);

-- GIN index for JSONB queries (trend analysis, filtering)
CREATE INDEX idx_analysis_results_gin ON analysis_results USING GIN (results);
```

### Rationale

1. **JSONB over separate tables**: Each tool produces different output structures (PhotoStats: orphaned files count, Photo Pairing: camera groups, Pipeline Validation: CONSISTENT/PARTIAL/INCONSISTENT breakdowns). Separate tables would require 3+ schemas and complex joins. JSONB stores variable structures naturally.

2. **Schema versioning**: Adding `schema_version` field (e.g., "1.0.0") to results JSON enables handling tool evolution. When tools add/change output fields, new results store updated schema version. Queries can filter by version or handle multiple versions gracefully.

3. **Pre-generated HTML storage**: Storing `report_html` in TEXT column avoids re-rendering from JSONB (FR-046: regenerate reports from stored results <500ms). Jinja2 template changes won't break historical reports.

4. **GIN indexing**: PostgreSQL GIN (Generalized Inverted Index) on JSONB enables fast queries like "find all PhotoStats results with orphaned_files_count > 10". Supports trend analysis (FR-047) efficiently.

5. **Separate tool column**: Using VARCHAR tool identifier instead of polymorphic table simplifies queries and satisfies NFR1.2 (<1s for 1000+ results).

### Alternatives Considered

**Alternative A: Separate tables per tool (analysis_photostats, analysis_pairing, analysis_pipeline)**
- ❌ Rejected: Requires 3+ tables, complex unions for listing all results (FR-044), and migration headaches when tools evolve
- ❌ Violates YAGNI: Over-engineered for v1 when JSONB handles variable schemas elegantly

**Alternative B: MongoDB (document database)**
- ❌ Rejected: Additional infrastructure complexity (separate database server), less mature Python tooling than PostgreSQL+SQLAlchemy
- ❌ Weaker consistency guarantees: ACID transactions critical for FR-019 (discard partial results on failure)
- ✅ Would simplify schema evolution but JSONB achieves same flexibility with better ecosystem

**Alternative C: Store results as separate JSON files on filesystem**
- ❌ Rejected: Cannot support NFR1.2 (queries <1s for 1000+ results), no transactions (FR-019), no concurrent access control
- ❌ No query capabilities: Cannot filter by date range, collection, or tool efficiently

### Implementation Notes

1. **JSONB structure per tool** (example):
   ```json
   {
     "schema_version": "1.0.0",
     "tool": "photostats",
     "summary": {
       "total_files": 5000,
       "orphaned_files_count": 12,
       "missing_sidecars_count": 3
     },
     "orphaned_files": ["AB3D0001.jpg", "..."],
     "missing_sidecars": ["AB3D0002.cr3"]
   }
   ```

2. **Schema evolution strategy**:
   - Backend services check `schema_version` when parsing results
   - Migration scripts can transform old versions if needed (but generally avoid)
   - Frontend displays warning for unsupported schema versions

3. **Query examples for trend analysis**:
   ```sql
   -- Orphaned files trend for collection
   SELECT executed_at,
          (results->'summary'->>'orphaned_files_count')::int as count
   FROM analysis_results
   WHERE collection_id = ? AND tool = 'photostats'
   ORDER BY executed_at DESC LIMIT 10;
   ```

4. **Performance considerations**:
   - GIN index size grows with JSONB complexity; monitor index bloat
   - For large result sets (1M+ files), consider pagination with LIMIT/OFFSET
   - Pre-generated HTML avoids Jinja2 rendering costs for historical reports

5. **Encoding**: All file operations for report_html and JSON serialization MUST use `encoding='utf-8'` (Constitution: Cross-Platform File Encoding)

---

## Research Task 2: Credential Encryption Strategy

### Question

How to securely encrypt/decrypt AWS S3, GCS, and SMB credentials in database without storing plaintext keys?

### Decision

**Use Python cryptography library with Fernet (symmetric encryption), environment-based master key storage, and Connector pattern for credential reuse.**

**Note**: Credentials are stored in dedicated `Connector` entities (not per-collection) to enable:
- Credential reuse across multiple collections (e.g., 50 S3 buckets share one AWS account)
- Simplified master key rotation (re-encrypt Connector table instead of every Collection)

Implementation:
```python
from cryptography.fernet import Fernet
import os

class CredentialEncryptor:
    def __init__(self):
        # Master key from environment variable (set on server startup)
        key = os.environ.get('PHOTO_ADMIN_ENCRYPTION_KEY')
        if not key:
            raise ValueError("PHOTO_ADMIN_ENCRYPTION_KEY environment variable not set")
        self.cipher = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        """Encrypt credentials for database storage"""
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt credentials from database"""
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

Storage in database (Connector pattern):
```sql
CREATE TABLE connectors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,  -- 's3', 'gcs', 'smb'
    credentials TEXT NOT NULL,  -- Encrypted JSON string
    -- ... other fields
);

CREATE TABLE collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    location TEXT NOT NULL,
    connector_id INTEGER REFERENCES connectors(id),  -- NULL for local, required for remote
    -- ... other fields
);
```

### Rationale

1. **Fernet symmetric encryption**: AES-128 in CBC mode with HMAC for authentication. Simple API (`encrypt()`/`decrypt()`), secure defaults, no complex key management. Meets security requirement (no plaintext storage per FR-010).

2. **Environment variable for master key**: Storing encryption key in environment variable (not in code/database) follows best practices. Key rotation possible by re-encrypting all credentials with new key and updating environment variable.

3. **JSON storage in TEXT**: Each connector type needs different credential fields (S3: access_key + secret_key, GCS: service_account_json, SMB: username + password). Store credentials as encrypted JSON string (TEXT column). Encrypt entire JSON string before storage. **Connector pattern**: Multiple collections share one connector, reducing credential duplication and simplifying key rotation.

4. **No system keyring (v1 simplicity)**: System keyring (keyring library) requires platform-specific setup (macOS Keychain, Windows Credential Vault, Linux Secret Service). Environment variable approach is cross-platform and simpler for localhost deployment (Assumption #10: local-only for v1).

5. **Encryption-at-rest**: PostgreSQL itself doesn't need encryption-at-rest for v1 (localhost deployment). Master key in environment variable provides encryption layer above database storage.

### Alternatives Considered

**Alternative A: System keyring (keyring library)**
- ❌ Rejected: Requires platform-specific setup, complicates deployment
- ❌ Over-engineered for v1: Local-only deployment doesn't need OS-level secret storage
- ✅ Consider for v2 if multi-user or remote deployment needed

**Alternative B: HashiCorp Vault or AWS Secrets Manager**
- ❌ Rejected: Massive over-engineering for v1, requires external infrastructure
- ❌ Violates YAGNI and Constitution simplicity principles
- ✅ Only justified if deploying to production with strict compliance requirements

**Alternative C: Asymmetric encryption (RSA)**
- ❌ Rejected: More complex (public/private key pairs), slower performance
- ❌ No benefit: Symmetric encryption sufficient when master key is secured via environment variable

**Alternative D: No encryption (store plaintext)**
- ❌ Rejected: Security risk (database backups, logs expose credentials)
- ❌ Violates FR-010 (securely store credentials)

### Implementation Notes

1. **Master key generation and setup** (one-time setup):
   - **Tool**: `setup_master_key.py` - Interactive CLI tool for generating and configuring master key
   - **Features**:
     - Generate cryptographically secure key (`Fernet.generate_key()`)
     - Display platform-specific instructions (macOS/Linux/Windows)
     - Optional: Save to secure file (`~/.photo_admin_master_key.txt` with chmod 600)
     - Validate existing key format
     - Warn about key loss consequences
   - **Server startup validation**: `web_server.py` checks for `PHOTO_ADMIN_MASTER_KEY` env var on startup
     - If missing: Print error message pointing to `setup_master_key.py` and exit
     - If invalid format: Validate with `Fernet(key)` and exit with helpful error
   - **Benefits**: Prevents server startup without encryption, provides clear setup guidance

   Manual key generation (if tool unavailable):
   ```python
   from cryptography.fernet import Fernet
   key = Fernet.generate_key()
   print(f"PHOTO_ADMIN_MASTER_KEY={key.decode()}")
   # Add to .env file (gitignored)
   ```

2. **Credential storage workflow**:
   - User creates Connector in web UI (provide name, type, credentials)
   - Backend encrypts entire credential JSON before saving to `connectors` table
   - User creates Collections referencing existing Connector (via connector_id foreign key)
   - FastAPI dependency injects CredentialEncryptor into connector_service

3. **Credential retrieval workflow**:
   - Backend fetches encrypted credentials from database
   - Decrypts before passing to remote storage adapters (S3Adapter, GCSAdapter, SMBAdapter)
   - Never log decrypted credentials (only log "Credentials loaded successfully")

4. **Key rotation strategy** (future):
   - Generate new master key (via `setup_master_key.py --rotate`)
   - Fetch all connectors from `connectors` table (far fewer than collections)
   - Decrypt with old key, re-encrypt with new key, update database
   - Update PHOTO_ADMIN_MASTER_KEY environment variable
   - **Benefit of Connector pattern**: Rotate N connectors instead of M collections (where M >> N)
   - Update environment variable
   - Restart server

5. **Error handling**:
   - Invalid master key: Raise clear error on server startup
   - Decryption failure: Collection marked as "inaccessible" with error message "Invalid credentials (decryption failed)"
   - Missing environment variable: Server refuses to start (fail fast)

6. **Security considerations**:
   - Master key MUST NOT be committed to version control (.env in .gitignore)
   - Rotate master key if compromised
   - Database backups contain encrypted credentials (safe)
   - Logs MUST NOT contain decrypted credentials

---

## Research Task 3: File Listing Cache Implementation

### Question

How to cache remote file listings with collection-aware TTL (1hr/24hr/7day) while achieving 80% API call reduction?

### Decision

**Use in-memory cache (Python dict with TTL metadata) for v1, with cache keyed by collection ID.**

Implementation:
```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
import threading

@dataclass
class CachedFileListing:
    files: List[str]  # List of file paths
    cached_at: datetime
    ttl_seconds: int

    def is_expired(self) -> bool:
        expiry = self.cached_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry

class FileListingCache:
    """In-memory cache for remote collection file listings"""

    def __init__(self):
        self._cache: dict[int, CachedFileListing] = {}  # collection_id -> CachedFileListing
        self._lock = threading.Lock()  # Thread-safe for concurrent requests

    def get(self, collection_id: int) -> Optional[List[str]]:
        """Get cached file listing if not expired"""
        with self._lock:
            cached = self._cache.get(collection_id)
            if cached and not cached.is_expired():
                return cached.files
            elif cached and cached.is_expired():
                del self._cache[collection_id]  # Remove expired entry
            return None

    def set(self, collection_id: int, files: List[str], ttl_seconds: int):
        """Store file listing with TTL"""
        with self._lock:
            self._cache[collection_id] = CachedFileListing(
                files=files,
                cached_at=datetime.utcnow(),
                ttl_seconds=ttl_seconds
            )

    def invalidate(self, collection_id: int):
        """Manually invalidate cache (FR-013a: manual refresh)"""
        with self._lock:
            self._cache.pop(collection_id, None)

    def clear(self):
        """Clear entire cache (for testing or memory management)"""
        with self._lock:
            self._cache.clear()
```

TTL mapping (Collection state → Cache TTL):
```python
COLLECTION_STATE_TTL = {
    "Live": 3600,      # 1 hour (active work, frequent changes)
    "Closed": 86400,   # 24 hours (infrequent changes)
    "Archived": 604800 # 7 days (infrastructure monitoring only)
}
```

### Rationale

1. **In-memory cache for v1 simplicity**: Python dict with TTL checks avoids external dependencies (Redis). Suitable for localhost deployment (Assumption #10). Cache persists during server lifetime but resets on restart (acceptable for v1).

2. **Collection-aware TTL**: Different collection states require different freshness guarantees (Assumption #7). Live collections (active photography) need 1-hour TTL; Archived collections (rarely change) can use 7-day TTL. User-configurable override per collection (FR-013).

3. **80% API call reduction**: With proper TTL, most collection access hits cache. Example: 10 collections analyzed monthly = 10 API calls/month vs 10 API calls per analysis (100+ calls) = 90% reduction.

4. **Thread safety**: FastAPI async endpoints may access cache concurrently. `threading.Lock` ensures safe read/write operations.

5. **Manual invalidation support**: FR-013a requires manual refresh button with cost warning (>100K files). `invalidate()` method forces cache expiry.

### Alternatives Considered

**Alternative A: Redis for persistent caching**
- ❌ Rejected: External dependency (Redis server), over-engineered for v1
- ❌ Violates Constitution simplicity: In-memory cache sufficient for localhost deployment
- ✅ Consider for v2 if multi-process deployment or persistent cache needed

**Alternative B: SQLite database for cache storage**
- ❌ Rejected: Slower than in-memory dict, requires file I/O, adds complexity
- ❌ No significant benefit: Cache doesn't need durability (re-fetch on server restart is acceptable)

**Alternative C: Filesystem cache (JSON files per collection)**
- ❌ Rejected: Slower than memory, requires file management, complicates invalidation
- ❌ Cross-platform encoding issues (Windows/Linux path separators, UTF-8 handling)

**Alternative D: No caching (always fetch from remote)**
- ❌ Rejected: Violates NFR1.3 (80% cache reduction), causes API rate limiting (Risk #2 in PRD)
- ❌ Poor UX: Slow collection listing, expensive for large collections (1M+ files)

### Implementation Notes

1. **Cache initialization**: Create singleton FileListingCache instance in FastAPI app startup:
   ```python
   from fastapi import FastAPI

   app = FastAPI()
   app.state.file_cache = FileListingCache()
   ```

2. **Collection service integration**:
   ```python
   async def get_collection_files(collection_id: int, cache: FileListingCache) -> List[str]:
       # Try cache first
       cached_files = cache.get(collection_id)
       if cached_files:
           return cached_files

       # Cache miss - fetch from remote storage
       collection = get_collection(collection_id)
       adapter = get_storage_adapter(collection)
       files = await adapter.list_files(collection.location)

       # Store in cache with collection-specific TTL
       ttl = collection.cache_ttl or COLLECTION_STATE_TTL[collection.state]
       cache.set(collection_id, files, ttl)

       return files
   ```

3. **Manual refresh with cost warning** (FR-013a):
   ```python
   @app.post("/api/collections/{id}/refresh")
   async def refresh_collection(id: int):
       collection = get_collection(id)
       cached_files = app.state.file_cache.get(id)

       # Show warning if file count exceeds threshold
       if cached_files and len(cached_files) > 100_000:
           return {
               "warning": "This collection has 150,000 files. Refreshing will incur API costs.",
               "requires_confirmation": True
           }

       # Invalidate cache and fetch new listing
       app.state.file_cache.invalidate(id)
       files = await get_collection_files(id, app.state.file_cache)
       return {"message": "Cache refreshed", "file_count": len(files)}
   ```

4. **Memory management**: Cache stores file paths (strings), not file contents. For 1M files × 100 chars/path = 100MB memory (acceptable). Consider LRU eviction if memory becomes concern.

5. **Cache metrics** (for monitoring):
   - Cache hit rate: hits / (hits + misses)
   - API call reduction: (cached_requests / total_requests) × 100%
   - Average cache TTL per collection state

6. **Testing considerations**:
   - Mock datetime.utcnow() to test expiry logic
   - Test thread safety with concurrent access
   - Verify cache invalidation on manual refresh

---

## Research Task 4: Job Queue for Concurrent Analysis

### Question

Should we use FastAPI BackgroundTasks or Celery/RQ for analysis job queue with position tracking and cancellation?

### Decision

**Use FastAPI BackgroundTasks with in-memory job queue for v1.**

Implementation:
```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
import asyncio
import threading

class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AnalysisJob:
    id: str  # UUID
    collection_id: int
    tool: str  # 'photostats', 'photo_pairing', 'pipeline_validation'
    pipeline_id: Optional[int]
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Dict[str, any] = field(default_factory=dict)  # {files_scanned: 100, stage: "scanning"}
    error_message: Optional[str] = None

class JobQueue:
    """In-memory job queue for analysis tasks"""

    def __init__(self):
        self._jobs: Dict[str, AnalysisJob] = {}
        self._queue: List[str] = []  # job_ids in order
        self._lock = threading.Lock()
        self._current_job: Optional[str] = None  # Currently running job_id

    def enqueue(self, job: AnalysisJob) -> int:
        """Add job to queue, return position (1-indexed)"""
        with self._lock:
            self._jobs[job.id] = job
            self._queue.append(job.id)
            return len(self._queue)  # Position in queue

    def dequeue(self) -> Optional[AnalysisJob]:
        """Get next job from queue"""
        with self._lock:
            if not self._queue:
                return None
            job_id = self._queue.pop(0)
            job = self._jobs[job_id]
            self._current_job = job_id
            return job

    def get_position(self, job_id: str) -> Optional[int]:
        """Get job position in queue (1-indexed, None if not queued)"""
        with self._lock:
            try:
                return self._queue.index(job_id) + 1
            except ValueError:
                return None

    def cancel(self, job_id: str):
        """Cancel queued job (cannot cancel running job)"""
        with self._lock:
            if job_id in self._queue:
                self._queue.remove(job_id)
                self._jobs[job_id].status = JobStatus.CANCELLED
            elif self._current_job == job_id:
                raise ValueError("Cannot cancel running job")
            else:
                raise ValueError("Job not found or already completed")

    def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        """Get job by ID"""
        return self._jobs.get(job_id)
```

FastAPI integration:
```python
from fastapi import FastAPI, BackgroundTasks
import uuid

app = FastAPI()
app.state.job_queue = JobQueue()

@app.post("/api/tools/photostats")
async def run_photostats(collection_id: int, background_tasks: BackgroundTasks):
    # Check for existing job on same collection
    existing_job = find_active_job(collection_id, "photostats")
    if existing_job:
        position = app.state.job_queue.get_position(existing_job.id)
        return {
            "message": "Analysis queued",
            "job_id": existing_job.id,
            "position": position,
            "estimated_start_minutes": position * 5  # Rough estimate
        }

    # Create new job
    job = AnalysisJob(
        id=str(uuid.uuid4()),
        collection_id=collection_id,
        tool="photostats",
        pipeline_id=None,
        status=JobStatus.QUEUED,
        created_at=datetime.utcnow()
    )

    position = app.state.job_queue.enqueue(job)

    # Start worker if queue was empty
    if position == 1:
        background_tasks.add_task(process_job_queue)

    return {
        "message": "Analysis queued",
        "job_id": job.id,
        "position": position,
        "estimated_start_minutes": (position - 1) * 5
    }

async def process_job_queue():
    """Worker that processes jobs sequentially"""
    while True:
        job = app.state.job_queue.dequeue()
        if not job:
            break  # Queue empty

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()

        try:
            # Run analysis tool
            result = await run_analysis_tool(job)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
```

### Rationale

1. **FastAPI BackgroundTasks for v1**: Simple, built-in mechanism for async tasks. No external infrastructure (Celery requires Redis/RabbitMQ broker). Satisfies FR-043 (sequential queue with position display).

2. **Sequential processing per collection**: Queue prevents concurrent analysis on same collection (FR-043). Jobs processed one at a time maintains simplicity and avoids resource contention.

3. **In-memory job tracking**: Stores job metadata (id, status, progress) in Python dict. Sufficient for localhost deployment (Assumption #10). Jobs lost on server restart (acceptable for v1).

4. **Position tracking**: Queue maintains FIFO order, calculates position for user display (Clarification #1: "Position: 2. Estimated start: 5 minutes").

5. **Cancellation support**: Can cancel queued jobs (remove from queue), but not running jobs (too complex for v1). Satisfies Clarification #3 (cancel jobs on collection deletion).

### Alternatives Considered

**Alternative A: Celery with Redis broker**
- ❌ Rejected: Requires external infrastructure (Redis server), complex setup
- ❌ Over-engineered for v1: In-memory queue sufficient for localhost deployment
- ✅ Consider for v2 if: distributed deployment, job persistence across restarts, advanced scheduling

**Alternative B: RQ (Redis Queue)**
- ❌ Rejected: Still requires Redis, less feature-rich than Celery
- ❌ Same concerns as Celery: external dependency, over-engineering

**Alternative C: Python multiprocessing.Queue**
- ❌ Rejected: Complicates FastAPI async model, harder to integrate with WebSocket progress
- ❌ No built-in job tracking (id, status, progress)

**Alternative D: Database-backed queue (poll jobs table)**
- ❌ Rejected: Polling database inefficient, adds latency
- ❌ Complicates job lifecycle management (QUEUED → RUNNING → COMPLETED)

### Implementation Notes

1. **Job ID generation**: Use UUID4 for unique job identifiers (globally unique, no collisions).

2. **Progress tracking**: Update job.progress dict from analysis tool:
   ```python
   job.progress = {
       "files_scanned": 1500,
       "issues_found": 12,
       "stage": "Scanning photos",
       "percent_complete": 30
   }
   ```

3. **WebSocket integration** (see Research Task 6): WebSocket handler subscribes to job progress updates.

4. **Job cleanup**: Periodically remove completed/failed jobs older than 24 hours to prevent memory growth:
   ```python
   async def cleanup_old_jobs():
       """Background task to remove old jobs"""
       cutoff = datetime.utcnow() - timedelta(hours=24)
       for job_id, job in list(app.state.job_queue._jobs.items()):
           if job.completed_at and job.completed_at < cutoff:
               del app.state.job_queue._jobs[job_id]
   ```

5. **Error handling**:
   - Analysis tool failure: Set job.status = FAILED, store error_message (FR-040)
   - Server restart: All jobs lost (acceptable for v1, document limitation)
   - Collection becomes inaccessible mid-analysis: Job fails, error_message = "Collection inaccessible"

6. **Testing considerations**:
   - Mock analysis tool execution (fast tests)
   - Test queue order (FIFO)
   - Test cancellation (queued vs running)
   - Test concurrent enqueue operations (thread safety)

7. **Performance**: Single-worker queue means one analysis at a time globally. For v1 (localhost, single user), acceptable. Multi-worker queue deferred to future if concurrent analysis needed.

---

## Research Task 5: YAML Import Conflict Resolution UI

### Question

How to build side-by-side comparison UI for YAML import conflicts when existing database settings differ from imported YAML?

### Decision

**Use React component with diff view showing database values vs YAML values, allowing user to select winner per conflicting key.**

Frontend component structure:
```jsx
// ConflictResolver.jsx
import React, { useState } from 'react';

function ConflictResolver({ conflicts, onResolve }) {
  const [selections, setSelections] = useState({});

  // conflicts = [
  //   {
  //     key: "photo_extensions",
  //     db_value: [".dng", ".cr3"],
  //     yaml_value: [".dng", ".cr3", ".tiff"],
  //     type: "list"
  //   },
  //   {
  //     key: "camera_mappings.AB3D[0].serial_number",
  //     db_value: "12345",
  //     yaml_value: "67890",
  //     type: "string"
  //   }
  // ]

  const handleSelect = (conflictKey, source) => {
    setSelections({ ...selections, [conflictKey]: source });
  };

  const handleResolve = () => {
    onResolve(selections);  // {key: "database" | "yaml"}
  };

  return (
    <div className="conflict-resolver">
      <h2>Configuration Import Conflicts</h2>
      <p>The following settings differ between database and YAML. Choose which values to keep:</p>

      {conflicts.map(conflict => (
        <ConflictRow
          key={conflict.key}
          conflict={conflict}
          selection={selections[conflict.key]}
          onSelect={handleSelect}
        />
      ))}

      <button onClick={handleResolve} disabled={Object.keys(selections).length !== conflicts.length}>
        Resolve Conflicts
      </button>
    </div>
  );
}

function ConflictRow({ conflict, selection, onSelect }) {
  return (
    <div className="conflict-row">
      <div className="conflict-key">{conflict.key}</div>

      <div className="conflict-options">
        <div className={`option ${selection === 'database' ? 'selected' : ''}`}
             onClick={() => onSelect(conflict.key, 'database')}>
          <h4>Database (Current)</h4>
          <pre>{JSON.stringify(conflict.db_value, null, 2)}</pre>
        </div>

        <div className={`option ${selection === 'yaml' ? 'selected' : ''}`}
             onClick={() => onSelect(conflict.key, 'yaml')}>
          <h4>YAML (Import)</h4>
          <pre>{JSON.stringify(conflict.yaml_value, null, 2)}</pre>
        </div>
      </div>
    </div>
  );
}

export default ConflictResolver;
```

Backend conflict detection:
```python
from typing import List, Dict, Any

@dataclass
class ConfigConflict:
    key: str
    db_value: Any
    yaml_value: Any
    type: str  # "string", "list", "dict"

def detect_conflicts(db_config: Dict, yaml_config: Dict) -> List[ConfigConflict]:
    """Compare database and YAML config, return conflicts"""
    conflicts = []

    # Top-level keys
    for key in yaml_config:
        if key not in db_config:
            continue  # No conflict, YAML adds new key

        db_val = db_config[key]
        yaml_val = yaml_config[key]

        if db_val != yaml_val:
            # Handle nested objects (camera_mappings)
            if isinstance(db_val, dict) and isinstance(yaml_val, dict):
                conflicts.extend(_detect_nested_conflicts(key, db_val, yaml_val))
            else:
                conflicts.append(ConfigConflict(
                    key=key,
                    db_value=db_val,
                    yaml_value=yaml_val,
                    type=_infer_type(yaml_val)
                ))

    return conflicts

def _detect_nested_conflicts(prefix: str, db_dict: Dict, yaml_dict: Dict) -> List[ConfigConflict]:
    """Recursively detect conflicts in nested dictionaries"""
    conflicts = []
    for key in yaml_dict:
        full_key = f"{prefix}.{key}"
        if key not in db_dict:
            continue
        if db_dict[key] != yaml_dict[key]:
            conflicts.append(ConfigConflict(
                key=full_key,
                db_value=db_dict[key],
                yaml_value=yaml_dict[key],
                type=_infer_type(yaml_dict[key])
            ))
    return conflicts

@app.post("/api/config/import")
async def import_yaml_config(file: UploadFile):
    """Import YAML config with conflict detection"""
    yaml_config = yaml.safe_load(await file.read())
    db_config = get_current_config()

    conflicts = detect_conflicts(db_config, yaml_config)

    if conflicts:
        # Store pending import in session for later resolution
        session_id = store_pending_import(yaml_config, conflicts)
        return {
            "status": "conflicts",
            "session_id": session_id,
            "conflicts": [asdict(c) for c in conflicts]
        }
    else:
        # No conflicts, import directly
        apply_yaml_config(yaml_config)
        return {"status": "success", "message": "Configuration imported"}

@app.post("/api/config/resolve")
async def resolve_conflicts(session_id: str, selections: Dict[str, str]):
    """Apply user's conflict resolution selections"""
    pending = get_pending_import(session_id)
    yaml_config = pending["yaml_config"]
    db_config = get_current_config()

    # Merge configs based on selections
    merged = {}
    for conflict_key, source in selections.items():
        if source == "database":
            merged[conflict_key] = _get_nested_value(db_config, conflict_key)
        else:  # "yaml"
            merged[conflict_key] = _get_nested_value(yaml_config, conflict_key)

    # Apply merged config
    apply_yaml_config(yaml_config, overrides=merged)
    delete_pending_import(session_id)

    return {"status": "success", "message": "Configuration imported with conflict resolution"}
```

### Rationale

1. **Side-by-side comparison**: Clear visual diff shows both values (database current vs YAML import). User clicks to select winner per conflict. Satisfies Clarification #4.

2. **Nested object support**: Handles complex configs (camera_mappings with nested serial_number, name fields). Flattens keys with dot notation (e.g., "camera_mappings.AB3D[0].serial_number").

3. **Atomic transaction**: Backend stores pending import in session, only applies after user resolves all conflicts. Prevents partial imports (FR-019: database transactions).

4. **No automatic merging**: Avoids complex merge strategies (union, intersection, deep merge). User makes all decisions explicitly (Constitution: clear over clever).

5. **Session-based workflow**: Store pending import server-side (in-memory dict with session_id). Frontend displays conflicts, user resolves, backend applies. Simpler than multi-step wizard.

### Alternatives Considered

**Alternative A: Automatic merge strategies (union, last-write-wins)**
- ❌ Rejected: Can produce unexpected results, loses user data silently
- ❌ Violates user-centric design: Users should control conflict resolution explicitly

**Alternative B: Three-way merge (common ancestor + 2 versions)**
- ❌ Rejected: Over-engineered, no "ancestor" version in this context
- ❌ Config changes don't have version history (unlike git)

**Alternative C: Show all conflicts upfront, no side-by-side**
- ❌ Rejected: Poor UX, hard to compare values (especially lists/dicts)
- ❌ User can't see what they're choosing between

**Alternative D: Always overwrite database with YAML (no conflict resolution)**
- ❌ Rejected: Loses user's database config changes
- ❌ Violates FR-021 (conflict resolution UI required)

### Implementation Notes

1. **Conflict types**:
   - Simple values (strings, integers): Direct comparison
   - Lists: Compare order and contents (e.g., [".dng", ".cr3"] vs [".dng", ".cr3", ".tiff"])
   - Dicts: Recursive comparison (camera_mappings)

2. **UI/UX considerations**:
   - Highlight differences (red = removed, green = added)
   - Use JSON pretty-print for readability
   - Require selection for ALL conflicts before proceeding (disable "Resolve" button until complete)
   - Show count: "3 conflicts require resolution"

3. **Backend storage**:
   - In-memory session storage for v1 (sufficient for localhost)
   - Session expiry: 1 hour (user must complete import or restart)
   - Store: `pending_imports[session_id] = {yaml_config, conflicts, created_at}`

4. **Testing considerations**:
   - Test nested conflict detection (camera_mappings)
   - Test atomic import (rollback if error during apply)
   - Test session expiry
   - Test edge cases (empty lists, null values)

5. **Error handling**:
   - Invalid YAML file: Show parse error before conflict detection
   - Database write failure during apply: Rollback transaction, show error
   - Session expired: Show "Import session expired, please restart"

6. **Encoding**: YAML file upload MUST be decoded with UTF-8 (Constitution: Cross-Platform File Encoding)

---

## Research Task 6: WebSocket Protocol for Progress Updates

### Question

How to stream real-time progress (files scanned, issues found) via WebSocket during analysis execution?

### Decision

**Use FastAPI WebSocket with JSON event protocol for real-time progress updates.**

WebSocket endpoint:
```python
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

@app.websocket("/api/tools/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()

    job = app.state.job_queue.get_job(job_id)
    if not job:
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Job not found"}
        })
        await websocket.close()
        return

    try:
        # Send initial status
        await websocket.send_json({
            "event": "status",
            "data": {
                "job_id": job.id,
                "status": job.status.value,
                "position": app.state.job_queue.get_position(job_id)
            }
        })

        # Stream progress updates
        while job.status in [JobStatus.QUEUED, JobStatus.RUNNING]:
            await asyncio.sleep(1)  # Poll every second

            await websocket.send_json({
                "event": "progress",
                "data": {
                    "status": job.status.value,
                    "progress": job.progress,  # {files_scanned, issues_found, stage, percent_complete}
                    "position": app.state.job_queue.get_position(job_id)
                }
            })

        # Send final status
        if job.status == JobStatus.COMPLETED:
            await websocket.send_json({
                "event": "complete",
                "data": {
                    "result_id": job.result_id,  # Link to stored analysis result
                    "message": "Analysis completed"
                }
            })
        elif job.status == JobStatus.FAILED:
            await websocket.send_json({
                "event": "error",
                "data": {
                    "message": job.error_message
                }
            })
        elif job.status == JobStatus.CANCELLED:
            await websocket.send_json({
                "event": "cancelled",
                "data": {"message": "Job was cancelled"}
            })

    except WebSocketDisconnect:
        # Client disconnected, continue job in background
        pass
    finally:
        await websocket.close()
```

Frontend WebSocket client:
```jsx
// useAnalysisProgress.js
import { useEffect, useState } from 'react';

function useAnalysisProgress(jobId) {
  const [progress, setProgress] = useState(null);
  const [status, setStatus] = useState('connecting');
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!jobId) return;

    const ws = new WebSocket(`ws://localhost:8000/api/tools/progress/${jobId}`);

    ws.onopen = () => {
      setStatus('connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.event) {
        case 'status':
        case 'progress':
          setProgress(message.data);
          setStatus(message.data.status);
          break;

        case 'complete':
          setProgress(message.data);
          setStatus('completed');
          break;

        case 'error':
          setError(message.data.message);
          setStatus('error');
          break;

        case 'cancelled':
          setStatus('cancelled');
          break;
      }
    };

    ws.onerror = (error) => {
      setError('WebSocket connection error');
      setStatus('error');
    };

    ws.onclose = () => {
      if (status === 'running') {
        // Unexpected disconnect, show reconnection message
        setError('Connection lost. Job continues in background.');
      }
    };

    return () => ws.close();
  }, [jobId]);

  return { progress, status, error };
}

// ProgressMonitor.jsx
function ProgressMonitor({ jobId }) {
  const { progress, status, error } = useAnalysisProgress(jobId);

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (status === 'completed') {
    return <div>Analysis complete! <a href={`/results/${progress.result_id}`}>View Report</a></div>;
  }

  return (
    <div className="progress-monitor">
      <h3>Analysis Progress</h3>
      <p>Status: {status}</p>
      {progress && (
        <>
          <p>Stage: {progress.progress.stage}</p>
          <p>Files Scanned: {progress.progress.files_scanned}</p>
          <p>Issues Found: {progress.progress.issues_found}</p>
          <ProgressBar percent={progress.progress.percent_complete} />
        </>
      )}
    </div>
  );
}
```

Message schema:
```json
// Event: status (initial)
{
  "event": "status",
  "data": {
    "job_id": "uuid",
    "status": "queued" | "running",
    "position": 2  // Queue position (null if running)
  }
}

// Event: progress (periodic updates)
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

// Event: complete (success)
{
  "event": "complete",
  "data": {
    "result_id": 123,
    "message": "Analysis completed"
  }
}

// Event: error (failure)
{
  "event": "error",
  "data": {
    "message": "Collection inaccessible: Network timeout"
  }
}

// Event: cancelled
{
  "event": "cancelled",
  "data": {
    "message": "Job was cancelled"
  }
}
```

### Rationale

1. **FastAPI WebSocket**: Built-in support, no external dependencies. Async-native (non-blocking for concurrent connections). Satisfies FR-037 (real-time progress updates).

2. **JSON event protocol**: Structured messages with `event` type and `data` payload. Easy to extend (add new event types), type-safe in frontend.

3. **Polling vs push**: Backend polls job.progress every 1 second and pushes to WebSocket. Simpler than pub/sub (Redis) for v1. Analysis tools update job.progress dict directly.

4. **Graceful disconnects**: Client disconnect doesn't stop job (FR-038: background execution). User can reconnect by reopening WebSocket to same job_id.

5. **Queue position updates**: WebSocket sends position updates for queued jobs (Clarification #1: display queue position). Client shows "Position: 2. Estimated start: 5 minutes".

### Alternatives Considered

**Alternative A: Server-Sent Events (SSE)**
- ❌ Rejected: One-way only (server → client), cannot send client commands (future: pause/resume)
- ❌ Less flexible than WebSocket for interactive features

**Alternative B: Polling REST API (GET /api/tools/status/{job_id})**
- ❌ Rejected: Higher latency (client polls every 2-3 seconds), more HTTP overhead
- ❌ Not "real-time" (user experience worse than WebSocket push)

**Alternative C: Redis Pub/Sub for progress events**
- ❌ Rejected: Requires Redis infrastructure, over-engineered for v1
- ❌ In-memory job queue sufficient for localhost deployment

**Alternative D: Long polling**
- ❌ Rejected: Complex to implement, higher latency than WebSocket
- ❌ WebSocket is standard for real-time updates

### Implementation Notes

1. **Analysis tool integration**: Tools update job.progress during execution:
   ```python
   def run_photostats(collection_id: int, job: AnalysisJob):
       files = get_collection_files(collection_id)
       total_files = len(files)

       for i, file in enumerate(files):
           # Update progress
           job.progress = {
               "files_scanned": i + 1,
               "issues_found": len(orphaned_files),
               "stage": "Scanning photos",
               "percent_complete": int((i + 1) / total_files * 100)
           }

           # ... analyze file ...
   ```

2. **WebSocket connection lifecycle**:
   - Client connects: Send initial status
   - While job active: Poll job.progress every 1 second, push updates
   - Job completes: Send final event (complete/error/cancelled), close connection
   - Client disconnects: Job continues, client can reconnect

3. **Reconnection handling**: Frontend should handle WebSocket close and allow user to reconnect:
   ```jsx
   const reconnect = () => {
     // Create new WebSocket with same job_id
   };
   ```

4. **Testing considerations**:
   - Mock WebSocket client in frontend tests
   - Test backend WebSocket endpoint with pytest-asyncio and websockets library
   - Test disconnect scenarios (client closes, server closes)

5. **Error handling**:
   - Invalid job_id: Send error event, close connection
   - Job already completed: Send complete event immediately, close
   - Server error: Send error event, close connection

6. **Performance**: One WebSocket connection per active job. For localhost deployment (single user), acceptable. If 100+ concurrent jobs needed, consider connection pooling.

7. **Security** (future): For remote deployment, add WebSocket authentication (JWT token in connection handshake).

---

## Research Task 7: Pipeline Validation Integration

### Question

How to validate pipeline structure (cycles, orphaned nodes) and generate filename previews for form-based pipeline editor?

### Decision

**Use graph algorithms (topological sort for cycle detection, DFS for orphaned node detection) with validation rules per node type.**

Validation implementation:
```python
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

@dataclass
class ValidationError:
    node_id: str
    error_type: str  # "orphaned", "cycle", "invalid_property", "missing_edge"
    message: str
    guidance: str  # Actionable fix suggestion

class PipelineValidator:
    """Validates pipeline structure and generates filename previews"""

    def __init__(self, pipeline_config: Dict):
        self.nodes = pipeline_config["nodes"]  # {node_id: {type, properties, ...}}
        self.edges = pipeline_config["edges"]  # [{source, target, ...}]

    def validate(self) -> Tuple[bool, List[ValidationError]]:
        """Validate pipeline structure (FR-028)"""
        errors = []

        # Check for cycles
        cycle_errors = self._detect_cycles()
        errors.extend(cycle_errors)

        # Check for orphaned nodes
        orphaned_errors = self._detect_orphaned_nodes()
        errors.extend(orphaned_errors)

        # Validate node types and properties
        node_errors = self._validate_nodes()
        errors.extend(node_errors)

        # Validate edges (valid source/target references)
        edge_errors = self._validate_edges()
        errors.extend(edge_errors)

        return (len(errors) == 0, errors)

    def _detect_cycles(self) -> List[ValidationError]:
        """Use topological sort to detect cycles"""
        # Build adjacency list
        graph = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            graph[edge["source"]].append(edge["target"])

        # Kahn's algorithm for topological sort
        in_degree = {node_id: 0 for node_id in self.nodes}
        for edge in self.edges:
            in_degree[edge["target"]] += 1

        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        sorted_nodes = []

        while queue:
            node_id = queue.pop(0)
            sorted_nodes.append(node_id)
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If not all nodes sorted, cycle exists
        if len(sorted_nodes) != len(self.nodes):
            cycle_nodes = [n for n in self.nodes if n not in sorted_nodes]
            return [ValidationError(
                node_id=cycle_nodes[0],
                error_type="cycle",
                message=f"Cycle detected involving nodes: {', '.join(cycle_nodes)}",
                guidance="Remove one edge to break the cycle. Pipelines must be directed acyclic graphs (DAGs)."
            )]

        return []

    def _detect_orphaned_nodes(self) -> List[ValidationError]:
        """Detect nodes with no incoming edges (except Capture)"""
        nodes_with_incoming = {edge["target"] for edge in self.edges}

        errors = []
        for node_id, node in self.nodes.items():
            # Capture nodes can have no incoming edges (they're entry points)
            if node["type"] == "Capture":
                continue

            if node_id not in nodes_with_incoming:
                errors.append(ValidationError(
                    node_id=node_id,
                    error_type="orphaned",
                    message=f"Node '{node_id}' has no incoming edges",
                    guidance="Connect this node to a previous stage in the pipeline."
                ))

        return errors

    def _validate_nodes(self) -> List[ValidationError]:
        """Validate node-specific properties"""
        errors = []

        for node_id, node in self.nodes.items():
            node_type = node["type"]

            # Validate required properties
            if node_type == "Process":
                if "processing_method" not in node.get("properties", {}):
                    errors.append(ValidationError(
                        node_id=node_id,
                        error_type="invalid_property",
                        message=f"Processing node '{node_id}' missing processing_method",
                        guidance="Add a processing method (e.g., HDR, BW, Pano) to this node."
                    ))

            elif node_type == "File":
                if "file_extension" not in node.get("properties", {}):
                    errors.append(ValidationError(
                        node_id=node_id,
                        error_type="invalid_property",
                        message=f"File node '{node_id}' missing file_extension",
                        guidance="Specify file extension (e.g., .dng, .jpg) for this node."
                    ))

            elif node_type == "Termination":
                if "termination_type" not in node.get("properties", {}):
                    errors.append(ValidationError(
                        node_id=node_id,
                        error_type="invalid_property",
                        message=f"Termination node '{node_id}' missing termination_type",
                        guidance="Add termination type (e.g., Archive, Delete, Export) to this node."
                    ))

        return errors

    def _validate_edges(self) -> List[ValidationError]:
        """Validate edge references"""
        errors = []
        node_ids = set(self.nodes.keys())

        for edge in self.edges:
            if edge["source"] not in node_ids:
                errors.append(ValidationError(
                    node_id=edge["source"],
                    error_type="missing_edge",
                    message=f"Edge references non-existent source node '{edge['source']}'",
                    guidance="Remove this edge or create the missing source node."
                ))

            if edge["target"] not in node_ids:
                errors.append(ValidationError(
                    node_id=edge["target"],
                    error_type="missing_edge",
                    message=f"Edge references non-existent target node '{edge['target']}'",
                    guidance="Remove this edge or create the missing target node."
                ))

        return errors

    def preview_filenames(self, camera_id: str = "AB3D", start_counter: int = 1) -> List[str]:
        """Generate expected filenames from pipeline (FR-031)"""
        # Perform graph traversal from Capture nodes
        filenames = []

        # Find all paths from Capture to Termination
        capture_nodes = [nid for nid, n in self.nodes.items() if n["type"] == "Capture"]

        for capture_id in capture_nodes:
            paths = self._find_all_paths(capture_id)

            for path in paths:
                # Build filename from path (camera_id + counter + properties)
                filename_parts = [camera_id, f"{start_counter:04d}"]

                for node_id in path:
                    node = self.nodes[node_id]
                    if node["type"] == "Process":
                        filename_parts.append(node["properties"]["processing_method"])
                    elif node["type"] == "File":
                        ext = node["properties"]["file_extension"]

                filename = "-".join(filename_parts[:-1]) + filename_parts[-1]  # AB3D0001-HDR.dng
                filenames.append(filename)

        return filenames

    def _find_all_paths(self, start_node: str) -> List[List[str]]:
        """Find all paths from start node to Termination nodes (DFS)"""
        # Build adjacency list
        graph = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            graph[edge["source"]].append(edge["target"])

        paths = []

        def dfs(node_id: str, path: List[str]):
            path.append(node_id)

            # If termination node, save path
            if self.nodes[node_id]["type"] == "Termination":
                paths.append(path.copy())
            else:
                # Continue traversal
                for neighbor in graph[node_id]:
                    dfs(neighbor, path)

            path.pop()

        dfs(start_node, [])
        return paths
```

API integration:
```python
@app.post("/api/pipelines/{id}/validate")
async def validate_pipeline(id: int):
    """Validate pipeline structure (FR-028)"""
    pipeline = get_pipeline(id)
    validator = PipelineValidator(pipeline.config)

    is_valid, errors = validator.validate()

    return {
        "valid": is_valid,
        "errors": [
            {
                "node_id": e.node_id,
                "error_type": e.error_type,
                "message": e.message,
                "guidance": e.guidance
            }
            for e in errors
        ]
    }

@app.get("/api/pipelines/{id}/preview")
async def preview_filenames(id: int, camera_id: str = "AB3D", start_counter: int = 1):
    """Generate expected filenames (FR-031)"""
    pipeline = get_pipeline(id)
    validator = PipelineValidator(pipeline.config)

    filenames = validator.preview_filenames(camera_id, start_counter)

    return {
        "camera_id": camera_id,
        "filenames": filenames
    }
```

### Rationale

1. **Topological sort for cycles**: Kahn's algorithm detects cycles in O(V+E) time. If topological sort fails to visit all nodes, cycle exists (FR-028: detect cycles).

2. **DFS for orphaned nodes**: Traverse graph, check if each non-Capture node has incoming edges. Capture nodes are entry points (no incoming required).

3. **Node type validation**: Each node type has required properties (Process → processing_method, File → file_extension, Termination → termination_type). Validation enforces completeness (FR-027: support all node types).

4. **Filename preview via graph traversal**: Find all paths from Capture to Termination, build filename strings from node properties along path. Demonstrates pipeline correctness (FR-031).

5. **Actionable error messages**: Each ValidationError includes guidance for fixing (Constitution: clear, actionable error messages).

### Alternatives Considered

**Alternative A: No cycle detection (assume users create DAGs)**
- ❌ Rejected: Users make mistakes, cycles cause infinite loops in Pipeline Validation tool
- ❌ Violates FR-028 (validate pipeline structure)

**Alternative B: Visual graph editor for validation (React Flow)**
- ✅ Planned for v2 (PRD Future Enhancements): React Flow graph editor with real-time validation
- ❌ Deferred for v1: Form-based editor sufficient, React Flow adds complexity

**Alternative C: YAML schema validation (JSON Schema)**
- ❌ Rejected: Schema validates syntax but not semantics (cycles, orphaned nodes, property references)
- ❌ Insufficient: Need graph algorithms for structural validation

### Implementation Notes

1. **Pipeline config structure**:
   ```json
   {
     "nodes": {
       "capture1": {
         "type": "Capture",
         "properties": {}
       },
       "file1": {
         "type": "File",
         "properties": {"file_extension": ".dng"}
       },
       "process1": {
         "type": "Process",
         "properties": {"processing_method": "HDR"}
       },
       "term1": {
         "type": "Termination",
         "properties": {"termination_type": "Archive"}
       }
     },
     "edges": [
       {"source": "capture1", "target": "file1"},
       {"source": "file1", "target": "process1"},
       {"source": "process1", "target": "term1"}
     ]
   }
   ```

2. **Frontend integration**: Form-based pipeline editor calls `/api/pipelines/{id}/validate` on save. Displays errors with node highlighting.

3. **Filename preview use case**: User creates pipeline, previews filenames to verify correctness before running Pipeline Validation tool.

4. **Testing considerations**:
   - Test cycle detection (simple cycle, complex multi-node cycles)
   - Test orphaned node detection (isolated nodes, nodes with only outgoing edges)
   - Test filename preview (branching pipelines, multiple Capture nodes)
   - Test edge case: empty pipeline (no nodes/edges)

5. **Performance**: Topological sort O(V+E), DFS O(V+E). For pipelines with 20 nodes, <1ms validation time.

---

## Research Task 8: CLI Tool Database Integration

### Question

How to extend PhotoAdminConfig to read from database with YAML fallback while maintaining <10% performance overhead?

### Decision

**Extend PhotoAdminConfig with database connection support, fallback to YAML if database unavailable, cache config in memory.**

Implementation:
```python
# utils/config_manager.py
import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

class PhotoAdminConfig:
    """Manages configuration from database or YAML fallback"""

    def __init__(self, config_path: Optional[str] = None, db_url: Optional[str] = None):
        self._config = None
        self._source = None  # "database" or "yaml"

        # Try database first
        if db_url or os.environ.get('PHOTO_ADMIN_DB_URL'):
            try:
                self._load_from_database(db_url or os.environ['PHOTO_ADMIN_DB_URL'])
                self._source = "database"
                return
            except Exception as e:
                # Database unavailable, fall back to YAML
                print(f"Database unavailable ({e}), falling back to YAML config")

        # Fallback to YAML
        self._load_from_yaml(config_path)
        self._source = "yaml"

    def _load_from_database(self, db_url: str):
        """Load configuration from database"""
        # Use NullPool for CLI tools (no connection pooling needed)
        engine = create_engine(db_url, poolclass=NullPool)

        with Session(engine) as session:
            # Fetch all configuration keys
            from models.configuration import Configuration
            configs = session.query(Configuration).all()

            # Build config dict
            self._config = {}
            for cfg in configs:
                self._config[cfg.key] = cfg.value  # value is already JSON-deserialized

            # Validate required keys
            self._validate_config()

        engine.dispose()  # Close connection immediately (CLI tool pattern)

    def _load_from_yaml(self, config_path: Optional[str] = None):
        """Load configuration from YAML file (existing implementation)"""
        # ... existing YAML loading logic ...
        pass

    @property
    def photo_extensions(self) -> list:
        return self._config.get('photo_extensions', [])

    @property
    def metadata_extensions(self) -> list:
        return self._config.get('metadata_extensions', [])

    @property
    def camera_mappings(self) -> dict:
        return self._config.get('camera_mappings', {})

    @property
    def processing_methods(self) -> dict:
        return self._config.get('processing_methods', {})

    @property
    def config_source(self) -> str:
        """Return 'database' or 'yaml' for debugging"""
        return self._source

    def ensure_camera_mapping(self, camera_id: str) -> dict:
        """Interactive prompt for unknown camera IDs (FR-025)"""
        if camera_id in self.camera_mappings:
            return self.camera_mappings[camera_id]

        # Prompt user
        camera_name = input(f"Unknown camera ID '{camera_id}'. Enter camera name: ")
        serial_number = input(f"Enter serial number for {camera_name}: ")

        mapping = {
            "name": camera_name,
            "serial_number": serial_number
        }

        # Save to config (database or YAML)
        if self._source == "database":
            self._save_camera_mapping_to_db(camera_id, mapping)
        else:
            self._save_camera_mapping_to_yaml(camera_id, mapping)

        self.camera_mappings[camera_id] = mapping
        return mapping
```

CLI tool usage (no changes):
```python
# photo_stats.py
from utils.config_manager import PhotoAdminConfig

def main():
    # Automatically tries database first, falls back to YAML
    config = PhotoAdminConfig()

    print(f"Config loaded from: {config.config_source}")

    photo_extensions = config.photo_extensions
    # ... rest of tool logic unchanged ...
```

Database URL configuration:
```bash
# .env file (gitignored)
PHOTO_ADMIN_DB_URL=postgresql://user:password@localhost:5432/photo_admin
```

### Rationale

1. **Database-first with YAML fallback**: CLI tools try database connection first (via environment variable), fall back to YAML if unavailable (FR-051). Seamless for users.

2. **NullPool for CLI tools**: SQLAlchemy connection pooling unnecessary for short-lived CLI processes. NullPool creates connection, uses it, disposes immediately. Reduces overhead.

3. **In-memory caching**: Load config once at startup, cache in PhotoAdminConfig instance. No repeated database queries during tool execution. <10% overhead (FR-053).

4. **No breaking changes**: CLI tool code unchanged (still uses `PhotoAdminConfig()`). Database integration transparent to tool logic.

5. **Environment variable for DB URL**: Follows 12-factor app principles. Users set `PHOTO_ADMIN_DB_URL` once, all CLI tools use database automatically.

### Alternatives Considered

**Alternative A: CLI flag for database mode (--use-database)**
- ❌ Rejected: Requires users to remember flag every time
- ❌ Poor UX: Users want "just work" behavior

**Alternative B: Separate CLI tools (photo_stats_db.py)**
- ❌ Rejected: Duplicates code, confuses users (which tool to use?)
- ❌ Violates Constitution: CLI tools should remain standalone

**Alternative C: Always require database (no YAML fallback)**
- ❌ Rejected: Breaks existing CLI workflows, forces database setup
- ❌ Violates FR-051 (fallback to YAML when database unavailable)

**Alternative D: SQLite for local database**
- ✅ Alternative: SQLite viable for localhost deployment (simpler than PostgreSQL)
- ❌ PostgreSQL chosen for JSONB support (Research Task 1), but SQLite with JSON1 extension could work
- Consider SQLite for easier local development setup

### Implementation Notes

1. **Database URL detection order**:
   - Explicit parameter: `PhotoAdminConfig(db_url='postgresql://...')`
   - Environment variable: `PHOTO_ADMIN_DB_URL`
   - No database: Fall back to YAML

2. **Connection lifecycle**:
   - CLI tools: Create connection, load config, dispose immediately (NullPool)
   - Web server: Use connection pooling (default SQLAlchemy pool)

3. **Error handling**:
   - Database unreachable: Print warning, fall back to YAML
   - Invalid DB URL: Print error, fall back to YAML
   - YAML also missing: Show interactive setup prompt (existing behavior)

4. **Performance measurement**:
   - Baseline (YAML): Load config in 50ms
   - Database: Load config in <55ms (<10% overhead)
   - Use connection reuse for web server (no overhead after first request)

5. **Testing considerations**:
   - Mock database connection for unit tests
   - Test fallback behavior (database unreachable)
   - Test interactive prompts (camera mapping, processing methods)

6. **Migration path for users**:
   - User runs web interface, imports YAML to database
   - Set `PHOTO_ADMIN_DB_URL` environment variable
   - CLI tools automatically use database
   - YAML config.yaml can be archived/removed (optional)

7. **Encoding**: Database connection string and YAML file loading MUST use UTF-8 (Constitution: Cross-Platform File Encoding)

8. **Backwards compatibility**: Users without database setup continue using YAML with zero changes.

---

## Summary of Decisions

| Research Task | Decision | Key Technology |
|---------------|----------|----------------|
| 1. Database Schema | PostgreSQL JSONB with schema versioning | PostgreSQL 12+, GIN indexes |
| 2. Credential Encryption | Fernet symmetric encryption with env key | Python cryptography |
| 3. File Listing Cache | In-memory dict with TTL per collection state | Python dict + threading.Lock |
| 4. Job Queue | FastAPI BackgroundTasks with in-memory queue | FastAPI async |
| 5. YAML Import Conflicts | Side-by-side diff UI with user selection | React component |
| 6. WebSocket Progress | FastAPI WebSocket with JSON events | FastAPI WebSocket |
| 7. Pipeline Validation | Topological sort + DFS graph algorithms | Python graph traversal |
| 8. CLI Database Integration | Database-first with YAML fallback + NullPool | SQLAlchemy NullPool |

All decisions prioritize **v1 simplicity** (no over-engineering), meet **performance constraints** (<2s, <1s, 80% cache reduction), and align with **Constitution principles** (YAGNI, clear errors, no over-engineering).

## Next Steps

1. ✅ **Phase 0 Complete**: All 8 research tasks resolved with decisions documented
2. **Phase 1**: Begin design phase
   - Create data-model.md (SQLAlchemy models, relationships, indexes)
   - Create contracts/openapi.yaml (REST API specification)
   - Create contracts/websocket.md (WebSocket protocol)
   - Create quickstart.md (setup guide for developers)
3. **Phase 2**: Run `/speckit.tasks` to generate implementation tasks based on research decisions

## Open Questions for Phase 1

1. Should we use SQLite as alternative to PostgreSQL for easier local development?
   - PostgreSQL chosen for JSONB, but SQLite with JSON1 extension viable
   - Decision: Document PostgreSQL as primary, SQLite as optional for v1

2. Should we implement Redis cache as optional upgrade path from in-memory?
   - In-memory sufficient for v1, Redis deferred
   - Decision: Document Redis as v2 enhancement for multi-process deployment

3. Should we add metrics/monitoring for cache hit rates, job queue lengths?
   - Useful for optimization but not critical for v1
   - Decision: Add basic logging, defer full metrics to v2

All major technical decisions resolved. Ready for Phase 1 design.
