from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import uuid
import json
import urllib.request
import os

app = Flask(__name__)
CORS(app)

# Optional: Configure Gemini API Key for Jago AI Chatbot
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

JAGO_SYSTEM_PROMPT = """You are **Jago**, the official AI assistant for the Unified Tribal Scholarship Platform — a government portal by the Ministry of Tribal Affairs, India.

## YOUR ROLE
You help students, nodal officers, admins, and bank/DBT users navigate the portal. You answer questions clearly, warmly, and accurately. Use emojis naturally. Keep answers concise but thorough. Use bullet points and bold text for readability. Always stay on-topic about the portal and tribal welfare scholarships.

## PORTAL OVERVIEW
This is a unified digital platform that consolidates all tribal (ST) scholarship schemes into one journey: Discover > Apply > Verify > Approve > Receive. It features:
- Combined Login/Register for 4 roles: Student, Nodal Officer, Admin, Bank/DBT
- Scholarship discovery and application
- Document Wallet with API integrations (DigiLocker, API Setu)
- Common Verification Layer (CVL) with exception/manual-review workflow
- Event-driven Notification Center
- DBT (Direct Benefit Transfer) payment simulation
- Grievance system
- Duplicate/integrity detection

## SCHOLARSHIP SCHEMES (5 total)

### 1. Pre-Matric Scholarship
- For: ST students in Class 9-10
- Income Limit: family income up to Rs 2.5 lakh/year
- Benefits: Tuition fee, maintenance allowance, book grant
- Duration: Renewable annually

### 2. Post-Matric Scholarship
- For: ST students from Class 11 onwards (graduation, post-graduation)
- Income Limit: family income up to Rs 2.5 lakh/year
- Benefits: Compulsory fees, maintenance allowance, study tour charges
- Duration: Full course, renewable yearly

### 3. Top Class Scholarship
- For: ST students in notified premier institutions (IITs, IIMs, NITs, AIIMS, etc.)
- Income Limit: family income up to Rs 6 lakh/year
- Benefits: Full tuition, living expenses, books, computer, thesis support
- Duration: Full course

### 4. National Fellowship for ST (NFST)
- For: M.Phil/Ph.D research scholars
- Eligibility: Must qualify NET/JRF by UGC. No income bar.
- Benefits: Rs 31,000/month (JRF), Rs 35,000/month (SRF), HRA, contingency grant
- Duration: Up to 5 years

### 5. National Overseas Scholarship (NOS)
- For: Masters/Ph.D abroad
- Income Limit: family income up to Rs 6 lakh/year
- Benefits: Full tuition, maintenance, airfare, visa, insurance
- Slots: ~20/year. Must be in top-500 QS/THE university. Age below 35.

## APPLICATION PROCESS
1. Register/Login as Student
2. Browse schemes in Scholarships tab
3. Click Apply, fill institution, course, academic year, income
4. Go to Document Wallet, fetch docs via DigiLocker API or API Setu
5. Submit application
6. Application enters CVL verification automatically
7. Track via dashboard, notifications

## DOCUMENT WALLET AND API INTEGRATION
- DigiLocker API: Fetches verified government documents (income cert, caste cert, Aadhaar). Pre-verified.
- API Setu: Connects to government departments for academic certificates, domicile, etc.
- Documents are fetched on-demand, verified in real-time, stored securely
- Reusable across multiple applications
- When docs are linked to a SUBMITTED application, it auto-advances to CVL_REVIEW

## COMMON VERIFICATION LAYER (CVL)
1. CVL Auto-Check: Automated cross-referencing of documents via APIs
2. Exception Handling: Mismatches/flags routed to manual review
3. Nodal Officer Review: Institution officer reviews and approves
4. Admin Sanction: Final administrative approval

Status Flow: SUBMITTED then CVL_REVIEW then VERIFIED then NODAL_APPROVED then SANCTIONED then DBT_PROCESSING then PAID

## DBT (DIRECT BENEFIT TRANSFER)
- After sanction, payment goes through PFMS
- NPCI Aadhaar Payment Bridge (APB) verifies Aadhaar-seeded bank account
- Funds credited directly; UTR reference generated
- Student must have Aadhaar linked to bank account
- To link: Visit bank branch, Fill Aadhaar seeding form, 2-3 days
- NPCI helpline: 1800-102-3837

## TIMELINES
- Application Review: 3-7 working days
- CVL Verification: 1-3 working days
- Nodal Approval: 5-10 working days
- Admin Sanction: 7-15 working days
- DBT Processing: 3-5 working days
- Total: approximately 3-6 weeks

## GRIEVANCE SYSTEM
- File from Grievances tab
- Provide subject + description
- Track via Notification Center
- Auto-escalation for unresolved issues

## NOTIFICATION CENTER
Real-time notifications for: submission, document updates, CVL changes, nodal decisions, payments (with UTR), grievance updates. Unread count on bell icon.

## PORTAL ROLES
- Student: Discover, apply, upload docs, track, receive payments
- Nodal Officer: Review applications, verification queues, approve/flag
- Admin: Monitor schemes, operations, audit, metrics, sanctions
- Bank/DBT: Process payment batches, transactions, reconciliation

## SECURITY
- Role-based access control
- OAuth 2.0 for API integrations
- Audit trail for all actions
- Privacy-first, no unauthorized data sharing
- Government IT security standards compliant

## DUPLICATE AND INTEGRITY
- Duplicate detection (same Aadhaar/student)
- Cross-scheme overlap prevention
- Document cross-verification against issuing authorities
- Income validation against government databases

## IMPORTANT RULES FOR YOU (JAGO)
- Never make up information not covered above
- If asked about something outside the portal, politely redirect
- Suggest relevant portal actions (e.g., Go to the Scholarships tab to apply)
- Be empathetic, many users are first-generation students from tribal communities
- Support in simple, clear language
- If user describes a problem, suggest specific steps AND offer to file a grievance
- Always end with a helpful follow-up suggestion
"""

