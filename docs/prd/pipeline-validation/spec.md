# PRD: Photo Processing Pipeline Validation Tool

**Feature ID:** 003-pipeline-validation
**Version:** 1.0.0 (Draft)
**Date:** 2025-12-25
**Author:** Claude (Generated from flowchart analysis)
**Status:** Draft - Awaiting Review

---

## Executive Summary

A new tool to validate photo file collections against defined processing pipeline paths, ensuring image groups contain all expected file types from camera capture through archival. This tool combines the image grouping capabilities of the Photo Pairing Tool with the metadata linking logic of PhotoStats to classify groups as **consistent** (complete pipeline path) or **inconsistent** (missing expected files).

---

## Background & Motivation

### Current State

**Existing Tools:**
1. **PhotoStats** - Identifies valid CR3+XMP metadata pairs based on matching filenames
2. **Photo Pairing Tool** - Groups files by camera ID and counter (e.g., AB3D0001.CR3, AB3D0001.DNG, AB3D0001.TIF)

### Problem Statement

Photographers follow complex processing workflows where a single captured image flows through multiple stages:
- Camera capture → Raw file (CR3)
- Import → Metadata application (XMP sidecar)
- Conversion → Open format (DNG)
- Processing → Developed files (TIF)
- Export → Web formats (JPG lossless, JPG lossy)
- Archive → Two endpoints: Black Box Archive or Browsable Archive

**Current tools cannot:**
1. Validate that a group of files represents a **complete, valid pipeline path**
2. Identify which files are **missing** from an incomplete workflow
3. Classify groups by their **archival readiness** (Black Box vs Browsable)
4. Configure and validate against **user-defined pipeline paths**

### Business Value

- **Quality Assurance:** Ensure archival collections are complete before storage
- **Workflow Validation:** Detect incomplete processing workflows
- **Storage Planning:** Classify which archives are ready for long-term storage
- **Audit Trail:** Document which processing paths were used for each image

---

## Goals & Non-Goals

### Goals

1. **Pipeline Configuration**
   - Define processing pipeline stages and their expected file types in `config.yaml`
   - Support multiple valid pipeline paths (different workflows)
   - Configure archival endpoints (Black Box Archive, Browsable Archive)

2. **Image Group Validation**
   - Classify image groups as **consistent** (complete path) or **inconsistent** (missing files)
   - Identify which specific pipeline path a consistent group follows
   - Report missing file types for inconsistent groups

3. **Metadata Integration**
   - Link raw files to their metadata sidecars (CR3→XMP) using PhotoStats logic
   - Validate metadata presence at appropriate pipeline stages

4. **Reporting**
   - Interactive HTML reports with pipeline visualizations
   - Statistics on consistency rates by pipeline path
   - List of incomplete groups with actionable remediation steps

### Non-Goals (v1.0)

- **File generation:** Tool will NOT create missing files
- **Automatic remediation:** Tool will NOT move or delete files
- **Multi-image workflows:** Advanced features like HDR merging, panorama stitching (may be v2.0)
- **Cloud storage integration:** Local filesystem analysis only
- **Real-time monitoring:** Batch analysis mode only

---

## Functional Requirements

### FR-1: Pipeline Configuration

**Description:** Allow users to define processing pipeline paths in `config.yaml`

