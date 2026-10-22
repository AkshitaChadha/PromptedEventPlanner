import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}

    allowed_origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    from app.routes.health import health_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    return app