jago_conversations = {}

users = {}
applications = {}
documents = {}
notifications = {}
grievances = {}
dbt_transactions = {}

DB_FILE = os.path.join(os.path.dirname(__file__), "database.json")

def load_db():
    global users, applications, documents, notifications, grievances, dbt_transactions
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                users = data.get("users", {})
                applications = data.get("applications", {})
                documents = data.get("documents", {})
                notifications = data.get("notifications", {})
                grievances = data.get("grievances", {})
                dbt_transactions = data.get("dbt_transactions", {})
        except:
            pass

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump({
            "users": users,
            "applications": applications,
            "documents": documents,
            "notifications": notifications,
            "grievances": grievances,
            "dbt_transactions": dbt_transactions
        }, f)

load_db()

SCHEMES = [
{"id":"pre-matric","name":"Pre-Matric Scholarship","level":"School","description":"Scholarship support for eligible ST students at pre-matric level."},
{"id":"post-matric","name":"Post-Matric Scholarship","level":"Higher Education","description":"Support for eligible ST students pursuing post-matric studies."},
{"id":"top-class","name":"Top Class Scholarship","level":"Higher Education","description":"Support for eligible ST students in notified premier institutions."},
{"id":"nfst","name":"National Fellowship (NFST)","level":"Research","description":"Fellowship support for eligible ST research scholars."},
{"id":"nos","name":"National Overseas Scholarship (NOS)","level":"Overseas","description":"Support for eligible ST students pursuing approved overseas study."},
]

def add_notification(user_id, title, message, kind="info"):
    n = {
        "id": str(uuid.uuid4()), "user_id": user_id, "title": title,
        "message": message, "kind": kind, "read": False,
        "created_at": datetime.utcnow().isoformat()
    }
    notifications.setdefault(user_id, []).insert(0, n)
    save_db()
    return n

# ── Jago AI Chat ──

