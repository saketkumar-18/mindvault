
import pytest
from fastapi.testclient import TestClient
from mindvault.api.app import create_app
from mindvault.config import Settings


@pytest.fixture(scope="session")
def monkeypatch_session():
    import _pytest.monkeypatch

    mp = _pytest.monkeypatch.MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope="session", autouse=True)
def env(monkeypatch_session, tmp_path_factory):
    home = tmp_path_factory.mktemp("mindvault_test_home")
    monkeypatch_session.setenv("MV_HOME", str(home))
    monkeypatch_session.setenv("MV_EMBEDDING_PROVIDER", "hash")
    monkeypatch_session.setenv("MV_LLM_PROVIDER", "mock")
    monkeypatch_session.setenv("MV_DEBUG", "0")
    return home


@pytest.fixture()
def settings(env) -> Settings:
    return Settings()


@pytest.fixture()
def app() -> TestClient:
    app = create_app()
    return TestClient(app)


@pytest.fixture()
def client(app) -> TestClient:
    return app