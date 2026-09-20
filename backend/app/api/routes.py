from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter()

users = {}
applications = {}
documents = {}
notifications = {}
grievances = {}
dbt_transactions = {}

SCHEMES = [
{"id":"pre-matric","name":"Pre-Matric Scholarship","level":"School","description":"Scholarship support for eligible ST students at pre-matric level."},
{"id":"post-matric","name":"Post-Matric Scholarship","level":"Higher Education","description":"Support for eligible ST students pursuing post-matric studies."},
{"id":"top-class","name":"Top Class Scholarship","level":"Higher Education","description":"Support for eligible ST students in notified premier institutions."},
{"id":"nfst","name":"National Fellowship (NFST)","level":"Research","description":"Fellowship support for eligible ST research scholars."},
{"id":"nos","name":"National Overseas Scholarship (NOS)","level":"Overseas","description":"Support for eligible ST students pursuing approved overseas study."},
]

class Auth(BaseModel):
    mode: str
    role: str
    identifier: str
    password: Optional[str] = None
    name: Optional[str] = None

class ApplicationCreate(BaseModel):
    student_id: str
    scheme_id: str
    institution: str
    course: str
    academic_year: str
    annual_income: float = Field(ge=0)
    category: str = "ST"

class DocumentCreate(BaseModel):
    student_id: str
    name: str
    source: str
    document_type: str

class StatusUpdate(BaseModel):
    status: str
    remarks: Optional[str] = ""

class GrievanceCreate(BaseModel):
    student_id: str
    subject: str
    description: str

def add_notification(user_id, title, message, kind="info"):
    n = {
        "id": str(uuid.uuid4()), "user_id": user_id, "title": title,
        "message": message, "kind": kind, "read": False,
        "created_at": datetime.utcnow().isoformat()
    }
    notifications.setdefault(user_id, []).insert(0, n)
    return n

@router.post("/auth")
def auth(payload: Auth):
    if payload.mode == "register":
        if payload.role != "student":
            raise HTTPException(403, "Only student self-registration is enabled in this prototype.")
        uid = "STU-" + uuid.uuid4().hex[:8].upper()
        users[uid] = {"id":uid, "name":payload.name or "Student", "identifier":payload.identifier, "role":"student"}
        add_notification(uid, "Welcome to the Scholarship Portal", "Your student account was created successfully.", "success")
        return {"ok": True, "user": users[uid], "message":"Registration successful"}
    for uid,u in users.items():
        if u["identifier"] == payload.identifier and u["role"] == payload.role:
            return {"ok": True, "user":u, "message":"Login successful"}
    # Demo accounts
    demo = {"student":"STU-DEMO","nodal":"NODAL-DEMO","admin":"ADMIN-DEMO","bank":"DBT-DEMO"}
    if payload.role in demo:
        uid=demo[payload.role]
        users.setdefault(uid, {"id":uid, "name":payload.role.title()+" Demo", "identifier":payload.identifier, "role":payload.role})
        return {"ok":True,"user":users[uid],"message":"Demo login successful"}
    raise HTTPException(401, "Account not found. Register as a student or use a demo role.")

@router.get("/schemes")
def schemes():
    return SCHEMES

@router.get("/students/{student_id}/dashboard")
def dashboard(student_id: str):
    apps=[a for a in applications.values() if a["student_id"]==student_id]
    docs=[d for d in documents.values() if d["student_id"]==student_id]
    return {
        "applications":apps, "documents":docs,
        "notifications":notifications.get(student_id,[]),
        "journey": ["Discover","Apply","Document Wallet","CVL Verification","Nodal Review","Approval","DBT","Received"]
    }

@router.post("/applications")
def create_application(payload: ApplicationCreate):
    aid="APP-"+uuid.uuid4().hex[:10].upper()
    a=payload.model_dump() | {
        "id":aid, "status":"SUBMITTED", "created_at":datetime.utcnow().isoformat(),
        "status_history":[{"status":"SUBMITTED","at":datetime.utcnow().isoformat(),"remarks":"Application submitted"}],
        "cvl_status":"PENDING"
    }
    applications[aid]=a
    add_notification(payload.student_id,"Application submitted",f"{aid} has been submitted successfully.","success")
    add_notification(payload.student_id,"Verification started","Your application has entered the verification workflow.","info")
    return a

