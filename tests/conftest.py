from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "todo_project"

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from todo_project import app, bcrypt, db  # noqa: E402
from todo_project.models import User  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    database_path = tmp_path / "test.db"
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path}",
        WTF_CSRF_ENABLED=False,
        LOGIN_DISABLED=False,
    )

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        user = User(
            username="tester",
            password=bcrypt.generate_password_hash("validpassword").decode("utf-8"),
        )
        db.session.add(user)
        db.session.commit()

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        db.session.remove()
        db.drop_all()
