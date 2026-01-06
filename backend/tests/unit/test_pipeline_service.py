"""
Unit tests for PipelineService.

Tests CRUD operations, validation, activation, preview, and version history.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from backend.src.models import Pipeline, PipelineHistory
from backend.src.services.exceptions import NotFoundError, ConflictError, ValidationError as ServiceValidationError


@pytest.fixture
def sample_nodes():
    """Sample pipeline nodes for testing."""
    return [
        {"id": "capture", "type": "capture", "properties": {"camera_id_pattern": "[A-Z0-9]{4}"}},
        {"id": "raw", "type": "file", "properties": {"extension": ".dng"}},
        {"id": "xmp", "type": "file", "properties": {"extension": ".xmp"}},
        {"id": "done", "type": "termination", "properties": {"termination_type": "Black Box Archive"}}
    ]


@pytest.fixture
def sample_edges():
    """Sample pipeline edges for testing."""
    return [
        {"from": "capture", "to": "raw"},
        {"from": "capture", "to": "xmp"},
        {"from": "raw", "to": "done"}
    ]


@pytest.fixture
def pipeline_service(test_db_session):
    """Create a PipelineService instance for testing."""
    from backend.src.services.pipeline_service import PipelineService
    return PipelineService(test_db_session)


@pytest.fixture
def sample_pipeline(test_db_session, sample_nodes, sample_edges):
    """Factory for creating sample Pipeline models."""
    def _create(
        name="Test Pipeline",
        description="Test description",
        nodes=None,
        edges=None,
        is_active=False,
        is_valid=True,
        version=1
    ):
        pipeline = Pipeline(
            name=name,
            description=description,
            nodes_json=nodes or sample_nodes,
            edges_json=edges or sample_edges,
            is_active=is_active,
            is_valid=is_valid,
            version=version
        )
        test_db_session.add(pipeline)
        test_db_session.commit()
        test_db_session.refresh(pipeline)
        return pipeline
    return _create


class TestPipelineServiceCRUD:
    """Tests for CRUD operations."""

    def test_create_pipeline(self, pipeline_service, sample_nodes, sample_edges):
        """Test creating a new pipeline."""
        result = pipeline_service.create(
            name="New Pipeline",
            description="New description",
            nodes=sample_nodes,
            edges=sample_edges
        )

        assert result.id is not None
        assert result.name == "New Pipeline"
        assert result.description == "New description"
        assert result.version == 1
        assert result.is_active is False
        assert len(result.nodes) == 4

    def test_create_pipeline_duplicate_name(self, pipeline_service, sample_pipeline, sample_nodes, sample_edges):
        """Test error when creating pipeline with duplicate name."""
        sample_pipeline(name="Existing")

        with pytest.raises(ConflictError) as exc_info:
            pipeline_service.create(
                name="Existing",
                nodes=sample_nodes,
                edges=sample_edges
            )
        assert "already exists" in str(exc_info.value).lower()

    def test_get_pipeline(self, pipeline_service, sample_pipeline):
        """Test getting a pipeline by ID."""
        pipeline = sample_pipeline(name="Get Test")

        result = pipeline_service.get(pipeline.id)

        assert result.id == pipeline.id
        assert result.name == "Get Test"

    def test_get_pipeline_not_found(self, pipeline_service):
        """Test error when getting non-existent pipeline."""
        with pytest.raises(NotFoundError):
            pipeline_service.get(99999)

    def test_list_pipelines(self, pipeline_service, sample_pipeline):
        """Test listing all pipelines."""
        sample_pipeline(name="List Test 1")
        sample_pipeline(name="List Test 2")

        results = pipeline_service.list()

        assert len(results) >= 2
        names = [r.name for r in results]
        assert "List Test 1" in names
        assert "List Test 2" in names

    def test_list_pipelines_filter_active(self, pipeline_service, sample_pipeline):
        """Test filtering pipelines by active status."""
        sample_pipeline(name="Active", is_active=True)
        sample_pipeline(name="Inactive", is_active=False)

        results = pipeline_service.list(is_active=True)

        assert all(r.is_active for r in results)

    def test_list_pipelines_filter_valid(self, pipeline_service, sample_pipeline):
        """Test filtering pipelines by validation status."""
        sample_pipeline(name="Valid", is_valid=True)
        sample_pipeline(name="Invalid", is_valid=False)

        results = pipeline_service.list(is_valid=True)

        assert all(r.is_valid for r in results)

    def test_update_pipeline(self, pipeline_service, sample_pipeline):
        """Test updating a pipeline."""
        pipeline = sample_pipeline(name="Update Test")

        result = pipeline_service.update(
            pipeline_id=pipeline.id,
            description="Updated description",
            change_summary="Changed description"
        )

        assert result.description == "Updated description"
        assert result.version == 2

    def test_update_pipeline_nodes(self, pipeline_service, sample_pipeline, sample_nodes):
        """Test updating pipeline nodes."""
        pipeline = sample_pipeline(name="Node Update Test")
        new_nodes = sample_nodes + [
            {"id": "hdr", "type": "process", "properties": {"suffix": "-HDR"}}
        ]

        result = pipeline_service.update(
            pipeline_id=pipeline.id,
            nodes=new_nodes,
            change_summary="Added HDR node"
        )

        assert len(result.nodes) == 5

    def test_update_pipeline_not_found(self, pipeline_service):
        """Test error when updating non-existent pipeline."""
        with pytest.raises(NotFoundError):
            pipeline_service.update(
                pipeline_id=99999,
                description="New description"
            )

    def test_delete_pipeline(self, pipeline_service, sample_pipeline, test_db_session):
        """Test deleting a pipeline."""
        pipeline = sample_pipeline(name="Delete Test")
        pipeline_id = pipeline.id

        result = pipeline_service.delete(pipeline_id)

        assert result == pipeline_id

        # Verify deleted
        deleted = test_db_session.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
        assert deleted is None

    def test_delete_pipeline_not_found(self, pipeline_service):
        """Test error when deleting non-existent pipeline."""
        with pytest.raises(NotFoundError):
            pipeline_service.delete(99999)

    def test_delete_active_pipeline(self, pipeline_service, sample_pipeline):
        """Test error when deleting active pipeline."""
        pipeline = sample_pipeline(name="Active Delete Test", is_active=True)

        with pytest.raises(ConflictError) as exc_info:
            pipeline_service.delete(pipeline.id)
        assert "active" in str(exc_info.value).lower()


class TestPipelineServiceValidation:
    """Tests for pipeline validation."""

    def test_validate_valid_pipeline(self, pipeline_service, sample_pipeline):
        """Test validating a valid pipeline."""
        pipeline = sample_pipeline(name="Valid Test")

        result = pipeline_service.validate(pipeline.id)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_pipeline_with_cycle_allowed(self, pipeline_service, sample_pipeline):
        """Test that cycles are allowed in pipelines."""
        # Cycles are valid - the CLI pipeline_validation tool handles
        # loop execution limits to prevent infinite loops at runtime
        cyclic_edges = [
            {"from": "capture", "to": "file"},
            {"from": "file", "to": "process"},
            {"from": "process", "to": "file"},  # Cycle back to file!
            {"from": "process", "to": "done"},
        ]
        cyclic_nodes = [
            {"id": "capture", "type": "capture", "properties": {}},
            {"id": "file", "type": "file", "properties": {"extension": ".dng"}},
            {"id": "process", "type": "process", "properties": {"suffix": "-HDR"}},
            {"id": "done", "type": "termination", "properties": {"termination_type": "Black Box Archive"}},
        ]
        pipeline = sample_pipeline(
            name="Cyclic Test",
            nodes=cyclic_nodes,
            edges=cyclic_edges,
            is_valid=False  # Will be recalculated
        )

        result = pipeline_service.validate(pipeline.id)

        # Cycles are allowed - pipeline should be valid
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_pipeline_orphaned_node(self, pipeline_service, sample_pipeline):
        """Test validation detects orphaned nodes."""
        nodes_with_orphan = [
            {"id": "capture", "type": "capture", "properties": {}},
            {"id": "raw", "type": "file", "properties": {"extension": ".dng"}},
            {"id": "orphan", "type": "file", "properties": {"extension": ".xmp"}},  # Not connected
            {"id": "done", "type": "termination", "properties": {"termination_type": "Black Box Archive"}},
        ]
        edges = [
            {"from": "capture", "to": "raw"},
            {"from": "raw", "to": "done"},
        ]
        pipeline = sample_pipeline(
            name="Orphan Test",
            nodes=nodes_with_orphan,
            edges=edges,
            is_valid=True
        )

        result = pipeline_service.validate(pipeline.id)

        # Should detect orphaned node
        assert result.is_valid is False
        assert any("orphan" in str(e.message).lower() for e in result.errors)

    def test_validate_pipeline_not_found(self, pipeline_service):
        """Test error when validating non-existent pipeline."""
        with pytest.raises(NotFoundError):
            pipeline_service.validate(99999)


class TestPipelineServiceActivation:
    """Tests for pipeline activation."""

    def test_activate_pipeline(self, pipeline_service, sample_pipeline):
        """Test activating a valid pipeline."""
        pipeline = sample_pipeline(name="Activate Test", is_valid=True)

        result = pipeline_service.activate(pipeline.id)

        assert result.is_active is True

    def test_activate_deactivates_other(self, pipeline_service, sample_pipeline, test_db_session):
        """Test activating a pipeline deactivates the currently active one."""
        pipeline1 = sample_pipeline(name="First", is_active=True, is_valid=True)
        pipeline2 = sample_pipeline(name="Second", is_active=False, is_valid=True)

        result = pipeline_service.activate(pipeline2.id)

        assert result.is_active is True

        # Refresh pipeline1 to see updated state
        test_db_session.refresh(pipeline1)
        assert pipeline1.is_active is False

    def test_activate_invalid_pipeline(self, pipeline_service, sample_pipeline):
        """Test error when activating invalid pipeline."""
        pipeline = sample_pipeline(name="Invalid Activate Test", is_valid=False)

        with pytest.raises(ServiceValidationError) as exc_info:
            pipeline_service.activate(pipeline.id)
        assert "valid" in str(exc_info.value).lower()

    def test_activate_pipeline_not_found(self, pipeline_service):
        """Test error when activating non-existent pipeline."""
        with pytest.raises(NotFoundError):
            pipeline_service.activate(99999)

    def test_deactivate_pipeline(self, pipeline_service, sample_pipeline):
        """Test deactivating a pipeline."""
        pipeline = sample_pipeline(name="Deactivate Test", is_active=True)

        result = pipeline_service.deactivate(pipeline.id)

        assert result.is_active is False

    def test_deactivate_pipeline_not_found(self, pipeline_service):
        """Test error when deactivating non-existent pipeline."""
        with pytest.raises(NotFoundError):
            pipeline_service.deactivate(99999)


class TestPipelineServicePreview:
    """Tests for filename preview."""

    def test_preview_filenames(self, pipeline_service, sample_pipeline):
        """Test generating filename preview."""
        pipeline = sample_pipeline(name="Preview Test", is_valid=True)

        result = pipeline_service.preview_filenames(
            pipeline_id=pipeline.id,
            camera_id="AB3D",
            counter="0001"
        )

        assert result.base_filename == "AB3D0001"
        assert len(result.expected_files) > 0

    def test_preview_default_values(self, pipeline_service, sample_pipeline):
        """Test preview with default camera_id and counter."""
        pipeline = sample_pipeline(name="Default Preview Test", is_valid=True)

        result = pipeline_service.preview_filenames(pipeline_id=pipeline.id)

        assert result.base_filename is not None

    def test_preview_invalid_pipeline(self, pipeline_service, sample_pipeline):
        """Test error when previewing invalid pipeline."""
        pipeline = sample_pipeline(name="Invalid Preview Test", is_valid=False)

        with pytest.raises(ServiceValidationError):
            pipeline_service.preview_filenames(pipeline_id=pipeline.id)

    def test_preview_pipeline_not_found(self, pipeline_service):
        """Test error when previewing non-existent pipeline."""
        with pytest.raises(NotFoundError):
            pipeline_service.preview_filenames(pipeline_id=99999)


class TestPipelineServiceHistory:
    """Tests for version history."""

    def test_get_history_empty(self, pipeline_service, sample_pipeline):
        """Test getting history for pipeline with no history."""
        pipeline = sample_pipeline(name="No History Test")

        result = pipeline_service.get_history(pipeline.id)

        assert isinstance(result, list)

    def test_get_history_with_entries(self, pipeline_service, sample_pipeline, test_db_session, sample_nodes, sample_edges):
        """Test getting history with entries."""
        pipeline = sample_pipeline(name="History Test")

        # Add history entry
        history = PipelineHistory(
            pipeline_id=pipeline.id,
            version=1,
            nodes_json=sample_nodes,
            edges_json=sample_edges,
            change_summary="Initial version"
        )
        test_db_session.add(history)
        test_db_session.commit()

        result = pipeline_service.get_history(pipeline.id)

        assert len(result) >= 1
        assert result[0].version == 1
        assert result[0].change_summary == "Initial version"

    def test_get_history_pipeline_not_found(self, pipeline_service):
        """Test error when getting history for non-existent pipeline."""
        with pytest.raises(NotFoundError):
            pipeline_service.get_history(99999)

    def test_version_history_created_on_update(self, pipeline_service, sample_pipeline):
        """Test that history is created when updating pipeline."""
        pipeline = sample_pipeline(name="History Create Test")

        pipeline_service.update(
            pipeline_id=pipeline.id,
            description="Updated",
            change_summary="Updated description"
        )

        history = pipeline_service.get_history(pipeline.id)
        assert len(history) >= 1


class TestPipelineServiceImportExport:
    """Tests for YAML import/export."""

    def test_import_from_yaml(self, pipeline_service):
        """Test importing pipeline from YAML string."""
        yaml_content = """
