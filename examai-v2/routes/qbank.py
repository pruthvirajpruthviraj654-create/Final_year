# routes/qbank.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from database import db
from models.question import Question

qbank_bp = Blueprint("qbank", __name__)

def _uid(): return int(get_jwt_identity())

@qbank_bp.route("/", methods=["GET"])
@jwt_required()
def list_q():
    uid = _uid()
    search = request.args.get("search","")
    sub    = request.args.get("subject","")
    diff   = request.args.get("difficulty","")
    qtype  = request.args.get("type","")
    page   = int(request.args.get("page",1))
    per    = int(request.args.get("per_page",20))
    q = Question.query.filter_by(user_id=uid)
    if search: q = q.filter(Question.text.ilike(f"%{search}%"))
    if sub:  q = q.filter_by(subject=sub)
    if diff: q = q.filter_by(difficulty=diff)
    if qtype:q = q.filter_by(q_type=qtype)
    pag = q.order_by(Question.created_at.desc()).paginate(page=page,per_page=per,error_out=False)
    return jsonify({"success":True,"questions":[x.to_dict() for x in pag.items],"total":pag.total}),200

@qbank_bp.route("/add", methods=["POST"])
@jwt_required()
def add_q():
    uid  = _uid()
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text: return jsonify({"success":False,"message":"Text required."}),400
    q = Question(user_id=uid, text=text,
        subject=data.get("subject","General"), difficulty=data.get("difficulty","Medium"),
        q_type=data.get("q_type","Short"), unit=data.get("unit","Unit 1"),
        topic=data.get("topic",""), marks=int(data.get("marks",2)),
        answer=data.get("answer",""),
        options=json.dumps(data.get("options",[])) if data.get("options") else "[]",
        bloom_level=data.get("bloom_level",""))
    db.session.add(q); db.session.commit()
    return jsonify({"success":True,"message":"Added!","question":q.to_dict()}),201

@qbank_bp.route("/<int:qid>", methods=["PUT"])
@jwt_required()
def update_q(qid):
    q = Question.query.filter_by(id=qid,user_id=_uid()).first()
    if not q: return jsonify({"success":False,"message":"Not found."}),404
    data = request.get_json(silent=True) or {}
    for f in ["text","subject","difficulty","q_type","unit","topic","marks","answer","bloom_level"]:
        if f in data: setattr(q,f,data[f])
    if "options" in data: q.options = json.dumps(data["options"])
    db.session.commit()
    return jsonify({"success":True,"message":"Updated!","question":q.to_dict()}),200

@qbank_bp.route("/<int:qid>", methods=["DELETE"])
@jwt_required()
def del_q(qid):
    q = Question.query.filter_by(id=qid,user_id=_uid()).first()
    if not q: return jsonify({"success":False,"message":"Not found."}),404
    db.session.delete(q); db.session.commit()
    return jsonify({"success":True,"message":"Deleted."}),200

@qbank_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    uid = _uid()
    qs  = Question.query.filter_by(user_id=uid).all()
    by_sub,by_diff,by_type = {},{},{}
    for q in qs:
        by_sub[q.subject]  = by_sub.get(q.subject,0)+1
        by_diff[q.difficulty]=by_diff.get(q.difficulty,0)+1
        by_type[q.q_type]  = by_type.get(q.q_type,0)+1
    return jsonify({"success":True,"total":len(qs),"by_subject":by_sub,"by_diff":by_diff,"by_type":by_type}),200
