"""
Unit tests for Collections API endpoints.

Tests CRUD operations, accessibility testing, cache refresh, and error handling
for the /api/collections endpoints.
"""

import pytest
import tempfile
from fastapi.testclient import TestClient


class TestCollectionAPICreate:
    """Tests for POST /api/collections - T104w"""

    def test_create_local_collection_with_accessibility_test(self, test_client, sample_collection_data):
        """Should create local collection with accessibility test - T104w"""
        with tempfile.TemporaryDirectory() as temp_dir:
            data = sample_collection_data(
                name="Local Photos",
                type="local",
                location=temp_dir,
                state="live"
            )

            response = test_client.post("/api/collections", json=data)

            assert response.status_code == 201
            json_data = response.json()
            assert json_data["name"] == "Local Photos"
            assert json_data["type"] == "local"
            assert json_data["is_accessible"] is True
            assert json_data["last_error"] is None

    def test_create_local_collection_inaccessible_directory(self, test_client, sample_collection_data):
        """Should create collection but mark as inaccessible"""
        data = sample_collection_data(
            name="Inaccessible",
            type="local",
            location="/nonexistent/directory"
        )

        response = test_client.post("/api/collections", json=data)

        # Service creates collection but marks it as inaccessible
        assert response.status_code == 201
        json_data = response.json()
        assert json_data["is_accessible"] is False
        assert json_data["last_error"] is not None

    def test_create_remote_collection_with_connector(self, test_client, sample_connector, sample_collection_data):
        """Should create remote collection with valid connector - T104w"""
        connector = sample_connector(name="S3 Connector", type="s3")

        data = sample_collection_data(
            name="S3 Photos",
            type="s3",
            location="s3://bucket/photos",
            connector_id=connector.id
        )

        response = test_client.post("/api/collections", json=data)

        assert response.status_code == 201
        json_data = response.json()
        assert json_data["name"] == "S3 Photos"
        assert json_data["type"] == "s3"
        assert json_data["connector_id"] == connector.id

    def test_create_collection_duplicate_name(self, test_client, sample_collection):
        """Should return 409 for duplicate name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_collection(name="Existing Collection", type="local", location=temp_dir)

            # Try to create another with same name
            with tempfile.TemporaryDirectory() as temp_dir2:
                data = {
                    "name": "Existing Collection",
                    "type": "local",
                    "location": temp_dir2,
                    "state": "live"
                }

                response = test_client.post("/api/collections", json=data)

                assert response.status_code == 409
                assert "already exists" in response.json()["detail"]


class TestCollectionAPIList:
    """Tests for GET /api/collections - T104w"""

    def test_list_all_collections(self, test_client, sample_collection):
        """Should return all collections"""
        with tempfile.TemporaryDirectory() as temp_dir1, \
             tempfile.TemporaryDirectory() as temp_dir2:
            sample_collection(name="Collection 1", type="local", location=temp_dir1)
            sample_collection(name="Collection 2", type="local", location=temp_dir2)

            response = test_client.get("/api/collections")

            assert response.status_code == 200
            json_data = response.json()
            assert len(json_data) == 2

    def test_list_collections_filter_by_state(self, test_client, sample_collection):
        """Should filter collections by state - T104w"""
        with tempfile.TemporaryDirectory() as temp_dir1, \
             tempfile.TemporaryDirectory() as temp_dir2, \
             tempfile.TemporaryDirectory() as temp_dir3:
            sample_collection(name="Live 1", type="local", location=temp_dir1, state="live")
            sample_collection(name="Live 2", type="local", location=temp_dir2, state="live")
            sample_collection(name="Archived", type="local", location=temp_dir3, state="archived")

            response = test_client.get("/api/collections?state=live")

            assert response.status_code == 200
            json_data = response.json()
            assert len(json_data) == 2
            assert all(c["state"] == "live" for c in json_data)

    def test_list_collections_filter_by_type(self, test_client, sample_collection, sample_connector):
        """Should filter collections by type - T104w"""
        with tempfile.TemporaryDirectory() as temp_dir:
            connector = sample_connector(name="S3 Test", type="s3")

            sample_collection(name="Local", type="local", location=temp_dir)
            sample_collection(name="S3", type="s3", location="s3://bucket", connector_id=connector.id)

            response = test_client.get("/api/collections?type=local")

            assert response.status_code == 200
            json_data = response.json()
            assert len(json_data) == 1
            assert json_data[0]["type"] == "local"

    def test_list_collections_accessible_only(self, test_client, sample_collection):
        """Should filter accessible collections only - T104w"""
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_collection(name="Accessible", type="local", location=temp_dir, is_accessible=True)
            sample_collection(
                name="Inaccessible",
                type="local",
                location="/fake/path",
                is_accessible=False,
                last_error="Directory not found"
            )

            response = test_client.get("/api/collections?accessible_only=true")

            assert response.status_code == 200
            json_data = response.json()
            assert len(json_data) == 1
            assert json_data[0]["name"] == "Accessible"
            assert json_data[0]["is_accessible"] is True


class TestCollectionAPIGet:
    """Tests for GET /api/collections/{id}"""

    def test_get_collection_by_id(self, test_client, sample_collection):
        """Should return collection by ID"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(name="Test Collection", type="local", location=temp_dir)

            response = test_client.get(f"/api/collections/{collection.id}")

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["id"] == collection.id
            assert json_data["name"] == "Test Collection"

    def test_get_collection_not_found(self, test_client):
        """Should return 404 if collection not found"""
        response = test_client.get("/api/collections/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestCollectionAPIUpdate:
    """Tests for PUT /api/collections/{id}"""

    def test_update_collection_name(self, test_client, sample_collection):
        """Should update collection name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(name="Original", type="local", location=temp_dir)

            response = test_client.put(
                f"/api/collections/{collection.id}",
                json={"name": "Updated"}
            )

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["name"] == "Updated"

    def test_update_collection_state(self, test_client, sample_collection):
        """Should update collection state"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(name="Test", type="local", location=temp_dir, state="live")

            response = test_client.put(
                f"/api/collections/{collection.id}",
                json={"state": "archived"}
            )

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["state"] == "archived"

    def test_update_collection_not_found(self, test_client):
        """Should return 404 if collection not found"""
        response = test_client.put(
            "/api/collections/999",
            json={"name": "Updated"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestCollectionAPIDelete:
    """Tests for DELETE /api/collections - T104w"""

    def test_delete_collection_success(self, test_client, sample_collection):
        """Should delete collection and return 204 - T104w"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(name="To Delete", type="local", location=temp_dir)

            response = test_client.delete(f"/api/collections/{collection.id}")

            assert response.status_code == 204

            # Verify deletion
            get_response = test_client.get(f"/api/collections/{collection.id}")
            assert get_response.status_code == 404

    @pytest.mark.skip(reason="has_analysis_results and has_active_jobs are TODO placeholders")
    def test_delete_collection_with_results_requires_force(self, test_client, sample_collection, mocker):
        """Should require force=true when results exist - T104w"""
        # This test is skipped because the service layer has TODO placeholders
        # for has_analysis_results and has_active_jobs checks
        # Once implemented, this test should be enabled and updated
        pass

    def test_delete_collection_with_force_flag(self, test_client, sample_collection):
        """Should delete with force=true - T104w"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(name="Force Delete", type="local", location=temp_dir)

            response = test_client.delete(f"/api/collections/{collection.id}?force=true")

            assert response.status_code == 204

    def test_delete_collection_not_found(self, test_client):
        """Should return 404 if collection not found"""
        response = test_client.delete("/api/collections/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestCollectionAPITestAccessibility:
    """Tests for POST /api/collections/{id}/test - T104x"""

    def test_test_local_collection_accessible(self, test_client, sample_collection):
        """Should test local collection accessibility - T104x"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(name="Test", type="local", location=temp_dir)

            response = test_client.post(f"/api/collections/{collection.id}/test")

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["success"] is True
            assert "accessible" in json_data["message"].lower()

    def test_test_local_collection_inaccessible(self, test_client, sample_collection):
        """Should detect inaccessible local collection"""
        collection = sample_collection(
            name="Inaccessible",
            type="local",
            location="/nonexistent/path",
            is_accessible=False,
            last_error="Directory not found"
        )

        response = test_client.post(f"/api/collections/{collection.id}/test")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is False
        assert "not accessible" in json_data["message"].lower() or "not found" in json_data["message"].lower()

    def test_test_remote_collection_with_connector(self, test_client, sample_connector, sample_collection, mocker):
        """Should test remote collection via connector"""
        connector = sample_connector(name="S3", type="s3")
        collection = sample_collection(
            name="S3 Collection",
            type="s3",
            location="s3://bucket",
            connector_id=connector.id
        )

        # Mock successful adapter test
        mock_adapter = mocker.patch('backend.src.services.connector_service.S3Adapter')
        mock_adapter.return_value.test_connection.return_value = (True, "Connected")

        response = test_client.post(f"/api/collections/{collection.id}/test")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

    def test_test_collection_not_found(self, test_client):
        """Should return 404 if collection not found"""
        response = test_client.post("/api/collections/999/test")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestCollectionAPIRefreshCache:
    """Tests for POST /api/collections/{id}/refresh - T104x"""

    def test_refresh_cache_small_collection(self, test_client, sample_collection):
        """Should refresh cache for small collection - T104x"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            import os
            for i in range(5):
                open(os.path.join(temp_dir, f"photo{i}.jpg"), 'w').close()

            collection = sample_collection(name="Small", type="local", location=temp_dir)

            response = test_client.post(f"/api/collections/{collection.id}/refresh")

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["success"] is True
            assert json_data["file_count"] == 5

    def test_refresh_cache_large_collection_requires_confirm(self, test_client, sample_collection, mocker):
        """Should require confirmation for large collections - T104x"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(name="Large", type="local", location=temp_dir)

            # Mock get_collection_files to simulate large collection
            mocker.patch(
                'backend.src.services.collection_service.CollectionService._fetch_collection_files',
                return_value=[f"photo{i}.jpg" for i in range(150000)]
            )

            response = test_client.post(f"/api/collections/{collection.id}/refresh?threshold=100000")

            assert response.status_code == 400
            assert "confirm" in response.json()["detail"].lower() or "threshold" in response.json()["detail"].lower()

    def test_refresh_cache_large_collection_with_confirm(self, test_client, sample_collection, mocker):
        """Should refresh large collection with confirm=true - T104x"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(name="Large", type="local", location=temp_dir)

            # Mock get_collection_files to simulate large collection
            mocker.patch(
                'backend.src.services.collection_service.CollectionService._fetch_collection_files',
                return_value=[f"photo{i}.jpg" for i in range(150000)]
            )

            response = test_client.post(
                f"/api/collections/{collection.id}/refresh?confirm=true&threshold=100000"
            )

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["success"] is True
            assert json_data["file_count"] == 150000

    def test_refresh_cache_custom_threshold(self, test_client, sample_collection, mocker):
        """Should use custom threshold parameter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = sample_collection(name="Medium", type="local", location=temp_dir)

            # Mock 60K files
            mocker.patch(
                'backend.src.services.collection_service.CollectionService._fetch_collection_files',
                return_value=[f"photo{i}.jpg" for i in range(60000)]
            )

            # Should fail with threshold=50K
            response = test_client.post(f"/api/collections/{collection.id}/refresh?threshold=50000")

            assert response.status_code == 400

    def test_refresh_cache_invalidates_cache(self, test_client, sample_collection, test_cache):
        """Should invalidate existing cache - T104x"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            import os
            open(os.path.join(temp_dir, "photo.jpg"), 'w').close()

            collection = sample_collection(name="Test", type="local", location=temp_dir)

            # Pre-populate cache with old data (using test_cache which is used by test_client)
            test_cache.set(collection.id, ["old_file.jpg"], ttl_seconds=3600)

            response = test_client.post(f"/api/collections/{collection.id}/refresh")

            assert response.status_code == 200
            json_data = response.json()
            assert json_data["file_count"] == 1

            # Verify new files are cached
            cached_files = test_cache.get(collection.id)
            assert cached_files is not None
            assert "photo.jpg" in cached_files

    def test_refresh_cache_not_found(self, test_client):
        """Should return 404 if collection not found"""
        response = test_client.post("/api/collections/999/refresh")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
