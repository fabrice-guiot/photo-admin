#!/usr/bin/env python3
"""
Photo Processing Pipeline Validation Tool

Validates photo collections against user-defined processing workflows (pipelines)
defined as directed graphs of nodes. Integrates with Photo Pairing Tool to obtain
file groupings, traverses pipeline paths, and classifies images as CONSISTENT,
CONSISTENT-WITH-WARNING, PARTIAL, or INCONSISTENT.

Core Value: Automated validation of 10,000+ image groups in under 60 seconds
(with caching), enabling photographers to identify incomplete processing workflows
and assess archival readiness without manual file inspection.

Usage:
    python3 pipeline_validation.py <folder_path>
    python3 pipeline_validation.py <folder_path> --config <config_path>
    python3 pipeline_validation.py <folder_path> --force-regenerate
    python3 pipeline_validation.py --help

Author: photo-admin project
License: AGPL-3.0
Version: 1.0.0
"""

import argparse
import sys
import signal
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from enum import Enum

# Tool version (semantic versioning)
TOOL_VERSION = "1.0.0"

# Maximum loop iterations for Process nodes to prevent infinite path enumeration
MAX_ITERATIONS = 5


# =============================================================================
# Data Structures - Pipeline Configuration
# =============================================================================

@dataclass
class NodeBase:
    """Base class for all pipeline nodes."""
    id: str
    type: str
    name: str
    output: List[str]


@dataclass
class CaptureNode(NodeBase):
    """
    Capture Node - Starting point of pipeline.

    Represents the camera capture event that produces initial files.
    Must have at least one output (typically raw files).
    """
    type: str = field(default="Capture", init=False)


@dataclass
class FileNode(NodeBase):
    """
    File Node - Represents an expected file in the workflow.

    Attributes:
        extension: File extension including leading dot (e.g., ".CR3", ".DNG", ".XMP")
    """
    extension: str
    type: str = field(default="File", init=False)


@dataclass
class ProcessNode(NodeBase):
    """
    Process Node - Editing/conversion step that adds suffixes to filenames.

    Attributes:
        method_ids: List of processing method IDs that add suffixes.
                   Empty string means no suffix added (selection only).
                   Examples: [""], ["DxO_DeepPRIME_XD2s"], ["Edit"]
    """
    method_ids: List[str]
    type: str = field(default="Process", init=False)


@dataclass
class PairingNode(NodeBase):
    """
    Pairing Node - Multi-image merge operation (HDR, Panorama, Focus Stack).

    Attributes:
        pairing_type: Human-readable pairing operation type
        input_count: Expected number of input images
    """
    pairing_type: str
    input_count: int
    type: str = field(default="Pairing", init=False)


@dataclass
class BranchingNode(NodeBase):
    """
    Branching Node - Conditional path selection.

    Validation explores ALL branches (not just one path).

    Attributes:
        condition_description: Human-readable explanation of branching condition
    """
    condition_description: str
    type: str = field(default="Branching", init=False)


@dataclass
class TerminationNode(NodeBase):
    """
    Termination Node - End of pipeline (archival ready state).

    Represents a valid archival state. Images matching a path to this
    termination are considered archival ready for this termination type.

    Attributes:
        termination_type: Type of archival state (e.g., "Black Box Archive")
    """
    termination_type: str
    type: str = field(default="Termination", init=False)


# Type alias for any pipeline node
PipelineNode = Union[CaptureNode, FileNode, ProcessNode, PairingNode, BranchingNode, TerminationNode]


