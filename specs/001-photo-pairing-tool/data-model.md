# Data Model: Photo Pairing Tool

**Feature**: Photo Pairing Tool
**Date**: 2025-12-23
**Phase**: 1 - Data Model Design

## Overview

This document defines the data entities and their relationships for the Photo Pairing Tool. The tool uses simple Python data structures (dictionaries and lists) following the YAGNI principle.

## Core Entities

### ImageGroup

Represents a collection of related files that share the same 8-character filename prefix (camera ID + counter).

**Structure**:
```python
{
    'group_id': str,              # 8-character prefix (e.g., 'AB3D0001')
    'camera_id': str,             # First 4 characters (e.g., 'AB3D')
    'counter': str,               # Characters 5-8 (e.g., '0001')
    'files': List[Path],          # Full paths to all files in this group
    'properties': Set[str],       # Unique processing methods found across files
    'separate_images': Dict[str, List[Path]]  # Numeric suffixes -> files
}
```

**Example**:
```python
{
    'group_id': 'AB3D0035',
    'camera_id': 'AB3D',
    'counter': '0035',
    'files': [
        Path('AB3D0035.dng'),
        Path('AB3D0035-HDR.tiff'),
        Path('AB3D0035-2.cr3')
    ],
    'properties': {'HDR'},
    'separate_images': {
        '2': [Path('AB3D0035-2.cr3')]
    }
}
```

**Validation Rules**:
- `camera_id`: Exactly 4 uppercase alphanumeric characters [A-Z0-9]{4}
- `counter`: Exactly 4 digits, range 0001-9999 (0000 invalid)
- `properties`: Excludes all-numeric suffixes (those go to separate_images)
- `files`: At least one file must exist in the group

**Relationships**:
- One-to-one with CameraMapping (via camera_id)
- One-to-many with ProcessingMethod (via properties set)
- Contains multiple files representing the same logical image

### CameraMapping

Associates a 4-character camera ID code with human-readable information.

**Structure**:
```python
{
    'id': str,                    # 4-character camera ID (e.g., 'AB3D')
    'name': str,                  # Human-readable camera name (required)
    'serial_number': str          # Optional serial number (can be empty string)
}
```

**Storage**: Persisted in YAML config file under `camera_mappings` key

**YAML Example**:
```yaml
camera_mappings:
  AB3D:
    name: "Canon EOS R5"
    serial_number: "12345"
  XYZW:
    name: "Sony A7IV"
    serial_number: ""  # Optional - empty if not provided
```

**Validation Rules**:
- `id`: Must match [A-Z0-9]{4} pattern
- `name`: Required, non-empty string after strip()
- `serial_number`: Optional, can be empty string

**Lifecycle**:
1. Tool discovers new camera ID in filename
2. Prompts user for name and optional serial number
3. Saves to config file immediately
4. Used for all future files with that camera ID

### ProcessingMethod

Describes a post-processing technique identified by dash-prefixed keywords in filenames.

**Structure**:
```python
{
    'keyword': str,               # Keyword from filename (e.g., 'HDR', 'property 2')
    'description': str            # User-provided description
}
```

**Storage**: Persisted in YAML config file under `processing_methods` key

**YAML Example**:
```yaml
processing_methods:
  "HDR": "High Dynamic Range processing"
  "BW": "Black and white conversion"
  "PANO": "Panorama stitching"
  "property 2": "Description for property 2"  # Spaces allowed in keywords
```

**Extraction Rules**:
- Keywords start with dash (`-`) in filename
- Terminate at next dash or file extension
- Can contain: alphanumeric (A-Z, a-z, 0-9) and spaces
- No special characters except spaces
- Case-sensitive
- Empty keywords make filename invalid

**Validation Rules**:
- `keyword`: Non-empty, alphanumeric + spaces only
- `description`: Required when prompting user
- All-numeric keywords (e.g., `-2`, `-123`) are NOT processing methods - they're separate image identifiers

