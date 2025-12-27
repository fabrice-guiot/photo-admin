"""
Tests for Pipeline Validation Tool

This module tests the pipeline validation functionality including:
- Pipeline configuration loading and validation
- Path enumeration through directed graph
- File validation against pipeline paths
- Status classification (CONSISTENT, PARTIAL, etc.)
- Cache operations and invalidation
- HTML report generation
"""

import pytest
import json
import yaml
import tempfile
import subprocess
import sys
import signal
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open
import pipeline_validation


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_pipeline_config():
    """Sample pipeline configuration for testing."""
    return {
        'nodes': [
            {
                'id': 'capture',
                'type': 'Capture',
                'name': 'Camera Capture',
                'output': ['raw_image_1', 'xmp_metadata_1']
            },
            {
                'id': 'raw_image_1',
                'type': 'File',
                'extension': '.CR3',
                'name': 'Canon Raw File',
                'output': ['selection_process']
            },
            {
                'id': 'xmp_metadata_1',
                'type': 'File',
                'extension': '.XMP',
                'name': 'XMP Metadata',
                'output': []
            },
            {
                'id': 'selection_process',
                'type': 'Process',
                'method_ids': [''],
                'name': 'Image Selection',
                'output': ['dng_conversion']
            },
            {
                'id': 'dng_conversion',
                'type': 'Process',
                'method_ids': ['DxO_DeepPRIME_XD2s'],
                'name': 'DNG Conversion',
                'output': ['openformat_raw_image']
            },
            {
                'id': 'openformat_raw_image',
                'type': 'File',
                'extension': '.DNG',
                'name': 'DNG File',
                'output': ['termination_blackbox']
            },
            {
                'id': 'termination_blackbox',
                'type': 'Termination',
                'termination_type': 'Black Box Archive',
                'name': 'Black Box Archive Ready',
                'output': []
            }
        ]
    }


@pytest.fixture
def sample_pipeline_with_loop():
    """Sample pipeline with a loop (Branching node that loops back)."""
    return {
        'nodes': [
            {
                'id': 'capture',
                'type': 'Capture',
                'name': 'Camera Capture',
                'output': ['raw_image']
            },
            {
                'id': 'raw_image',
                'type': 'File',
                'extension': '.CR3',
                'name': 'Canon Raw File',
                'output': ['edit_process']
            },
            {
                'id': 'edit_process',
                'type': 'Process',
                'method_ids': ['Edit'],
                'name': 'Photoshop Editing',
                'output': ['branching_decision']
            },
            {
                'id': 'branching_decision',
                'type': 'Branching',
                'condition_description': 'User decides: Create TIFF or continue editing',
                'name': 'TIFF Generation Decision',
                'output': ['generate_tiff', 'edit_process']  # Second output loops back
            },
            {
                'id': 'generate_tiff',
                'type': 'Process',
                'method_ids': [''],
                'name': 'Generate TIFF',
                'output': ['tiff_file']
            },
            {
                'id': 'tiff_file',
                'type': 'File',
                'extension': '.TIF',
                'name': 'TIFF File',
                'output': ['termination']
            },
            {
                'id': 'termination',
                'type': 'Termination',
                'termination_type': 'Black Box Archive',
                'name': 'Archive Ready',
                'output': []
            }
        ]
    }


@pytest.fixture
def sample_imagegroups():
    """Sample ImageGroups from Photo Pairing Tool for testing."""
    return [
        {
            'group_id': 'AB3D0001',
            'camera_id': 'AB3D',
            'counter': '0001',
            'separate_images': {
                '': {  # Base image
                    'files': [
                        'AB3D0001.CR3',
                        'AB3D0001.XMP',
                        'AB3D0001-DxO_DeepPRIME_XD2s.DNG'
                    ],
                    'properties': []
                }
            }
        },
        {
            'group_id': 'AB3D0002',
            'camera_id': 'AB3D',
            'counter': '0002',
            'separate_images': {
                '': {
                    'files': [
                        'AB3D0002.CR3',
                        'AB3D0002.XMP'
                        # Missing DNG file - PARTIAL status expected
                    ],
                    'properties': []
                }
            }
        },
        {
            'group_id': 'AB3D0003',
            'camera_id': 'AB3D',
            'counter': '0003',
            'separate_images': {
                '': {
                    'files': [
                        'AB3D0003.CR3',
                        'AB3D0003.XMP',
                        'AB3D0003-DxO_DeepPRIME_XD2s.DNG',
                        'AB3D0003-backup.CR3'  # Extra file - CONSISTENT-WITH-WARNING expected
                    ],
                    'properties': []
                }
            }
        }
    ]


