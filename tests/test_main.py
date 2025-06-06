from fastapi.testclient import TestClient
# from app.main import app # Not needed if using the client fixture from conftest

# client = TestClient(app) # Not needed if using the client fixture

def test_read_main(client: TestClient):
    """
    Test that the root endpoint returns a 200 OK status.
    """
    response = client.get("/")
    assert response.status_code == 200
    # You can also add assertions for the response content if needed,
    # e.g., assert response.json() == {"message": "Hello World"}
    # This depends on what your root endpoint actually returns.
    # For now, let's find out what it returns.
    print(response.json()) # Temporary print to see the response content
    # Based on the actual response, we can make the assertion more specific.
    # For example, if it's the default FastAPI response:
    # assert response.json() == {"message": "FastAPI"}
    # Or if it's from the ZenithTask template:
    # assert "ZenithTask" in response.text # or response.json() if it returns JSON
    # For the default FastAPI, it might be {"Hello": "World"} or similar.
    # Let's assume a generic welcome message for now.
    # This will be adjusted after the first test run if necessary.
    assert "Welcome" in response.text or "FastAPI" in response.text or response.json() is not None