**Lifecycle**:
1. Tool finds dash-prefixed keyword in filename
2. Checks if keyword is all-numeric (skip if true - it's a separate image ID)
3. Checks if mapping exists in config
4. If not, prompts user for description
5. Saves to config file
6. Attaches to ImageGroup's properties set

### SeparateImage

Identifies distinct images within a group using all-numeric dash-prefixed suffixes.

**Concept**: Files like `AB3D0035-2.dng` represent a different image than `AB3D0035.dng`, even though they share the same 8-character base.

**Structure** (embedded in ImageGroup):
```python
# Within ImageGroup entity
'separate_images': {
    '2': [Path('AB3D0035-2.cr3'), Path('AB3D0035-2-HDR.tiff')],
    '123': [Path('AB3D0035-123.dng')]
}
```

**Detection Logic**:
- Dash-prefixed property is all digits: `property.isdigit() == True`
- First all-numeric property in filename determines separate image ID
- Later properties can still be processing methods

**Example Parsing**:
- `AB3D0035.dng` → Base image (no suffix)
- `AB3D0035-2.dng` → Separate image #2
- `AB3D0035-HDR-2.dng` → Separate image #2 with HDR processing
- `AB3D0035-2-HDR.dng` → Separate image #2 with HDR processing (same as above)

**Impact on Analytics**:
- Total images count = sum of (1 base image + N separate images) across all groups
- Group without separate images = 1 image
- Group with separate images {2, 3} = 3 images total (base + 2 + 3)

### InvalidFile

Tracks files that don't conform to the expected naming convention.

**Structure**:
```python
{
    'filename': str,              # Just the filename, not full path
    'path': Path,                 # Full path for reference
    'reason': str                 # Specific validation failure message
}
```

**Example**:
```python
{
    'filename': 'abc0001.dng',
    'path': Path('/photos/abc0001.dng'),
    'reason': 'Camera ID must be uppercase alphanumeric [A-Z0-9]'
}
```

**Validation Failure Reasons**:
- "Camera ID must be uppercase alphanumeric [A-Z0-9]" - lowercase or special chars
- "Camera ID must be exactly 4 characters" - too short/long
- "Counter must be 4 digits between 0001 and 9999" - invalid counter
- "Counter cannot be 0000" - specifically 0000
- "Empty property name detected" - filename has `--` or ends with `-` before extension
- "Invalid characters in property name" - property contains special chars (not alphanumeric or space)

**Reporting**:
- Count displayed in HTML report
- Table listing all invalid files with reasons
- Helps users identify files to rename

## Analytics Aggregations

### CameraUsage

**Structure**:
```python
{
    'AB3D': {
        'name': 'Canon EOS R5',
        'serial_number': '12345',
        'image_count': 150,       # Total images (including separate images)
        'group_count': 125        # Total groups
    },
    'XYZW': {
        'name': 'Sony A7IV',
        'serial_number': '',
        'image_count': 75,
        'group_count': 70
    }
}
```

**Calculation**:
- `image_count`: Sum of images across all groups for this camera (count base + separate images)
- `group_count`: Number of unique 8-character prefixes starting with this camera ID

### MethodUsage

**Structure**:
```python
{
    'HDR': {
        'description': 'High Dynamic Range processing',
        'image_count': 45         # Images with this processing method
    },
    'BW': {
        'description': 'Black and white conversion',
        'image_count': 30
    }
}
```

**Calculation**:
- `image_count`: Count of images (base + separate) that have this property attached

### ReportStatistics

**Structure**:
```python
{
    'total_files_scanned': int,
    'total_groups': int,
    'total_images': int,              # Sum of all images across groups
    'total_invalid_files': int,
    'avg_files_per_group': float,
    'max_files_per_group': int,
    'cameras_used': int,              # Unique camera IDs
    'processing_methods_used': int    # Unique processing methods
}
```

**Example**:
```python
{
    'total_files_scanned': 500,
    'total_groups': 200,
    'total_images': 225,              # 200 base + 25 separate images
    'total_invalid_files': 5,
    'avg_files_per_group': 2.5,
    'max_files_per_group': 8,
    'cameras_used': 3,
    'processing_methods_used': 5
}
```

## Data Flow

1. **Scanning Phase**:
   - Read folder, discover files with photo extensions
   - Validate each filename against pattern
   - Build ImageGroup dictionary by 8-char prefix
   - Accumulate invalid files list

2. **Configuration Phase**:
   - For each unique camera_id in groups, check CameraMapping
   - For each unique property in groups, check ProcessingMethod
   - Prompt user for missing mappings
   - Save updates to YAML config file

3. **Analytics Phase**:
   - Calculate CameraUsage from groups
   - Calculate MethodUsage from groups
   - Compute ReportStatistics

4. **Reporting Phase**:
   - Generate HTML with all aggregations
   - Include tables and charts for visualizations
   - List invalid files with reasons

## Persistence

**Configuration (YAML)**:
- Location: `./config/config.yaml` or `~/.photo-admin/config.yaml`
- Managed by: PhotoAdminConfig class
- Updated by: Tool when new cameras/methods discovered
- Format: YAML with two new top-level keys

**Reports (HTML)**:
- Location: Current directory
- Filename: `photo_pairing_report_YYYY-MM-DD_HH-MM-SS.html`
- One report per run
- Self-contained (embedded CSS/JS via CDN)

**No Database**: All analysis is ephemeral - run tool to regenerate report. Only config is persisted.
