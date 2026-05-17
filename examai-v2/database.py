# ============================================================
# database.py — DB instance + seeding
# ============================================================
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime

db = SQLAlchemy()

def init_db(app):
    with app.app_context():
        db.create_all()
        _seed()

def _seed():
    from models.user import User
    if User.query.count() == 0:
        users = [
            User(name="Dr. Admin",    email="admin@examai.edu",
                 password_hash=generate_password_hash("admin123"),
                 department="Computer Science", university="VisionCampus University",
                 college_name="VisionCampus University", role="admin"),
            User(name="Dr. Ramesh Kumar", email="teacher@examai.edu",
                 password_hash=generate_password_hash("teacher123"),
                 department="Computer Science", university="VisionCampus University",
                 college_name="VisionCampus University", role="teacher"),
        ]
        for u in users:
            db.session.add(u)
        db.session.commit()
        print("[DB] ✅ Demo users seeded — admin@examai.edu/admin123 | teacher@examai.edu/teacher123")