@router.get("/applications")
def list_applications(role: str="student", student_id: Optional[str]=None):
    vals=list(applications.values())
    if role=="student" and student_id:
        vals=[a for a in vals if a["student_id"]==student_id]
    return vals

@router.patch("/applications/{app_id}/status")
def update_application(app_id: str, payload: StatusUpdate):
    if app_id not in applications: raise HTTPException(404,"Application not found")
    a=applications[app_id]
    a["status"]=payload.status
    a["status_history"].append({"status":payload.status,"at":datetime.utcnow().isoformat(),"remarks":payload.remarks})
    uid=a["student_id"]
    title_map={
        "CVL_REVIEW":"CVL verification requires review",
        "VERIFIED":"Verification completed",
        "NODAL_APPROVED":"Nodal verification completed",
        "SANCTIONED":"Scholarship sanctioned",
        "DBT_PROCESSING":"DBT payment processing started",
        "PAID":"Scholarship payment successful",
        "PAYMENT_FAILED":"Scholarship payment failed"
    }
    add_notification(uid,title_map.get(payload.status,"Application status updated"),payload.remarks or f"Your application is now {payload.status}.","warning" if "FAILED" in payload.status else "info")
    return a

@router.post("/documents")
def add_document(payload: DocumentCreate):
    did="DOC-"+uuid.uuid4().hex[:8].upper()
    d=payload.model_dump() | {"id":did,"status":"VERIFIED" if payload.source=="DigiLocker" else "PENDING","created_at":datetime.utcnow().isoformat()}
    documents[did]=d
    add_notification(payload.student_id,"Document Wallet updated",f"{payload.name} is now available in your wallet.","success")
    return d

@router.get("/documents/{student_id}")
def get_documents(student_id: str):
    return [d for d in documents.values() if d["student_id"]==student_id]

@router.get("/notifications/{user_id}")
def get_notifications(user_id: str):
    return notifications.get(user_id,[])

@router.patch("/notifications/{notification_id}/read")
def read_notification(notification_id: str):
    for vals in notifications.values():
        for n in vals:
            if n["id"]==notification_id:
                n["read"]=True
                return n
    raise HTTPException(404,"Notification not found")

@router.post("/grievances")
def create_grievance(payload: GrievanceCreate):
    gid="GRV-"+uuid.uuid4().hex[:8].upper()
    g=payload.model_dump() | {"id":gid,"status":"SUBMITTED","created_at":datetime.utcnow().isoformat()}
    grievances[gid]=g
    add_notification(payload.student_id,"Grievance submitted",f"Your grievance {gid} was received.","success")
    return g

@router.get("/grievances")
def list_grievances():
    return list(grievances.values())

@router.get("/dbt/transactions")
def dbt():
    return list(dbt_transactions.values())

@router.post("/dbt/{app_id}/process")
def process_dbt(app_id: str):
    if app_id not in applications: raise HTTPException(404,"Application not found")
    a=applications[app_id]
    if a["status"] not in ("SANCTIONED","DBT_PROCESSING"):
        raise HTTPException(400,"Application must be sanctioned before DBT processing.")
    txid="TXN-"+uuid.uuid4().hex[:10].upper()
    tx={"id":txid,"application_id":app_id,"student_id":a["student_id"],"status":"SUCCESS","utr":"DEMO"+uuid.uuid4().hex[:12].upper(),"created_at":datetime.utcnow().isoformat()}
    dbt_transactions[txid]=tx
    a["status"]="PAID"
    a["status_history"].append({"status":"PAID","at":datetime.utcnow().isoformat(),"remarks":"Demo DBT transaction completed"})
    add_notification(a["student_id"],"Payment successful",f"Your scholarship payment was completed. UTR: {tx['utr']}","success")
    return tx

@router.get("/admin/metrics")
def metrics():
    return {
        "applications":len(applications),
        "documents":len(documents),
        "grievances":len(grievances),
        "notifications":sum(len(v) for v in notifications.values()),
        "payments":len(dbt_transactions),
        "manual_review":sum(1 for a in applications.values() if a["status"]=="CVL_REVIEW")
    }
