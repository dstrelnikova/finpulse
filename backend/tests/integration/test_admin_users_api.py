import pytest


@pytest.mark.integration
def test_admin_users_list_forbidden_without_permission(client, auth_headers_for):
    res = client.get("/admin/users", headers=auth_headers_for("user@example.com"))
    assert res.status_code == 403


@pytest.mark.integration
def test_admin_users_list_success_for_admin(client, auth_headers_for):
    res = client.get(
        "/admin/users?page=1&page_size=2&sort_by=email&sort_dir=asc",
        headers=auth_headers_for("admin@example.com"),
    )
    assert res.status_code == 200

    body = res.json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert isinstance(body["items"], list)
    assert body["total"] >= len(body["items"])


@pytest.mark.integration
def test_set_roles_returns_400_for_unknown_role(client, auth_headers_for):
    res = client.put(
        "/admin/users/1/roles",
        headers=auth_headers_for("admin@example.com"),
        json={"roles": ["superadmin"]},
    )
    assert res.status_code == 400
