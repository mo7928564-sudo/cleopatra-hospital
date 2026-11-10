import os
import json
import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Header, Query, UploadFile, File, Form, status
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import jwt
import io
import csv

# Openpyxl for Excel files
try:
    import openpyxl
except ImportError:
    openpyxl = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "chg_intelligence.db")
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cleopatra_executive_jwt_super_secret_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

app = FastAPI(
    title="Cleopatra Hospitals Group - Executive Intelligence API",
    description="Secure Executive Dashboard with Department-Level Row Level Security (RLS)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# DATABASE CONNECTION & RLS QUERY HELPER
# ------------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def hash_password(password: str) -> str:
    salt = "chg_secure_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ------------------------------------------------------------------------------
# AUTHENTICATION & ROW LEVEL SECURITY (RLS) CONTEXT
# ------------------------------------------------------------------------------
class CurrentUser:
    def __init__(self, id: str, email: str, full_name: str, role: str, department_id: Optional[str], is_active: int):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.role = role
        self.department_id = department_id
        self.is_active = is_active

    @property
    def is_super_admin(self) -> bool:
        return self.role == "SUPER_ADMIN"

    @property
    def is_ceo(self) -> bool:
        return self.role == "CEO"

    @property
    def has_company_wide_access(self) -> bool:
        return self.role in ("SUPER_ADMIN", "CEO")

def get_current_user(authorization: Optional[str] = Header(None)) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid authentication token")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, email, full_name, role, department_id, is_active FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="User account not found")
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="Account is disabled. Contact system administrator.")

    return CurrentUser(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        role=row["role"],
        department_id=row["department_id"],
        is_active=row["is_active"]
    )

def enforce_rls_department_filter(user: CurrentUser, requested_dept_id: Optional[str] = None) -> Optional[str]:
    """
    Genuine Row Level Security enforcement:
    - If user is DEPARTMENT_MANAGER or VIEWER, their department is IMMUTABLY locked to user.department_id.
    - If user is SUPER_ADMIN or CEO, they may filter by any department or view company-wide (None).
    """
    if not user.has_company_wide_access:
        # Enforce strict RLS: Manager cannot see outside their department
        return user.department_id
    # For CEO / Super Admin, allow optional department filtering
    return requested_dept_id if requested_dept_id and requested_dept_id != "all" else None