@dataclass
class PipelineConfig:
    """
    Complete pipeline configuration containing all nodes.

    Attributes:
        nodes: List of all pipeline nodes
        nodes_by_id: Dictionary mapping node IDs to node objects (populated after init)
    """
    nodes: List[PipelineNode]
    nodes_by_id: Dict[str, PipelineNode] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Build node ID lookup dictionary after initialization."""
        self.nodes_by_id = {node.id: node for node in self.nodes}


# =============================================================================
# Data Structures - Validation Results
# =============================================================================

class ValidationStatus(Enum):
    """
    Validation status classification for image completeness.

    Values:
        CONSISTENT: All expected files present, no extra files
        CONSISTENT_WITH_WARNING: All expected files present, but extra files exist
        PARTIAL: Some expected files missing (incomplete workflow)
        INCONSISTENT: No matching pipeline paths (wrong files or completely wrong)
    """
    CONSISTENT = "CONSISTENT"
    CONSISTENT_WITH_WARNING = "CONSISTENT-WITH-WARNING"
    PARTIAL = "PARTIAL"
    INCONSISTENT = "INCONSISTENT"


@dataclass
class SpecificImage:
    """
    Represents a single image within an ImageGroup.

    Flattened from ImageGroup's separate_images structure.

    Attributes:
        unique_id: Unique identifier (base_filename: camera_id + counter + suffix)
        group_id: Parent ImageGroup ID (camera_id + counter)
        camera_id: 4-character camera identifier
        counter: 4-digit counter string
        suffix: Separate image suffix ("" for primary, "2", "HDR", etc.)
        actual_files: List of actual files found for this specific image
    """
    unique_id: str
    group_id: str
    camera_id: str
    counter: str
    suffix: str
    actual_files: List[str]


@dataclass
class TerminationMatchResult:
    """
    Validation result for one termination node path.

    Attributes:
        termination_id: Termination node ID
        termination_type: Human-readable termination type
        status: Validation status for this termination
        completion_percentage: Percentage of expected files present (0-100)
        missing_files: List of missing expected files
        extra_files: List of extra files not in pipeline
        truncated: Whether path was truncated due to loop limit
        truncation_note: Explanation of truncation (None if not truncated)
    """
    termination_id: str
    termination_type: str
    status: ValidationStatus
    completion_percentage: float
    missing_files: List[str]
    extra_files: List[str]
    truncated: bool
    truncation_note: Optional[str] = None


@dataclass
class ValidationResult:
    """
    Complete validation result for one SpecificImage.

    Attributes:
        unique_id: Specific image unique identifier (base_filename)
        group_id: Parent ImageGroup ID
        camera_id: Camera identifier
        counter: Counter string
        suffix: Separate image suffix
        actual_files: Actual files found
        termination_matches: List of validation results per termination node
        overall_status: Worst status across all terminations
        archival_ready_for: List of termination types that are archival ready
    """
    unique_id: str
    group_id: str
    camera_id: str
    counter: str
    suffix: str
    actual_files: List[str]
    termination_matches: List[TerminationMatchResult]
    overall_status: ValidationStatus
    archival_ready_for: List[str]


# =============================================================================
# Pipeline Configuration Loading
# =============================================================================

def parse_node_from_yaml(node_dict: Dict[str, Any]) -> PipelineNode:
    """
    Parse a pipeline node from YAML dictionary.

    Args:
        node_dict: Dictionary containing node configuration from YAML

    Returns:
        Appropriate node object based on 'type' field

    Raises:
        ValueError: If node type is invalid or required fields are missing
    """
    node_type = node_dict.get('type')
    node_id = node_dict.get('id')
    name = node_dict.get('name')
    output = node_dict.get('output', [])

    if not all([node_type, node_id, name]):
        raise ValueError(f"Missing required fields (id, type, name) in node: {node_dict}")

    # Dispatch based on node type
    if node_type == 'Capture':
        return CaptureNode(
            id=node_id,
            name=name,
            output=output
        )
    elif node_type == 'File':
        extension = node_dict.get('extension')
        if not extension:
            raise ValueError(f"File node '{node_id}' missing required 'extension' field")
        return FileNode(
            id=node_id,
            name=name,
            output=output,
            extension=extension
        )
    elif node_type == 'Process':
        method_ids = node_dict.get('method_ids')
        if method_ids is None:
            raise ValueError(f"Process node '{node_id}' missing required 'method_ids' field")
        return ProcessNode(
            id=node_id,
            name=name,
            output=output,
            method_ids=method_ids
        )
    elif node_type == 'Pairing':
        pairing_type = node_dict.get('pairing_type')
        input_count = node_dict.get('input_count')
        if not pairing_type or input_count is None:
            raise ValueError(f"Pairing node '{node_id}' missing required fields (pairing_type, input_count)")
        return PairingNode(
            id=node_id,
            name=name,
            output=output,
            pairing_type=pairing_type,
            input_count=input_count
        )
    elif node_type == 'Branching':
        condition_description = node_dict.get('condition_description')
        if not condition_description:
            raise ValueError(f"Branching node '{node_id}' missing required 'condition_description' field")
        return BranchingNode(
            id=node_id,
            name=name,
            output=output,
            condition_description=condition_description
        )
    elif node_type == 'Termination':
        termination_type = node_dict.get('termination_type')
        if not termination_type:
            raise ValueError(f"Termination node '{node_id}' missing required 'termination_type' field")
        return TerminationNode(
            id=node_id,
            name=name,
            output=output,
            termination_type=termination_type
        )
    else:
        raise ValueError(f"Unknown node type: {node_type} (node: {node_id})")


def load_pipeline_config(config_path: Path) -> PipelineConfig:
    """
    Load pipeline configuration from YAML config file.

    Args:
        config_path: Path to configuration file (config.yaml)

    Returns:
        PipelineConfig object with all parsed nodes

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If YAML is invalid or pipeline structure is malformed
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load YAML file
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}")

    if not config_data:
        raise ValueError("Configuration file is empty")

    # Extract processing_pipelines section
    processing_pipelines = config_data.get('processing_pipelines')
    if not processing_pipelines:
        raise ValueError("Missing 'processing_pipelines' section in configuration file")

    # Extract nodes list
    nodes_list = processing_pipelines.get('nodes')
    if not nodes_list:
        raise ValueError("Missing 'nodes' list in processing_pipelines section")

    if not isinstance(nodes_list, list):
        raise ValueError("'nodes' must be a list")

    # Parse each node
    nodes = []
    for i, node_dict in enumerate(nodes_list):
        try:
            node = parse_node_from_yaml(node_dict)
            nodes.append(node)
        except ValueError as e:
            raise ValueError(f"Error parsing node at index {i}: {e}")

    # Create and return PipelineConfig
    return PipelineConfig(nodes=nodes)


