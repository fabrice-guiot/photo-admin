# Flowchart to Configuration Mapping

⚠️ **DEPRECATED - NEEDS UPDATE**

This document is based on the deprecated stage-based configuration model and contains **incorrect JPG terminology**.

**Current Issues:**
1. Uses "lossless JPG" and "lossy JPG" - **JPG is inherently lossy by design**
2. Correct terminology: "lowres JPG" (low-resolution) and "hires JPG" (high-resolution)
3. Based on linear stage model, not current node-based architecture

**Correct Information:**
- **TIF is the only lossless version** of the final processed image
- **lowres JPG**: Lower resolution for web browsing (smaller file, may use more aggressive compression)
- **hires JPG**: Higher resolution for sharing (larger file, less aggressive compression)
- Both JPG versions can be rebuilt from the TIF file

**Action Required:** This document will be rewritten to reflect the node-based pipeline architecture from `pipeline-config-example.yaml` and `node-architecture-analysis.md`.

---

## Legacy Content (Deprecated)

This document explains how the Photo Processing Pipeline flowchart translates into the `processing_pipelines` configuration.

---

## Flowchart Overview

The flowchart shows a photographer's workflow from camera capture through archival, with two archival endpoints:
- **Black Box Archive** - Long-term preservation storage (infrequent access)
- **Browsable Archive** - Web-accessible storage (frequent browsing)

---

## Stage Mapping

### Flowchart → Configuration Stages

| Flowchart Element | Config Stage ID | File Types | Metadata Required |
|-------------------|-----------------|------------|-------------------|
| "Camera captures" → "Raw File (CR3)" | `capture` | .cr3 | No (not yet created) |
| "Import into Lightroom" → "Sanction Process" | `import` | .cr3 + .xmp | **Yes** (XMP created here) |
| "Digital Photo Developing" → "DNG File" | `dng_conversion` | .dng + .xmp | Yes (shared or new XMP) |
| "Export from Lightroom" → "Targeted Tone Mapping in Adobe Lightroom" | `tone_mapping` | .tif/.tiff | No (metadata embedded) |
| "Individual Image Processing in Photoshop" | `individual_processing` | .tif with properties (HDR, BW) | No |
| "JPG File (lossless)" | `web_export_lossless` | .jpg with LOSSLESS property | No |
| "JPG File (lossy)" | `web_export_lossy` | .jpg with WEB property | No |

---

## Path Mapping

### Path 1: Raw Archive (Black Box)

**Flowchart Path:**
```
Camera → Raw File (CR3) → Import → Sanction → [Black Box Archive]
```

**Configuration:**
```yaml
- id: raw_archive_path
  name: "Raw Archive - Black Box"
  archival_type: black_box
  stages:
    - capture      # CR3 file
    - import       # XMP sidecar added
  validation:
    terminal: true  # Valid archival endpoint
```

**Expected Files:**
- `AB3D0001.cr3`
- `AB3D0001.xmp`

**Validation Logic:**
- Group is **CONSISTENT** if both files exist
- Group is **INCONSISTENT** if XMP missing
- Archival ready: **YES** (terminal path)

---

### Path 2: DNG Archive (Black Box)

**Flowchart Path:**
```
Camera → Raw File (CR3) → Import → Digital Photo Developing → DNG File → [Black Box Archive]
```

**Configuration:**
```yaml
- id: dng_archive_path
  name: "DNG Archive - Black Box"
  archival_type: black_box
  stages:
    - capture         # CR3 (optional, may be deleted)
    - import          # XMP created
    - dng_conversion  # DNG file
  validation:
    terminal: true
    optional_stages:
      - capture  # CR3 can be deleted after conversion
```

**Expected Files (Minimum):**
- `AB3D0001.dng`
- `AB3D0001.xmp`

**Expected Files (Complete):**
- `AB3D0001.cr3` (original, may be deleted)
- `AB3D0001.dng`
- `AB3D0001.xmp`