@app.route("/api/jago/chat", methods=["POST"])
def jago_chat():
    payload = request.json
    user_msg = payload.get("message", "").strip()
    session_id = payload.get("session_id", "default")

    if not user_msg:
        return jsonify({"reply": "Please type a question and I'll help you!", "suggestions": []})

    if session_id not in jago_conversations:
        jago_conversations[session_id] = []
    
    jago_conversations[session_id].append({"role": "user", "parts": [{"text": user_msg}]})
    history = jago_conversations[session_id][-20:]

    if not GEMINI_API_KEY:
        reply = _offline_reply(user_msg)
    if any(w in m for w in ['secure', 'safe', 'privacy', 'protect']):
        return "Your data is protected with role-based access — only you, verifying officers, and admins on a need-to-know basis can see your records. Documents are fetched via DigiLocker/API Setu rather than stored as raw uploads, and all actions are logged for audit."
    if any(w in m for w in ['reject', 'denied', 'declined', 'fail']):
        return "If your application is rejected, you'll see the specific reason in your Notification Center and Application Status page — usually a document mismatch or an income/eligibility gap. You can fix the issue and reapply, or raise a Grievance if you believe it's an error."
        jago_conversations[session_id].append({"role": "model", "parts": [{"text": reply}]})
        return jsonify({
            "reply": reply,
            "suggestions": _get_suggestions(user_msg),
            "ai_powered": False
        })

    try:
        body = json.dumps({
            "system_instruction": {"parts": [{"text": JAGO_SYSTEM_PROMPT}]},
            "contents": history,
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "maxOutputTokens": 1024
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        reply = result["candidates"][0]["content"]["parts"][0]["text"]
        jago_conversations[session_id].append({"role": "model", "parts": [{"text": reply}]})

        return jsonify({
            "reply": reply,
            "ai_powered": True,
            "suggestions": _get_suggestions(user_msg)
        })

    except Exception as e:
        print(f"[Jago AI Error] {e}")
        return jsonify({
            "reply": f"I'm having trouble connecting right now. Please try again.\n\nError: {str(e)[:200]}",
            "suggestions": ["Which schemes can I apply for?", "How do I apply?", "How does DBT work?"],
            "ai_powered": False
        })

@app.route("/api/jago/set-key", methods=["POST"])
def jago_set_key():
    global GEMINI_API_KEY
    payload = request.json
    key = payload.get("key", "").strip()
    if key:
        GEMINI_API_KEY = key
        return jsonify({"ok": True, "message": "Gemini API key configured successfully!"})
    return jsonify({"ok": False, "message": "No key provided"}), 400

@app.route("/api/jago/status", methods=["GET"])
def jago_status():
    return jsonify({"ai_enabled": bool(GEMINI_API_KEY), "model": GEMINI_MODEL})

def _offline_reply(msg):
    """Rule-based fallback so Jago answers real questions with zero API-key setup.
    Swap in GEMINI_API_KEY any time for open-ended AI answers instead."""
    m = msg.lower()
    if any(w in m for w in ['hi', 'hello', 'hey', 'namaste']) and len(m) < 20:
        return "Hi! 👋 I'm Jago. Ask me about the 5 scholarship schemes, eligibility, how to apply, documents, verification, or DBT payments."
    if 'pre-matric' in m or 'pre matric' in m:
        return "📘 **Pre-Matric Scholarship**: For ST students in Class 9-10. Family income must be ≤ ₹2.5 lakh/year. Covers tuition, maintenance allowance and book grant, renewable annually."
    if 'post-matric' in m or 'post matric' in m:
        return "📗 **Post-Matric Scholarship**: For ST students from Class 11 onward (including graduation/PG). Family income ≤ ₹2.5 lakh/year. Covers compulsory fees + maintenance allowance, renewable each year."
    if 'top class' in m or 'top-class' in m:
        return "📙 **Top Class Scholarship**: For ST students admitted to premier institutes (IITs, IIMs, NITs, AIIMS). Family income ≤ ₹6 lakh/year. Covers full tuition, living expenses, books and computer."
    if 'nfst' in m or 'fellowship' in m:
        return "📕 **National Fellowship (NFST)**: For M.Phil/PhD scholars who qualify NET/JRF. No income bar. ₹31,000/month (JRF) or ₹35,000/month (SRF), plus HRA and contingency, for up to 5 years."
    if 'nos' in m or 'overseas' in m:
        return "📔 **National Overseas Scholarship (NOS)**: For Masters/PhD abroad. Family income ≤ ₹6 lakh/year, age below 35, admission to a top-500 QS/THE university. ~20 slots/year — covers tuition, maintenance, airfare, visa and insurance."
    if any(w in m for w in ['scheme', 'scholarship', 'which', 'list', 'available']) and 'apply' not in m:
        return "There are 5 schemes: **Pre-Matric** (Class 9-10), **Post-Matric** (Class 11+), **Top Class** (premier institutes), **NFST** (M.Phil/PhD), and **NOS** (study abroad). Ask me about any one for its eligibility and benefits!"
    if any(w in m for w in ['eligib', 'criteria', 'qualify', 'income']):
        return "Eligibility depends on the scheme: Pre/Post-Matric need family income ≤ ₹2.5 lakh/year; Top Class and NOS need ≤ ₹6 lakh/year; NFST needs NET/JRF qualification with no income limit. Which scheme are you asking about?"
    if any(w in m for w in ['apply', 'application', 'submit', 'form']):
        return "**To apply:** 1) Register/login as Student 2) Go to Scholarships tab and pick a scheme 3) Click Apply, fill institution/course/income 4) Go to Document Wallet and fetch docs via DigiLocker/API Setu 5) Submit. Your application then enters CVL verification automatically."
    if any(w in m for w in ['document', 'upload', 'digilocker', 'certificate', 'setu']):
        return "Your Document Wallet pulls verified documents via **DigiLocker** (Aadhaar, income, caste certificates) and **API Setu** (academic/domicile records) — fetched once, reused across all 5 schemes. No repeat uploads needed."
    if any(w in m for w in ['verif', 'cvl', 'nodal', 'review']):
        return "**CVL (Common Verification Layer)** auto cross-checks your documents against source systems. Mismatches get flagged for manual review by a Nodal Officer, then final Admin sanction. Flow: SUBMITTED → CVL_REVIEW → VERIFIED → NODAL_APPROVED → SANCTIONED."
    if any(w in m for w in ['dbt', 'payment', 'money', 'transfer', 'bank']):
        return "After sanction, payment goes through **PFMS** and the **NPCI Aadhaar Payment Bridge** to your Aadhaar-seeded bank account — a UTR reference is generated once paid. If your Aadhaar isn't seeded yet, visit your bank branch (takes 2-3 days)."
    if any(w in m for w in ['grievance', 'complaint', 'problem', 'stuck', 'help']):
        return "You can file a grievance from the Grievances tab with a subject and description — you'll get updates in your Notification Center, and it auto-escalates if unresolved."
    return "I can help with the 5 scholarship schemes, eligibility, how to apply, documents, verification (CVL), or DBT payments — what would you like to know? (For open-ended AI answers, add a free Gemini key via the setup button above.)"

def _get_suggestions(msg):
    lower = msg.lower()
    if any(w in lower for w in ['scheme', 'scholarship', 'which', 'list', 'available']):
        return ['What is the eligibility criteria?', 'How do I apply?', 'Tell me about Post-Matric']
    if any(w in lower for w in ['eligib', 'criteria', 'qualify', 'income']):
        return ['How do I apply?', 'What documents are needed?', 'Tell me about NFST']
    if any(w in lower for w in ['apply', 'application', 'submit', 'form']):
        return ['What documents are needed?', 'How long does it take?', 'How to track status?']
    if any(w in lower for w in ['document', 'upload', 'digilocker', 'certificate']):
        return ['What happens after verification?', 'Is my data secure?', 'What if rejected?']
    if any(w in lower for w in ['verif', 'cvl', 'nodal', 'review']):
        return ['How long does verification take?', 'What if it fails?', 'How does DBT work?']
    if any(w in lower for w in ['dbt', 'payment', 'money', 'transfer', 'bank']):
        return ['What if payment fails?', 'How to link Aadhaar?', 'How to track?']
    if any(w in lower for w in ['grievance', 'complaint', 'problem', 'stuck', 'help']):
        return ['How to track my application?', 'What if payment fails?', 'Contact support']
    return ['Which schemes can I apply for?', 'How do I apply?', 'How does DBT work?']

@app.route("/api/setu/cvl-verify", methods=["POST"])
def cvl_verify():
    import random
    payload = request.json
    results = []
    for _ in range(8):
        results.append({"status": "VERIFIED", "time_ms": int(80 + random.random() * 200)})
    return jsonify({"status": "SUCCESS", "results": results})

@app.route("/api/setu/api-status", methods=["GET"])
def api_status():
    apis = [
        {
            "name": "UIDAI Aadhaar eKYC", "icon": "🆔", "provider": "API Setu", "method": "POST",
            "endpoint": "https://apisetu.gov.in/uidai/v2.0/ekyc", "status": "Connected", "latency": "42ms",
            "req": "{\n  \"aadhaar_number\": \"XXXX-XXXX-1234\",\n  \"consent\": \"Y\"\n}",
            "res": "{\n  \"status\": \"SUCCESS\",\n  \"data\": {\"name\": \"...\", \"dob\": \"...\"}\n}"
        },
        {
            "name": "State eTaal", "icon": "📜", "provider": "API Setu", "method": "POST",
            "endpoint": "https://apisetu.gov.in/etaal/v1/certificate", "status": "Connected", "latency": "85ms",
            "req": "{\n  \"cert_no\": \"ST/2026/99812\",\n  \"state_code\": \"OR\"\n}",
            "res": "{\n  \"valid\": true,\n  \"category\": \"ST\",\n  \"issued_to\": \"...\"\n}"
        },
        {
            "name": "Duplicate Check Engine", "icon": "🔍", "provider": "Custom Pipeline", "method": "POST",
            "endpoint": "https://internal.tribal.gov.in/api/v1/integrity/check", "status": "Connected", "latency": "12ms",
            "req": "{\n  \"aadhaar_hash\": \"a8f5f167f...\",\n  \"scheme_id\": \"post-matric\"\n}",
            "res": "{\n  \"overlap_detected\": false,\n  \"active_schemes\": []\n}"
        },
        {
            "name": "UDISE+ Registry", "icon": "🏫", "provider": "API Setu", "method": "GET",
            "endpoint": "https://apisetu.gov.in/moe/udise/v1/student/{id}", "status": "Connected", "latency": "55ms",
            "req": "Headers:\n  Authorization: Bearer <token>\n  X-API-KEY: <key>",
            "res": "{\n  \"enrolled\": true,\n  \"institution_code\": \"211...\"\n}"
        },
        {
            "name": "PFMS / NPCI Bridge", "icon": "🏦", "provider": "API Setu", "method": "POST",
            "endpoint": "https://apisetu.gov.in/npci/apb/v3/status", "status": "Connected", "latency": "140ms",
            "req": "{\n  \"aadhaar\": \"XXXX-XXXX-1234\",\n  \"amount\": 45000\n}",
            "res": "{\n  \"seeded\": true,\n  \"bank_iin\": \"607152\"\n}"
        },
        {
            "name": "Jago AI Vector DB", "icon": "🤖", "provider": "Custom Pipeline", "method": "POST",
            "endpoint": "https://internal.tribal.gov.in/api/v1/jago/rag", "status": "Connected", "latency": "450ms",
            "req": "{\n  \"query\": \"eligibility for top class\",\n  \"vector_search\": true\n}",
            "res": "{\n  \"answer\": \"...\",\n  \"sources\": [\"rules_2026.pdf\"]\n}"
        }
    ]
    return jsonify({"apis": apis})

# ── Portal endpoints ──

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "environment": "demo"})

