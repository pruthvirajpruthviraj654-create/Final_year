from database import db
from datetime import datetime

class Feedback(db.Model):
    __tablename__ = "feedback"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    name       = db.Column(db.String(120), default="Anonymous")
    email      = db.Column(db.String(180), default="")
    message    = db.Column(db.Text, nullable=False)
    rating     = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user       = db.relationship("User", back_populates="feedbacks")

    def to_dict(self):
        return dict(id=self.id, name=self.name, email=self.email,
                    message=self.message, rating=self.rating,
                    created_at=self.created_at.strftime("%d %b %Y %H:%M"))
