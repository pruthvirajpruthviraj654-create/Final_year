# ============================================================
# app.py — ExamAI v2 Main Flask Application
# AI-Powered Syllabus-Based Question Paper Generator
# ============================================================
import os
from flask import Flask, jsonify, render_template, redirect, url_for
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import ActiveConfig
from database import db, init_db


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or ActiveConfig)

    db.init_app(app)
    JWTManager(app)
    CORS(app, supports_credentials=True)

    os.makedirs(app.config.get("UPLOAD_FOLDER","static/uploads"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path,"instance"), exist_ok=True)

    # Blueprints
    from routes.auth     import auth_bp
    from routes.paper    import paper_bp
    from routes.qbank    import qbank_bp
    from routes.admin    import admin_bp
    from routes.api      import api_bp
    from routes.syllabus import syllabus_bp

    app.register_blueprint(auth_bp,     url_prefix="/auth")
    app.register_blueprint(paper_bp,    url_prefix="/paper")
    app.register_blueprint(qbank_bp,    url_prefix="/qbank")
    app.register_blueprint(admin_bp,    url_prefix="/admin")
    app.register_blueprint(api_bp,      url_prefix="/api")
    app.register_blueprint(syllabus_bp, url_prefix="/syllabus")

    # Page routes
    @app.route("/")
    def index(): return render_template("index.html")

    @app.route("/login")
    def login_page(): return render_template("login.html")

    @app.route("/register")
    def register_page(): return render_template("register.html")

    @app.route("/dashboard")
    def dashboard_page(): return render_template("dashboard.html")

    @app.route("/generate")
    def generate_page(): return render_template("generate.html")

    @app.route("/syllabus-page")
    def syllabus_page(): return render_template("syllabus.html")

    @app.route("/history")
    def history_page(): return render_template("history.html")

    @app.route("/qbank")
    def qbank_page(): return render_template("qbank.html")

    @app.route("/analytics")
    def analytics_page(): return render_template("analytics.html")

    @app.route("/settings")
    def settings_page(): return render_template("settings.html")

    @app.route("/admin-panel")
    def admin_page(): return render_template("admin.html")

    @app.errorhandler(404)
    def not_found(e): return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e): return render_template("errors/500.html"), 500

    return app


if __name__ == "__main__":
    app = create_app()
    init_db(app)
    app.run(debug=True, port=5000, host="0.0.0.0")