@app.route("/api/auth", methods=["POST"])
def auth():
    payload = request.json
    mode = payload.get("mode")
    role = payload.get("role")
    identifier = payload.get("identifier")
    if mode == "register":
        if not identifier:
            return jsonify({"detail": "Mobile number or email is required."}), 400
        if role != "student":
            return jsonify({"detail": "Only student self-registration is enabled."}), 403
        
        # Check if already registered
        for uid,u in users.items():
            if u["identifier"] == identifier and u["role"] == "student":
                return jsonify({"detail": "An account with this email/mobile already exists. Please login."}), 400

        uid = "STU-" + uuid.uuid4().hex[:8].upper()
        users[uid] = {"id":uid, "name":payload.get("name") or "Student", "identifier":identifier, "role":"student"}
        add_notification(uid, "Welcome to the Scholarship Portal", "Your student account was created successfully.", "success")
        save_db()
        return jsonify({"ok": True, "user": users[uid], "message":"Registration successful"})
        
    for uid,u in users.items():
        if u["identifier"] == identifier and u["role"] == role:
            return jsonify({"ok": True, "user":u, "message":"Login successful"})
            
    demo = {"nodal":"NODAL-DEMO","admin":"ADMIN-DEMO","bank":"DBT-DEMO"}
    if role in demo:
        uid=demo[role]
        if uid not in users:
            users[uid] = {"id":uid, "name":role.title()+" Demo", "identifier":identifier, "role":role}
            save_db()
        return jsonify({"ok":True,"user":users[uid],"message":"Demo login successful"})
        
    return jsonify({"detail": "Account not found. Please register."}), 401

