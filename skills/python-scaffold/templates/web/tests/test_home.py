from django.test import Client


def test_home_renders_the_shell(client: Client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.content.decode()
    assert "{{PROJECT}}" in body
    assert "Ping" in body


def test_ping_returns_the_htmx_fragment(client: Client) -> None:
    response = client.get("/ping/", HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    body = response.content.decode()
    assert "pong" in body
    assert "<html" not in body
