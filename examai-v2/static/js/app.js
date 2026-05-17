/* ExamAI v2 — Complete Frontend JavaScript */
"use strict";

// ── Auth helpers ──────────────────────────────────────────────
const Auth = {
  getToken(){ return localStorage.getItem("examai_token"); },
  setToken(t){ localStorage.setItem("examai_token", t); },
  getUser(){ try{ return JSON.parse(localStorage.getItem("examai_user")||"null"); }catch{ return null; } },
  setUser(u){ localStorage.setItem("examai_user", JSON.stringify(u)); },
  clear(){ localStorage.removeItem("examai_token"); localStorage.removeItem("examai_user"); },
  isLoggedIn(){ return !!this.getToken(); },
  isAdmin(){ const u=this.getUser(); return u&&u.role==="admin"; },
  requireAuth(){ if(!this.isLoggedIn()){ window.location.href="/login"; return false; } return true; },
};

// ── API client ────────────────────────────────────────────────
const API = {
  async request(method, url, body=null, isForm=false){
    const headers = {};
    const token = Auth.getToken();
    if(token) headers["Authorization"] = "Bearer "+token;
    if(!isForm && body) headers["Content-Type"] = "application/json";
    const opts = { method, headers, credentials:"include" };
    if(body) opts.body = isForm ? body : JSON.stringify(body);
    try{
      const resp = await fetch(url, opts);
      const data = await resp.json().catch(()=>({}));
      if(resp.status===401 && !url.includes("/auth/login")){
        Auth.clear(); window.location.href="/login"; return;
      }
      return { ok: resp.ok, status: resp.status, data };
    }catch(e){
      return { ok:false, data:{ success:false, message: e.message } };
    }
  },
  get(url){ return this.request("GET", url); },
  post(url, body){ return this.request("POST", url, body); },
  put(url, body){ return this.request("PUT", url, body); },
  del(url){ return this.request("DELETE", url); },
};

// ── Toast ─────────────────────────────────────────────────────
function showToast(msg, type="info", ms=3500){
  const box = document.getElementById("toast-box");
  if(!box) return;
  const icons = { success:"✅", error:"❌", info:"ℹ️", warn:"⚠️" };
  const t = document.createElement("div");
  t.className = "toast " + type;
  t.innerHTML = `<span>${icons[type]||"ℹ️"}</span><span>${msg}</span>`;
  box.appendChild(t);
  setTimeout(()=>t.remove(), ms);
}

// ── Modal ─────────────────────────────────────────────────────
function openModal(id){ document.getElementById(id)?.classList.add("open"); }
function closeModal(id){ document.getElementById(id)?.classList.remove("open"); }
document.addEventListener("click", e=>{
  if(e.target.classList.contains("modal-overlay")) e.target.classList.remove("open");
});

// ── Sidebar user info ─────────────────────────────────────────
function loadUserInfo(){
  const u = Auth.getUser();
  if(!u) return;
  const name = document.getElementById("sidebar-user-name");
  const role = document.getElementById("sidebar-user-role");
  const av   = document.getElementById("sidebar-avatar");
  if(name) name.textContent = u.name || "User";
  if(role) role.textContent = (u.role||"teacher").charAt(0).toUpperCase()+(u.role||"teacher").slice(1);
  if(av)   av.textContent   = (u.name||"U").substring(0,2).toUpperCase();
}

// ── Auth: Login ───────────────────────────────────────────────
async function handleLogin(){
  const email    = document.getElementById("login-email")?.value.trim();
  const password = document.getElementById("login-pass")?.value.trim();
  const errEl    = document.getElementById("login-error");
  if(!email||!password){ if(errEl){errEl.textContent="Email and password required.";errEl.style.display="block";} return; }
  const btn = document.getElementById("login-btn");
  if(btn){ btn.textContent="Signing in…"; btn.disabled=true; }
  const res = await API.post("/auth/login", { email, password });
  if(btn){ btn.textContent="Sign In →"; btn.disabled=false; }
  if(res?.ok && res.data?.success){
    Auth.setToken(res.data.access_token);
    Auth.setUser(res.data.user);
    showToast("Welcome back, "+res.data.user.name+"! 👋","success");
    setTimeout(()=>{ window.location.href = res.data.user.role==="admin" ? "/admin-panel" : "/dashboard"; }, 600);
  } else {
    const msg = res?.data?.message || "Login failed.";
    if(errEl){ errEl.textContent=msg; errEl.style.display="block"; }
    showToast(msg,"error");
  }
}