@app.route("/api/schemes", methods=["GET"])
def schemes():
    return jsonify(SCHEMES)

@app.route("/api/students/<student_id>/dashboard", methods=["GET"])
def dashboard(student_id):
    apps=[a for a in applications.values() if a["student_id"]==student_id]
    docs=[d for d in documents.values() if d["student_id"]==student_id]
    return jsonify({"applications":apps, "documents":docs, "notifications":notifications.get(student_id,[]),
        "journey": ["Discover","Apply","Document Wallet","CVL Verification","Nodal Review","Approval","DBT","Received"]})

@app.route("/api/applications", methods=["POST", "GET"])
def applications_endpoint():
    if request.method == "POST":
        payload = request.json
        aid="APP-"+uuid.uuid4().hex[:10].upper()
        status = payload.get("status", "SUBMITTED")
        exc = payload.get("exception_reason", "")
        a={**payload, "id":aid, "status":status, "exception_reason":exc, "created_at":datetime.utcnow().isoformat(),
            "status_history":[{"status":status,"at":datetime.utcnow().isoformat(),"remarks":exc or "Application submitted"}], "cvl_status":"PENDING"}
        applications[aid]=a
        add_notification(payload.get("student_id"),"Application submitted",f"{aid} has been submitted successfully.","success")
        if exc:
            add_notification(payload.get("student_id"),"Manual Review Required",f"Flagged for manual review: {exc}","warning")
        else:
            add_notification(payload.get("student_id"),"Verification started","Your application has entered the verification workflow.","info")
        save_db()
        return jsonify(a)
    else:
        role = request.args.get("role", "student")
        student_id = request.args.get("student_id")
        vals=list(applications.values())
        if role=="student" and student_id:
            vals=[a for a in vals if a["student_id"]==student_id]
        return jsonify(vals)