**Configuration Schema:**
```yaml
# Processing pipeline configuration
processing_pipelines:
  # Define stages of the processing workflow
  stages:
    # Stage 1: Camera Capture
    - id: capture
      name: "Camera Capture"
      file_types:
        - extension: .cr3
          required: true
          metadata_sidecar: .xmp
          metadata_required: false  # XMP may come later

    # Stage 2: Import & Sanction
    - id: import
      name: "Import & Lightroom Sanction"
      file_types:
        - extension: .cr3
          required: true
          metadata_sidecar: .xmp
          metadata_required: true  # XMP must exist after import

    # Stage 3: Digital Photo Developing (DNG Conversion)
    - id: dng_conversion
      name: "DNG Conversion"
      file_types:
        - extension: .dng
          required: true
          metadata_sidecar: .xmp
          metadata_required: true
          inherits_metadata: true  # Can use CR3's XMP or have its own

    # Stage 4: Export & Tone Mapping
    - id: tone_mapping
      name: "Tone Mapping in Adobe Lightroom"
      file_types:
        - extension: .tif
          required: true
          metadata_sidecar: .xmp
          metadata_required: false  # TIF embeds metadata

    # Stage 5: Individual Processing
    - id: individual_processing
      name: "Individual Image Processing (Photoshop)"
      file_types:
        - extension: .tif
          required: true
          properties:  # Can have processing method properties
            - HDR
            - BW
            - PANO

    # Stage 6: Web Export (Lossless)
    - id: web_export_lossless
      name: "JPG Export (Lossless)"
      file_types:
        - extension: .jpg
          required: true
          properties:
            - LOSSLESS

    # Stage 7: Web Export (Lossy for browsable)
    - id: web_export_lossy
      name: "JPG Export (Lossy)"
      file_types:
        - extension: .jpg
          required: true
          properties:
            - WEB

  # Define valid paths through the pipeline
  paths:
    # Path 1: Raw Archive (Black Box)
    - id: raw_archive_path
      name: "Raw Archive - Black Box"
      description: "Original raw files with metadata, archived without processing"
      archival_type: black_box
      stages:
        - capture
        - import
      validation:
        must_have_all: true  # All stages required
        terminal: true       # Valid archival endpoint

    # Path 2: DNG Archive (Black Box)
    - id: dng_archive_path
      name: "DNG Archive - Black Box"
      description: "Converted to open DNG format with metadata"
      archival_type: black_box
      stages:
        - capture
        - import
        - dng_conversion
      validation:
        must_have_all: true
        terminal: true

    # Path 3: Developed Archive (Black Box)
    - id: developed_archive_path
      name: "Developed Archive - Black Box"
      description: "Fully developed TIF files ready for master archive"
      archival_type: black_box
      stages:
        - capture
        - import
        - dng_conversion
        - tone_mapping
      validation:
        must_have_all: true
        terminal: true

    # Path 4: Full Workflow to Browsable Archive
    - id: browsable_archive_path
      name: "Browsable Archive - Complete Workflow"
      description: "Full workflow from capture through web-ready JPG"
      archival_type: browsable
      stages:
        - capture
        - import
        - dng_conversion
        - tone_mapping
        - individual_processing
        - web_export_lossy
      validation:
        must_have_all: true
        terminal: true

    # Path 5: Partial Processing (Inconsistent - for detection)
    - id: partial_processing
      name: "Partial Processing"
      description: "Incomplete workflow - missing expected files"
      archival_type: null
      stages:
        - capture
        # Other stages may or may not exist
      validation:
        must_have_all: false
        terminal: false  # NOT a valid archival endpoint
```

**Validation Rules:**
- Each stage must have unique `id`
- File extensions must match existing `photo_extensions` config
- Metadata sidecars must match `metadata_extensions`
- Pipeline paths must reference valid stage IDs
- At least one path must be marked as `terminal: true` (valid archival endpoint)

---

### FR-2: Image Group Analysis

**Description:** Extend Photo Pairing Tool's image grouping to include pipeline validation

**Input:**
- Image groups from Photo Pairing Tool (files with same camera_id + counter)
- Configuration from `processing_pipelines`

**Processing Logic:**
```python
for each image_group:
    # 1. Get all file types in group
    file_types = extract_extensions(image_group.files)

    # 2. Check metadata linking (from PhotoStats)
    metadata_links = validate_metadata_sidecars(image_group)

    # 3. Match against pipeline paths
    matching_paths = []
    for path in config.processing_pipelines.paths:
        if group_matches_path(image_group, path):
            matching_paths.append(path)

    # 4. Classify group
    if matching_paths:
        if any(path.validation.terminal for path in matching_paths):
            group.status = "CONSISTENT"
            group.matched_paths = matching_paths
        else:
            group.status = "PARTIAL"
            group.matched_paths = matching_paths
    else:
        group.status = "INCONSISTENT"
        group.missing_files = calculate_missing_files(image_group)
```