**Validation Logic:**
- Group is **CONSISTENT** if DNG + XMP exist (CR3 optional)
- CR3 presence is optional (photographer may delete after conversion)
- Archival ready: **YES**

---

### Path 3: Developed Archive (Black Box)

**Flowchart Path:**
```
... → DNG → Export from Lightroom → Tone Mapping → TIF → [Black Box Archive]
```

**Configuration:**
```yaml
- id: developed_archive_path
  name: "Developed Master Archive - Black Box"
  archival_type: black_box
  stages:
    - capture        # CR3 (optional)
    - import         # XMP
    - dng_conversion # DNG
    - tone_mapping   # TIF
  validation:
    terminal: true
    optional_stages:
      - capture
```

**Expected Files (Minimum):**
- `AB3D0001.dng`
- `AB3D0001.xmp`
- `AB3D0001.tif`

**Expected Files (Complete):**
- `AB3D0001.cr3` (original, may be deleted)
- `AB3D0001.dng`
- `AB3D0001.xmp`
- `AB3D0001.tif`

**Validation Logic:**
- Group is **CONSISTENT** if DNG + XMP + TIF exist
- CR3 optional (may be deleted to save space)
- Archival ready: **YES**

---

### Path 4: Browsable Archive (Complete Workflow)

**Flowchart Path:**
```
... → TIF → Individual Processing → TIF (processed) → JPG (lossless) → JPG (lossy/paring) → [Browsable Archive]
```

**Configuration:**
```yaml
- id: browsable_archive_path
  name: "Browsable Archive - Complete Workflow"
  archival_type: browsable
  stages:
    - capture
    - import
    - dng_conversion
    - tone_mapping
    - individual_processing  # HDR, BW, etc.
    - web_export_lossy      # WEB property
  validation:
    terminal: true
    optional_stages:
      - capture
      - individual_processing  # Not all images need advanced processing
```

**Expected Files (Minimum - Simple Workflow):**
- `AB3D0001.dng`
- `AB3D0001.xmp`
- `AB3D0001.tif`
- `AB3D0001-WEB.jpg`

**Expected Files (Complete - Advanced Processing):**
- `AB3D0001.cr3` (original, optional)
- `AB3D0001.dng`
- `AB3D0001.xmp`
- `AB3D0001.tif` (base tone mapping)
- `AB3D0001-HDR.tif` (individual processing)
- `AB3D0001-HDR-WEB.jpg` (web export)

**Validation Logic:**
- Group is **CONSISTENT** if has web-ready JPG
- Individual processing stage is optional
- Properties (HDR, BW) indicate advanced processing
- Archival ready: **YES** (browsable)

---

## Metadata Linking Rules

### CR3 → XMP Linking

**Flowchart:**
```
Raw File (CR3) → Import/Sanction → Metadata File (.XMP)
```

**Configuration Rule:**
```yaml
stages:
  - id: import
    file_types:
      - extension: .cr3
        metadata_sidecar: .xmp
        metadata_required: true  # MUST have XMP after import
```

**Validation:**
- `AB3D0001.cr3` **requires** `AB3D0001.xmp` after import stage
- Files are "linked" by base filename matching
- Uses PhotoStats' pairing logic

---

### DNG Metadata Handling

**Flowchart:**
```
DNG File ← can use CR3's XMP OR have separate XMP
```

**Configuration Rule:**
```yaml
validation_rules:
  allow_shared_xmp:
    - source: .cr3
      target: .dng
      # CR3 and DNG can share same XMP
```

**Validation:**
- **Option 1:** `AB3D0001.dng` uses `AB3D0001.xmp` (shared with CR3)
- **Option 2:** `AB3D0001-DNG.xmp` (separate XMP for DNG)
- Both are valid, tool checks for either

---

### TIF Metadata Handling

**Flowchart:**
```
TIF file → typically embeds metadata (XMP optional)
```