@app.route("/api/applications/<app_id>/status", methods=["PATCH"])
def update_application(app_id):
    payload = request.json
    if app_id not in applications: return jsonify({"detail":"Application not found"}), 404
    a=applications[app_id]
    status = payload.get("status")
    remarks = payload.get("remarks", "")
    a["status"] = status
    a["status_history"].append({"status":status,"at":datetime.utcnow().isoformat(),"remarks":remarks})
    uid=a["student_id"]
    title_map={"CVL_REVIEW":"CVL verification requires review","VERIFIED":"Verification completed",
        "NODAL_APPROVED":"Nodal verification completed","SANCTIONED":"Scholarship sanctioned",
        "DBT_PROCESSING":"DBT payment processing started","PAID":"Scholarship payment successful","PAYMENT_FAILED":"Scholarship payment failed"}
    add_notification(uid,title_map.get(status,"Application status updated"),remarks or f"Your application is now {status}.","warning" if "FAILED" in status else "info")
    save_db()
    return jsonify(a)

@app.route("/api/documents", methods=["POST"])
def add_document():
    payload = request.json
    did = "DOC-"+uuid.uuid4().hex[:8].upper()
    source = payload.get("source", "")
    is_api = any(source.startswith(prefix) for prefix in ("DigiLocker", "UDISE+", "UDID", "API Setu", "UIDAI", "NTA"))
    d={**payload, "id":did,"status":"VERIFIED" if is_api else "PENDING","created_at":datetime.utcnow().isoformat()}
    documents[did]=d
    add_notification(payload.get("student_id"),"Document Wallet updated",f"{payload.get('name')} is now available in your wallet.","success")
    save_db()
    return jsonify(d)

