def test_login_page_responds(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Login" in response.data


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
