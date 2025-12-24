# Feature Specification: Photo Pairing Tool

**Feature Branch**: `001-photo-pairing-tool`
**Created**: 2025-12-23
**Status**: Draft
**Input**: User description: "Tool to analyze photo filenames, pair related files, and extract camera and processing method analytics"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First Run Analysis (Priority: P1)

A photographer wants to analyze their photo collection for the first time. They run the tool on a folder containing photos from multiple cameras with various processing methods applied. The tool discovers new camera IDs and processing methods in the filenames, prompts the photographer to provide friendly names and descriptions, then generates a comprehensive report showing which cameras were used and what processing was applied.

**Why this priority**: This is the core value proposition - enabling users to gain insights into their photo collection through filename analysis. Without this, the tool has no purpose.

**Independent Test**: Can be fully tested by running the tool on a sample folder with photos from 2+ cameras and 2+ processing methods, verifying that prompts appear, configuration is saved, and a complete HTML report is generated.

**Acceptance Scenarios**:

1. **Given** a folder with photos named `AB3D0001.dng`, `AB3D0001-HDR.tiff`, `XYZW0001.cr3`, **When** the user runs the tool for the first time, **Then** the tool prompts for camera names for both "AB3D" and "XYZW", saves the mappings, and continues analysis
2. **Given** photos with processing method suffixes like `-HDR` and `-BW`, **When** the tool encounters these for the first time, **Then** it prompts the user for descriptions of each method and saves them for future use
3. **Given** the analysis completes successfully, **When** the user opens the generated HTML report, **Then** they see metrics including total images, groups detected, and breakdowns by camera and processing method

---

### User Story 2 - Subsequent Analysis with Existing Config (Priority: P2)

A photographer who has already configured camera and processing method mappings wants to analyze a new batch of photos. They run the tool on a different folder. The tool uses existing configuration without prompting, only asking about truly new camera IDs or processing methods it hasn't seen before.

**Why this priority**: Streamlined workflow for repeat usage is essential for tool adoption. Users shouldn't be re-prompted for information they've already provided.

**Independent Test**: Run the tool twice - once to establish config, second time on a new folder with overlapping camera IDs/methods. Verify no prompts appear for known mappings.

**Acceptance Scenarios**:

1. **Given** camera mappings already exist in configuration, **When** the user analyzes a new folder with photos from known cameras, **Then** no camera prompts appear and analysis proceeds automatically
2. **Given** a new processing method appears that wasn't in previous analyses, **When** the tool encounters it, **Then** it prompts only for that new method while using existing mappings for known methods

---

### User Story 3 - Invalid Filename Detection and Reporting (Priority: P3)

A photographer has a mixed collection with some files that don't follow their naming convention. They want to identify which files are non-compliant so they can rename or organize them separately.

**Why this priority**: Data quality is important but secondary to core analytics functionality. This helps users maintain consistent naming practices.

**Independent Test**: Analyze a folder containing both valid and invalid filenames, verify that invalid files are listed separately in the report with clear reasons why they're invalid.

**Acceptance Scenarios**:

1. **Given** a folder with files like `abc0001.dng` (lowercase), `AB3D0000.dng` (invalid counter), and valid files, **When** analysis runs, **Then** the report shows a count of invalid files and lists them with explanations
2. **Given** a file named `AB3D0035-.ext` with an empty property, **When** analysis runs, **Then** it's marked as invalid with reason "empty property name detected"

---

### Edge Cases

- What happens when a filename has duplicate properties (e.g., `AB3D0001-HDR-HDR.dng`)?
- How does the system handle very long filenames with many processing methods?
- What if a user cancels a configuration prompt mid-analysis?
- How are files with numeric-only suffixes distinguished from processing method properties?
- What happens when the same camera ID produces different serial numbers in config?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST analyze image filenames following the pattern: 4 uppercase alphanumeric characters + 4 digits (0001-9999) + optional properties
- **FR-002**: System MUST identify files not matching the naming convention and track them as "invalid image files"
- **FR-003**: System MUST group files with identical first 8 characters (camera ID + counter) as representing the same base image
- **FR-004**: System MUST extract camera identification from the first 4 characters of valid filenames
- **FR-005**: System MUST prompt users to provide camera names and optional serial numbers for new camera IDs encountered
- **FR-006**: System MUST extract processing methods from dash-prefixed properties in filenames (excluding all-numeric properties)
- **FR-007**: System MUST prompt users to provide descriptions for new processing methods encountered
- **FR-008**: System MUST distinguish separate images within a group using all-numeric dash-prefixed suffixes (e.g., `-2`, `-123`)
- **FR-009**: System MUST persist camera mappings and processing method descriptions to configuration file for future runs
- **FR-010**: System MUST generate an interactive HTML report with statistics, charts, and breakdowns
- **FR-011**: System MUST respect configured photo extensions and ignore metadata sidecar files (version 1.0)
- **FR-012**: System MUST handle duplicate properties in filenames by attaching each unique property only once per file
- **FR-013**: System MUST provide clear error messages for invalid filenames explaining what rule was violated
- **FR-014**: System MUST use the shared PhotoAdminConfig class for configuration management
- **FR-015**: Users MUST be able to run the tool on any folder containing supported photo file types

### Key Entities

- **Image Group**: A collection of related files sharing the same 8-character filename prefix (camera ID + counter). Represents a unique photo that may exist in multiple formats or with different processing applied.

- **Camera Mapping**: Association between a 4-character camera ID code and human-readable information (camera name and optional serial number). Stored persistently in configuration.

- **Processing Method**: A post-processing technique applied to an image, identified by dash-prefixed keywords in filenames. Each method has a user-provided description stored in configuration.

- **Separate Image**: Distinct images within a group, identified by all-numeric dash-prefixed suffixes. Used to track multiple exposures or variants captured with the same camera counter value.

- **Invalid File**: An image file that doesn't conform to the expected naming convention. Tracked separately with validation failure reasons.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can analyze a folder of 1000+ photos and receive a complete report in under 60 seconds (excluding configuration prompts)
- **SC-002**: System accurately groups 100% of validly-named files by their 8-character prefix with zero false groupings
- **SC-003**: Camera and processing method mappings persist across runs - users provide information once and never need to repeat it for known identifiers
- **SC-004**: Invalid files are identified with 100% accuracy and each includes a specific, actionable explanation of what naming rule was violated
- **SC-005**: HTML reports clearly present metrics and breakdowns that photographers can understand without technical knowledge
- **SC-006**: Users can determine their most-used camera and most-applied processing methods within 30 seconds of opening the report
- **SC-007**: The tool operates independently without requiring any other photo-admin tools to be installed or running

## Assumptions

- Photo filenames follow a consistent 8-character prefix convention established by the photographer's workflow
- Camera ID codes (first 4 characters) are unique per camera and don't change over time
- Processing method keywords in filenames are meaningful to the photographer and worth tracking as analytics
- Users are willing to provide one-time configuration input when new cameras or methods are detected
- HTML report format is acceptable for viewing results (no need for CSV, JSON, or other export formats in v1.0)
- Sidecar files can be safely ignored in version 1.0 (future enhancement to include them in groups)
- Photographers organize photos into folders for analysis (tool processes one folder at a time)
- File extensions for photo types are already configured in shared PhotoAdminConfig
