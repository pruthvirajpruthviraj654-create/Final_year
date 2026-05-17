# routes/paper.py
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json

from database import db
from models.paper    import Paper
from models.user     import User
from models.syllabus import Syllabus
from services.ai_service  import generate_questions_ai
from services.pdf_service import generate_pdf
from services.difficulty_engine import compute_section_distribution

paper_bp = Blueprint("paper", __name__)

def _uid(): return int(get_jwt_identity())

@paper_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate():
    user = User.query.get(_uid())
    data = request.get_json(silent=True) or {}

    subject     = data.get("subject", "DBMS")
    exam_type   = data.get("exam_type", "End Semester Examination")
    difficulty  = data.get("difficulty", "Mixed")
    q_count     = int(data.get("q_count", 20))
    total_marks = int(data.get("total_marks", 100))
    duration    = data.get("duration", "3 Hours")
    bloom_level = data.get("bloom_level", "L2-Understand")
    units       = data.get("units", [])
    q_types     = data.get("q_types", ["MCQ","Short","Medium","Long"])
    marks_config= data.get("marks_config", [])
    syllabus_id = data.get("syllabus_id")
    topics      = data.get("topics", [])

    # Load syllabus context
    syllabus_context = ""
    if syllabus_id:
        syl = Syllabus.query.filter_by(id=syllabus_id, user_id=user.id).first()
        if syl:
            if not topics:
                topics = syl.get_topics()[:20]
            if not units:
                units = [u["unit_name"] for u in syl.get_units()]
            syllabus_context = syl.raw_text[:1500]

    if not marks_config:
        marks_config = compute_section_distribution(total_marks, q_types)

    result = generate_questions_ai(
        subject=subject, exam_type=exam_type, difficulty=difficulty,
        q_count=q_count, total_marks=total_marks, duration=duration,
        bloom_level=bloom_level, units=units, q_types=q_types,
        marks_config=marks_config, topics=topics,
        syllabus_context=syllabus_context,
        api_key=user.api_key, model=user.ai_model,
        college_name=user.college_name or "VisionCampus University",
        department=user.department or "Computer Science",
    )
    return jsonify({"success": True, "paper": result}), 200


@paper_bp.route("/save", methods=["POST"])
@jwt_required()
def save():
    user = User.query.get(_uid())
    data = request.get_json(silent=True) or {}
    p = Paper(
        user_id   = user.id,
        syllabus_id= data.get("syllabus_id"),
        title     = data.get("title") or f"{data.get('subject')} – {data.get('exam_type','Exam')}",
        subject   = data.get("subject",""),
        exam_type = data.get("exam_type","End Semester Examination"),
        difficulty= data.get("difficulty","Mixed"),
        bloom_level=data.get("bloom_level",""),
        units     = ", ".join(data.get("units",[])) if isinstance(data.get("units",[]),list) else "",
        selected_topics=json.dumps(data.get("topics",[])),
        total_marks=int(data.get("total_marks",100)),
        duration  = data.get("duration","3 Hours"),
        q_count   = int(data.get("q_count",20)),
        content   = data.get("content",""),
        paper_json= json.dumps(data.get("paper_json",{})),
        syllabus_based=bool(data.get("syllabus_id") or data.get("topics",[])),
        created_at= datetime.utcnow(),
    )
    db.session.add(p); db.session.commit()
    return jsonify({"success": True, "message": "Saved!", "paper_id": p.id, "paper": p.to_dict()}), 201


@paper_bp.route("/list", methods=["GET"])
@jwt_required()
def list_papers():
    uid = _uid()
    page = int(request.args.get("page", 1))
    per  = int(request.args.get("per_page", 10))
    sub  = request.args.get("subject","")
    q = Paper.query.filter_by(user_id=uid)
    if sub: q = q.filter_by(subject=sub)
    pag = q.order_by(Paper.created_at.desc()).paginate(page=page, per_page=per, error_out=False)
    return jsonify({"success": True, "papers": [p.to_dict() for p in pag.items],
                    "total": pag.total, "pages": pag.pages, "page": page}), 200


@paper_bp.route("/<int:pid>", methods=["GET"])
@jwt_required()
def get_paper(pid):
    p = Paper.query.filter_by(id=pid, user_id=_uid()).first()
    if not p: return jsonify({"success": False, "message": "Not found."}), 404
    return jsonify({"success": True, "paper": p.to_dict(include_content=True)}), 200


@paper_bp.route("/<int:pid>", methods=["DELETE"])
@jwt_required()
def delete_paper(pid):
    p = Paper.query.filter_by(id=pid, user_id=_uid()).first()
    if not p: return jsonify({"success": False, "message": "Not found."}), 404
    db.session.delete(p); db.session.commit()
    return jsonify({"success": True, "message": "Deleted."}), 200


@paper_bp.route("/<int:pid>/pdf", methods=["GET"])
@jwt_required()
def download_pdf(pid):
    user = User.query.get(_uid())
    p    = Paper.query.filter_by(id=pid, user_id=user.id).first()
    if not p: return jsonify({"success": False, "message": "Not found."}), 404
    data = p.to_dict(include_content=True)
    data["college_name"] = user.college_name or "VisionCampus University"
    data["department"]   = user.department or "Computer Science"
    path = generate_pdf(data)
    safe = "".join(c for c in p.title if c.isalnum() or c in " _-").strip().replace(" ","_")
    return send_file(path, as_attachment=True, download_name=f"{safe}_{pid}.pdf",
                     mimetype="application/pdf")


@paper_bp.route("/analytics", methods=["GET"])
@jwt_required()
def analytics():
    uid = _uid()
    papers = Paper.query.filter_by(user_id=uid).all()
    sub_cnt, diff_cnt, monthly = {}, {}, {}
    for p in papers:
        sub_cnt[p.subject] = sub_cnt.get(p.subject, 0) + 1
        d = (p.difficulty or "Mixed").lower()
        diff_cnt[d] = diff_cnt.get(d, 0) + 1
        mo = p.created_at.strftime("%b")
        monthly[mo] = monthly.get(mo, 0) + 1
    return jsonify({"success": True, "total_papers": len(papers),
                    "subject_counts": sub_cnt, "diff_counts": diff_cnt,
                    "monthly_counts": monthly}), 200
