"""
Unit tests for External ID support in API endpoints.

Tests cover:
- GET endpoints accepting external IDs (US1: T025-T027)
- External ID in list/create responses (US2: T037-T038)
- Backward compatibility with numeric IDs (US4: T050-T051)

Phase 3 User Story 1: Access Entity via External ID
Phase 4 User Story 2: API External ID Support
Phase 6 User Story 4: Backward Compatibility
"""

import tempfile
import pytest
from fastapi.testclient import TestClient


class TestCollectionExternalIdAccess:
    """Tests for GET /api/collections/{identifier} with external IDs - T025"""

    def test_get_collection_by_external_id(self, test_client, sample_collection):
        """Should retrieve collection using external ID"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="Test Collection",
                type="local",
                location=temp_dir
            )

            # Get collection by external ID
            response = test_client.get(f"/api/collections/{collection.external_id}")

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["id"] == collection.id
            assert json_data["name"] == "Test Collection"
            assert json_data["external_id"] == collection.external_id

    def test_get_collection_by_numeric_id_still_works(self, test_client, sample_collection):
        """Should still retrieve collection using numeric ID (backward compat)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="Test Collection",
                type="local",
                location=temp_dir
            )

            # Get collection by numeric ID
            response = test_client.get(f"/api/collections/{collection.id}")

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["id"] == collection.id
            assert json_data["external_id"] == collection.external_id

    def test_get_collection_invalid_external_id_format(self, test_client):
        """Should return 400 for malformed external ID"""
        response = test_client.get("/api/collections/invalid_format")

        assert response.status_code == 400
        assert "Invalid identifier format" in response.json()["detail"]

    def test_get_collection_wrong_prefix(self, test_client, sample_collection):
        """Should return 400 for external ID with wrong prefix"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="Test Collection",
                type="local",
                location=temp_dir
            )

            # Replace col_ with con_ (connector prefix)
            wrong_prefix_id = collection.external_id.replace("col_", "con_")

            response = test_client.get(f"/api/collections/{wrong_prefix_id}")

            assert response.status_code == 400
            assert "prefix mismatch" in response.json()["detail"].lower()

    def test_get_collection_external_id_not_found(self, test_client):
        """Should return 404 for valid external ID format but non-existent entity"""
        # Valid format external ID that doesn't exist
        fake_external_id = "col_01hgw2bbg00000000000000000"

        response = test_client.get(f"/api/collections/{fake_external_id}")

        assert response.status_code == 404

    def test_get_collection_external_id_case_insensitive(self, test_client, sample_collection):
        """Should handle external ID case-insensitively"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="Test Collection",
                type="local",
                location=temp_dir
            )

            # Use uppercase external ID
            upper_id = collection.external_id.upper()

            response = test_client.get(f"/api/collections/{upper_id}")

            assert response.status_code == 200
            assert response.json()["id"] == collection.id


class TestConnectorExternalIdAccess:
    """Tests for GET /api/connectors/{identifier} with external IDs - T026"""

    def test_get_connector_by_external_id(self, test_client, sample_connector):
        """Should retrieve connector using external ID"""
        connector = sample_connector(name="S3 Test Connector", type="s3")

        response = test_client.get(f"/api/connectors/{connector.external_id}")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["id"] == connector.id
        assert json_data["name"] == "S3 Test Connector"
        assert json_data["external_id"] == connector.external_id

    def test_get_connector_by_numeric_id_still_works(self, test_client, sample_connector):
        """Should still retrieve connector using numeric ID"""
        connector = sample_connector(name="GCS Connector", type="gcs")

        response = test_client.get(f"/api/connectors/{connector.id}")

        assert response.status_code == 200
        assert response.json()["id"] == connector.id

    def test_get_connector_wrong_prefix(self, test_client, sample_connector):
        """Should return 400 for external ID with wrong prefix"""
        connector = sample_connector(name="Test Connector", type="s3")

        # Replace con_ with col_ (collection prefix)
        wrong_prefix_id = connector.external_id.replace("con_", "col_")

        response = test_client.get(f"/api/connectors/{wrong_prefix_id}")

        assert response.status_code == 400
        assert "prefix mismatch" in response.json()["detail"].lower()

    def test_get_connector_external_id_not_found(self, test_client):
        """Should return 404 for valid external ID format but non-existent"""
        fake_external_id = "con_01hgw2bbg00000000000000000"

        response = test_client.get(f"/api/connectors/{fake_external_id}")

        assert response.status_code == 404


