from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.config import API_SECRET_KEY


@pytest.mark.parametrize(
    "filename, status",
    [("TestFile.txt", 200), ("EmptyFile.txt", 400), ("Ethiopia_DH_CaseStudy.pdf", 200)],
)
async def test_ingestion(client: TestClient, filename: str, status: int) -> None:
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_SECRET_KEY}",
    }

    with open(Path(__file__).parent / f"data/{filename}", "rb") as f:
        files = {"file": (filename, f, "text/plain")}
        response = client.post("/ingestion", headers=headers, files=files)

    assert response.status_code == status