@pytest.fixture
def temp_photo_folder(tmp_path):
    """Create a temporary folder with test photo files and Photo Pairing cache."""
    photo_dir = tmp_path / "test_photos"
    photo_dir.mkdir()

    # Create sample files
    files = [
        'AB3D0001.CR3',
        'AB3D0001.XMP',
        'AB3D0001-DxO_DeepPRIME_XD2s.DNG',
        'AB3D0002.CR3',
        'AB3D0002.XMP'
    ]

    for filename in files:
        (photo_dir / filename).write_text(f"Mock content for {filename}")

    # Create Photo Pairing cache
    cache_data = {
        'version': '1.0',
        'tool_version': '1.0.0',
        'created_at': datetime.now().isoformat(),
        'folder_path': str(photo_dir),
        'imagegroups': [
            {
                'group_id': 'AB3D0001',
                'camera_id': 'AB3D',
                'counter': '0001',
                'separate_images': {
                    '': {
                        'files': [
                            'AB3D0001.CR3',
                            'AB3D0001.XMP',
                            'AB3D0001-DxO_DeepPRIME_XD2s.DNG'
                        ],
                        'properties': []
                    }
                }
            },
            {
                'group_id': 'AB3D0002',
                'camera_id': 'AB3D',
                'counter': '0002',
                'separate_images': {
                    '': {
                        'files': [
                            'AB3D0002.CR3',
                            'AB3D0002.XMP'
                        ],
                        'properties': []
                    }
                }
            }
        ]
    }

    cache_file = photo_dir / '.photo_pairing_imagegroups'
    cache_file.write_text(json.dumps(cache_data, indent=2))

    return photo_dir


@pytest.fixture
def mock_config():
    """Mock PhotoAdminConfig for testing."""
    config = MagicMock()
    config.photo_extensions = ['.cr3', '.dng', '.tiff']
    config.metadata_extensions = ['.xmp']
    config.camera_mappings = {
        'AB3D': [{'name': 'Canon EOS R5', 'serial_number': '12345'}]
    }
    config.processing_methods = {
        'DxO_DeepPRIME_XD2s': 'DNG Conversion with DeepPRIME',
        'Edit': 'Photoshop Editing'
    }
    return config


# =============================================================================
# Phase 1: Setup Tests (Skeleton/Smoke Tests)
# =============================================================================