# ------------------------------------------------------------------------------
# AUTH ROUTES
# ------------------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/api/auth/login")
def login(req: LoginRequest):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    pwd_hash = hash_password(req.password)
    c.execute("""
        SELECT u.id, u.email, u.full_name, u.role, u.department_id, u.is_active, d.department_name
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.id
        WHERE LOWER(u.email) = LOWER(?) AND u.password_hash = ?
    """, (req.email.strip(), pwd_hash))
    user = c.fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    if not user["is_active"]:
        conn.close()
        raise HTTPException(status_code=403, detail="Account has been deactivated. Contact an administrator.")

    # Update last login (safely in case of read-only serverless environment)
    try:
        now_str = datetime.utcnow().isoformat()
        c.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now_str, user["id"]))
        conn.commit()
    except Exception:
        pass
    conn.close()

    token = create_access_token({
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "dept": user["department_id"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "department_id": user["department_id"],
            "department_name": user["department_name"]
        }
    }

@app.get("/api/auth/me")
def get_me(user: CurrentUser = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.email, u.full_name, u.role, u.department_id, u.is_active, u.last_login_at, d.department_name, d.clinical_specialty
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.id
        WHERE u.id = ?
    """, (user.id,))
    row = c.fetchone()
    conn.close()
    return dict(row)

# ------------------------------------------------------------------------------
# DEPARTMENTS & METADATA
# ------------------------------------------------------------------------------
@app.get("/api/departments")
def list_departments(user: CurrentUser = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # If user is department manager or viewer, only show their permitted department
    if not user.has_company_wide_access:
        c.execute("SELECT * FROM departments WHERE id = ? ORDER BY department_name", (user.department_id,))
    else:
        c.execute("SELECT * FROM departments ORDER BY department_name")
    
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# ------------------------------------------------------------------------------
# EXECUTIVE KPIS & ANALYTICS (RLS PROTECTED)
# ------------------------------------------------------------------------------
@app.get("/api/analytics/kpis")
def get_kpis(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department_id: Optional[str] = None,
    payer: Optional[str] = None,
    urgency: Optional[str] = None,
    include_duplicates: bool = False,
    user: CurrentUser = Depends(get_current_user)
):
    # Enforce RLS
    effective_dept_id = enforce_rls_department_filter(user, department_id)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    conditions = []
    params = []

    if not include_duplicates:
        conditions.append("is_duplicate_flag = 0")
    if effective_dept_id:
        conditions.append("department_id = ?")
        params.append(effective_dept_id)
    if start_date:
        conditions.append("admission_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("admission_date <= ?")
        params.append(end_date)
    if payer and payer != "all":
        conditions.append("insurance_payer = ?")
        params.append(payer)
    if urgency and urgency != "all":
        conditions.append("admission_urgency = ?")
        params.append(urgency)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    # Primary aggregation
    query = f"""
        SELECT 
            COUNT(*) as total_admissions,
            COALESCE(SUM(gross_billing_amount), 0) as total_revenue,
            COALESCE(AVG(gross_billing_amount), 0) as avg_revenue_per_patient,
            COALESCE(AVG(length_of_stay_days), 0) as avg_los,
            COALESCE(SUM(CASE WHEN gross_billing_amount < 0 THEN gross_billing_amount ELSE 0 END), 0) as total_adjustments,
            COUNT(CASE WHEN gross_billing_amount < 0 THEN 1 END) as adjustment_count,
            COUNT(DISTINCT attending_physician) as active_doctors,
            COUNT(DISTINCT hospital_branch) as active_facilities
        FROM financial_admissions
        {where_clause}
    """
    c.execute(query, params)
    kpi_row = c.fetchone()

    total_adm = kpi_row[0] or 0
    total_rev = kpi_row[1] or 0.0
    avg_rev = kpi_row[2] or 0.0
    avg_los = kpi_row[3] or 0.0
    total_adj = kpi_row[4] or 0.0
    adj_count = kpi_row[5] or 0
    active_docs = kpi_row[6] or 0
    active_facs = kpi_row[7] or 0

    # Net revenue after adjustments
    net_rev = total_rev # Since total_rev already sums signed amounts

    # Standard Healthcare Benchmark calculations (68% standard hospital operating cost ratio)
    estimated_operating_expenses = total_rev * 0.68
    gross_operating_profit = total_rev - estimated_operating_expenses
    profit_margin_pct = (gross_operating_profit / total_rev * 100) if total_rev > 0 else 0

    # Department target / budget comparison
    if effective_dept_id:
        c.execute("SELECT budget_annual, target_annual FROM departments WHERE id = ?", (effective_dept_id,))
        dept_info = c.fetchone()
        annual_budget = (dept_info[0] or 300000000.0) if dept_info else 300000000.0
        annual_target = (dept_info[1] or 320000000.0) if dept_info else 320000000.0
    else:
        c.execute("SELECT SUM(budget_annual), SUM(target_annual) FROM departments")
        dept_info = c.fetchone()
        annual_budget = dept_info[0] or 1800000000.0
        annual_target = dept_info[1] or 1920000000.0

    target_achievement_pct = (total_rev / annual_target * 100) if annual_target > 0 else 0
    budget_variance = total_rev - annual_budget

    conn.close()

    return {
        "total_revenue": round(total_rev, 2),
        "net_revenue": round(net_rev, 2),
        "total_admissions": total_adm,
        "avg_revenue_per_patient": round(avg_rev, 2),
        "avg_length_of_stay": round(avg_los, 1),
        "total_adjustments": round(total_adj, 2),
        "adjustment_count": adj_count,
        "estimated_expenses": round(estimated_operating_expenses, 2),
        "gross_operating_profit": round(gross_operating_profit, 2),
        "profit_margin_pct": round(profit_margin_pct, 1),
        "annual_budget": annual_budget,
        "annual_target": annual_target,
        "target_achievement_pct": round(target_achievement_pct, 1),
        "budget_variance": round(budget_variance, 2),
        "active_physicians": active_docs,
        "active_facilities": active_facs,
        "rls_department_enforced": effective_dept_id
    }

# ------------------------------------------------------------------------------
# MONTHLY REVENUE & TRENDS (RLS PROTECTED)
# ------------------------------------------------------------------------------
@app.get("/api/analytics/monthly-trends")
def get_monthly_trends(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department_id: Optional[str] = None,
    include_duplicates: bool = False,
    user: CurrentUser = Depends(get_current_user)
):
    effective_dept_id = enforce_rls_department_filter(user, department_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    conditions = []
    params = []
    if not include_duplicates:
        conditions.append("is_duplicate_flag = 0")
    if effective_dept_id:
        conditions.append("department_id = ?")
        params.append(effective_dept_id)
    if start_date:
        conditions.append("admission_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("admission_date <= ?")
        params.append(end_date)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT 
            SUBSTR(admission_date, 1, 7) as year_month,
            COUNT(*) as admissions,
            SUM(gross_billing_amount) as revenue,
            AVG(gross_billing_amount) as avg_revenue,
            AVG(length_of_stay_days) as avg_los
        FROM financial_admissions
        {where_clause}
        GROUP BY SUBSTR(admission_date, 1, 7)
        ORDER BY year_month ASC
    """
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    trends = []
    for r in rows:
        rev = r[2] or 0.0
        exp = rev * 0.68
        prof = rev - exp
        trends.append({
            "period": r[0],
            "admissions": r[1],
            "revenue": round(rev, 2),
            "expenses": round(exp, 2),
            "profit": round(prof, 2),
            "avg_revenue": round(r[3] or 0.0, 2),
            "avg_los": round(r[4] or 0.0, 1)
        })
    return trends

# ------------------------------------------------------------------------------
# DEPARTMENT COMPARISON & CONTRIBUTION (RLS PROTECTED)
# ------------------------------------------------------------------------------
@app.get("/api/analytics/department-breakdown")
def get_department_breakdown(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department_id: Optional[str] = None,
    include_duplicates: bool = False,
    user: CurrentUser = Depends(get_current_user)
):
    effective_dept_id = enforce_rls_department_filter(user, department_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    conditions = []
    params = []
    if not include_duplicates:
        conditions.append("fa.is_duplicate_flag = 0")
    if effective_dept_id:
        conditions.append("fa.department_id = ?")
        params.append(effective_dept_id)
    if start_date:
        conditions.append("fa.admission_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("fa.admission_date <= ?")
        params.append(end_date)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT 
            d.id,
            d.department_name,
            d.clinical_specialty,
            COUNT(fa.id) as admissions,
            COALESCE(SUM(fa.gross_billing_amount), 0) as revenue,
            COALESCE(AVG(fa.gross_billing_amount), 0) as avg_revenue,
            COALESCE(AVG(fa.length_of_stay_days), 0) as avg_los
        FROM departments d
        LEFT JOIN financial_admissions fa ON d.id = fa.department_id
        {where_clause}
        GROUP BY d.id, d.department_name, d.clinical_specialty
        ORDER BY revenue DESC
    """
    c.execute(query, params)
    rows = c.fetchall()

    total_revenue_sum = sum(r[4] for r in rows) or 1.0
    result = []
    for r in rows:
        rev = r[4] or 0.0
        exp = rev * 0.68
        prof = rev - exp
        contrib_pct = (rev / total_revenue_sum) * 100
        result.append({
            "department_id": r[0],
            "department_name": r[1],
            "clinical_specialty": r[2],
            "admissions": r[3],
            "revenue": round(rev, 2),
            "expenses": round(exp, 2),
            "profit": round(prof, 2),
            "avg_revenue": round(r[5] or 0.0, 2),
            "avg_los": round(r[6] or 0.0, 1),
            "contribution_pct": round(contrib_pct, 2)
        })
    conn.close()
    return result

# ------------------------------------------------------------------------------
# CLINICAL & OPERATIONAL BREAKDOWNS (RLS PROTECTED)
# ------------------------------------------------------------------------------
@app.get("/api/analytics/operational-breakdowns")
def get_operational_breakdowns(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department_id: Optional[str] = None,
    include_duplicates: bool = False,
    user: CurrentUser = Depends(get_current_user)
):
    effective_dept_id = enforce_rls_department_filter(user, department_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    conditions = []
    params = []
    if not include_duplicates:
        conditions.append("is_duplicate_flag = 0")
    if effective_dept_id:
        conditions.append("department_id = ?")
        params.append(effective_dept_id)
    if start_date:
        conditions.append("admission_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("admission_date <= ?")
        params.append(end_date)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    # 1. Payers
    c.execute(f"""
        SELECT insurance_payer, COUNT(*), SUM(gross_billing_amount), AVG(gross_billing_amount)
        FROM financial_admissions {where_clause}
        GROUP BY insurance_payer ORDER BY SUM(gross_billing_amount) DESC
    """, params)
    payers = [{"name": r[0], "count": r[1], "revenue": round(r[2], 2), "avg_bill": round(r[3], 2)} for r in c.fetchall()]

    # 2. Admission Urgency
    c.execute(f"""
        SELECT admission_urgency, COUNT(*), SUM(gross_billing_amount), AVG(length_of_stay_days)
        FROM financial_admissions {where_clause}
        GROUP BY admission_urgency ORDER BY COUNT(*) DESC
    """, params)
    urgencies = [{"urgency": r[0], "count": r[1], "revenue": round(r[2], 2), "avg_los": round(r[3], 1)} for r in c.fetchall()]

    # 3. Test Results / Diagnostics
    c.execute(f"""
        SELECT diagnostic_outcome, COUNT(*), SUM(gross_billing_amount)
        FROM financial_admissions {where_clause}
        GROUP BY diagnostic_outcome ORDER BY COUNT(*) DESC
    """, params)
    tests = [{"outcome": r[0], "count": r[1], "revenue": round(r[2], 2)} for r in c.fetchall()]

    # 4. Medication split
    c.execute(f"""
        SELECT prescribed_medication, COUNT(*), SUM(gross_billing_amount)
        FROM financial_admissions {where_clause}
        GROUP BY prescribed_medication ORDER BY COUNT(*) DESC LIMIT 5
    """, params)
    meds = [{"medication": r[0], "count": r[1], "revenue": round(r[2], 2)} for r in c.fetchall()]

    conn.close()
    return {
        "payers": payers,
        "urgencies": urgencies,
        "diagnostics": tests,
        "medications": meds
    }

# ------------------------------------------------------------------------------
# EXECUTIVE INSIGHTS & ACTIONS GENERATOR (PHASE 3 REQUIREMENT)
# ------------------------------------------------------------------------------
@app.get("/api/analytics/executive-insights")
def get_executive_insights(
    department_id: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user)
):
    effective_dept_id = enforce_rls_department_filter(user, department_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    dept_clause = " WHERE is_duplicate_flag = 0 " + (f"AND department_id = '{effective_dept_id}'" if effective_dept_id else "")
    
    # 1. Negative adjustments audit
    c.execute(f"""
        SELECT COUNT(*), SUM(gross_billing_amount)
        FROM financial_admissions 
        WHERE gross_billing_amount < 0 {f"AND department_id = '{effective_dept_id}'" if effective_dept_id else ""}
    """)
    adj_row = c.fetchone()
    adj_count = adj_row[0] or 0
    adj_total = adj_row[1] or 0.0

    # 2. Top revenue department
    c.execute(f"""
        SELECT d.department_name, SUM(fa.gross_billing_amount) as rev
        FROM financial_admissions fa
        JOIN departments d ON fa.department_id = d.id
        WHERE fa.is_duplicate_flag = 0
        GROUP BY d.department_name
        ORDER BY rev DESC LIMIT 1
    """)
    top_dept = c.fetchone()

    # 3. High LOS bottleneck
    c.execute(f"""
        SELECT d.department_name, AVG(fa.length_of_stay_days) as avg_stay
        FROM financial_admissions fa
        JOIN departments d ON fa.department_id = d.id
        WHERE fa.is_duplicate_flag = 0
        GROUP BY d.department_name
        ORDER BY avg_stay DESC LIMIT 1
    """)
    high_stay_dept = c.fetchone()

    # 4. Payer concentration
    c.execute(f"""
        SELECT insurance_payer, COUNT(*), SUM(gross_billing_amount)
        FROM financial_admissions
        {dept_clause}
        GROUP BY insurance_payer
        ORDER BY SUM(gross_billing_amount) DESC LIMIT 1
    """)
    top_payer = c.fetchone()

    conn.close()

    insights = []
    
    # Insight 1: Billing Adjustments & Revenue Leakage
    insights.append({
        "type": "warning" if adj_count > 0 else "success",
        "title": "Revenue Leakage & Insurance Adjustments Audit",
        "what_happened": f"Identified {adj_count} transactions with negative billing values totaling ${abs(adj_total):,.2f}.",
        "numerical_impact": f"-${abs(adj_total):,.2f} billed revenue adjustment",
        "affected_unit": "Revenue Cycle Management & Payer Claims",
        "action_required": "Initiate automated claim reconciliation with top payers to investigate clawbacks, patient refunds, and deductible reversals."
    })

    # Insight 2: Department Contribution Leader
    if top_dept and user.has_company_wide_access:
        insights.append({
            "type": "positive",
            "title": f"Top Volume Specialty: {top_dept[0]}",
            "what_happened": f"{top_dept[0]} is generating highest aggregate billed revenue at ${top_dept[1]:,.2f}.",
            "numerical_impact": f"${top_dept[1]:,.2f} gross revenue yield",
            "affected_unit": top_dept[0],
            "action_required": "Evaluate capacity expansion, surgical suite scheduling, and doctor recruitment to capture unmet patient demand."
        })

    # Insight 3: Bed Utilization & Length of Stay
    if high_stay_dept:
        insights.append({
            "type": "info",
            "title": "Bed Turnaround & Length of Stay Optimization",
            "what_happened": f"{high_stay_dept[0]} exhibits the longest average inpatient duration at {high_stay_dept[1]:.1f} days.",
            "numerical_impact": f"{high_stay_dept[1]:.1f} days ALOS (Group avg: 15.5 days)",
            "affected_unit": high_stay_dept[0],
            "action_required": "Implement early discharge planning protocols and step-down unit routing to reduce bed turnaround time by 10-15%."
        })

    # Insight 4: Payer Concentration Risk
    if top_payer:
        insights.append({
            "type": "primary",
            "title": f"Payer Concentration: {top_payer[0]}",
            "what_happened": f"{top_payer[0]} represents the single largest commercial payer channel ({top_payer[1]:,} claims, ${top_payer[2]:,.2f}).",
            "numerical_impact": f"${top_payer[2]:,.2f} in receivables",
            "affected_unit": "Commercial Contracts & Treasury",
            "action_required": "Renegotiate reimbursement tariff structures and establish service level agreements for prompt 30-day settlement."
        })

    return insights

# ------------------------------------------------------------------------------
# DETAILED TRANSACTIONS & EXPORT (RLS PROTECTED)
# ------------------------------------------------------------------------------
@app.get("/api/transactions")
def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=5, le=200),
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department_id: Optional[str] = None,
    payer: Optional[str] = None,
    urgency: Optional[str] = None,
    include_duplicates: bool = False,
    user: CurrentUser = Depends(get_current_user)
):
    effective_dept_id = enforce_rls_department_filter(user, department_id)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    conditions = []
    params = []

    if not include_duplicates:
        conditions.append("fa.is_duplicate_flag = 0")
    if effective_dept_id:
        conditions.append("fa.department_id = ?")
        params.append(effective_dept_id)
    if start_date:
        conditions.append("fa.admission_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("fa.admission_date <= ?")
        params.append(end_date)
    if payer and payer != "all":
        conditions.append("fa.insurance_payer = ?")
        params.append(payer)
    if urgency and urgency != "all":
        conditions.append("fa.admission_urgency = ?")
        params.append(urgency)
    if search:
        search_pattern = f"%{search.strip().lower()}%"
        conditions.append("(LOWER(fa.patient_name) LIKE ? OR LOWER(fa.attending_physician) LIKE ? OR LOWER(fa.hospital_branch) LIKE ? OR LOWER(fa.transaction_reference) LIKE ?)")
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    # Count total
    c.execute(f"SELECT COUNT(*) FROM financial_admissions fa {where_clause}", params)
    total_count = c.fetchone()[0]

    # Fetch rows
    offset = (page - 1) * limit
    fetch_params = params + [limit, offset]
    c.execute(f"""
        SELECT 
            fa.id, fa.transaction_reference, fa.patient_name, fa.age, fa.gender, fa.blood_type,
            d.department_name, fa.medical_condition, fa.admission_date, fa.discharge_date,
            fa.length_of_stay_days, fa.attending_physician, fa.hospital_branch, fa.insurance_payer,
            fa.gross_billing_amount, fa.room_number, fa.admission_urgency, fa.prescribed_medication,
            fa.diagnostic_outcome, fa.is_duplicate_flag, fa.is_adjustment_flag
        FROM financial_admissions fa
        JOIN departments d ON fa.department_id = d.id
        {where_clause}
        ORDER BY fa.admission_date DESC
        LIMIT ? OFFSET ?
    """, fetch_params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    return {
        "page": page,
        "limit": limit,
        "total": total_count,
        "pages": (total_count + limit - 1) // limit,
        "records": rows
    }

class CreateTransactionRequest(BaseModel):
    patient_name: str
    age: int
    gender: str
    blood_type: str = "O+"
    department_id: str
    admission_date: str
    discharge_date: str
    attending_physician: str
    hospital_branch: str
    insurance_payer: str
    gross_billing_amount: float
    room_number: Optional[int] = None
    admission_urgency: str = "Elective"
    prescribed_medication: Optional[str] = "None"
    diagnostic_outcome: str = "Normal"

@app.post("/api/transactions")
def create_single_transaction(data: CreateTransactionRequest, user: CurrentUser = Depends(get_current_user)):
    # 1. Enforce RBAC
    if user.role == "VIEWER":
        raise HTTPException(status_code=403, detail="Viewers are restricted to read-only access.")
    
    # 2. Enforce Row Level Security (RLS)
    effective_dept_id = data.department_id
    if user.role == "DEPARTMENT_MANAGER":
        if data.department_id != user.department_id:
            raise HTTPException(status_code=403, detail="RLS Violation: You can only record admissions for your assigned department.")
        effective_dept_id = user.department_id

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Look up department specialty
    c.execute("SELECT clinical_specialty, department_name FROM departments WHERE id = ?", (effective_dept_id,))
    dept_row = c.fetchone()
    if not dept_row:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid department ID.")

    specialty = dept_row[0]

    # Calculate Length of Stay
    try:
        d_adm = datetime.strptime(data.admission_date, "%Y-%m-%d")
        d_dis = datetime.strptime(data.discharge_date, "%Y-%m-%d")
        los = max(1, (d_dis - d_adm).days)
    except Exception:
        los = 1

    rec_id = f"ADM-MAN-{uuid.uuid4().hex[:6].upper()}"
    tx_ref = f"CHG-TX-{data.admission_date.replace('-', '')}-{uuid.uuid4().hex[:4].upper()}"
    is_adj = 1 if data.gross_billing_amount < 0 else 0

    c.execute("""
        INSERT INTO financial_admissions (
            id, transaction_reference, patient_name, age, gender, blood_type,
            department_id, medical_condition, admission_date, discharge_date,
            length_of_stay_days, attending_physician, hospital_branch, insurance_payer,
            gross_billing_amount, room_number, admission_urgency, prescribed_medication,
            diagnostic_outcome, is_duplicate_flag, is_adjustment_flag, uploaded_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?);
    """, (
        rec_id, tx_ref, data.patient_name.strip().title(), data.age, data.gender, data.blood_type,
        effective_dept_id, specialty, data.admission_date, data.discharge_date,
        los, data.attending_physician.strip(), data.hospital_branch.strip(), data.insurance_payer.strip(),
        data.gross_billing_amount, data.room_number, data.admission_urgency, data.prescribed_medication,
        data.diagnostic_outcome, is_adj, user.id
    ))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": "Admission record added successfully",
        "id": rec_id,
        "transaction_reference": tx_ref
    }

@app.get("/api/transactions/export")
def export_transactions(
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    department_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user)
):
    effective_dept_id = enforce_rls_department_filter(user, department_id)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    conditions = ["fa.is_duplicate_flag = 0"]
    params = []
    if effective_dept_id:
        conditions.append("fa.department_id = ?")
        params.append(effective_dept_id)
    if start_date:
        conditions.append("fa.admission_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("fa.admission_date <= ?")
        params.append(end_date)

    where_clause = " WHERE " + " AND ".join(conditions)

    c.execute(f"""
        SELECT 
            fa.transaction_reference, fa.patient_name, fa.age, fa.gender, fa.blood_type,
            d.department_name, fa.medical_condition, fa.admission_date, fa.discharge_date,
            fa.length_of_stay_days, fa.attending_physician, fa.hospital_branch, fa.insurance_payer,
            fa.gross_billing_amount, fa.room_number, fa.admission_urgency, fa.prescribed_medication,
            fa.diagnostic_outcome
        FROM financial_admissions fa
        JOIN departments d ON fa.department_id = d.id
        {where_clause}
        ORDER BY fa.admission_date DESC
        LIMIT 10000
    """, params)
    rows = c.fetchall()
    conn.close()

    # Stream CSV
    output = io.StringIO()
    writer = csv.writer(output)
    headers = [
        "Transaction Ref", "Patient Name", "Age", "Gender", "Blood Type",
        "Department", "Medical Condition", "Admission Date", "Discharge Date",
        "Length of Stay", "Doctor", "Hospital Facility", "Insurance Provider",
        "Gross Billing Amount", "Room Number", "Admission Type", "Medication", "Test Results"
    ]
    writer.writerow(headers)
    for r in rows:
        writer.writerow(list(r))
    
    output.seek(0)
    filename = f"chg_financial_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ------------------------------------------------------------------------------
# ADMIN USER MANAGEMENT (SUPER_ADMIN ONLY)
# ------------------------------------------------------------------------------
class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str
    department_id: Optional[str] = None
    is_active: bool = True

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

@app.get("/api/admin/users")
def get_admin_users(user: CurrentUser = Depends(get_current_user)):
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied. Super Administrator privileges required.")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.email, u.full_name, u.role, u.department_id, u.is_active, u.last_login_at, u.created_at,
               d.department_name, d.clinical_specialty
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.id
        ORDER BY u.created_at DESC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.post("/api/admin/users")
def create_admin_user(data: CreateUserRequest, user: CurrentUser = Depends(get_current_user)):
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Administrator privileges required.")
    
    if data.role not in ('SUPER_ADMIN', 'CEO', 'DEPARTMENT_MANAGER', 'VIEWER'):
        raise HTTPException(status_code=400, detail="Invalid user role.")
    
    if data.role in ('DEPARTMENT_MANAGER', 'VIEWER') and not data.department_id:
        raise HTTPException(status_code=400, detail="Department assignment is mandatory for Department Managers and Viewers.")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        new_id = f"usr-{uuid.uuid4().hex[:8]}"
        pwd_hash = hash_password(data.password)
        c.execute("""
            INSERT INTO users (id, email, password_hash, full_name, role, department_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (new_id, data.email.strip().lower(), pwd_hash, data.full_name.strip(), data.role, data.department_id, 1 if data.is_active else 0))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="User with this email address already exists.")
    
    conn.close()
    return {"message": "User created successfully", "user_id": new_id}

@app.put("/api/admin/users/{user_id}")
def update_admin_user(user_id: str, data: UpdateUserRequest, user: CurrentUser = Depends(get_current_user)):
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Administrator privileges required.")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Verify user exists
    c.execute("SELECT id, role FROM users WHERE id = ?", (user_id,))
    target = c.fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")

    updates = []
    params = []
    if data.full_name is not None:
        updates.append("full_name = ?")
        params.append(data.full_name.strip())
    if data.role is not None:
        if data.role not in ('SUPER_ADMIN', 'CEO', 'DEPARTMENT_MANAGER', 'VIEWER'):
            raise HTTPException(status_code=400, detail="Invalid role.")
        updates.append("role = ?")
        params.append(data.role)
    if data.department_id is not None:
        updates.append("department_id = ?")
        params.append(data.department_id if data.department_id != "" else None)
    if data.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if data.is_active else 0)
    if data.password:
        updates.append("password_hash = ?")
        params.append(hash_password(data.password))

    if updates:
        params.append(user_id)
        c.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    conn.close()
    return {"message": "User updated successfully"}

# ------------------------------------------------------------------------------
# FILE IMPORT & DYNAMIC DATA MAPPING ENGINE (ADMIN ONLY)
# ------------------------------------------------------------------------------
@app.post("/api/admin/upload-preview")
async def preview_upload_file(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user)
):
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Administrator privileges required.")
    
    content = await file.read()
    filename = file.filename or "unknown"
    
    rows = []
    headers = []
    delimiter = ";"

    if filename.endswith(".csv"):
        text = content.decode("utf-8", errors="replace")
        # Detect delimiter
        first_line = text.split("\n")[0]
        delimiter = ";" if ";" in first_line else ","
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        try:
            headers = [h.strip() for h in next(reader)]
            for i, r in enumerate(reader):
                if i < 10 and r:
                    rows.append(r)
        except StopIteration:
            pass
    elif filename.endswith((".xlsx", ".xls")):
        if not openpyxl:
            raise HTTPException(status_code=500, detail="Excel parser (openpyxl) not installed")
        wb = openpyxl.load_workbook(filename=io.BytesIO(content), data_only=True)
        sheet = wb.active
        all_rows = list(sheet.iter_rows(values_only=True))
        if all_rows:
            headers = [str(h).strip() if h is not None else f"Column_{idx}" for idx, h in enumerate(all_rows[0])]
            for r in all_rows[1:11]:
                rows.append([str(c) if c is not None else "" for c in r])
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .csv or .xlsx files.")

    # Standard Target Fields for Ingestion Mapping
    standard_targets = [
        {"key": "patient_name", "label": "Patient Name", "required": True},
        {"key": "age", "label": "Age", "required": True},
        {"key": "gender", "label": "Gender", "required": True},
        {"key": "blood_type", "label": "Blood Type", "required": False},
        {"key": "department_name", "label": "Department / Medical Condition", "required": True},
        {"key": "admission_date", "label": "Date of Admission", "required": True},
        {"key": "discharge_date", "label": "Discharge Date", "required": True},
        {"key": "doctor", "label": "Doctor / Physician", "required": True},
        {"key": "hospital", "label": "Hospital Facility", "required": True},
        {"key": "insurance_payer", "label": "Insurance Provider", "required": True},
        {"key": "billing_amount", "label": "Billing Amount (Revenue)", "required": True},
        {"key": "room_number", "label": "Room Number", "required": False},
        {"key": "admission_type", "label": "Admission Type (Urgency)", "required": False},
        {"key": "medication", "label": "Medication", "required": False},
        {"key": "test_results", "label": "Test Results", "required": False}
    ]

    # Automatic Smart Suggestion Matching
    suggested_mapping = {}
    for std in standard_targets:
        std_key_lower = std["key"].lower().replace("_", "")
        std_label_lower = std["label"].lower().replace(" ", "").replace("/", "")
        for h in headers:
            h_clean = h.lower().replace(" ", "").replace("_", "").replace("/", "")
            if h_clean == std_key_lower or h_clean in std_label_lower or std_key_lower in h_clean:
                suggested_mapping[std["key"]] = h
                break

    return {
        "file_name": filename,
        "delimiter": delimiter,
        "headers": headers,
        "preview_rows": rows,
        "standard_targets": standard_targets,
        "suggested_mapping": suggested_mapping
    }

class CommitImportRequest(BaseModel):
    file_name: str
    column_mapping: Dict[str, str]
    append_mode: bool = True # True = Append, False = Replace

@app.post("/api/admin/import-commit")
async def commit_file_import(
    file: UploadFile = File(...),
    column_mapping_json: str = Form(...),
    append_mode: bool = Form(True),
    user: CurrentUser = Depends(get_current_user)
):
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Administrator privileges required.")
    
    mapping = json.loads(column_mapping_json)
    content = await file.read()
    filename = file.filename or "uploaded_data.csv"

    # Read rows
    rows_data = []
    if filename.endswith(".csv"):
        text = content.decode("utf-8", errors="replace")
        delim = ";" if ";" in text.split("\n")[0] else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delim)
        for r in reader:
            rows_data.append(r)
    elif filename.endswith((".xlsx", ".xls")):
        wb = openpyxl.load_workbook(filename=io.BytesIO(content), data_only=True)
        sheet = wb.active
        all_rows = list(sheet.iter_rows(values_only=True))
        if all_rows:
            hdrs = [str(h).strip() if h else f"Col_{i}" for i, h in enumerate(all_rows[0])]
            for r in all_rows[1:]:
                row_dict = {hdrs[i]: str(v) if v is not None else "" for i, v in enumerate(r)}
                rows_data.append(row_dict)

    if not rows_data:
        raise HTTPException(status_code=400, detail="The uploaded file contains no data rows.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load department map
    cursor.execute("SELECT id, clinical_specialty, department_name FROM departments")
    dept_rows = cursor.fetchall()
    dept_map = {}
    for d_id, specialty, d_name in dept_rows:
        dept_map[specialty.lower()] = d_id
        dept_map[d_name.lower()] = d_id

    batch_id = str(uuid.uuid4())
    imported_count = 0
    duplicate_count = 0
    rejected_count = 0
    records_to_insert = []

    # Get seen duplicate hashes
    cursor.execute("SELECT patient_name, admission_date, attending_physician, hospital_branch, gross_billing_amount FROM financial_admissions")
    existing_seen = set((r[0].lower(), r[1], r[2], r[3], round(float(r[4]), 2)) for r in cursor.fetchall())

    for idx, r in enumerate(rows_data):
        try:
            p_name = r.get(mapping.get("patient_name", ""), "").strip().title()
            cond = r.get(mapping.get("department_name", ""), "").strip()
            
            # Department resolution
            matched_dept_id = dept_map.get(cond.lower())
            if not matched_dept_id:
                # Fuzzy match
                for spec_key, did in dept_map.items():
                    if spec_key in cond.lower() or cond.lower() in spec_key:
                        matched_dept_id = did
                        break

            # If ownership is unclear, reject record (Phase 7 rule)
            if not matched_dept_id:
                rejected_count += 1
                continue

            age = int(float(r.get(mapping.get("age", ""), 0)))
            gender = r.get(mapping.get("gender", ""), "Other").strip()
            blood = r.get(mapping.get("blood_type", ""), "Unknown").strip()
            
            d_adm_raw = r.get(mapping.get("admission_date", ""), "").strip()
            d_dis_raw = r.get(mapping.get("discharge_date", ""), "").strip()
            
            # Date parse
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y'):
                try:
                    d_adm = datetime.strptime(d_adm_raw, fmt).strftime('%Y-%m-%d')
                    break
                except:
                    d_adm = datetime.utcnow().strftime('%Y-%m-%d')
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y'):
                try:
                    d_dis = datetime.strptime(d_dis_raw, fmt).strftime('%Y-%m-%d')
                    break
                except:
                    d_dis = d_adm

            los = max(1, (datetime.strptime(d_dis, '%Y-%m-%d') - datetime.strptime(d_adm, '%Y-%m-%d')).days)
            doc = r.get(mapping.get("doctor", ""), "Unknown Doctor").strip()
            hosp = r.get(mapping.get("hospital", ""), "CHG Central").strip()
            payer = r.get(mapping.get("insurance_payer", ""), "Direct").strip()
            billing = float(r.get(mapping.get("billing_amount", ""), 0.0))
            room = int(float(r.get(mapping.get("room_number", ""), 101))) if r.get(mapping.get("room_number", "")) else None
            urgency = r.get(mapping.get("admission_type", ""), "Elective").strip()
            med = r.get(mapping.get("medication", ""), "None").strip()
            outcome = r.get(mapping.get("test_results", ""), "Normal").strip()

            dedup_key = (p_name.lower(), d_adm, doc, hosp, round(billing, 2))
            is_dup = 0
            if dedup_key in existing_seen:
                is_dup = 1
                duplicate_count += 1
            else:
                existing_seen.add(dedup_key)

            is_adj = 1 if billing < 0 else 0
            rec_id = f"IMP-{batch_id[:6]}-{idx:06d}"
            tx_ref = f"CHG-IMP-{idx:06d}-{uuid.uuid4().hex[:4].upper()}"

            records_to_insert.append((
                rec_id, tx_ref, p_name, age, gender, blood, matched_dept_id, cond,
                d_adm, d_dis, los, doc, hosp, payer, billing, room,
                urgency, med, outcome, is_dup, is_adj, user.id, batch_id
            ))
            imported_count += 1
        except Exception:
            rejected_count += 1

    # Insert into database
    if records_to_insert:
        cursor.executemany("""
            INSERT INTO financial_admissions (
                id, transaction_reference, patient_name, age, gender, blood_type,
                department_id, medical_condition, admission_date, discharge_date,
                length_of_stay_days, attending_physician, hospital_branch, insurance_payer,
                gross_billing_amount, room_number, admission_urgency, prescribed_medication,
                diagnostic_outcome, is_duplicate_flag, is_adjustment_flag, uploaded_by, import_batch_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, records_to_insert)

    cursor.execute("""
        INSERT INTO import_logs (id, file_name, file_type, total_records, imported_records, duplicate_records, rejected_records, column_mapping_json, imported_by, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (batch_id, filename, "CSV/XLSX", len(rows_data), imported_count, duplicate_count, rejected_count, json.dumps(mapping), user.id, "SUCCESS"))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "batch_id": batch_id,
        "total_rows": len(rows_data),
        "imported": imported_count,
        "duplicates_flagged": duplicate_count,
        "rejected_unmapped": rejected_count
    }

@app.get("/api/admin/import-history")
def get_import_history(user: CurrentUser = Depends(get_current_user)):
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Administrator privileges required.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM import_logs ORDER BY created_at DESC LIMIT 50")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.delete("/api/admin/import-batches/{batch_id}")
def delete_import_batch(batch_id: str, user: CurrentUser = Depends(get_current_user)):
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Administrator privileges required.")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check batch exists
    c.execute("SELECT id, file_name, imported_records FROM import_logs WHERE id = ?", (batch_id,))
    batch = c.fetchone()
    if not batch:
        conn.close()
        raise HTTPException(status_code=404, detail="Import batch record not found.")

    # Delete records imported with this batch_id
    c.execute("DELETE FROM financial_admissions WHERE import_batch_id = ?", (batch_id,))
    deleted_count = c.rowcount

    # Remove from import logs
    c.execute("DELETE FROM import_logs WHERE id = ?", (batch_id,))
    
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": f"Batch {batch_id} deleted successfully. {deleted_count} records removed from the ledger.",
        "deleted_count": deleted_count
    }

# ------------------------------------------------------------------------------
# SERVE FRONTEND STATIC FILES & SPA ENTRY POINT
# ------------------------------------------------------------------------------
if os.path.exists(ASSETS_DIR):
    try:
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    except Exception:
        pass

if os.path.exists(STATIC_DIR):
    try:
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    except Exception:
        pass

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database_exists": os.path.exists(DB_PATH),
        "static_exists": os.path.exists(STATIC_DIR)
    }

@app.get("/")
def serve_index():
    candidates = [
        os.path.join(STATIC_DIR, "index.html"),
        os.path.join(BASE_DIR, "index.html")
    ]
    for c in candidates:
        if os.path.exists(c):
            return FileResponse(c)
    return {"message": "Cleopatra Hospitals Group API running. Static files loading..."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