@app.route("/api/documents/<student_id>", methods=["GET"])
def get_documents(student_id):
    return jsonify([d for d in documents.values() if d["student_id"]==student_id])

@app.route("/api/notifications/<user_id>", methods=["GET"])
def get_notifications(user_id):
    return jsonify(notifications.get(user_id,[]))

@app.route("/api/notifications/<notification_id>/read", methods=["PATCH"])
def read_notification(notification_id):
    for vals in notifications.values():
        for n in vals:
            if n["id"]==notification_id:
                n["read"]=True
                save_db()
                return jsonify(n)
    return jsonify({"detail":"Notification not found"}), 404

@app.route("/api/grievances", methods=["POST", "GET"])
def grievances_endpoint():
    if request.method == "POST":
        payload = request.json
        gid="GRV-"+uuid.uuid4().hex[:8].upper()
        g={**payload, "id":gid,"status":"SUBMITTED","created_at":datetime.utcnow().isoformat()}
        grievances[gid]=g
        add_notification(payload.get("student_id"),"Grievance submitted",f"Your grievance {gid} was received.","success")
        save_db()
        return jsonify(g)
    else:
        return jsonify(list(grievances.values()))

@app.route("/api/dbt/transactions", methods=["GET"])
def dbt():
    return jsonify(list(dbt_transactions.values()))

@app.route("/api/dbt/<app_id>/process", methods=["POST"])
def process_dbt(app_id):
    payload = request.json or {}
    if app_id not in applications: return jsonify({"detail":"Application not found"}), 404
    a=applications[app_id]
    if a["status"] not in ("SANCTIONED","DBT_PROCESSING"):
        return jsonify({"detail":"Application must be sanctioned before DBT processing."}), 400
    txid="TXN-"+uuid.uuid4().hex[:10].upper()
    utr_val = payload.get("utr") or ("DEMO"+uuid.uuid4().hex[:12].upper())
    tx={"id":txid,"application_id":app_id,"student_id":a["student_id"],"status":"SUCCESS","utr":utr_val,"created_at":datetime.utcnow().isoformat()}
    dbt_transactions[txid]=tx
    a["status"]="PAID"
    a["status_history"].append({"status":"PAID","at":datetime.utcnow().isoformat(),"remarks":"Demo DBT transaction completed"})
    add_notification(a["student_id"],"Payment successful",f"Your scholarship payment was completed. UTR: {tx['utr']}","success")
    save_db()
    return jsonify(tx)

@app.route("/api/admin/metrics", methods=["GET"])
def metrics():
    return jsonify({"applications":len(applications),"documents":len(documents),"grievances":len(grievances),
        "notifications":sum(len(v) for v in notifications.values()),"payments":len(dbt_transactions),
        "manual_review":sum(1 for a in applications.values() if a["status"]=="CVL_REVIEW")})

if __name__ == "__main__":
    print("\n[Jago AI]", "Gemini key configured" if GEMINI_API_KEY else "No key - set GEMINI_API_KEY or use the setup button in Jago")
    print("[Server] Starting API on http://localhost:8000\n")
    app.run(host="127.0.0.1", port=8000, debug=True)