// ── Auth: Register ────────────────────────────────────────────
async function handleRegister(){
  const name     = document.getElementById("reg-name")?.value.trim();
  const email    = document.getElementById("reg-email")?.value.trim();
  const password = document.getElementById("reg-pass")?.value.trim();
  const confirm  = document.getElementById("reg-confirm")?.value.trim();
  const dept     = document.getElementById("reg-dept")?.value.trim();
  const uni      = document.getElementById("reg-uni")?.value.trim();
  const errEl    = document.getElementById("reg-error");
  if(!name||!email||!password){ if(errEl){errEl.textContent="All fields required.";errEl.style.display="block";} return; }
  if(password!==confirm){ if(errEl){errEl.textContent="Passwords do not match.";errEl.style.display="block";} return; }
  if(password.length<6){ if(errEl){errEl.textContent="Password min 6 characters.";errEl.style.display="block";} return; }
  const btn = document.getElementById("reg-btn");
  if(btn){ btn.textContent="Creating…"; btn.disabled=true; }
  const res = await API.post("/auth/register", { name, email, password, department:dept, university:uni });
  if(btn){ btn.textContent="Create Account →"; btn.disabled=false; }
  if(res?.ok && res.data?.success){
    Auth.setToken(res.data.access_token);
    Auth.setUser(res.data.user);
    showToast("Account created! Welcome 🎉","success");
    setTimeout(()=>{ window.location.href="/dashboard"; }, 700);
  } else {
    const msg = res?.data?.message || "Registration failed.";
    if(errEl){ errEl.textContent=msg; errEl.style.display="block"; }
    showToast(msg,"error");
  }
}

// ── Auth: Logout ──────────────────────────────────────────────
async function handleLogout(){
  await API.post("/auth/logout");
  Auth.clear();
  showToast("Signed out.","info");
  setTimeout(()=>{ window.location.href="/"; }, 500);
}

// ── QBank: load list ──────────────────────────────────────────
async function loadQBank(){
  const search = document.getElementById("qb-search")?.value||"";
  const sub    = document.getElementById("qb-sub")?.value||"";
  const diff   = document.getElementById("qb-diff")?.value||"";
  const type   = document.getElementById("qb-type")?.value||"";
  const cnt    = document.getElementById("qb-count");
  const list   = document.getElementById("qbank-list");
  if(!list) return;
  const params = new URLSearchParams({per_page:100});
  if(search) params.append("search",search);
  if(sub)    params.append("subject",sub);
  if(diff)   params.append("difficulty",diff);
  if(type)   params.append("type",type);
  const res = await API.get("/qbank/?"+params);
  if(!res?.ok){ list.innerHTML="<div style='color:var(--danger);padding:20px'>Failed to load.</div>"; return; }
  const qs = res.data.questions||[];
  if(cnt) cnt.textContent = qs.length+" of "+(res.data.total||qs.length)+" questions";
  if(!qs.length){
    list.innerHTML="<div style='text-align:center;padding:40px;color:var(--muted)'>No questions match filters.</div>";
    return;
  }
  const diffCls = d => d==="Easy"?"tag-easy":d==="Hard"?"tag-hard":"tag-medium";
  list.innerHTML = qs.map(q=>`
    <div class="q-item">
      <div class="q-item-header">
        <p class="q-text">${esc(q.text.substring(0,200))}${q.text.length>200?"…":""}</p>
        <div class="q-item-actions">
          <button class="btn btn-outline btn-sm" onclick="openEditQ(${q.id})">Edit</button>
          <button class="btn btn-danger-sm btn-sm" onclick="deleteQ(${q.id})">Del</button>
        </div>
      </div>
      <div class="q-item-tags">
        <span class="tag tag-blue">${esc(q.subject)}</span>
        <span class="tag ${diffCls(q.difficulty)}">${esc(q.difficulty)}</span>
        <span class="tag tag-teal">${esc(q.q_type)}</span>
        <span class="tag" style="background:var(--cream);border:1px solid var(--border);color:var(--muted)">${esc(q.unit)}</span>
        ${q.topic?`<span class="tag tag-blue" style="background:rgba(44,62,122,.06)">${esc(q.topic)}</span>`:""}
        <span class="tag" style="background:var(--cream);border:1px solid var(--border);color:var(--muted)">${q.marks}M</span>
      </div>
    </div>`).join("");
}