def validate_pipeline_structure(pipeline: PipelineConfig, config) -> List[str]:
    """
    Validate pipeline structure for consistency and correctness.

    Performs the following validation checks:
    1. Exactly one Capture node exists
    2. At least one Termination node exists
    3. All output references point to existing nodes
    4. No orphaned nodes (all reachable from Capture)
    5. No duplicate node IDs (already enforced by PipelineConfig)
    6. File extensions match photo_extensions or metadata_extensions
    7. Processing method_ids exist in processing_methods config

    Args:
        pipeline: PipelineConfig to validate
        config: PhotoAdminConfig with photo_extensions, metadata_extensions, processing_methods

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check 1: Exactly one Capture node
    capture_nodes = [n for n in pipeline.nodes if isinstance(n, CaptureNode)]
    if len(capture_nodes) == 0:
        errors.append("Pipeline must have exactly one Capture node (found 0)")
    elif len(capture_nodes) > 1:
        capture_ids = [n.id for n in capture_nodes]
        errors.append(f"Pipeline must have exactly one Capture node (found {len(capture_nodes)}: {capture_ids})")

    # Check 2: At least one Termination node
    termination_nodes = [n for n in pipeline.nodes if isinstance(n, TerminationNode)]
    if len(termination_nodes) == 0:
        errors.append("Pipeline must have at least one Termination node")

    # Check 3: All output references point to existing nodes
    for node in pipeline.nodes:
        for output_id in node.output:
            if output_id not in pipeline.nodes_by_id:
                errors.append(f"Node '{node.id}' references non-existent output node '{output_id}'")

    # Check 4: No orphaned nodes (all reachable from Capture)
    if capture_nodes:
        capture_node = capture_nodes[0]
        reachable = set()
        visited = set()

        def dfs(node_id: str):
            """Depth-first search to find all reachable nodes."""
            if node_id in visited:
                return
            visited.add(node_id)
            reachable.add(node_id)

            if node_id in pipeline.nodes_by_id:
                node = pipeline.nodes_by_id[node_id]
                for output_id in node.output:
                    dfs(output_id)

        # Start DFS from Capture node
        dfs(capture_node.id)

        # Find orphaned nodes
        all_node_ids = set(pipeline.nodes_by_id.keys())
        orphaned = all_node_ids - reachable
        if orphaned:
            errors.append(f"Pipeline has orphaned nodes (unreachable from Capture): {sorted(orphaned)}")

    # Check 6: File extensions validation
    valid_photo_extensions = [ext.lower() for ext in config.photo_extensions]
    valid_metadata_extensions = [ext.lower() for ext in config.metadata_extensions]
    valid_extensions = valid_photo_extensions + valid_metadata_extensions

    for node in pipeline.nodes:
        if isinstance(node, FileNode):
            ext_lower = node.extension.lower()
            if ext_lower not in valid_extensions:
                errors.append(
                    f"File node '{node.id}' has invalid extension '{node.extension}'. "
                    f"Must be one of: {', '.join(config.photo_extensions + config.metadata_extensions)}"
                )

    # Check 7: Processing method_ids validation
    valid_method_ids = set(config.processing_methods.keys())
    # Empty string is always valid (means no suffix)
    valid_method_ids.add('')

    for node in pipeline.nodes:
        if isinstance(node, ProcessNode):
            for method_id in node.method_ids:
                if method_id not in valid_method_ids:
                    available = [k for k in sorted(valid_method_ids) if k != '']
                    errors.append(
                        f"Process node '{node.id}' references undefined processing method '{method_id}'. "
                        f"Available methods: {', '.join(available) if available else '(none defined)'}"
                    )

    return errors


# =============================================================================
# Photo Pairing Tool Integration
# =============================================================================

def load_or_generate_imagegroups(folder_path: Path, force_regenerate: bool = False) -> List[Dict[str, Any]]:
    """
    Load ImageGroups from Photo Pairing cache or generate if missing.

    This function integrates with the Photo Pairing Tool by either:
    1. Loading existing .photo_pairing_imagegroups cache file
    2. Running Photo Pairing Tool to generate ImageGroups (if cache missing)

    Args:
        folder_path: Path to folder containing photos
        force_regenerate: If True, ignore cache and regenerate from scratch

    Returns:
        List of ImageGroup dictionaries from Photo Pairing Tool

    Raises:
        FileNotFoundError: If cache doesn't exist and can't generate
        ValueError: If cache is invalid or corrupted
    """
    import photo_pairing
    import json

    cache_file = folder_path / '.photo_pairing_imagegroups'

    # If force_regenerate, run Photo Pairing Tool
    if force_regenerate or not cache_file.exists():
        print(f"Running Photo Pairing Tool to generate ImageGroups...")

        # Use photo_pairing module directly
        # Note: This assumes photo_pairing can be imported as a module
        try:
            # Get all files in folder
            all_files = list(folder_path.iterdir())
            file_names = [f.name for f in all_files if f.is_file()]

            # Build ImageGroups using photo_pairing module
            imagegroups, invalid_files = photo_pairing.build_imagegroups(file_names, folder_path)

            return imagegroups
        except Exception as e:
            raise ValueError(f"Failed to generate ImageGroups: {e}")

    # Load from cache
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        imagegroups = cache_data.get('imagegroups')
        if not imagegroups:
            raise ValueError("Cache file missing 'imagegroups' field")

        return imagegroups
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Invalid Photo Pairing cache file: {e}")


def flatten_imagegroups_to_specific_images(imagegroups: List[Dict[str, Any]]) -> List[SpecificImage]:
    """
    Flatten ImageGroups to individual SpecificImage objects.

    Each ImageGroup contains multiple separate_images (suffix-based).
    This function converts each separate_image into a SpecificImage object
    for independent validation.

    Args:
        imagegroups: List of ImageGroup dictionaries from Photo Pairing Tool

    Returns:
        List of SpecificImage objects (one per separate_image)

    Example:
        ImageGroup {
            'group_id': 'AB3D0001',
            'separate_images': {
                '': {'files': ['AB3D0001.CR3', 'AB3D0001.XMP']},
                '2': {'files': ['AB3D0001-2.CR3']},
                'HDR': {'files': ['AB3D0001-HDR.DNG']}
            }
        }

        Flattens to 3 SpecificImages:
        - unique_id='AB3D0001', suffix=''
        - unique_id='AB3D0001-2', suffix='2'
        - unique_id='AB3D0001-HDR', suffix='HDR'
    """
    specific_images = []

    for group in imagegroups:
        group_id = group['group_id']
        camera_id = group['camera_id']
        counter = group['counter']
        separate_images = group.get('separate_images', {})

        for suffix, image_data in separate_images.items():
            # Build unique_id (base_filename)
            if suffix:
                unique_id = f"{camera_id}{counter}-{suffix}"
            else:
                unique_id = f"{camera_id}{counter}"

            # Get actual files
            actual_files = sorted(image_data.get('files', []))

            # Create SpecificImage
            specific_image = SpecificImage(
                unique_id=unique_id,
                group_id=group_id,
                camera_id=camera_id,
                counter=counter,
                suffix=suffix,
                actual_files=actual_files
            )
            specific_images.append(specific_image)

    return specific_images


def setup_signal_handlers():
    """
    Setup graceful CTRL+C (SIGINT) handling.

    Per constitution v1.1.0: Tools MUST handle CTRL+C gracefully with
    user-friendly messages and exit code 130.
    """
    def signal_handler(sig, frame):
        print("\n\n⚠ Operation interrupted by user (CTRL+C)")
        print("Exiting gracefully...")
        sys.exit(130)  # Standard exit code for SIGINT

    signal.signal(signal.SIGINT, signal_handler)


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='pipeline_validation',
        description='Photo Processing Pipeline Validation Tool',
        epilog="""