**Output Structure:**
```python
{
    'group_id': 'AB3D0001',
    'camera_id': 'AB3D',
    'counter': '0001',
    'status': 'CONSISTENT' | 'PARTIAL' | 'INCONSISTENT',
    'matched_paths': [
        {
            'path_id': 'dng_archive_path',
            'path_name': 'DNG Archive - Black Box',
            'archival_type': 'black_box',
            'completion': 100  # percentage
        }
    ],
    'files': [
        {
            'filename': 'AB3D0001.cr3',
            'stage': 'capture',
            'metadata_sidecar': 'AB3D0001.xmp',
            'metadata_status': 'LINKED'
        },
        {
            'filename': 'AB3D0001.dng',
            'stage': 'dng_conversion',
            'metadata_sidecar': 'AB3D0001.xmp',
            'metadata_status': 'SHARED'
        }
    ],
    'missing_files': [
        {
            'stage': 'tone_mapping',
            'expected_extension': '.tif',
            'reason': 'Required for complete developed_archive_path'
        }
    ],
    'archival_ready': true | false
}
```

---

### FR-3: Metadata Sidecar Validation

**Description:** Validate metadata files are present at required pipeline stages

**Requirements:**
1. **CR3→XMP Linking:** Use PhotoStats' base filename matching
   - `AB3D0001.cr3` must have `AB3D0001.xmp`

2. **DNG Metadata:**
   - Can share XMP with CR3 (`AB3D0001.xmp` used by both)
   - Or have separate XMP (`AB3D0001-DNG.xmp`)
   - Or embed metadata (no XMP required if `metadata_required: false`)

3. **TIF Metadata:**
   - Typically embeds metadata (XMP optional)
   - If `metadata_required: false`, XMP absence is valid

4. **Stage-Specific Validation:**
   - `import` stage: XMP **must** exist for CR3 files
   - `capture` stage: XMP **may** exist but not required

**Validation Logic:**
```python
def validate_metadata_at_stage(file, stage_config):
    if stage_config.metadata_sidecar is None:
        return {'status': 'NOT_REQUIRED', 'sidecar': None}

    # Look for metadata sidecar
    sidecar_path = find_metadata_sidecar(file, stage_config.metadata_sidecar)

    if sidecar_path:
        return {'status': 'LINKED', 'sidecar': sidecar_path}
    elif stage_config.metadata_required:
        return {'status': 'MISSING_REQUIRED', 'sidecar': None}
    else:
        return {'status': 'MISSING_OPTIONAL', 'sidecar': None}
```

---

### FR-4: Consistency Classification

**Description:** Classify image groups into consistency tiers

**Classification Tiers:**

| Status | Description | Criteria | Archival Ready |
|--------|-------------|----------|----------------|
| **CONSISTENT** | Complete valid pipeline path | Matches at least one `terminal: true` path with 100% file completion | **YES** |
| **PARTIAL** | Matches non-terminal path | Matches path but not marked as terminal archival endpoint | **NO** |
| **INCONSISTENT** | Missing files from all paths | Does not match any complete path | **NO** |
| **INVALID** | Has validation errors | Metadata required but missing, or other validation failures | **NO** |

**Edge Cases:**
- **Multiple Path Match:** Group matches multiple valid paths → report all matching paths
- **Superset Path:** Group has MORE files than required by path → still CONSISTENT if minimum requirements met
- **Processing Properties:** Files with properties (e.g., `AB3D0001-HDR.tif`) → match `individual_processing` stage

---

### FR-5: HTML Report Generation

**Description:** Generate interactive HTML report using Jinja2 templates (consistent with existing tools)

