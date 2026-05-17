from database import db
from datetime import datetime
import json

class Paper(db.Model):
    __tablename__ = "papers"
    id           = db.Column(db.Integer,     primary_key=True)
    user_id      = db.Column(db.Integer,     db.ForeignKey("users.id"), nullable=False, index=True)
    syllabus_id  = db.Column(db.Integer,     db.ForeignKey("syllabi.id"), nullable=True)
    title        = db.Column(db.String(250), nullable=False)
    subject      = db.Column(db.String(100), nullable=False, index=True)
    exam_type    = db.Column(db.String(120), default="End Semester Examination")
    difficulty   = db.Column(db.String(50),  default="mixed")
    bloom_level  = db.Column(db.String(120), default="All Levels")
    units        = db.Column(db.String(300), default="")
    selected_topics = db.Column(db.Text,     default="[]")
    total_marks  = db.Column(db.Integer,     default=100)
    duration     = db.Column(db.String(60),  default="3 Hours")
    q_count      = db.Column(db.Integer,     default=20)
    content      = db.Column(db.Text,        default="")
    paper_json   = db.Column(db.Text,        default="{}")
    syllabus_based = db.Column(db.Boolean,   default=False)
    ai_generated = db.Column(db.Boolean,     default=True)
    created_at   = db.Column(db.DateTime,    default=datetime.utcnow)
    author       = db.relationship("User",   back_populates="papers")

    def get_paper_json(self):
        try:
            return json.loads(self.paper_json) if self.paper_json else {}
        except Exception:
            return {}

    def to_dict(self, include_content=False):
        d = dict(id=self.id, title=self.title, subject=self.subject,
                 exam_type=self.exam_type, difficulty=self.difficulty,
                 bloom_level=self.bloom_level, units=self.units,
                 total_marks=self.total_marks, duration=self.duration,
                 q_count=self.q_count, syllabus_based=self.syllabus_based,
                 created_at=self.created_at.strftime("%d %b %Y"),
                 author_name=self.author.name if self.author else "")
        if include_content:
            d["content"]    = self.content
            d["paper_json"] = self.get_paper_json()
        return d