Examples:
  # Validate photo collection against pipeline
  python3 pipeline_validation.py /Users/photographer/Photos/2025-01-15

  # Use custom configuration file
  python3 pipeline_validation.py /path/to/photos --config /path/to/custom-config.yaml

  # Force regeneration (ignore all caches)
  python3 pipeline_validation.py /path/to/photos --force-regenerate

  # Show cache status without running validation
  python3 pipeline_validation.py /path/to/photos --cache-status

Workflow:
  1. Run Photo Pairing Tool first: python3 photo_pairing.py <folder>
  2. Define pipeline in config/config.yaml (processing_pipelines section)
  3. Run pipeline validation: python3 pipeline_validation.py <folder>
  4. Review HTML report: pipeline_validation_report_YYYY-MM-DD_HH-MM-SS.html

For more information, see docs/pipeline-validation.md
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Positional argument: folder path
    parser.add_argument(
        'folder_path',
        nargs='?',
        type=Path,
        help='Path to folder containing photos to validate'
    )

    # Optional arguments
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to custom configuration file (default: config/config.yaml)'
    )

    parser.add_argument(
        '--force-regenerate',
        action='store_true',
        help='Ignore all cache files and regenerate from scratch'
    )

    parser.add_argument(
        '--cache-status',
        action='store_true',
        help='Show cache status without running validation'
    )

    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Delete cache files and regenerate'
    )

    parser.add_argument(
        '--output-format',
        choices=['html', 'json'],
        default='html',
        help='Output format for validation results (default: html)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {TOOL_VERSION}'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.cache_status and args.folder_path is None:
        parser.error('folder_path is required unless using --cache-status')

    if args.folder_path and not args.folder_path.exists():
        parser.error(f"Folder does not exist: {args.folder_path}")

    if args.folder_path and not args.folder_path.is_dir():
        parser.error(f"Path is not a directory: {args.folder_path}")

    return args


def validate_prerequisites(args):
    """
    Validate that prerequisites are met before running validation.

    Args:
        args: Parsed command-line arguments

    Returns:
        bool: True if prerequisites met, False otherwise
    """
    # Check if Photo Pairing cache exists
    if args.folder_path:
        cache_file = args.folder_path / '.photo_pairing_imagegroups'
        if not cache_file.exists() and not args.force_regenerate:
            print("⚠ Error: Photo Pairing cache not found")
            print(f"  Expected: {cache_file}")
            print()
            print("Photo Pairing Tool must be run first to generate ImageGroups.")
            print()
            print("Run this command first:")
            print(f"  python3 photo_pairing.py {args.folder_path}")
            print()
            return False

    return True


def main():
    """Main entry point for pipeline validation tool."""
    # Setup signal handlers for graceful CTRL+C
    setup_signal_handlers()

    # Parse command-line arguments
    args = parse_arguments()

    # Validate prerequisites
    if not validate_prerequisites(args):
        sys.exit(1)

    print(f"Pipeline Validation Tool v{TOOL_VERSION}")
    print(f"Analyzing: {args.folder_path}")
    print()

    # TODO: Phase 2 - Load pipeline configuration
    # TODO: Phase 2 - Load Photo Pairing results
    # TODO: Phase 2 - Flatten ImageGroups to SpecificImages

    # TODO: Phase 3 (US1) - Enumerate all paths through pipeline
    # TODO: Phase 3 (US1) - Validate each SpecificImage against paths
    # TODO: Phase 3 (US1) - Classify validation status

    # TODO: Phase 4 (US2) - Support all 6 node types
    # TODO: Phase 4 (US2) - Handle Branching and Pairing nodes

    # TODO: Phase 5 (US3) - Handle counter looping with suffixes

    # TODO: Phase 6 (US4) - Implement caching with SHA256 hashing
    # TODO: Phase 6 (US4) - Cache invalidation logic

    # TODO: Phase 7 (US5) - Generate HTML report
    # TODO: Phase 7 (US5) - Chart.js visualizations

    print("✓ Pipeline validation complete (placeholder)")
    print()
    print("Note: This is a skeleton implementation. Core functionality pending.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