**Report Sections:**

1. **Executive Summary**
   - Total image groups analyzed
   - Consistency breakdown (pie chart)
   - Archival readiness statistics

2. **Pipeline Path Statistics**
   - For each configured path:
     - Number of groups matching this path
     - Completion rate
     - Archival type distribution

3. **Consistent Groups**
   - Table of groups ready for archival
   - Matched pipeline path(s)
   - File inventory

4. **Inconsistent Groups**
   - Table of incomplete groups
   - Missing files highlighted
   - Recommended actions

5. **Metadata Validation**
   - Groups with metadata issues
   - Missing required XMP files
   - Orphaned metadata

6. **Pipeline Visualization**
   - Flowchart showing configured pipeline
   - Highlight which paths are most common
   - Show dropout points (where groups become inconsistent)

**Visualizations (Chart.js):**
- Pie chart: Consistency status distribution
- Bar chart: Groups per pipeline path
- Stacked bar chart: Stage completion rates
- Sankey diagram: Flow through pipeline stages (v2.0)

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Pipeline Validation Tool                    │
│                   (pipeline_validation.py)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Photo Pairing│    │  PhotoStats  │    │   Config     │
│  (Grouping)  │    │  (Metadata)  │    │  (Pipeline)  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Validator  │
                    │    Engine    │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │HTML Reporter │
                    │  (Jinja2)    │
                    └──────────────┘
```

### Module Structure

**New Files:**
```
photo-admin/
├── pipeline_validation.py          # Main CLI tool
├── utils/
│   ├── pipeline_config.py         # Pipeline config parser
│   └── pipeline_validator.py      # Validation engine
├── templates/
│   └── pipeline_report.html.j2    # Jinja2 template
├── config/
│   └── pipeline-template.yaml     # Default pipeline config
└── tests/
    └── test_pipeline_validation.py
```

**Class Hierarchy:**

```python
# utils/pipeline_config.py
class PipelineStage:
    id: str
    name: str
    file_types: List[FileTypeRequirement]

class FileTypeRequirement:
    extension: str
    required: bool
    metadata_sidecar: Optional[str]
    metadata_required: bool
    properties: Optional[List[str]]

class PipelinePath:
    id: str
    name: str
    description: str
    archival_type: Optional[str]  # 'black_box' | 'browsable' | null
    stages: List[str]  # stage IDs
    validation: PathValidation

class PathValidation:
    must_have_all: bool
    terminal: bool

class PipelineConfig:
    stages: List[PipelineStage]
    paths: List[PipelinePath]

    @classmethod
    def load_from_yaml(cls, config_path: Path)

    def validate(self) -> Tuple[bool, Optional[str]]
```

```python
# utils/pipeline_validator.py
class ImageGroupValidator:
    def __init__(self, pipeline_config: PipelineConfig)

    def validate_group(self, image_group: dict) -> GroupValidationResult

    def match_pipeline_paths(self, image_group: dict) -> List[PipelinePath]

    def calculate_missing_files(self, image_group: dict, target_path: PipelinePath) -> List[dict]

    def validate_metadata_links(self, image_group: dict) -> List[MetadataLink]

class GroupValidationResult:
    status: str  # 'CONSISTENT' | 'PARTIAL' | 'INCONSISTENT' | 'INVALID'
    matched_paths: List[PipelinePath]
    missing_files: List[dict]
    metadata_status: List[MetadataLink]
    archival_ready: bool
```

### Integration with Existing Tools

**Reuse from Photo Pairing Tool:**
- `scan_folder()` - File discovery
- `build_imagegroups()` - Group files by camera_id + counter
- FilenameParser validation

**Reuse from PhotoStats:**
- `_analyze_pairing()` - Metadata sidecar detection
- Base filename matching logic

**Reuse from PhotoAdminConfig:**
- YAML configuration loading
- `photo_extensions` and `metadata_extensions`

**New Configuration Section:**
- Add `processing_pipelines` to existing `config.yaml`
- Maintain backward compatibility with existing tools

---

## User Experience

### CLI Usage

```bash
# Basic usage - analyze current directory
python3 pipeline_validation.py /path/to/photos

