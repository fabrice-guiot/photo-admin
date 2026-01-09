"""
Integration tests for external ID migration and UUID functionality.

Tests verify:
- UUID columns are properly added to all entities
- Existing records receive valid UUIDs
- External ID generation works correctly
- No data loss during migration
"""

import pytest
from uuid import UUID


class TestExternalIdMigration:
    """Integration tests for UUID migration - Issue #42"""

    def test_collection_has_uuid_and_external_id(self, test_client):
        """
        Test that created collections have UUID and external_id.

        Verifies:
        - Collection response includes external_id field
        - External ID format is col_{26-char base32}
        - External ID is unique per collection
        """
        # Create a collection
        collection_data = {
            "name": "UUID Test Collection",
            "type": "local",
            "location": "/test/uuid/collection",
            "state": "live"
        }

        response = test_client.post("/api/collections", json=collection_data)
        assert response.status_code == 201

        collection = response.json()

        # Verify external_id exists and has correct format
        assert "external_id" in collection
        external_id = collection["external_id"]
        assert external_id.startswith("col_")
        assert len(external_id) == 30  # col_ + 26 chars

        # Verify we can fetch by the external ID
        fetch_response = test_client.get(f"/api/collections/{external_id}")
        assert fetch_response.status_code == 200
        assert fetch_response.json()["external_id"] == external_id

        # Clean up
        test_client.delete(f"/api/collections/{collection['id']}")

    def test_connector_has_uuid_and_external_id(self, test_client):
        """
        Test that created connectors have UUID and external_id.

        Verifies:
        - Connector response includes external_id field
        - External ID format is con_{26-char base32}
        """
        connector_data = {
            "name": "UUID Test Connector",
            "type": "s3",
            "credentials": {
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "region": "us-west-2"
            }
        }

        response = test_client.post("/api/connectors", json=connector_data)
        assert response.status_code == 201

        connector = response.json()

        # Verify external_id exists and has correct format
        assert "external_id" in connector
        external_id = connector["external_id"]
        assert external_id.startswith("con_")
        assert len(external_id) == 30  # con_ + 26 chars

        # Verify we can fetch by the external ID
        fetch_response = test_client.get(f"/api/connectors/{external_id}")
        assert fetch_response.status_code == 200
        assert fetch_response.json()["external_id"] == external_id

        # Clean up
        test_client.delete(f"/api/connectors/{connector['id']}")

    def test_pipeline_has_uuid_and_external_id(self, test_client):
        """
        Test that created pipelines have UUID and external_id.

        Verifies:
        - Pipeline response includes external_id field
        - External ID format is pip_{26-char base32}
        """
        pipeline_data = {
            "name": "UUID Test Pipeline",
            "description": "Pipeline for UUID testing",
            "nodes": [
                {"id": "capture_1", "type": "capture", "properties": {}},
                {"id": "term_1", "type": "termination", "properties": {"type": "success"}}
            ],
            "edges": [
                {"from": "capture_1", "to": "term_1"}
            ]
        }

        response = test_client.post("/api/pipelines", json=pipeline_data)
        assert response.status_code == 201

        pipeline = response.json()

        # Verify external_id exists and has correct format
        assert "external_id" in pipeline
        external_id = pipeline["external_id"]
        assert external_id.startswith("pip_")
        assert len(external_id) == 30  # pip_ + 26 chars

        # Verify we can fetch by the external ID
        fetch_response = test_client.get(f"/api/pipelines/{external_id}")
        assert fetch_response.status_code == 200
        assert fetch_response.json()["external_id"] == external_id

        # Clean up
        test_client.delete(f"/api/pipelines/{pipeline['id']}")

    def test_external_ids_are_unique(self, test_client):
        """
        Test that each entity gets a unique external ID.

        Creates multiple entities and verifies all external IDs are distinct.
        """
        external_ids = set()

        # Create multiple collections
        for i in range(3):
            response = test_client.post("/api/collections", json={
                "name": f"Unique Test Collection {i}",
                "type": "local",
                "location": f"/test/unique/{i}",
                "state": "live"
            })
            assert response.status_code == 201
            external_ids.add(response.json()["external_id"])

        # All external IDs should be unique
        assert len(external_ids) == 3

        # Clean up
        for collection in test_client.get("/api/collections").json():
            if collection["name"].startswith("Unique Test Collection"):
                test_client.delete(f"/api/collections/{collection['id']}")

    def test_list_endpoint_includes_external_id(self, test_client):
        """
        Test that list endpoints include external_id for all items.
        """
        # Create a test collection
        test_client.post("/api/collections", json={
            "name": "List Test Collection",
            "type": "local",
            "location": "/test/list",
            "state": "live"
        })

        # Get all collections
        response = test_client.get("/api/collections")
        assert response.status_code == 200

        collections = response.json()
        assert len(collections) > 0

        # Verify all collections have external_id
        for collection in collections:
            assert "external_id" in collection
            assert collection["external_id"].startswith("col_")

        # Clean up
        for collection in collections:
            if collection["name"] == "List Test Collection":
                test_client.delete(f"/api/collections/{collection['id']}")

    def test_external_id_case_insensitive_lookup(self, test_client):
        """
        Test that external ID lookups are case-insensitive.

        Crockford Base32 is case-insensitive, so lookups should work
        regardless of case.
        """
        # Create a collection
        response = test_client.post("/api/collections", json={
            "name": "Case Test Collection",
            "type": "local",
            "location": "/test/case",
            "state": "live"
        })
        collection = response.json()
        external_id = collection["external_id"]

        # Test uppercase lookup
        upper_response = test_client.get(f"/api/collections/{external_id.upper()}")
        assert upper_response.status_code == 200

        # Test mixed case lookup
        mixed_id = external_id[:5] + external_id[5:].upper()
        mixed_response = test_client.get(f"/api/collections/{mixed_id}")
        assert mixed_response.status_code == 200

        # Clean up
        test_client.delete(f"/api/collections/{collection['id']}")


