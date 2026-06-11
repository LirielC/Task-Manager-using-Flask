def test_login_page_responds(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Login" in response.data


def test_security_headers_are_present(client):
    response = client.get("/login")

    assert response.headers["Content-Security-Policy"].startswith("default-src 'self'")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Embedder-Policy"] == "require-corp"
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_session_cookie_sets_samesite(client):
    response = client.post(
        "/login",
        data={"username": "tester", "password": "validpassword"},
        follow_redirects=False,
    )

    cookie_header = response.headers["Set-Cookie"]

    assert "HttpOnly" in cookie_header
    assert "SameSite=Lax" in cookie_header


def test_protected_route_redirects_when_not_authenticated(client):
    response = client.get("/all_tasks", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_invalid_login_does_not_authenticate(client):
    response = client.post(
        "/login",
        data={"username": "tester", "password": "wrong-password"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Login Unsuccessful" in response.data

    protected_response = client.get("/all_tasks", follow_redirects=False)
    assert protected_response.status_code == 302
    assert "/login" in protected_response.headers["Location"]


def test_add_task_route_is_protected(client):
    response = client.get("/add_task", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