# Specify custom config
python3 pipeline_validation.py /path/to/photos --config /path/to/config.yaml

# Filter by archival type
python3 pipeline_validation.py /path/to/photos --archival-type black_box

# Show only inconsistent groups
python3 pipeline_validation.py /path/to/photos --show-inconsistent

# Output JSON instead of HTML
python3 pipeline_validation.py /path/to/photos --output-format json
```

### Help Text

```
Photo Pipeline Validation Tool - Validate photo collections against processing workflows

USAGE:
    python3 pipeline_validation.py <folder> [options]

ARGUMENTS:
    <folder>    Path to folder containing photo files

OPTIONS:
    --config PATH               Custom config file path
    --archival-type TYPE        Filter by archival type (black_box, browsable)
    --show-inconsistent         Show only inconsistent groups
    --output-format FORMAT      Output format: html (default), json
    --help, -h                  Show this help message

EXAMPLE WORKFLOW:
    1. Configure pipeline paths in config/config.yaml
    2. Run tool on photo collection:
       $ python3 pipeline_validation.py ~/Photos/2024
    3. Review HTML report for:
       - Groups ready for Black Box Archive
       - Groups ready for Browsable Archive
       - Incomplete groups needing additional processing
    4. Take action based on report recommendations

CONFIGURATION:
    The tool uses config/config.yaml to define:
    - Processing pipeline stages (capture, import, develop, export)
    - Valid pipeline paths (raw archive, DNG archive, browsable archive)
    - Archival readiness criteria

    See config/pipeline-template.yaml for examples.

For more information, see docs/pipeline-validation.md
```

### Interactive Configuration

When pipeline config is missing or incomplete:

```
⚠ Warning: No pipeline configuration found in config.yaml

Would you like to:
  1. Generate default pipeline configuration
  2. Specify custom pipeline config file
  3. Skip pipeline validation (analyze groups only)

Enter choice (1-3): 1

✓ Generated default pipeline configuration in config/config.yaml

Default pipeline includes:
  - Raw Archive Path (CR3 + XMP → Black Box)
  - DNG Archive Path (CR3 → DNG + XMP → Black Box)
  - Browsable Archive Path (Full workflow → JPG → Browsable)

You can customize these paths by editing config/config.yaml
Continue with analysis? (y/n): y
```

### Report Preview

```
================================================================================
                    Pipeline Validation Report
================================================================================
Scanned: /home/user/Photos/2024
Analysis Date: 2025-12-25 14:30:00
Total Image Groups: 1,247

Summary:
  ✓ Consistent (Archival Ready):     892 groups (71.5%)
  ⚠ Partial Processing:               203 groups (16.3%)
  ✗ Inconsistent (Missing Files):     152 groups (12.2%)

Archival Readiness:
  Black Box Archive Ready:  654 groups (52.4%)
  Browsable Archive Ready:  238 groups (19.1%)
  Not Ready:                355 groups (28.5%)

Pipeline Path Distribution:
  Raw Archive Path:         420 groups (33.7%)
  DNG Archive Path:         234 groups (18.8%)
  Browsable Archive:        238 groups (19.1%)
  Partial/Inconsistent:     355 groups (28.5%)

Metadata Status:
  ✓ All metadata linked:    1,095 groups (87.8%)
  ⚠ Missing optional XMP:      98 groups (7.9%)
  ✗ Missing required XMP:      54 groups (4.3%)

