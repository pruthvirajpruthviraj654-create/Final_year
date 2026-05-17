from database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    department    = db.Column(db.String(120), default="")
    university    = db.Column(db.String(200), default="")
    college_name  = db.Column(db.String(200), default="")
    role          = db.Column(db.String(20),  default="teacher")
    api_key       = db.Column(db.String(400), default="")
    ai_model      = db.Column(db.String(100), default="openai/gpt-3.5-turbo")
    is_active     = db.Column(db.Boolean,     default=True)
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow)
    last_login    = db.Column(db.DateTime,    nullable=True)

    papers    = db.relationship("Paper",       back_populates="author",   lazy="dynamic", cascade="all,delete-orphan")
    questions = db.relationship("Question",    back_populates="owner",    lazy="dynamic", cascade="all,delete-orphan")
    syllabi   = db.relationship("Syllabus",    back_populates="owner",    lazy="dynamic", cascade="all,delete-orphan")
    feedbacks = db.relationship("Feedback",    back_populates="user",     lazy="dynamic", cascade="all,delete-orphan")

    def to_dict(self, include_sensitive=False):
        d = dict(id=self.id, name=self.name, email=self.email,
                 department=self.department, university=self.university,
                 college_name=self.college_name, role=self.role,
                 ai_model=self.ai_model, is_active=self.is_active,
                 created_at=self.created_at.strftime("%d %b %Y"),
                 paper_count=self.papers.count(), q_count=self.questions.count())
        if include_sensitive:
            d["api_key"] = self.api_key
        return d