class TestPipelineExternalIdAccess:
    """Tests for GET /api/pipelines/{identifier} with external IDs - T027"""

    def test_get_pipeline_by_external_id(self, test_client, sample_pipeline):
        """Should retrieve pipeline using external ID"""
        pipeline = sample_pipeline(name="RAW Workflow")

        response = test_client.get(f"/api/pipelines/{pipeline.external_id}")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["id"] == pipeline.id
        assert json_data["name"] == "RAW Workflow"
        assert json_data["external_id"] == pipeline.external_id

    def test_get_pipeline_by_numeric_id_still_works(self, test_client, sample_pipeline):
        """Should still retrieve pipeline using numeric ID"""
        pipeline = sample_pipeline(name="JPEG Workflow")

        response = test_client.get(f"/api/pipelines/{pipeline.id}")

        assert response.status_code == 200
        assert response.json()["id"] == pipeline.id

    def test_get_pipeline_wrong_prefix(self, test_client, sample_pipeline):
        """Should return 400 for external ID with wrong prefix"""
        pipeline = sample_pipeline(name="Test Pipeline")

        # Replace pip_ with col_ (collection prefix)
        wrong_prefix_id = pipeline.external_id.replace("pip_", "col_")

        response = test_client.get(f"/api/pipelines/{wrong_prefix_id}")

        assert response.status_code == 400
        assert "prefix mismatch" in response.json()["detail"].lower()

    def test_get_pipeline_external_id_not_found(self, test_client):
        """Should return 404 for valid external ID format but non-existent"""
        fake_external_id = "pip_01hgw2bbg00000000000000000"

        response = test_client.get(f"/api/pipelines/{fake_external_id}")

        assert response.status_code == 404


class TestExternalIdInListResponses:
    """Tests for external_id field in list responses - T037"""

    def test_list_collections_includes_external_id(self, test_client, sample_collection):
        """Should include external_id in collection list responses"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="List Test Collection",
                type="local",
                location=temp_dir
            )

            response = test_client.get("/api/collections")

            assert response.status_code == 200
            json_data = response.json()
            assert len(json_data) >= 1

            # Find our collection in the list
            found = next((c for c in json_data if c["id"] == collection.id), None)
            assert found is not None
            assert found["external_id"] == collection.external_id
            assert found["external_id"].startswith("col_")

    def test_list_connectors_includes_external_id(self, test_client, sample_connector):
        """Should include external_id in connector list responses"""
        connector = sample_connector(name="List Test Connector", type="s3")

        response = test_client.get("/api/connectors")

        assert response.status_code == 200
        json_data = response.json()

        found = next((c for c in json_data if c["id"] == connector.id), None)
        assert found is not None
        assert found["external_id"] == connector.external_id
        assert found["external_id"].startswith("con_")

    def test_list_pipelines_includes_external_id(self, test_client, sample_pipeline):
        """Should include external_id in pipeline list responses"""
        pipeline = sample_pipeline(name="List Test Pipeline")

        response = test_client.get("/api/pipelines")

        assert response.status_code == 200
        json_data = response.json()

        # Pipeline list response has an 'items' wrapper
        items = json_data.get("items", json_data)
        found = next((p for p in items if p["id"] == pipeline.id), None)
        assert found is not None
        assert found["external_id"] == pipeline.external_id
        assert found["external_id"].startswith("pip_")


class TestExternalIdInCreateResponses:
    """Tests for external_id field in create responses - T038"""

    def test_create_collection_returns_external_id(self, test_client, sample_collection_data):
        """Should return external_id when creating collection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            data = sample_collection_data(
                name="New Collection With External ID",
                type="local",
                location=temp_dir
            )

            response = test_client.post("/api/collections", json=data)

            assert response.status_code == 201
            json_data = response.json()
            assert "external_id" in json_data
            assert json_data["external_id"].startswith("col_")
            assert len(json_data["external_id"]) == 30  # 3 (prefix) + 1 (_) + 26 (base32)

    def test_create_connector_returns_external_id(self, test_client, sample_connector_data):
        """Should return external_id when creating connector"""
        data = sample_connector_data(name="New Connector With External ID", type="s3")

        response = test_client.post("/api/connectors", json=data)

        assert response.status_code == 201
        json_data = response.json()
        assert "external_id" in json_data
        assert json_data["external_id"].startswith("con_")

    def test_create_pipeline_returns_external_id(self, test_client, sample_pipeline_data):
        """Should return external_id when creating pipeline"""
        data = sample_pipeline_data(name="New Pipeline With External ID")

        response = test_client.post("/api/pipelines", json=data)

        assert response.status_code == 201
        json_data = response.json()
        assert "external_id" in json_data
        assert json_data["external_id"].startswith("pip_")