class TestCLIInterface:
    """Tests for command-line interface (Phase 1)."""

    def test_help_flag(self):
        """Test --help flag displays usage information."""
        result = subprocess.run(
            [sys.executable, 'pipeline_validation.py', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Pipeline Validation Tool' in result.stdout
        assert 'folder_path' in result.stdout

    def test_version_flag(self):
        """Test --version flag displays version."""
        result = subprocess.run(
            [sys.executable, 'pipeline_validation.py', '--version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert '1.0.0' in result.stdout

    def test_missing_folder_path(self):
        """Test error when folder_path is not provided."""
        result = subprocess.run(
            [sys.executable, 'pipeline_validation.py'],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert 'required' in result.stderr.lower() or 'required' in result.stdout.lower()


class TestSignalHandling:
    """Tests for graceful CTRL+C handling (Phase 1)."""

    def test_sigint_handler_setup(self):
        """Test that SIGINT handler is properly configured."""
        with patch('signal.signal') as mock_signal:
            pipeline_validation.setup_signal_handlers()
            mock_signal.assert_called_once_with(signal.SIGINT, pipeline_validation.setup_signal_handlers.__code__.co_consts[1])

    def test_sigint_exit_code(self):
        """Test that SIGINT handler exits with code 130."""
        # This test would require subprocess and sending SIGINT
        # Placeholder for actual implementation
        pass


class TestPrerequisiteValidation:
    """Tests for prerequisite checking (Phase 1)."""

    def test_missing_photo_pairing_cache(self, tmp_path):
        """Test error when Photo Pairing cache is missing."""
        # Create folder without cache
        folder = tmp_path / "no_cache"
        folder.mkdir()

        args = MagicMock()
        args.folder_path = folder
        args.force_regenerate = False

        result = pipeline_validation.validate_prerequisites(args)
        assert result is False

    def test_existing_photo_pairing_cache(self, temp_photo_folder):
        """Test success when Photo Pairing cache exists."""
        args = MagicMock()
        args.folder_path = temp_photo_folder
        args.force_regenerate = False

        result = pipeline_validation.validate_prerequisites(args)
        assert result is True

    def test_force_regenerate_skips_cache_check(self, tmp_path):
        """Test that --force-regenerate skips cache existence check."""
        folder = tmp_path / "no_cache"
        folder.mkdir()

        args = MagicMock()
        args.folder_path = folder
        args.force_regenerate = True

        # Should not fail even without cache when force_regenerate=True
        # This behavior may change based on implementation
        pass


# =============================================================================
# Phase 2: Foundational Tests (To be implemented)
# =============================================================================

class TestPipelineConfigLoading:
    """Tests for pipeline configuration loading (Phase 2)."""

    def test_load_pipeline_from_config(self, tmp_path, sample_pipeline_config):
        """Test loading pipeline configuration from config.yaml."""
        # Create test config file
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            'photo_extensions': ['.cr3', '.dng'],
            'metadata_extensions': ['.xmp'],
            'processing_methods': {
                'DxO_DeepPRIME_XD2s': 'DNG Conversion'
            },
            'processing_pipelines': sample_pipeline_config
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Load pipeline
        pipeline = pipeline_validation.load_pipeline_config(config_file)

        # Verify pipeline loaded correctly
        assert len(pipeline.nodes) == 7
        assert len(pipeline.nodes_by_id) == 7

        # Verify node types
        assert isinstance(pipeline.nodes_by_id['capture'], pipeline_validation.CaptureNode)
        assert isinstance(pipeline.nodes_by_id['raw_image_1'], pipeline_validation.FileNode)
        assert isinstance(pipeline.nodes_by_id['selection_process'], pipeline_validation.ProcessNode)
        assert isinstance(pipeline.nodes_by_id['termination_blackbox'], pipeline_validation.TerminationNode)

    def test_validate_pipeline_structure(self, tmp_path, sample_pipeline_config, mock_config):
        """Test validation of pipeline node structure."""
        # Create test config file
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            'processing_pipelines': sample_pipeline_config
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Load pipeline
        pipeline = pipeline_validation.load_pipeline_config(config_file)

        # Validate structure
        errors = pipeline_validation.validate_pipeline_structure(pipeline, mock_config)

        # Should have no errors
        assert len(errors) == 0

    def test_detect_invalid_node_references(self, tmp_path, mock_config):
        """Test detection of invalid output node references."""
        # Create pipeline with invalid reference
        invalid_pipeline_config = {
            'nodes': [
                {
                    'id': 'capture',
                    'type': 'Capture',
                    'name': 'Camera Capture',
                    'output': ['raw_image', 'non_existent_node']  # Invalid reference
                },
                {
                    'id': 'raw_image',
                    'type': 'File',
                    'extension': '.CR3',
                    'name': 'Raw File',
                    'output': []
                }
            ]
        }

        config_file = tmp_path / "invalid_config.yaml"
        config_data = {
            'processing_pipelines': invalid_pipeline_config
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Load pipeline
        pipeline = pipeline_validation.load_pipeline_config(config_file)

        # Validate structure - should detect invalid reference
        errors = pipeline_validation.validate_pipeline_structure(pipeline, mock_config)

        assert len(errors) > 0
        assert any('non_existent_node' in err for err in errors)


class TestPhotoPairingIntegration:
    """Tests for Photo Pairing integration (Phase 2)."""

    def test_load_photo_pairing_cache(self, temp_photo_folder):
        """Test loading Photo Pairing cache file."""
        # Load ImageGroups from cache
        imagegroups = pipeline_validation.load_or_generate_imagegroups(temp_photo_folder, force_regenerate=False)

        # Verify ImageGroups loaded
        assert len(imagegroups) == 2
        assert imagegroups[0]['group_id'] == 'AB3D0001'
        assert imagegroups[1]['group_id'] == 'AB3D0002'

    def test_flatten_imagegroups_to_specific_images(self, sample_imagegroups):
        """Test flattening ImageGroups to SpecificImages."""
        # Flatten ImageGroups
        specific_images = pipeline_validation.flatten_imagegroups_to_specific_images(sample_imagegroups)

        # Verify flattening - 3 groups with 1 separate image each = 3 SpecificImages
        assert len(specific_images) == 3  # AB3D0001, AB3D0002, AB3D0003

        # Check first image (AB3D0001 base image)
        img1 = [img for img in specific_images if img.unique_id == 'AB3D0001'][0]
        assert img1.group_id == 'AB3D0001'
        assert img1.camera_id == 'AB3D'
        assert img1.counter == '0001'
        assert img1.suffix == ''
        assert 'AB3D0001.CR3' in img1.actual_files
        assert 'AB3D0001.XMP' in img1.actual_files

        # Check second image (AB3D0002)
        img2 = [img for img in specific_images if img.unique_id == 'AB3D0002'][0]
        assert img2.group_id == 'AB3D0002'
        assert img2.suffix == ''
        assert 'AB3D0002.CR3' in img2.actual_files

        # Check third image (AB3D0003)
        img3 = [img for img in specific_images if img.unique_id == 'AB3D0003'][0]
        assert img3.group_id == 'AB3D0003'
        assert img3.suffix == ''
        assert 'AB3D0003-backup.CR3' in img3.actual_files  # Extra file


# =============================================================================
# Phase 3: Core Validation Tests (To be implemented)
# =============================================================================

class TestPathEnumeration:
    """Tests for pipeline path enumeration (Phase 3 - TODO)."""

    def test_enumerate_simple_path(self):
        """Test enumeration of simple linear pipeline path."""
        # TODO: Implement in Phase 3
        pass

    def test_enumerate_branching_paths(self):
        """Test enumeration with Branching nodes."""
        # TODO: Implement in Phase 3
        pass

    def test_handle_loop_truncation(self):
        """Test loop truncation after MAX_ITERATIONS."""
        # TODO: Implement in Phase 3
        pass


class TestFileValidation:
    """Tests for file validation against paths (Phase 3 - TODO)."""

    def test_classify_consistent(self):
        """Test CONSISTENT status classification."""
        # TODO: Implement in Phase 3
        pass

    def test_classify_partial(self):
        """Test PARTIAL status classification."""
        # TODO: Implement in Phase 3
        pass

    def test_classify_consistent_with_warning(self):
        """Test CONSISTENT-WITH-WARNING status classification."""
        # TODO: Implement in Phase 3
        pass

    def test_classify_inconsistent(self):
        """Test INCONSISTENT status classification."""
        # TODO: Implement in Phase 3
        pass


# =============================================================================
# Phase 4+: Advanced Feature Tests (To be implemented)
# =============================================================================

class TestCaching:
    """Tests for cache operations (Phase 6 - TODO)."""

    def test_cache_invalidation_on_config_change(self):
        """Test cache invalidation when pipeline config changes."""
        # TODO: Implement in Phase 6
        pass

    def test_cache_invalidation_on_folder_change(self):
        """Test cache invalidation when folder contents change."""
        # TODO: Implement in Phase 6
        pass


class TestHTMLReportGeneration:
    """Tests for HTML report generation (Phase 7 - TODO)."""

    def test_generate_html_report(self):
        """Test HTML report generation."""
        # TODO: Implement in Phase 7
        pass

    def test_report_contains_validation_summary(self):
        """Test report contains validation statistics."""
        # TODO: Implement in Phase 7
        pass
