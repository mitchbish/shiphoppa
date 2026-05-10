from fastapi.testclient import TestClient

from app.main import app, reset_store_for_tests, store


IMPORTER_HEADERS = {"Authorization": "Bearer shiphoppa-importer-dev"}


def test_post_import_project_creates_with_audit_and_version() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    audit_before = len(store.audit_events)
    versions_before = len(store.import_project_versions)

    response = client.post(
        "/import-projects",
        headers=IMPORTER_HEADERS,
        json={"title": "Q3 Furniture Import", "description": "Vanity tops from Foshan"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Q3 Furniture Import"
    assert body["status"] == "active"
    assert body["id"] in store.import_projects

    new_versions = [v for v in store.import_project_versions.values() if v.import_project_id == body["id"]]
    assert len(new_versions) == 1
    assert new_versions[0].action == "project_created"
    assert len(store.audit_events) > audit_before
    assert len(store.import_project_versions) > versions_before


def test_post_import_project_rejects_short_title() -> None:
    reset_store_for_tests()
    client = TestClient(app)

    response = client.post(
        "/import-projects",
        headers=IMPORTER_HEADERS,
        json={"title": "X"},
    )
    assert response.status_code == 422


def test_patch_import_project_updates_fields_and_writes_version() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    created = client.post(
        "/import-projects",
        headers=IMPORTER_HEADERS,
        json={"title": "Original Title"},
    ).json()

    versions_before = len([v for v in store.import_project_versions.values() if v.import_project_id == created["id"]])
    response = client.patch(
        f"/import-projects/{created['id']}",
        headers=IMPORTER_HEADERS,
        json={"title": "Renamed Project", "next_action": "Confirm supplier"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Renamed Project"
    assert body["next_action"] == "Confirm supplier"
    versions_after = len([v for v in store.import_project_versions.values() if v.import_project_id == created["id"]])
    assert versions_after == versions_before + 1


def test_patch_with_empty_body_returns_unchanged_project() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    created = client.post(
        "/import-projects",
        headers=IMPORTER_HEADERS,
        json={"title": "Stable Title"},
    ).json()

    response = client.patch(
        f"/import-projects/{created['id']}",
        headers=IMPORTER_HEADERS,
        json={},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Stable Title"


def test_patch_archives_project_sets_archived_at() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    created = client.post(
        "/import-projects",
        headers=IMPORTER_HEADERS,
        json={"title": "Archive Me"},
    ).json()

    response = client.patch(
        f"/import-projects/{created['id']}",
        headers=IMPORTER_HEADERS,
        json={"status": "archived"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "archived"
    assert body["archived_at"] is not None


def test_clone_import_project_creates_new_with_same_metadata() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    source = client.post(
        "/import-projects",
        headers=IMPORTER_HEADERS,
        json={"title": "Original", "description": "First import"},
    ).json()

    response = client.post(
        f"/import-projects/{source['id']}/clone",
        headers=IMPORTER_HEADERS,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] != source["id"]
    assert body["title"] == "Copy of Original"
    assert body["description"] == "First import"

    clone_versions = [v for v in store.import_project_versions.values() if v.import_project_id == body["id"]]
    assert any(v.action == "project_cloned" for v in clone_versions)


def test_clone_with_explicit_new_title() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    source = client.post(
        "/import-projects",
        headers=IMPORTER_HEADERS,
        json={"title": "Original"},
    ).json()

    response = client.post(
        f"/import-projects/{source['id']}/clone?new_title=Custom%20Clone",
        headers=IMPORTER_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Custom Clone"


def test_delete_import_project_soft_deletes() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    created = client.post(
        "/import-projects",
        headers=IMPORTER_HEADERS,
        json={"title": "Goner"},
    ).json()

    response = client.delete(
        f"/import-projects/{created['id']}",
        headers=IMPORTER_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "deleted_pending_retention"
    assert body["deleted_at"] is not None
    assert created["id"] in store.import_projects


def test_delete_is_idempotent() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    created = client.post(
        "/import-projects",
        headers=IMPORTER_HEADERS,
        json={"title": "Twice Deleted"},
    ).json()

    first = client.delete(f"/import-projects/{created['id']}", headers=IMPORTER_HEADERS)
    second = client.delete(f"/import-projects/{created['id']}", headers=IMPORTER_HEADERS)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "deleted_pending_retention"


def test_list_import_projects_filters_deleted_by_default() -> None:
    reset_store_for_tests()
    client = TestClient(app)
    keep = client.post("/import-projects", headers=IMPORTER_HEADERS, json={"title": "Active One"}).json()
    gone = client.post("/import-projects", headers=IMPORTER_HEADERS, json={"title": "Deleted One"}).json()
    client.delete(f"/import-projects/{gone['id']}", headers=IMPORTER_HEADERS)

    default_list = client.get("/import-projects", headers=IMPORTER_HEADERS).json()
    ids_in_default = {project["id"] for project in default_list}
    assert keep["id"] in ids_in_default
    assert gone["id"] not in ids_in_default

    full_list = client.get("/import-projects?include_deleted=true", headers=IMPORTER_HEADERS).json()
    ids_in_full = {project["id"] for project in full_list}
    assert gone["id"] in ids_in_full
