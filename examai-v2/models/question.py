from database import db
from datetime import datetime
import json

class Question(db.Model):
    __tablename__ = "questions"
    id          = db.Column(db.Integer,     primary_key=True)
    user_id     = db.Column(db.Integer,     db.ForeignKey("users.id"), nullable=False, index=True)
    text        = db.Column(db.Text,        nullable=False)
    subject     = db.Column(db.String(100), nullable=False, index=True)
    difficulty  = db.Column(db.String(30),  nullable=False)
    q_type      = db.Column(db.String(30),  nullable=False)
    unit        = db.Column(db.String(60),  default="Unit 1")
    topic       = db.Column(db.String(200), default="")
    marks       = db.Column(db.Integer,     default=1)
    answer      = db.Column(db.Text,        default="")
    options     = db.Column(db.Text,        default="[]")
    bloom_level = db.Column(db.String(60),  default="")
    used_count  = db.Column(db.Integer,     default=0)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)
    owner       = db.relationship("User",   back_populates="questions")

    def get_options(self):
        try:
            return json.loads(self.options) if self.options else []
        except Exception:
            return []

    def to_dict(self):
        return dict(id=self.id, text=self.text, subject=self.subject,
                    difficulty=self.difficulty, q_type=self.q_type,
                    unit=self.unit, topic=self.topic, marks=self.marks,
                    answer=self.answer, options=self.get_options(),
                    bloom_level=self.bloom_level, used_count=self.used_count,
                    created_at=self.created_at.strftime("%d %b %Y"))
