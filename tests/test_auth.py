from fastapi.testclient import TestClient
from MAIN_web import app

def test_register_short_password():
    client = TestClient(app, follow_redirects=False)
    response = client.post("/register_page", data={"username": "test_user", "password": "123"})
    print(response.status_code)
    assert "/register_page?error=short" in response.headers["location"]

def test_register_success():
    client = TestClient(app, follow_redirects = False)
    import uuid; name = str(uuid.uuid4())
    response = client.post("/register_page", data={"username": name, "password": "23546721962"})
    print(response.status_code)
    assert "/login_page" in response.headers["location"]

def test_login_success():
    client = TestClient(app, follow_redirects = False)
    import uuid; name = str(uuid.uuid4())
    password = str(uuid.uuid4())
    response = client.post("/register_page", data={"username":name, "password":password})
    print(response.status_code)
    assert "/login_page" in response.headers["location"]
    response = client.post("/login_page", data={"username":name, "password":password})
    print(response.status_code)
    assert "/page" in response.headers["location"]
    assert "token" in response.cookies

def test_login_wrong_password():
    client = TestClient(app, follow_redirects = False)
    import uuid; name = str(uuid.uuid4())
    password = "12345qwerty"
    response = client.post("/register_page", data={"username":name,"password":password})
    wrong_password = "qwertyuiop"
    response = client.post("/login_page", data={"username":name,"password":wrong_password})
    print(response.status_code)
    assert "/ login_page?error=invalid" in response.headers["location"]
    assert "token" not in response.cookies

def test_page_requires_login():
    client = TestClient(app, follow_redirects = False)
    response = client.get("/page")
    print(response.status_code)
    assert "/login_page" in response.headers["location"]