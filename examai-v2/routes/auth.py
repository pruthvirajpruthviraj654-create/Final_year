# routes/auth.py — JWT Authentication
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, set_access_cookies, set_refresh_cookies, unset_jwt_cookies)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database import db
from models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name, email = (data.get("name") or "").strip(), (data.get("email") or "").strip().lower()
    password   = (data.get("password") or "").strip()
    if not name or not email or len(password) < 6:
        return jsonify({"success": False, "message": "All fields required. Password min 6 chars."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Email already registered."}), 409
    user = User(name=name, email=email,
                password_hash=generate_password_hash(password),
                department=data.get("department",""), university=data.get("university",""),
                college_name=data.get("university",""), role="teacher")
    db.session.add(user); db.session.commit()
    at = create_access_token(identity=str(user.id))
    rt = create_refresh_token(identity=str(user.id))
    resp = jsonify({"success": True, "message": f"Welcome, {user.name}!",
                    "access_token": at, "refresh_token": rt, "user": user.to_dict()})
    set_access_cookies(resp, at); set_refresh_cookies(resp, rt)
    return resp, 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email, password = (data.get("email") or "").strip().lower(), (data.get("password") or "").strip()
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required."}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"success": False, "message": "Invalid credentials."}), 401
    if not user.is_active:
        return jsonify({"success": False, "message": "Account deactivated."}), 403
    user.last_login = datetime.utcnow(); db.session.commit()
    at = create_access_token(identity=str(user.id))
    rt = create_refresh_token(identity=str(user.id))
    resp = jsonify({"success": True, "message": f"Welcome back, {user.name}!",
                    "access_token": at, "refresh_token": rt, "user": user.to_dict()})
    set_access_cookies(resp, at); set_refresh_cookies(resp, rt)
    return resp, 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    resp = jsonify({"success": True, "message": "Logged out."})
    unset_jwt_cookies(resp); return resp, 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user: return jsonify({"success": False, "message": "Not found."}), 404
    return jsonify({"success": True, "user": user.to_dict(include_sensitive=True)}), 200

@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = User.query.get(int(get_jwt_identity()))
    if not user: return jsonify({"success": False, "message": "Not found."}), 404
    data = request.get_json(silent=True) or {}
    for field in ["name","department","university","college_name","api_key","ai_model"]:
        if field in data: setattr(user, field, data[field].strip() if isinstance(data[field], str) else data[field])
    new_pass = (data.get("new_password") or "").strip()
    if new_pass:
        if not check_password_hash(user.password_hash, data.get("current_password","")):
            return jsonify({"success": False, "message": "Current password incorrect."}), 401
        user.password_hash = generate_password_hash(new_pass)
    db.session.commit()
    return jsonify({"success": True, "message": "Profile updated!", "user": user.to_dict(include_sensitive=True)}), 200
