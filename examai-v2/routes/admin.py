# routes/admin.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models.user import User
from models.paper import Paper
from models.question import Question
from models.feedback import Feedback
from models.syllabus import Syllabus

admin_bp = Blueprint("admin", __name__)

def _require_admin():
    uid  = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or user.role != "admin":
        return None, (jsonify({"success":False,"message":"Admin access required."}),403)
    return user, None

@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    _, err = _require_admin()
    if err: return err
    return jsonify({"success":True,
        "total_users":User.query.count(),
        "total_papers":Paper.query.count(),
        "total_questions":Question.query.count(),
        "total_feedbacks":Feedback.query.count(),
        "total_syllabi":Syllabus.query.count(),
        "active_users":User.query.filter_by(is_active=True).count()}),200

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def all_users():
    _, err = _require_admin()
    if err: return err
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"success":True,"users":[u.to_dict() for u in users]}),200

@admin_bp.route("/users/<int:uid>/toggle", methods=["PUT"])
@jwt_required()
def toggle_user(uid):
    _, err = _require_admin()
    if err: return err
    u = User.query.get(uid)
    if not u: return jsonify({"success":False,"message":"Not found."}),404
    u.is_active = not u.is_active
    db.session.commit()
    return jsonify({"success":True,"message":f"User {'activated' if u.is_active else 'deactivated'}."}),200

@admin_bp.route("/users/<int:uid>", methods=["DELETE"])
@jwt_required()
def delete_user(uid):
    admin, err = _require_admin()
    if err: return err
    if admin.id == uid:
        return jsonify({"success":False,"message":"Cannot delete own account."}),400
    u = User.query.get(uid)
    if not u: return jsonify({"success":False,"message":"Not found."}),404
    db.session.delete(u); db.session.commit()
    return jsonify({"success":True,"message":"User deleted."}),200

@admin_bp.route("/papers", methods=["GET"])
@jwt_required()
def all_papers():
    _, err = _require_admin()
    if err: return err
    papers = Paper.query.order_by(Paper.created_at.desc()).limit(100).all()
    return jsonify({"success":True,"papers":[p.to_dict() for p in papers]}),200

@admin_bp.route("/feedback", methods=["GET"])
@jwt_required()
def all_feedback():
    _, err = _require_admin()
    if err: return err
    fbs = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return jsonify({"success":True,"feedbacks":[f.to_dict() for f in fbs]}),200
