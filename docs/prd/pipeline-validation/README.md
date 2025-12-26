# Feature Request: Photo Processing Pipeline Validation Tool

**Status:** Draft PRD - Awaiting Review
**Created:** 2025-12-25
**Updated:** 2025-12-26 (Node-Based Architecture)
**Branch:** `claude/analyze-photo-pipeline-D5tdA`

---

## Quick Start

This directory contains the complete Product Requirements Document (PRD) for a new pipeline validation tool that analyzes photo collections against defined processing workflows using a **node-based directed graph architecture**.

### 📄 Key Documents

1. **[node-architecture-analysis.md](node-architecture-analysis.md)** - Architecture Deep Dive ⭐ **START HERE**
   - **Critical insight: File nodes define valid Specific Images**
   - Detailed explanation of 6 node types (Capture, File, Process, Pairing, Branching, Termination)
   - Path traversal algorithms with examples
   - Integration with Photo Pairing Tool's ImageGroup structure
   - Edge cases and implementation implications

2. **[spec.md](spec.md)** - Complete PRD with Node-Based Architecture
   - Executive summary and goals
   - **FR-1: Node-based pipeline configuration** (replaces stage-based model)
   - **FR-2: Graph traversal validation algorithm**
   - Technical design and architecture
   - Testing strategy and success metrics
   - Timeline and future enhancements

3. **[pipeline-config-example.yaml](pipeline-config-example.yaml)** - Official Configuration Example
   - Complete v1 pipeline with all 6 node types
   - Real-world workflow: Camera → DNG → TIF → JPG → Archive
   - Supports branching (denoise options), looping (iterative edits), parallel paths
   - Heavily commented with explanations
   - Ready to adapt for your workflow

4. **[photo_processing_pipeline_configuration_proposal.md](photo_processing_pipeline_configuration_proposal.md)** - Configuration Proposal Document
   - Detailed explanation of the node-based configuration structure
   - Visual pipeline diagrams (horizontal and vertical views)
   - Complete annotated example with all node types

5. **[flowchart-to-config-mapping.md](flowchart-to-config-mapping.md)** - Implementation Guide ⚠️ **NEEDS UPDATE**
   - ⚠️ Currently based on deprecated stage-based model
   - Will be updated to reflect node-based architecture
   - Kept for legacy reference and comparison

6. **[pipeline-config-deprecated.yaml](pipeline-config-deprecated.yaml)** - Deprecated Configuration
   - Original linear stage-based model
   - Superseded by node-based architecture in pipeline-config-example.yaml
   - Kept for reference only

---

## What This Tool Does

### Core Concept

The Pipeline Validation Tool extends existing capabilities to validate that photo file groups represent **complete, valid processing workflows** from camera capture through archival.

```
┌─────────────────────────────────────────────────────────────┐
│ Photo Pairing Tool (Existing)                               │
│ Groups files: AB3D0001.cr3, AB3D0001.dng, AB3D0001.tif      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Pipeline Validation Tool (NEW)                              │
│ Validates group against configured pipeline paths           │
│                                                             │
│ ✓ CONSISTENT: Group matches complete archival path         │
│ ⚠ PARTIAL: Group incomplete, missing files identified      │
│ ✗ INCONSISTENT: Group doesn't match any valid path         │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

1. **Node-Based Pipeline Configuration**
   - Define workflows as directed graphs with 6 node types
   - **File nodes** explicitly represent actual files in filesystem
   - Support branching (conditional paths), looping (iterative processing), parallel execution
   - Multiple termination endpoints (Black Box Archive, Browsable Archive)

2. **Image Group Validation via Graph Traversal**
   - Traverse pipeline from Capture to Termination nodes
   - **Collect File nodes = expected files for Specific Image**
   - Compare actual ImageGroup files vs expected File nodes
   - Classify as CONSISTENT, PARTIAL, or INCONSISTENT

3. **Metadata Integration (PhotoStats + Pairing)**
   - Reuses PhotoStats' CR3→XMP linking logic
   - Pairing nodes validate metadata files exist
   - Supports shared XMP files (CR3 and DNG use same XMP)

4. **Comprehensive Reporting**
   - Interactive HTML reports (Jinja2 templates)
   - Pipeline visualizations (Chart.js)
   - Statistics on archival readiness by termination type
   - Lists of incomplete groups with specific missing files identified

---

## Example Use Case

### Your Photo Collection

```
AB3D0001.cr3        # Camera raw file
AB3D0001.xmp        # Lightroom metadata
AB3D0001.dng        # DNG conversion
AB3D0001.tif        # Developed TIF
```

### Validation Result

```yaml
Group: AB3D0001
Status: PARTIAL
Archival Ready: YES (Black Box) / NO (Browsable)
Matched Paths:
  - raw_archive_path (100%) ✓
  - dng_archive_path (100%) ✓
  - developed_archive_path (100%) ✓
