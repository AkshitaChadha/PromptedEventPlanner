import os

from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv


def create_app(test_config: dict | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
    default_database = Path(__file__).resolve().parents[2] / "celebrai.db"
    app.config["DATABASE_URL"] = os.getenv(
        "DATABASE_URL", f"sqlite:///{default_database.as_posix()}"
    )
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    if test_config:
        app.config.update(test_config)

    from app.database import initialize_database

    initialize_database(app)

    allowed_origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    from app.routes.health import health_bp
    from app.routes.events import events_bp
    from app.routes.expenses import expenses_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(expenses_bp, url_prefix="/api/events")

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"error": "Request body is too large."}), 413

    return app