**Configuration Rule:**
```yaml
stages:
  - id: tone_mapping
    file_types:
      - extension: .tif
        metadata_sidecar: .xmp
        metadata_required: false  # Optional, metadata often embedded
```

**Validation:**
- `AB3D0001.tif` does NOT require XMP
- XMP can exist (`AB3D0001.xmp`) but not mandatory
- TIF files typically embed XMP metadata internally

---

## Processing Properties

### Individual Processing Stage

**Flowchart:**
```
Individual Image Processing → HDR, BW, PANO, etc.
```

**Configuration:**
```yaml
stages:
  - id: individual_processing
    file_types:
      - extension: .tif
        properties:
          - HDR   # High Dynamic Range
          - BW    # Black and White
          - PANO  # Panorama
```

**File Naming:**
- Base file: `AB3D0001.tif` (from tone_mapping stage)
- HDR processed: `AB3D0001-HDR.tif` (individual_processing stage)
- Multiple properties: `AB3D0001-HDR-BW.tif`

**Validation:**
- Properties indicate which processing was applied
- Must be defined in `processing_methods` config
- Tool prompts for unknown properties

---

### Web Export Properties

**Flowchart:**
```
JPG (lossless) → LOSSLESS property
JPG (lossy) → WEB property
```

**Configuration:**
```yaml
stages:
  - id: web_export_lossless
    file_types:
      - extension: .jpg
        properties: [LOSSLESS]

  - id: web_export_lossy
    file_types:
      - extension: .jpg
        properties: [WEB]
```

**File Naming:**
- Lossless: `AB3D0001-LOSSLESS.jpg`
- Web-optimized: `AB3D0001-WEB.jpg`
- With processing: `AB3D0001-HDR-WEB.jpg`

---

## Inconsistent Group Detection

### Example 1: Missing XMP at Import

**Files Found:**
- `AB3D0001.cr3`

**Expected:**
- `AB3D0001.cr3`
- `AB3D0001.xmp` ← **MISSING**

**Classification:**
- Status: **INCONSISTENT**
- Matched paths: None (import stage requires XMP)
- Missing files:
  ```
  - stage: import
    expected_extension: .xmp
    reason: "Required for all archival paths"
  ```
- Archival ready: **NO**

**Recommendation:**
```
⚠ Import this file into Lightroom to create XMP sidecar
  Command: Import AB3D0001.cr3 into Lightroom
  Expected result: AB3D0001.xmp will be created
```

---

### Example 2: Partial DNG Conversion

**Files Found:**
- `AB3D0001.cr3`
- `AB3D0001.xmp`

**Expected (for DNG Archive):**
- `AB3D0001.cr3` (optional)
- `AB3D0001.xmp`
- `AB3D0001.dng` ← **MISSING**

**Classification:**
- Status: **PARTIAL** (matches `raw_archive_path` but not `dng_archive_path`)
- Matched paths:
  - `raw_archive_path` (100% complete) ✓
- Archival ready: **YES** (for raw archive) / **NO** (for DNG archive)

**Recommendation:**
```
✓ Ready for Raw Archive (Black Box)
⚠ To create DNG Archive, convert CR3 to DNG:
  Command: Use Lightroom "Export as DNG" feature
  Expected result: AB3D0001.dng will be created
```

---

### Example 3: Missing Web Export

**Files Found:**
- `AB3D0001.cr3`
- `AB3D0001.dng`
- `AB3D0001.xmp`
- `AB3D0001.tif`

**Expected (for Browsable Archive):**
- All above files ✓
- `AB3D0001-WEB.jpg` ← **MISSING**

**Classification:**
- Status: **PARTIAL** (matches `developed_archive_path` but not `browsable_archive_path`)
- Matched paths:
  - `raw_archive_path` (100%)
  - `dng_archive_path` (100%)
  - `developed_archive_path` (100%) ✓
