from fastapi.testclient import TestClient

from app.main import _local_output_url, _render_options_from_payload, app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint_points_reviewers_to_api_docs() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["docs"] == "/docs"
    assert payload["endpoints"]["upload_render"] == "POST /render"


def test_render_options_use_deployment_defaults() -> None:
    options = _render_options_from_payload({})

    assert str(options.output_dir) == "outputs"
    assert str(options.work_dir) == "work"
    assert options.template == "topcoder-star"


def test_local_output_url_maps_rendered_files_to_static_route() -> None:
    assert _local_output_url("outputs/job-123/profile_landscape.mp4") == (
        "/outputs/job-123/profile_landscape.mp4"
    )