Missing Files:
  - AB3D0001-WEB.jpg (needed for browsable_archive_path)

Recommendation:
  ✓ Ready for Black Box Archive (master preservation)
  ⚠ To create Browsable Archive, export web-ready JPG
```

---

## How It Works

### 1. Define Pipeline in Config

```yaml
processing_pipelines:
  stages:
    - id: capture
      file_types:
        - extension: .cr3
          metadata_sidecar: .xmp
          metadata_required: false

    - id: import
      file_types:
        - extension: .cr3
          metadata_sidecar: .xmp
          metadata_required: true  # XMP must exist

  paths:
    - id: raw_archive_path
      name: "Raw Archive - Black Box"
      stages: [capture, import]
      validation:
        terminal: true  # Valid archival endpoint
```

### 2. Run Validation

```bash
python3 pipeline_validation.py /path/to/photos
```

### 3. Review Report

```
✓ Consistent Groups: 892 (71.5%) - Ready for archival
⚠ Partial Groups: 203 (16.3%) - Missing some files
✗ Inconsistent Groups: 152 (12.2%) - Invalid or incomplete

Black Box Archive Ready: 654 groups
Browsable Archive Ready: 238 groups
```

---

## Flowchart Mapping

Your flowchart defines these archival endpoints:

| Archival Type | Pipeline Path | Required Files |
|---------------|---------------|----------------|
| **Black Box Archive** | Raw Archive | CR3 + XMP |
| **Black Box Archive** | DNG Archive | CR3 (optional) + DNG + XMP |
| **Black Box Archive** | Developed Archive | DNG + XMP + TIF |
| **Browsable Archive** | Complete Workflow | All above + JPG (web) |

The tool validates each image group (e.g., all files with prefix AB3D0001) against these paths.

---

## Integration with Existing Tools

### Builds On

1. **PhotoStats**
   - Reuses metadata sidecar detection (CR3→XMP pairing)
   - Uses base filename matching logic
   - Extends with stage-aware validation

2. **Photo Pairing Tool**
   - Reuses image grouping (files with same camera_id + counter)
   - Uses FilenameParser for validation
   - Extends with pipeline path matching

3. **PhotoAdminConfig**
   - Reuses YAML configuration loading
   - Uses existing `photo_extensions` and `metadata_extensions`
   - Adds new `processing_pipelines` section

### New Capabilities

- Multi-stage workflow validation
- Archival readiness classification
- Missing file identification
- Pipeline-aware metadata validation
- Configurable processing paths

---

## Next Steps

### For Review

1. **Read [spec.md](spec.md)** - Full PRD with all requirements
2. **Review [pipeline-config-example.yaml](pipeline-config-example.yaml)** - Sample configuration
3. **Check [flowchart-to-config-mapping.md](flowchart-to-config-mapping.md)** - Implementation details

### For Implementation

1. **Phase 1:** Pipeline configuration schema and parser
2. **Phase 2:** Validation engine
3. **Phase 3:** CLI tool and HTML reporting
4. **Phase 4:** Testing and documentation

**Estimated Timeline:** 9 weeks (see spec.md for detailed breakdown)

### Questions to Consider

1. Should the tool support multi-image workflows (HDR merging)? → **Recommended for v2.0**
2. How to handle shared XMP files between CR3 and DNG? → **Allow sharing by default**
3. Should partial paths ever be archival-ready? → **Configurable flag suggested**
4. Support for intermediate archival (e.g., archive at DNG stage)? → **Yes, via terminal paths**

---

## Configuration Schema

The pipeline configuration extends existing `config.yaml`:

```yaml
# Existing sections (unchanged)
photo_extensions: [.cr3, .dng, .tif, .jpg]
metadata_extensions: [.xmp]
require_sidecar: [.cr3]
camera_mappings: {...}
processing_methods: {...}