- Archival ready: **YES** (for black box) / **NO** (for browsable)

**Recommendation:**
```
✓ Ready for Developed Master Archive (Black Box)
⚠ To create Browsable Archive, export web JPG:
  Command: Export TIF as JPG with WEB property
  Expected result: AB3D0001-WEB.jpg will be created
```

---

## Archival Type Classification

### Black Box Archive

**Characteristics:**
- Long-term preservation
- Master files (RAW, DNG, TIF)
- Infrequent access
- High quality, large file sizes

**Paths:**
- `raw_archive_path` - Original CR3 + XMP
- `dng_archive_path` - Open format DNG + XMP
- `developed_archive_path` - Fully developed TIF

**Use Cases:**
- Professional photographer's master archive
- Museum/library digital preservation
- Legal/compliance archival requirements

---

### Browsable Archive

**Characteristics:**
- Web-accessible
- Includes web-optimized JPG files
- Frequent browsing and sharing
- Smaller file sizes

**Paths:**
- `browsable_archive_path` - Complete workflow with JPG export

**Use Cases:**
- Online portfolio websites
- Client galleries
- Social media ready files
- Family photo sharing

---

## Tool Integration

### Photo Pairing Tool Integration

**What Photo Pairing Does:**
- Groups files by camera_id + counter
- Example: `AB3D0001.cr3`, `AB3D0001.dng`, `AB3D0001.tif` → one group

**What Pipeline Validation Adds:**
- Validates group against pipeline paths
- Checks if group is complete
- Identifies missing files
- Determines archival readiness

**Combined Result:**
```
Group: AB3D0001
├─ Photo Pairing: 3 files in group
│  ├─ AB3D0001.cr3
│  ├─ AB3D0001.dng
│  └─ AB3D0001.xmp
│
└─ Pipeline Validation:
   ├─ Status: CONSISTENT
   ├─ Matched path: dng_archive_path
   ├─ Archival ready: YES (Black Box)
   └─ Missing files: None
```

---

### PhotoStats Integration

**What PhotoStats Does:**
- Identifies CR3 files
- Checks for matching XMP sidecars
- Reports orphaned files (CR3 without XMP)

**What Pipeline Validation Adds:**
- Stage-aware metadata validation
- Allows shared XMP (CR3 and DNG use same XMP)
- Validates metadata requirements per stage

**Combined Result:**
```
File: AB3D0001.cr3
├─ PhotoStats: Has sidecar AB3D0001.xmp ✓
│
└─ Pipeline Validation:
   ├─ Stage: import
   ├─ Metadata required: YES
   ├─ Metadata found: AB3D0001.xmp ✓
   └─ Status: VALID

File: AB3D0001.dng
├─ PhotoStats: No dedicated sidecar (uses AB3D0001.xmp)
│
└─ Pipeline Validation:
   ├─ Stage: dng_conversion
   ├─ Metadata required: YES
   ├─ Shared metadata: AB3D0001.xmp ✓
   └─ Status: VALID (shared XMP allowed)
```

---

## Configuration Best Practices

### 1. Define Your Workflow First

Before configuring pipeline paths, document your actual workflow:

```
1. Camera → CR3 files on memory card
2. Import → Lightroom creates XMP sidecars
3. Convert → Some files converted to DNG
4. Develop → Export tone-mapped TIF files
5. Process → Photoshop editing (HDR, BW)
6. Export → Web-ready JPG files
```

Then map each step to a stage in config.

---

### 2. Start with Terminal Paths

Define archival endpoints first:

```yaml
paths:
  # 1. Define terminal paths (valid archival endpoints)
  - id: raw_archive_path
    terminal: true
    archival_type: black_box

  - id: browsable_archive_path
    terminal: true
    archival_type: browsable

  # 2. Then add partial paths for detection
  - id: partial_import
    terminal: false
    archival_type: null
```

---

