# ============================================================
# routes/syllabus.py — Syllabus Upload, Parse, Manage
# ============================================================
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os, json

from database import db
from models.user     import User
from models.syllabus import Syllabus, SyllabusTopic
from services.syllabus_engine import (extract_text_from_file, analyze_syllabus,
                                       get_subject_default_topics)

syllabus_bp = Blueprint("syllabus", __name__)

ALLOWED_EXT = {"pdf", "txt", "docx", "doc"}

def _uid(): return int(get_jwt_identity())
def _ext(fn): return fn.rsplit(".", 1)[-1].lower() if "." in fn else ""


# ── Upload + parse syllabus file ──────────────────────────────
@syllabus_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload():
    uid     = _uid()
    subject = (request.form.get("subject") or "").strip()
    if not subject:
        return jsonify({"success": False, "message": "Subject is required."}), 400

    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"success": False, "message": "No file uploaded."}), 400

    ext = _ext(file.filename)
    if ext not in ALLOWED_EXT:
        return jsonify({"success": False,
                        "message": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXT)}"}), 400

    # Save file
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "static/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filename  = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, f"{uid}_{filename}")
    file.save(file_path)

    # Extract text
    raw_text = extract_text_from_file(file_path, ext)
    if not raw_text.strip():
        return jsonify({"success": False, "message": "Could not extract text from file."}), 422

    # Analyse
    analysis = analyze_syllabus(raw_text, subject)
    return _save_and_return(uid, subject, raw_text, filename, ext, analysis)


# ── Manual text entry ─────────────────────────────────────────
@syllabus_bp.route("/manual", methods=["POST"])
@jwt_required()
def manual():
    uid     = _uid()
    data    = request.get_json(silent=True) or {}
    subject = (data.get("subject") or "").strip()
    text    = (data.get("text") or "").strip()
    if not subject or not text:
        return jsonify({"success": False, "message": "Subject and text are required."}), 400

    analysis = analyze_syllabus(text, subject)
    return _save_and_return(uid, subject, text, "manual_entry.txt", "manual", analysis)


# ── Use subject default topics (no upload) ────────────────────
@syllabus_bp.route("/default", methods=["POST"])
@jwt_required()
def use_default():
    uid     = _uid()
    data    = request.get_json(silent=True) or {}
    subject = (data.get("subject") or "").strip()
    if not subject:
        return jsonify({"success": False, "message": "Subject is required."}), 400

    analysis = get_subject_default_topics(subject)
    if not analysis["units"]:
        return jsonify({"success": False, "message": f"No built-in topics for {subject}."}), 404

    raw_text = f"Default syllabus for {subject}"
    return _save_and_return(uid, subject, raw_text, "default", "default", analysis)


# ── Helper: save Syllabus + Topics to DB ─────────────────────
def _save_and_return(uid, subject, raw_text, filename, file_type, analysis):
    units        = analysis.get("units", [])
    topics_flat  = analysis.get("topics_flat", [])
    keywords     = analysis.get("keywords", [])

    syl = Syllabus(
        user_id     = uid,
        subject     = subject,
        title       = f"{subject} Syllabus",
        raw_text    = raw_text[:5000],
        file_name   = filename,
        file_type   = file_type,
        units_json  = json.dumps(units),
        topics_json = json.dumps(topics_flat),
        keywords_json=json.dumps(keywords),
    )
    db.session.add(syl)
    db.session.flush()

    # Save individual topics
    for unit_data in units:
        unit_name   = unit_data.get("unit_name", "Unit 1")
        unit_number = 1
        m = __import__("re").search(r"\d+", unit_name)
        if m: unit_number = int(m.group())
        for topic in unit_data.get("topics", []):
            t = SyllabusTopic(
                syllabus_id = syl.id,
                unit_number = unit_number,
                unit_name   = unit_name,
                topic       = topic,
                keywords    = json.dumps([w.lower() for w in topic.split() if len(w) > 3]),
            )
            db.session.add(t)

    db.session.commit()
    return jsonify({
        "success":      True,
        "message":      f"Syllabus processed. {len(topics_flat)} topics extracted.",
        "syllabus":     syl.to_dict(),
        "units":        units,
        "topics":       topics_flat,
        "keywords":     keywords,
        "topic_count":  len(topics_flat),
        "unit_count":   len(units),
    }), 201


# ── List syllabi for current user ─────────────────────────────
@syllabus_bp.route("/list", methods=["GET"])
@jwt_required()
def list_syllabi():
    uid     = _uid()
    subject = request.args.get("subject", "")
    q = Syllabus.query.filter_by(user_id=uid)
    if subject: q = q.filter_by(subject=subject)
    syllabi = q.order_by(Syllabus.created_at.desc()).all()
    return jsonify({"success": True,
                    "syllabi": [s.to_dict() for s in syllabi],
                    "total": len(syllabi)}), 200


# ── Get one syllabus with topics ──────────────────────────────
@syllabus_bp.route("/<int:syl_id>", methods=["GET"])
@jwt_required()
def get_syllabus(syl_id):
    uid = _uid()
    syl = Syllabus.query.filter_by(id=syl_id, user_id=uid).first()
    if not syl:
        return jsonify({"success": False, "message": "Syllabus not found."}), 404
    topics = [t.to_dict() for t in syl.topics.all()]
    d = syl.to_dict()
    d["all_topics"] = topics
    return jsonify({"success": True, "syllabus": d}), 200


# ── Delete syllabus ───────────────────────────────────────────
@syllabus_bp.route("/<int:syl_id>", methods=["DELETE"])
@jwt_required()
def delete_syllabus(syl_id):
    uid = _uid()
    syl = Syllabus.query.filter_by(id=syl_id, user_id=uid).first()
    if not syl:
        return jsonify({"success": False, "message": "Not found."}), 404
    db.session.delete(syl)
    db.session.commit()
    return jsonify({"success": True, "message": "Syllabus deleted."}), 200


# ── Get topics for a syllabus (unit-filtered) ─────────────────
@syllabus_bp.route("/<int:syl_id>/topics", methods=["GET"])
@jwt_required()
def get_topics(syl_id):
    uid  = _uid()
    syl  = Syllabus.query.filter_by(id=syl_id, user_id=uid).first()
    if not syl:
        return jsonify({"success": False, "message": "Not found."}), 404
    unit = request.args.get("unit", "")
    q = syl.topics
    if unit:
        q = q.filter(SyllabusTopic.unit_name.ilike(f"%{unit}%"))
    topics = [t.to_dict() for t in q.all()]
    return jsonify({"success": True, "topics": topics, "count": len(topics)}), 200