📄 Full report saved to: pipeline_validation_report_2025-12-25_14-30-00.html
================================================================================
```

---

## Testing Strategy

### Unit Tests

1. **Pipeline Configuration**
   - Load valid pipeline config from YAML
   - Detect invalid stage references
   - Validate circular dependencies
   - Test default config generation

2. **Stage Matching**
   - Match file to correct stage
   - Handle file with properties (HDR, BW)
   - Detect unknown file types

3. **Path Validation**
   - Group matches complete path
   - Group matches partial path
   - Group matches no paths
   - Group matches multiple paths

4. **Metadata Validation**
   - CR3 with XMP (linked)
   - CR3 without XMP (orphaned)
   - DNG sharing CR3's XMP
   - TIF without XMP (embedded metadata)

### Integration Tests

1. **Complete Workflows**
   - Raw archive path (CR3 + XMP only)
   - DNG archive path (CR3 + DNG + XMP)
   - Browsable archive path (full workflow)

2. **Incomplete Workflows**
   - Missing XMP at import stage
   - Missing DNG in conversion path
   - Missing JPG in browsable path

3. **Edge Cases**
   - Group with extra files (superset)
   - Group with mixed archival paths
   - Group with separate images (AB3D0001-2.cr3)

### Test Coverage Targets

- Pipeline configuration: >90%
- Validation engine: >85%
- Overall: >70%

---

## Success Metrics

### Launch Metrics (v1.0)

- **Adoption:** 50% of PhotoStats users try pipeline validation within 1 month
- **Usefulness:** Users run pipeline validation at least monthly
- **Configuration:** 80% of users customize at least one pipeline path

### Quality Metrics

- **Accuracy:** 95% accurate classification of consistent vs inconsistent groups
- **Performance:** Analyze 10,000 image groups in under 60 seconds
- **Usability:** Users can configure pipeline without reading full documentation

### User Feedback

- Collect feedback via GitHub issues
- Track most common pipeline configurations
- Identify missing pipeline stages or paths

---

## Open Questions

1. **Multi-Image Workflows:**
   - How to handle HDR merges (3 CR3 files → 1 TIF)?
   - Should pipeline validation support group-to-group relationships?
   - **Recommendation:** Defer to v2.0, focus on 1:1 file evolution in v1.0

2. **Separate Images:**
   - Files like `AB3D0001-2.cr3` represent separate captures with same counter
   - Should each separate image follow its own pipeline path?
   - **Recommendation:** YES - treat as separate image groups (AB3D0001-2, AB3D0001-3, etc.)

3. **Property Inheritance:**
   - If `AB3D0001.cr3` exists, can `AB3D0001-HDR.dng` reference it?
   - Should properties be inherited through pipeline stages?
   - **Recommendation:** Properties apply to specific processing stages, not inherited

4. **Partial Path Archival:**
   - Should "partial" groups (non-terminal paths) ever be archival-ready?
   - What if user wants to archive at intermediate stage?
   - **Recommendation:** Allow configuration flag `allow_intermediate_archival: true` per path

5. **XMP Sharing:**
   - Can CR3 and DNG share the same XMP file?
   - How to handle conflicting metadata?
   - **Recommendation:** YES - share by default unless separate XMP exists (e.g., `AB3D0001-DNG.xmp`)

---

## Dependencies

### Required

- Python 3.10+
- PyYAML >= 6.0 (existing)
- Jinja2 >= 3.1.0 (existing)
- pytest (testing)

### Optional

- Graphviz (for pipeline visualization - future)
- jsonschema (for YAML validation - future)

---

## Timeline (Estimated)

**Phase 1: Foundation (Week 1-2)**
- Design pipeline config schema
- Implement PipelineConfig class
- Write configuration validator
- Create default pipeline templates

**Phase 2: Validation Engine (Week 3-4)**
- Implement ImageGroupValidator
- Add stage matching logic
- Integrate metadata validation from PhotoStats
- Write unit tests (>85% coverage)

**Phase 3: CLI & Reporting (Week 5-6)**
- Build main CLI tool (pipeline_validation.py)
- Create Jinja2 HTML template
- Add Chart.js visualizations
- Implement JSON output format

**Phase 4: Testing & Documentation (Week 7-8)**
- Write integration tests
- Create user documentation (docs/pipeline-validation.md)
- Update CLAUDE.md with new tool
- Beta testing with sample photo collections

**Phase 5: Polish & Release (Week 9)**
- Address beta feedback
- Performance optimization
- Final QA
- Release v1.0.0

---

## Future Enhancements (v2.0+)

1. **Advanced Workflows:**
   - HDR merging (N:1 relationships)
   - Panorama stitching (N:1 relationships)
   - Focus stacking (N:1 relationships)

2. **Automated Remediation:**
   - Generate scripts to create missing files
   - Batch processing suggestions
   - Integration with Lightroom/Photoshop automation

3. **Cloud Storage:**
   - Validate files across multiple storage locations
   - Check cloud backup completeness
   - S3/Google Drive integration

4. **Real-Time Monitoring:**
   - Watch folders for new files
   - Alert when group becomes consistent
   - Webhook notifications

5. **Pipeline Templates:**
   - Share pipeline configurations
   - Import common workflows
   - Industry-standard pipeline presets

6. **Graphical Pipeline Editor:**
   - Visual pipeline configuration
   - Drag-and-drop stage builder
   - Interactive path testing

---

## Configuration Example

Here's a complete example of the pipeline configuration in `config.yaml`:

```yaml
# Existing configuration sections (unchanged)
photo_extensions:
  - .cr3
  - .dng
  - .tif
  - .tiff
  - .jpg
  - .jpeg