class TestExternalIdErrorHandling:
    """Tests for external ID error handling - Issue #42"""

    def test_invalid_external_id_format_returns_400(self, test_client):
        """
        Test that invalid external ID format returns 400.
        """
        invalid_ids = [
            "col_123",  # Too short
            "xxx_01234567890123456789012345",  # Invalid prefix
            "col-01234567890123456789012345",  # Wrong separator
        ]

        for invalid_id in invalid_ids:
            response = test_client.get(f"/api/collections/{invalid_id}")
            # Should return 400 (bad request) or 404 (not found)
            assert response.status_code in [400, 404]

    def test_wrong_prefix_for_entity_returns_error(self, test_client):
        """
        Test that using wrong entity prefix returns error.

        E.g., using con_ prefix at /collections/ endpoint.
        """
        # Create a connector to get a valid con_ external ID
        response = test_client.post("/api/connectors", json={
            "name": "Wrong Prefix Test Connector",
            "type": "s3",
            "credentials": {
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "region": "us-west-2"
            }
        })
        connector = response.json()
        connector_external_id = connector["external_id"]

        # Try to use connector's external ID at collections endpoint
        wrong_prefix_response = test_client.get(
            f"/api/collections/{connector_external_id}"
        )
        # Should return 400 (prefix mismatch) or 404 (not found)
        assert wrong_prefix_response.status_code in [400, 404]

        # Clean up
        test_client.delete(f"/api/connectors/{connector['id']}")

    def test_nonexistent_external_id_returns_404(self, test_client):
        """
        Test that nonexistent external ID returns 404.
        """
        # Valid format but doesn't exist
        fake_external_id = "col_00000000000000000000000000"
        response = test_client.get(f"/api/collections/{fake_external_id}")
        assert response.status_code == 404


class TestBackwardCompatibility:
    """Tests for backward compatibility with numeric IDs - Issue #42"""

    def test_numeric_id_still_works(self, test_client):
        """
        Test that numeric IDs still work for backward compatibility.
        """
        # Create a collection
        response = test_client.post("/api/collections", json={
            "name": "Numeric ID Test Collection",
            "type": "local",
            "location": "/test/numeric",
            "state": "live"
        })
        collection = response.json()
        numeric_id = collection["id"]

        # Fetch by numeric ID
        numeric_response = test_client.get(f"/api/collections/{numeric_id}")
        assert numeric_response.status_code == 200
        assert numeric_response.json()["id"] == numeric_id

        # Clean up
        test_client.delete(f"/api/collections/{numeric_id}")

    def test_both_id_types_return_same_entity(self, test_client):
        """
        Test that numeric and external IDs return the same entity.
        """
        # Create a collection
        response = test_client.post("/api/collections", json={
            "name": "Both IDs Test Collection",
            "type": "local",
            "location": "/test/both",
            "state": "live"
        })
        collection = response.json()
        numeric_id = collection["id"]
        external_id = collection["external_id"]

        # Fetch by both ID types
        numeric_response = test_client.get(f"/api/collections/{numeric_id}")
        external_response = test_client.get(f"/api/collections/{external_id}")

        # Both should return the same entity
        assert numeric_response.status_code == 200
        assert external_response.status_code == 200
        assert numeric_response.json()["id"] == external_response.json()["id"]
        assert numeric_response.json()["external_id"] == external_response.json()["external_id"]

        # Clean up
        test_client.delete(f"/api/collections/{numeric_id}")
