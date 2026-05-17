# routes/api.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from database import db
from models.user import User
from models.paper import Paper
from models.question import Question
from models.feedback import Feedback
from services.syllabus_engine import SUBJECT_TOPICS

api_bp = Blueprint("api", __name__)

SUBJECTS = list(SUBJECT_TOPICS.keys()) + ["PHP","SE","C","C++","Computer Graphics","Compiler Design"]

@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok","service":"ExamAI v2","timestamp":datetime.utcnow().isoformat()}),200

@api_bp.route("/subjects", methods=["GET"])
def subjects():
    return jsonify({"success":True,"subjects":SUBJECTS}),200

@api_bp.route("/analytics/overview", methods=["GET"])
@jwt_required()
def analytics_overview():
    uid    = int(get_jwt_identity())
    papers = Paper.query.filter_by(user_id=uid).all()
    qs     = Question.query.filter_by(user_id=uid).count()
    subs, diffs, monthly, qtypes = {},{},{},{}
    for p in papers:
        subs[p.subject] = subs.get(p.subject,0)+1
        d = (p.difficulty or "Mixed").lower()
        diffs[d] = diffs.get(d,0)+1
        monthly[p.created_at.strftime("%b")] = monthly.get(p.created_at.strftime("%b"),0)+1
    for q in Question.query.filter_by(user_id=uid).all():
        qtypes[q.q_type] = qtypes.get(q.q_type,0)+1
    return jsonify({"success":True,"total_papers":len(papers),"total_questions":qs,
                    "subjects":subs,"difficulties":diffs,"monthly":monthly,"q_types":qtypes}),200

@api_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json(silent=True) or {}
    if not (data.get("message") or "").strip():
        return jsonify({"success":False,"message":"Message required."}),400
    uid = None
    try:
        verify_jwt_in_request(optional=True)
        i = get_jwt_identity()
        uid = int(i) if i else None
    except Exception:
        pass
    fb = Feedback(user_id=uid, name=data.get("name","Anonymous"),
                  email=data.get("email",""), message=data["message"],
                  rating=max(1,min(5,int(data.get("rating",5)))))
    db.session.add(fb); db.session.commit()
    return jsonify({"success":True,"message":"Feedback submitted!"}),201