### 3. Use Optional Stages Wisely

Mark stages as optional when files may be deleted:

```yaml
stages:
  - capture  # CR3 may be deleted after DNG conversion
  - import
  - dng_conversion

optional_stages:
  - capture  # Allow archival even if CR3 deleted
```

**Why:** Photographers often delete large CR3 files after DNG conversion to save space.

---

### 4. Allow Shared Metadata

Enable XMP sharing between related file types:

```yaml
allow_shared_xmp:
  - source: .cr3
    target: .dng
```

**Why:** One XMP file can contain metadata for both CR3 and DNG, avoiding duplication.

---

### 5. Define Processing Properties

Document all processing methods used:

```yaml
processing_methods:
  HDR: "High Dynamic Range processing"
  BW: "Black and White conversion"
  PANO: "Panorama stitching"
  FOCUS: "Focus stacking"
  LOSSLESS: "Lossless JPG export"
  WEB: "Web-optimized JPG export"
```

**Why:** Tool will prompt for unknown properties, slowing down analysis.

---

## Validation Examples

### Example 1: Consistent Group (DNG Archive)

**Files:**
```
AB3D0001.cr3
AB3D0001.dng
AB3D0001.xmp
```

**Validation Result:**
```yaml
group_id: AB3D0001
status: CONSISTENT
archival_ready: true
matched_paths:
  - path_id: raw_archive_path
    completion: 100%
    archival_type: black_box
  - path_id: dng_archive_path
    completion: 100%
    archival_type: black_box
missing_files: []
```

**Report:**
```
✓ Group AB3D0001: CONSISTENT
  Ready for archival: YES (Black Box Archive)
  Matched paths:
    • Raw Archive Path (100%)
    • DNG Archive Path (100%)
```

---

### Example 2: Partial Group (Missing Web Export)

**Files:**
```
AB3D0001.cr3
AB3D0001.dng
AB3D0001.xmp
AB3D0001.tif
```

**Validation Result:**
```yaml
group_id: AB3D0001
status: PARTIAL
archival_ready: true  # For black_box, not for browsable
matched_paths:
  - path_id: developed_archive_path
    completion: 100%
    archival_type: black_box
missing_files:
  - stage: web_export_lossy
    expected_extension: .jpg
    expected_property: WEB
    reason: "Required for browsable_archive_path"
```

**Report:**
```
⚠ Group AB3D0001: PARTIAL
  Ready for archival: YES (Black Box Archive only)
  Matched paths:
    • Developed Archive Path (100%) ✓

  To create Browsable Archive:
    Missing: AB3D0001-WEB.jpg
    Action: Export TIF as web-optimized JPG
```

---

### Example 3: Inconsistent Group (Missing XMP)

**Files:**
```
AB3D0001.cr3
```

**Validation Result:**
```yaml
group_id: AB3D0001
status: INCONSISTENT
archival_ready: false
matched_paths: []
missing_files:
  - stage: import
    expected_extension: .xmp
    reason: "Required for all archival paths"
```

**Report:**
```
✗ Group AB3D0001: INCONSISTENT
  Ready for archival: NO
  Matched paths: None

  Missing required files:
    • AB3D0001.xmp (needed at import stage)
    Action: Import file into Lightroom to create XMP sidecar
```

---

## Summary

This mapping demonstrates how the flowchart translates into a comprehensive configuration system:

1. **Stages** define each step in the workflow with file type requirements
2. **Paths** define valid sequences through stages for specific archival goals
3. **Metadata rules** handle CR3→XMP linking and shared metadata
4. **Properties** identify processing methods (HDR, BW, WEB)
5. **Validation** classifies groups as CONSISTENT, PARTIAL, or INCONSISTENT
6. **Integration** combines Photo Pairing grouping with PhotoStats metadata logic

The result is a powerful tool that can validate whether photo collections are ready for archival and identify exactly what's missing from incomplete workflows.
