import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from app.main import app
from pymongo.errors import DuplicateKeyError, BulkWriteError
import copy

# DUMMY DATA
dummy_article_data = {
    "_id": ObjectId("507f191e810c19729de860ea"),
    "Title": "Test Article",
    "Date": "2022-01-01",
    "Link": "http://example.com",
    "Source": "http://source.com",
}

dummy_source_data = {
    "_id": ObjectId("507f191e810c19729de860eb"),
    "name": "Test Source",
    "base_url": "http://source.com",
    "url": "http://source.com/articles",
    "article_selector": ".article",
    "date_format": "%Y-%m-%d",
    "button_selector": None,
}


class DummyCollection:
    async def insert_one(self, data):
        inserted_id = (
            dummy_source_data["_id"] if "name" in data else dummy_article_data["_id"]
        )

        class DummyResult:
            pass

        DummyResult.inserted_id = inserted_id
        return DummyResult()

    async def find_one(self, query):
        if query.get("_id") == dummy_article_data["_id"]:
            return copy.deepcopy(dummy_article_data)
        if query.get("_id") == dummy_source_data["_id"]:
            return copy.deepcopy(dummy_source_data)
        return None

    async def find(self, *args, **kwargs):
        yield copy.deepcopy(dummy_article_data)

    async def update_one(self, query, update):
        if query.get("_id") == dummy_article_data["_id"]:

            new_data = update.get("$set", {})
            dummy_article_data.update(new_data)

            class DummyUpdateResult:
                modified_count = 1

            return DummyUpdateResult()
        else:

            class DummyUpdateResult:
                modified_count = 0

            return DummyUpdateResult()

    async def delete_one(self, query):
        class DummyDeleteResult:
            deleted_count = 1

        return DummyDeleteResult()

    async def create_index(self, key, unique=False):
        return None


class DummyDB:
    def __getitem__(self, name):
        return DummyCollection()


dummy_db = DummyDB()


@pytest.fixture(autouse=True)
def override_db(monkeypatch):
    """
    Fixture to override the database in the storage service with a dummy database.
    """
    import app.main as main_module

    monkeypatch.setattr(main_module, "db", dummy_db)


client = TestClient(app)


def test_create_article():
    """
    Test the endpoint for creating a single article.
    """
    article_payload = {
        "Title": "Test Article",
        "Date": "2022-01-01",
        "Link": "http://example.com",
        "Source": "http://source.com",
    }
    response = client.post("/articles/", json=article_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["Title"] == "Test Article"
    assert "id" in data


def test_list_articles():
    """
    Test the endpoint for listing articles.
    """
    response = client.get("/articles/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_article():
    """
    Test the endpoint for retrieving a single article by its id.
    """
    article_id = str(dummy_article_data["_id"])
    response = client.get(f"/articles/{article_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["Title"] == "Test Article"


def test_update_article():
    """
    Test the endpoint for updating an article.
    """
    article_id = str(dummy_article_data["_id"])
    update_payload = {
        "Title": "Updated Article",
        "Date": "2022-01-01",
        "Link": "http://example.com",
        "Source": "http://source.com",
    }
    response = client.put(f"/articles/{article_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["Title"] == "Updated Article"


def test_delete_article():
    """
    Test the endpoint for deleting an article.
    """
    article_id = str(dummy_article_data["_id"])
    response = client.delete(f"/articles/{article_id}")
    assert response.status_code == 204


def test_create_source():
    """
    Test the endpoint for creating a source.
    """
    source_payload = {
        "name": "Test Source",
        "base_url": "http://source.com",
        "url": "http://source.com/articles",
        "article_selector": "article",
        "date_format": "%Y-%m-%d",
        "button_selector": None,
    }
    response = client.post("/sources/", json=source_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Source"
    assert "id" in data


def test_list_sources():
    """
    Test the endpoint for listing sources.
    """
    response = client.get("/sources/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_source():
    """
    Test the endpoint for retrieving a single source by its id.
    """
    source_id = str(dummy_source_data["_id"])
    response = client.get(f"/sources/{source_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Source"


def test_update_source():
    """
    Test the endpoint for updating a source.
    """
    source_id = str(dummy_source_data["_id"])
    update_payload = {
        "name": "Updated Source",
        "base_url": "http://source.com",
        "url": "http://source.com/articles",
        "article_selector": ".article",
        "date_format": "%Y-%m-%d",
        "button_selector": None,
    }
    response = client.put(f"/sources/{source_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Source"


def test_delete_source():
    """
    Test the endpoint for deleting a source.
    """
    source_id = str(dummy_source_data["_id"])
    response = client.delete(f"/sources/{source_id}")
    assert response.status_code == 204
