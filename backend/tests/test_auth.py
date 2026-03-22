from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_register_user(client: TestClient, db_session: Session):
    response = client.post(
        "/api/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login_user(client: TestClient, db_session: Session):
    # 先注册一个用户
    client.post(
        "/api/auth/register",
        json={"username": "loginuser", "email": "login@example.com", "password": "loginpassword"}
    )
    
    # 测试登录
    response = client.post(
        "/api/auth/login",
        data={"username": "loginuser", "password": "loginpassword"} # OAuth2PasswordRequestForm expects form data
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