metadata_extensions:
  - .xmp

require_sidecar:
  - .cr3

camera_mappings:
  AB3D:
    - name: "Canon EOS R5"
      serial_number: "12345"

processing_methods:
  HDR: "High Dynamic Range processing"
  BW: "Black and White conversion"
  LOSSLESS: "Lossless JPG export"
  WEB: "Web-optimized JPG export"

# NEW: Processing pipeline configuration
processing_pipelines:
  stages:
    - id: capture
      name: "Camera Capture"
      file_types:
        - extension: .cr3
          required: true
          metadata_sidecar: .xmp
          metadata_required: false

    - id: import
      name: "Import & Sanction"
      file_types:
        - extension: .cr3
          required: true
          metadata_sidecar: .xmp
          metadata_required: true

    - id: dng_conversion
      name: "DNG Conversion"
      file_types:
        - extension: .dng
          required: true
          metadata_sidecar: .xmp
          metadata_required: true

    - id: tone_mapping
      name: "Tone Mapping"
      file_types:
        - extension: .tif
          required: true
          metadata_sidecar: .xmp
          metadata_required: false

    - id: individual_processing
      name: "Individual Processing"
      file_types:
        - extension: .tif
          required: true
          properties:
            - HDR
            - BW

    - id: web_export_lossy
      name: "Web Export"
      file_types:
        - extension: .jpg
          required: true
          properties:
            - WEB

  paths:
    - id: raw_archive
      name: "Raw Archive - Black Box"
      description: "Original CR3 + XMP, ready for long-term storage"
      archival_type: black_box
      stages:
        - capture
        - import
      validation:
        must_have_all: true
        terminal: true

    - id: dng_archive
      name: "DNG Archive - Black Box"
      description: "Converted to open DNG format for preservation"
      archival_type: black_box
      stages:
        - capture
        - import
        - dng_conversion
      validation:
        must_have_all: true
        terminal: true

    - id: browsable_archive
      name: "Browsable Archive - Web Ready"
      description: "Complete workflow with web-optimized exports"
      archival_type: browsable
      stages:
        - capture
        - import
        - dng_conversion
        - tone_mapping
        - individual_processing
        - web_export_lossy
      validation:
        must_have_all: true
        terminal: true
