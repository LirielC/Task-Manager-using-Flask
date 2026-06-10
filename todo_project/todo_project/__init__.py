import logging
import os
import secrets
import sys

from flask import Flask, flash, has_request_context, redirect, request, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy


def configure_logging(flask_app):
    formatter = logging.Formatter(
        "%(asctime)s level=%(levelname)s %(message)s"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    flask_app.logger.handlers.clear()
    flask_app.logger.addHandler(handler)
    flask_app.logger.setLevel(logging.INFO)
    flask_app.logger.propagate = False


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///site.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_HTTPONLY"] = True

configure_logging(app)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "danger"

bcrypt = Bcrypt(app)


def log_event(event_type, level=logging.INFO, user=None, **details):
    username = user or "anonymous"
    route = "n/a"
    client_ip = "unknown"

    if has_request_context():
        route = request.path
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.remote_addr or "unknown"
        if user is None and getattr(current_user, "is_authenticated", False):
            username = current_user.username

    safe_details = {
        key: str(value).replace(" ", "_")[:200]
        for key, value in details.items()
        if value is not None
    }
    payload = " ".join(f"{key}={value}" for key, value in safe_details.items())
    message = f"event={event_type} user={username} route={route} ip={client_ip}"
    if payload:
        message = f"{message} {payload}"
    app.logger.log(level, message)


@login_manager.unauthorized_handler
def unauthorized():
    log_event("ACESSO_NAO_AUTENTICADO", level=logging.WARNING, next_url=request.url)
    flash("Faça login para acessar esta funcionalidade.", "warning")
    return redirect(url_for("login", next=request.url))


# stdout is container-friendly and can be collected later by syslog/rsyslog,
# Loki/Promtail, Fluent Bit, or ELK in a DevSecOps pipeline.

# Always put Routes at end
from todo_project import routes