class TestBackwardCompatibilityNumericIds:
    """Tests for numeric ID backward compatibility - T050"""

    def test_numeric_ids_work_for_all_endpoints(
        self, test_client, sample_collection, sample_connector, sample_pipeline
    ):
        """All GET endpoints should accept numeric IDs"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="Numeric Test Collection",
                type="local",
                location=temp_dir
            )
            connector = sample_connector(name="Numeric Test Connector", type="s3")
            pipeline = sample_pipeline(name="Numeric Test Pipeline")

            # Test all GET endpoints with numeric IDs
            for entity_type, entity, prefix in [
                ("collections", collection, "col_"),
                ("connectors", connector, "con_"),
                ("pipelines", pipeline, "pip_"),
            ]:
                response = test_client.get(f"/api/{entity_type}/{entity.id}")

                assert response.status_code == 200
                json_data = response.json()
                assert json_data["id"] == entity.id
                assert json_data["external_id"].startswith(prefix)


class TestDeprecationWarningHeader:
    """Tests for deprecation warning header on numeric ID usage - T051"""

    def test_numeric_id_includes_deprecation_warning(self, test_client, sample_collection):
        """Should include X-Deprecation-Warning header for numeric ID requests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="Deprecation Test",
                type="local",
                location=temp_dir
            )

            response = test_client.get(f"/api/collections/{collection.id}")

            assert response.status_code == 200
            assert "X-Deprecation-Warning" in response.headers
            assert "external_id" in response.headers["X-Deprecation-Warning"].lower()

    def test_external_id_no_deprecation_warning(self, test_client, sample_collection):
        """Should NOT include deprecation warning for external ID requests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="No Deprecation Test",
                type="local",
                location=temp_dir
            )

            response = test_client.get(f"/api/collections/{collection.external_id}")

            assert response.status_code == 200
            assert "X-Deprecation-Warning" not in response.headers


class TestPutDeleteWithExternalIds:
    """Tests for PUT/DELETE endpoints accepting external IDs - T056, T057, T058"""

    # Collection tests - T056

    def test_update_collection_by_external_id(self, test_client, sample_collection):
        """Should update collection using external ID"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="Update Test Collection",
                type="local",
                location=temp_dir
            )

            update_data = {"name": "Updated Collection Name"}
            response = test_client.put(
                f"/api/collections/{collection.external_id}",
                json=update_data
            )

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["name"] == "Updated Collection Name"
            assert json_data["external_id"] == collection.external_id

    def test_update_collection_by_numeric_id_with_deprecation(self, test_client, sample_collection):
        """Should update collection using numeric ID with deprecation warning"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="Numeric Update Test",
                type="local",
                location=temp_dir
            )

            update_data = {"name": "Updated via Numeric ID"}
            response = test_client.put(
                f"/api/collections/{collection.id}",
                json=update_data
            )

            assert response.status_code == 200
            assert "X-Deprecation-Warning" in response.headers

    def test_delete_collection_by_external_id(self, test_client, sample_collection):
        """Should delete collection using external ID"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="Delete Test Collection",
                type="local",
                location=temp_dir
            )
            external_id = collection.external_id

            response = test_client.delete(f"/api/collections/{external_id}?force=true")

            assert response.status_code == 204

            # Verify deleted
            get_response = test_client.get(f"/api/collections/{external_id}")
            assert get_response.status_code == 404

    def test_delete_collection_by_numeric_id_with_deprecation(self, test_client, sample_collection):
        """Should delete collection using numeric ID with deprecation warning"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(
                name="Numeric Delete Test",
                type="local",
                location=temp_dir
            )

            response = test_client.delete(f"/api/collections/{collection.id}?force=true")

            assert response.status_code == 204
            assert "X-Deprecation-Warning" in response.headers

    # Connector tests - T057

    def test_update_connector_by_external_id(self, test_client, sample_connector):
        """Should update connector using external ID"""
        connector = sample_connector(name="Update Test Connector", type="s3")

        update_data = {"name": "Updated Connector Name"}
        response = test_client.put(
            f"/api/connectors/{connector.external_id}",
            json=update_data
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["name"] == "Updated Connector Name"
        assert json_data["external_id"] == connector.external_id

    def test_update_connector_by_numeric_id_with_deprecation(self, test_client, sample_connector):
        """Should update connector using numeric ID with deprecation warning"""
        connector = sample_connector(name="Numeric Update Connector", type="s3")

        update_data = {"name": "Updated via Numeric ID"}
        response = test_client.put(
            f"/api/connectors/{connector.id}",
            json=update_data
        )

        assert response.status_code == 200
        assert "X-Deprecation-Warning" in response.headers

    def test_delete_connector_by_external_id(self, test_client, sample_connector):
        """Should delete connector using external ID"""
        connector = sample_connector(name="Delete Test Connector", type="s3")
        external_id = connector.external_id

        response = test_client.delete(f"/api/connectors/{external_id}")

        assert response.status_code == 204

        # Verify deleted
        get_response = test_client.get(f"/api/connectors/{external_id}")
        assert get_response.status_code == 404

    def test_delete_connector_by_numeric_id_with_deprecation(self, test_client, sample_connector):
        """Should delete connector using numeric ID with deprecation warning"""
        connector = sample_connector(name="Numeric Delete Connector", type="s3")

        response = test_client.delete(f"/api/connectors/{connector.id}")

        assert response.status_code == 204
        assert "X-Deprecation-Warning" in response.headers

    # Pipeline tests - T058

    def test_update_pipeline_by_external_id(self, test_client, sample_pipeline):
        """Should update pipeline using external ID"""
        pipeline = sample_pipeline(name="Update Test Pipeline")

        update_data = {"name": "Updated Pipeline Name"}
        response = test_client.put(
            f"/api/pipelines/{pipeline.external_id}",
            json=update_data
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["name"] == "Updated Pipeline Name"
        assert json_data["external_id"] == pipeline.external_id

    def test_update_pipeline_by_numeric_id_still_works(self, test_client, sample_pipeline):
        """Should update pipeline using numeric ID (backward compat)"""
        pipeline = sample_pipeline(name="Numeric Update Pipeline")

        update_data = {"name": "Updated via Numeric ID"}
        response = test_client.put(
            f"/api/pipelines/{pipeline.id}",
            json=update_data
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated via Numeric ID"

    def test_delete_pipeline_by_external_id(self, test_client, sample_pipeline):
        """Should delete pipeline using external ID"""
        pipeline = sample_pipeline(name="Delete Test Pipeline")
        external_id = pipeline.external_id

        response = test_client.delete(f"/api/pipelines/{external_id}")

        assert response.status_code == 200  # Pipelines return 200 with message

        # Verify deleted
        get_response = test_client.get(f"/api/pipelines/{external_id}")
        assert get_response.status_code == 404

    def test_delete_pipeline_by_numeric_id_still_works(self, test_client, sample_pipeline):
        """Should delete pipeline using numeric ID (backward compat)"""
        pipeline = sample_pipeline(name="Numeric Delete Pipeline")

        response = test_client.delete(f"/api/pipelines/{pipeline.id}")

        assert response.status_code == 200  # Pipelines return 200 with message