let _editQId = null;
function openAddQ(){
  _editQId=null;
  const t=document.getElementById("modal-q-title");if(t)t.textContent="Add Question";
  const tx=document.getElementById("nq-text");if(tx)tx.value="";
  toggleMcqOpts();
  openModal("add-q-modal");
}
async function openEditQ(id){
  const res=await API.get("/qbank/"+id);
  if(!res?.ok){showToast("Failed","error");return;}
  const q=res.data.question;
  _editQId=id;
  const t=document.getElementById("modal-q-title");if(t)t.textContent="Edit Question";
  const set=(eid,val)=>{const el=document.getElementById(eid);if(el)el.value=val||"";};
  set("nq-text",q.text);set("nq-sub",q.subject);set("nq-diff",q.difficulty);
  set("nq-type",q.q_type);set("nq-topic",q.topic||"");set("nq-ans",q.answer||"");
  if(q.q_type==="MCQ"&&Array.isArray(q.options)){
    ["a","b","c","d"].forEach((l,i)=>set("opt-"+l, q.options[i]||""));
  }
  toggleMcqOpts();
  openModal("add-q-modal");
}
function toggleMcqOpts(){
  const t=document.getElementById("nq-type")?.value;
  const w=document.getElementById("mcq-opts-wrap");
  if(w) w.style.display=t==="MCQ"?"block":"none";
}
async function submitQ(){
  const text    = document.getElementById("nq-text")?.value.trim();
  const subject = document.getElementById("nq-sub")?.value;
  const q_type  = document.getElementById("nq-type")?.value;
  if(!text){showToast("Question text required.","error");return;}
  const options = q_type==="MCQ"
    ? ["opt-a","opt-b","opt-c","opt-d"].map(id=>document.getElementById(id)?.value||"")
    : [];
  const payload = {
    text, subject, q_type,
    difficulty: document.getElementById("nq-diff")?.value||"Medium",
    unit:       document.getElementById("nq-unit")?.value||"Unit 1",
    topic:      document.getElementById("nq-topic")?.value||"",
    answer:     document.getElementById("nq-ans")?.value||"",
    options,
  };
  const res = _editQId
    ? await API.put("/qbank/"+_editQId, payload)
    : await API.post("/qbank/add", payload);
  showToast(res?.data?.message||(_editQId?"Updated!":"Added!"), res?.ok?"success":"error");
  if(res?.ok){ closeModal("add-q-modal"); loadQBank(); }
}
async function deleteQ(id){
  if(!confirm("Delete this question?"))return;
  const res=await API.del("/qbank/"+id);
  showToast(res?.data?.message||"Deleted", res?.ok?"info":"error");
  if(res?.ok) loadQBank();
}

// ── Settings ──────────────────────────────────────────────────
async function loadSettings(){
  const res=await API.get("/auth/me");
  if(!res?.ok)return;
  const u=res.data.user;
  const set=(id,v)=>{const el=document.getElementById(id);if(el)el.value=v||"";};
  set("set-name",u.name);set("set-dept",u.department);
  set("set-uni",u.college_name||u.university);
  set("set-api-key",u.api_key);set("set-model",u.ai_model);
}
async function saveSettings(){
  const g=(id)=>document.getElementById(id)?.value?.trim()||"";
  const res=await API.put("/auth/profile",{
    name:g("set-name"), department:g("set-dept"),
    university:g("set-uni"), college_name:g("set-uni"),
    api_key:g("set-api-key"), ai_model:g("set-model"),
    current_password:g("set-curr-pass"), new_password:g("set-new-pass"),
  });
  showToast(res?.data?.message||"Saved!", res?.ok?"success":"error");
  if(res?.ok && res.data?.user){ Auth.setUser(res.data.user); loadUserInfo(); }
}

// ── Helpers ───────────────────────────────────────────────────
function esc(s){ return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

// ── Page auto-init ────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", ()=>{
  const path = window.location.pathname;
  const protected_pages = ["/dashboard","/generate","/syllabus-page","/history",
                            "/qbank","/analytics","/settings","/admin-panel"];
  if(protected_pages.some(p=>path.startsWith(p))){
    if(!Auth.requireAuth()) return;
    loadUserInfo();
  }
  if(path==="/settings")  loadSettings();
  if(path==="/qbank")     loadQBank();
  if(path==="/admin-panel"){ if(!Auth.isAdmin()){ window.location.href="/dashboard"; return; } }

  // QBank type toggle
  const nqt=document.getElementById("nq-type");
  if(nqt) nqt.addEventListener("change", toggleMcqOpts);
});
