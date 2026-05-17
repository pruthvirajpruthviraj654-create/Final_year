# ============================================================
# models/syllabus.py — Syllabus upload and topic extraction
# ============================================================
from database import db
from datetime import datetime
import json


class Syllabus(db.Model):
    """Stores uploaded or manually entered syllabus per subject."""
    __tablename__ = "syllabi"

    id           = db.Column(db.Integer,     primary_key=True)
    user_id      = db.Column(db.Integer,     db.ForeignKey("users.id"), nullable=False, index=True)
    subject      = db.Column(db.String(100), nullable=False, index=True)
    title        = db.Column(db.String(250), default="")
    raw_text     = db.Column(db.Text,        default="")   # original syllabus text
    file_name    = db.Column(db.String(300), default="")   # uploaded file name
    file_type    = db.Column(db.String(20),  default="manual")  # pdf|txt|docx|manual
    units_json   = db.Column(db.Text,        default="[]") # extracted units list
    topics_json  = db.Column(db.Text,        default="[]") # extracted flat topics list
    keywords_json= db.Column(db.Text,        default="[]") # keywords
    is_active    = db.Column(db.Boolean,     default=True)
    created_at   = db.Column(db.DateTime,    default=datetime.utcnow)

    owner  = db.relationship("User",          back_populates="syllabi")
    topics = db.relationship("SyllabusTopic", back_populates="syllabus",
                             cascade="all,delete-orphan", lazy="dynamic")

    def get_units(self):
        try:
            return json.loads(self.units_json) if self.units_json else []
        except Exception:
            return []

    def get_topics(self):
        try:
            return json.loads(self.topics_json) if self.topics_json else []
        except Exception:
            return []

    def get_keywords(self):
        try:
            return json.loads(self.keywords_json) if self.keywords_json else []
        except Exception:
            return []

    def to_dict(self):
        return dict(
            id=self.id, subject=self.subject, title=self.title,
            file_name=self.file_name, file_type=self.file_type,
            units=self.get_units(), topics=self.get_topics(),
            keywords=self.get_keywords(),
            topic_count=self.topics.count(),
            created_at=self.created_at.strftime("%d %b %Y"),
        )


class SyllabusTopic(db.Model):
    """Individual topic extracted from a syllabus."""
    __tablename__ = "syllabus_topics"

    id          = db.Column(db.Integer,     primary_key=True)
    syllabus_id = db.Column(db.Integer,     db.ForeignKey("syllabi.id"), nullable=False, index=True)
    unit_number = db.Column(db.Integer,     default=1)
    unit_name   = db.Column(db.String(200), default="")
    topic       = db.Column(db.String(300), nullable=False)
    subtopics   = db.Column(db.Text,        default="[]") # JSON list
    keywords    = db.Column(db.Text,        default="[]") # JSON list
    bloom_level = db.Column(db.String(50),  default="")   # suggested bloom level
    difficulty  = db.Column(db.String(30),  default="Medium")

    syllabus = db.relationship("Syllabus", back_populates="topics")

    def get_subtopics(self):
        try:
            return json.loads(self.subtopics) if self.subtopics else []
        except Exception:
            return []

    def get_keywords(self):
        try:
            return json.loads(self.keywords) if self.keywords else []
        except Exception:
            return []

    def to_dict(self):
        return dict(
            id=self.id, unit_number=self.unit_number, unit_name=self.unit_name,
            topic=self.topic, subtopics=self.get_subtopics(),
            keywords=self.get_keywords(), bloom_level=self.bloom_level,
            difficulty=self.difficulty,
        )