name: Imported Pipeline
description: Imported from YAML
nodes:
  - id: capture
    type: capture
    properties:
      camera_id_pattern: "[A-Z0-9]{4}"
  - id: raw
    type: file
    properties:
      extension: ".dng"
edges:
  - from: capture
    to: raw
"""
        result = pipeline_service.import_from_yaml(yaml_content)

        assert result.name == "Imported Pipeline"
        assert result.description == "Imported from YAML"
        assert len(result.nodes) == 2

    def test_import_from_yaml_invalid(self, pipeline_service):
        """Test error when importing invalid YAML."""
        yaml_content = "invalid: yaml: content: {"

        with pytest.raises(ServiceValidationError):
            pipeline_service.import_from_yaml(yaml_content)

    def test_export_to_yaml(self, pipeline_service, sample_pipeline):
        """Test exporting pipeline to YAML string."""
        pipeline = sample_pipeline(name="Export Test")

        result = pipeline_service.export_to_yaml(pipeline.id)

        assert "name: Export Test" in result
        assert "nodes:" in result
        assert "edges:" in result

    def test_export_pipeline_not_found(self, pipeline_service):
        """Test error when exporting non-existent pipeline."""
        with pytest.raises(NotFoundError):
            pipeline_service.export_to_yaml(99999)


class TestPipelineServiceStats:
    """Tests for statistics."""

    def test_get_stats_empty(self, pipeline_service):
        """Test stats with no pipelines."""
        result = pipeline_service.get_stats()

        assert result.total_pipelines == 0
        assert result.valid_pipelines == 0
        assert result.active_pipeline_id is None
        assert result.active_pipeline_name is None

    def test_get_stats_with_data(self, pipeline_service, sample_pipeline):
        """Test stats with pipelines."""
        sample_pipeline(name="Valid Active", is_valid=True, is_active=True)
        sample_pipeline(name="Valid Inactive", is_valid=True, is_active=False)
        sample_pipeline(name="Invalid", is_valid=False, is_active=False)

        result = pipeline_service.get_stats()

        assert result.total_pipelines >= 3
        assert result.valid_pipelines >= 2
        assert result.active_pipeline_id is not None
        assert result.active_pipeline_name == "Valid Active"