# NEW: Processing pipeline configuration
processing_pipelines:
  stages:
    - id: capture
      name: "Camera Capture"
      file_types: [...]

    - id: import
      name: "Import & Sanction"
      file_types: [...]

  paths:
    - id: raw_archive_path
      name: "Raw Archive - Black Box"
      archival_type: black_box
      stages: [capture, import]
      validation:
        must_have_all: true
        terminal: true
```

See [pipeline-config-example.yaml](pipeline-config-example.yaml) for complete example with 7 paths and 7 stages.

---

## Key Design Decisions

### 1. Consistency Classification

| Status | Description | Archival Ready |
|--------|-------------|----------------|
| **CONSISTENT** | Matches complete terminal path | YES |
| **PARTIAL** | Matches path but missing files for terminal paths | Depends on matched path |
| **INCONSISTENT** | Doesn't match any path | NO |

### 2. Metadata Handling

- **Stage-aware:** XMP required at import stage, optional at capture
- **Shared XMP:** CR3 and DNG can share same XMP file
- **Embedded metadata:** TIF files don't require XMP (metadata embedded)

### 3. Archival Types

- **Black Box Archive:** Master preservation (CR3, DNG, TIF)
- **Browsable Archive:** Web-accessible (includes JPG exports)

### 4. Properties vs Stages

- **Processing properties** (HDR, BW): Applied at specific stages
- **Separate images** (AB3D0001-2.cr3): Treated as distinct groups
- **Web properties** (LOSSLESS, WEB): Indicate export type

---

## Example Validation Scenarios

### Scenario 1: Ready for Black Box Archive

**Files:**
```
AB3D0001.cr3
AB3D0001.xmp
AB3D0001.dng
```

**Result:** ✓ CONSISTENT - Ready for DNG Archive (Black Box)

---

### Scenario 2: Missing Web Export

**Files:**
```
AB3D0001.cr3
AB3D0001.dng
AB3D0001.xmp
AB3D0001.tif
```

**Result:** ⚠ PARTIAL - Ready for Black Box, missing JPG for Browsable

**Recommendation:** Export TIF as AB3D0001-WEB.jpg

---

### Scenario 3: Missing Required Metadata

**Files:**
```
AB3D0001.cr3
```

**Result:** ✗ INCONSISTENT - Missing required XMP sidecar

**Recommendation:** Import into Lightroom to create AB3D0001.xmp

---

## Success Metrics

### Launch Targets (v1.0)

- 50% of PhotoStats users try pipeline validation within 1 month
- 95% accuracy in classifying consistent vs inconsistent groups
- Analyze 10,000 image groups in under 60 seconds

### User Experience

- Users can configure pipeline without reading full docs
- Clear, actionable recommendations for inconsistent groups
- Interactive HTML reports with visualizations

---

## Future Enhancements (v2.0+)

1. **Advanced Workflows:** HDR merging (N:1), panorama stitching
2. **Automated Remediation:** Generate scripts to create missing files
3. **Cloud Storage:** Validate files across S3, Google Drive
4. **Real-Time Monitoring:** Watch folders, webhook notifications
5. **Pipeline Templates:** Share configurations, industry presets
6. **Graphical Editor:** Visual pipeline builder

---

## Feedback & Questions

This is a **DRAFT PRD** awaiting stakeholder review.

**Please provide feedback on:**
- Pipeline configuration schema
- Validation logic and classification
- Use cases and workflows
- Integration with existing tools
- Testing strategy
- Timeline estimates

**Submit feedback via:**
- GitHub issues on this repository
- Email to project maintainers
- Comments on the pull request

---

## License

GNU Affero General Public License v3.0 (AGPL-3.0)

Same license as photo-admin project.