```

---

## Appendix A: Flowchart Analysis

Based on the provided flowchart, here are the identified pipeline paths:

### Path 1: Raw Archive (Black Box)
```
Camera Capture → Raw File (CR3) → Import → Sanction → CR3 + XMP → Black Box Archive
```

**Files Expected:**
- `AB3D0001.cr3`
- `AB3D0001.xmp`

### Path 2: DNG Archive (Black Box)
```
Camera Capture → Raw File (CR3) → Import → Digital Photo Developing → DNG + XMP → Black Box Archive
```

**Files Expected:**
- `AB3D0001.cr3` (may be discarded after conversion)
- `AB3D0001.dng`
- `AB3D0001.xmp`

### Path 3: Developed Archive (Black Box)
```
... → DNG → Export from Lightroom → Targeted Tone Mapping → TIF → Black Box Archive
```

**Files Expected:**
- `AB3D0001.cr3`
- `AB3D0001.dng`
- `AB3D0001.xmp`
- `AB3D0001.tif`

### Path 4: Browsable Archive
```
... → TIF → Individual Processing → TIF (processed) → JPG (lossless) → JPG (lossy) → Browsable Archive
```

**Files Expected:**
- `AB3D0001.cr3`
- `AB3D0001.dng`
- `AB3D0001.xmp`
- `AB3D0001.tif` (or `AB3D0001-HDR.tif`)
- `AB3D0001-WEB.jpg`

### Inconsistent Examples

**Missing XMP at Import:**
```
Files: AB3D0001.cr3
Status: INCONSISTENT
Missing: AB3D0001.xmp (required at import stage)
```

**Missing DNG for Archive:**
```
Files: AB3D0001.cr3, AB3D0001.xmp
Status: PARTIAL (matches raw_archive but not dng_archive)
```

**Missing JPG for Browsable:**
```
Files: AB3D0001.cr3, AB3D0001.dng, AB3D0001.xmp, AB3D0001.tif
Status: PARTIAL (matches developed_archive but not browsable_archive)
```

---

## Appendix B: Sample Validation Output

```json
{
  "scan_timestamp": "2025-12-25T14:30:00Z",
  "folder_path": "/home/user/Photos/2024",
  "total_groups": 1247,
  "summary": {
    "consistent": 892,
    "partial": 203,
    "inconsistent": 152
  },
  "archival_ready": {
    "black_box": 654,
    "browsable": 238,
    "not_ready": 355
  },
  "groups": [
    {
      "group_id": "AB3D0001",
      "camera_id": "AB3D",
      "counter": "0001",
      "status": "CONSISTENT",
      "archival_ready": true,
      "matched_paths": [
        {
          "path_id": "dng_archive",
          "path_name": "DNG Archive - Black Box",
          "archival_type": "black_box",
          "completion": 100
        }
      ],
      "files": [
        {
          "filename": "AB3D0001.cr3",
          "stage": "capture",
          "metadata_sidecar": "AB3D0001.xmp",
          "metadata_status": "LINKED"
        },
        {
          "filename": "AB3D0001.dng",
          "stage": "dng_conversion",
          "metadata_sidecar": "AB3D0001.xmp",
          "metadata_status": "SHARED"
        },
        {
          "filename": "AB3D0001.xmp",
          "stage": "import",
          "metadata_status": "PRIMARY"
        }
      ],
      "missing_files": []
    },
    {
      "group_id": "AB3D0042",
      "camera_id": "AB3D",
      "counter": "0042",
      "status": "INCONSISTENT",
      "archival_ready": false,
      "matched_paths": [],
      "files": [
        {
          "filename": "AB3D0042.cr3",
          "stage": "capture",
          "metadata_sidecar": null,
          "metadata_status": "MISSING_REQUIRED"
        }
      ],
      "missing_files": [
        {
          "stage": "import",
          "expected_extension": ".xmp",
          "reason": "Required for all archival paths"
        }
      ]
    }
  ]
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-25 | Claude | Initial draft based on flowchart analysis |

---

## Approval

- [ ] Product Owner
- [ ] Technical Lead
- [ ] User Representative

**Feedback & Questions:**
Please submit feedback via GitHub issue or email.
