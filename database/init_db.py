import csv
import sqlite3
import hashlib
import os
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "chg_intelligence.db")
CSV_PATH = r"c:\Users\a.mohsen\Downloads\New folder (2)\healthcare_dataset.csv"

def hash_password(password: str) -> str:
    # Standard secure SHA-256 with salt
    salt = "chg_secure_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable WAL mode for high concurrency
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # 1. Departments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id TEXT PRIMARY KEY,
        department_code TEXT UNIQUE NOT NULL,
        department_name TEXT NOT NULL,
        clinical_specialty TEXT NOT NULL,
        head_of_department TEXT,
        budget_annual REAL DEFAULT 300000000.0,
        target_annual REAL DEFAULT 320000000.0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Users & Profiles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('SUPER_ADMIN', 'CEO', 'DEPARTMENT_MANAGER', 'VIEWER')),
        department_id TEXT REFERENCES departments(id),
        is_active INTEGER DEFAULT 1,
        last_login_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 3. Financial Admissions Data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_admissions (
        id TEXT PRIMARY KEY,
        transaction_reference TEXT UNIQUE,
        patient_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        blood_type TEXT NOT NULL,
        department_id TEXT NOT NULL REFERENCES departments(id),
        medical_condition TEXT NOT NULL,
        admission_date TEXT NOT NULL,
        discharge_date TEXT NOT NULL,
        length_of_stay_days INTEGER NOT NULL,
        attending_physician TEXT NOT NULL,
        hospital_branch TEXT NOT NULL,
        insurance_payer TEXT NOT NULL,
        gross_billing_amount REAL NOT NULL,
        room_number INTEGER,
        admission_urgency TEXT NOT NULL,
        prescribed_medication TEXT,
        diagnostic_outcome TEXT NOT NULL,
        is_duplicate_flag INTEGER DEFAULT 0,
        is_adjustment_flag INTEGER DEFAULT 0,
        uploaded_by TEXT,
        import_batch_id TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Import Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS import_logs (
        id TEXT PRIMARY KEY,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        total_records INTEGER NOT NULL,
        imported_records INTEGER NOT NULL,
        duplicate_records INTEGER NOT NULL,
        rejected_records INTEGER NOT NULL,
        column_mapping_json TEXT,
        imported_by TEXT,
        status TEXT DEFAULT 'COMPLETED',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fa_dept ON financial_admissions(department_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fa_date ON financial_admissions(admission_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fa_payer ON financial_admissions(insurance_payer);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fa_urgency ON financial_admissions(admission_urgency);")

    # Seed Departments
    departments_data = [
        ("dept-onc-01", "ONC", "Department of Oncology", "Cancer", "Dr. Sherif Omar", 300000000.0, 320000000.0),
        ("dept-card-02", "CARD", "Department of Cardiology", "Hypertension", "Dr. Hani Gabriel", 300000000.0, 320000000.0),
        ("dept-endo-03", "ENDO", "Department of Endocrinology & Diabetes", "Diabetes", "Dr. Mona Soliman", 300000000.0, 320000000.0),
        ("dept-pulm-04", "PULM", "Department of Pulmonology & Respiratory", "Asthma", "Dr. Tarek Youssef", 300000000.0, 310000000.0),
        ("dept-ortho-05", "ORTHO", "Department of Orthopedics & Rheumatology", "Arthritis", "Dr. Khaled Emam", 300000000.0, 320000000.0),
        ("dept-bari-06", "BARI", "Department of Bariatrics & Metabolic Health", "Obesity", "Dr. Ahmed Mansour", 300000000.0, 310000000.0)
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO departments (id, department_code, department_name, clinical_specialty, head_of_department, budget_annual, target_annual)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, departments_data)

    # Seed Users for all required roles
    users_data = [
        ("usr-admin-01", "admin@cleopatra.com", hash_password("Admin@123"), "Dr. Ahmed Ezzeldin (Super Admin)", "SUPER_ADMIN", None, 1),
        ("usr-ceo-02", "ceo@cleopatra.com", hash_password("Ceo@123"), "Tamer Abdallah (Chief Executive Officer)", "CEO", None, 1),
        ("usr-mgr-onc-03", "oncology.manager@cleopatra.com", hash_password("Dept@123"), "Dr. Sherif Omar (Oncology HOD)", "DEPARTMENT_MANAGER", "dept-onc-01", 1),
        ("usr-mgr-card-04", "cardiology.manager@cleopatra.com", hash_password("Dept@123"), "Dr. Hani Gabriel (Cardiology HOD)", "DEPARTMENT_MANAGER", "dept-card-02", 1),
        ("usr-mgr-endo-05", "endocrinology.manager@cleopatra.com", hash_password("Dept@123"), "Dr. Mona Soliman (Endocrinology HOD)", "DEPARTMENT_MANAGER", "dept-endo-03", 1),
        ("usr-viewer-06", "viewer@cleopatra.com", hash_password("Viewer@123"), "Nour El-Din (Clinical Quality Analyst)", "VIEWER", "dept-onc-01", 1)
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO users (id, email, password_hash, full_name, role, department_id, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, users_data)
    
    conn.commit()
    conn.close()
    print("Database schema and core roles initialized successfully.")

def seed_admissions_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if data already loaded
    cursor.execute("SELECT count(*) FROM financial_admissions")
    count = cursor.fetchone()[0]
    if count >= 50000:
        print(f"Data already loaded ({count} records). Skipping reload.")
        conn.close()
        return

    # Map specialty to department id
    dept_map = {
        "Cancer": "dept-onc-01",
        "Hypertension": "dept-card-02",
        "Diabetes": "dept-endo-03",
        "Asthma": "dept-pulm-04",
        "Arthritis": "dept-ortho-05",
        "Obesity": "dept-bari-06"
    }

    print(f"Reading CSV dataset from {CSV_PATH}...")
    with open(CSV_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        seen_admissions = set()
        records_to_insert = []
        batch_id = str(uuid.uuid4())
        total_raw = 0
        duplicates_count = 0
        adjustments_count = 0

        for r in reader:
            total_raw += 1
            
            p_name = r['Name'].strip().title()
            age = int(r['Age'])
            gender = r['Gender'].strip()
            blood = r['Blood Type'].strip()
            cond = r['Medical Condition'].strip()
            dept_id = dept_map.get(cond, "dept-onc-01")
            
            # Format dates to ISO YYYY-MM-DD
            d_adm_raw = r['Date of Admission'].strip()
            d_dis_raw = r['Discharge Date'].strip()
            d_adm = datetime.strptime(d_adm_raw, '%d/%m/%Y').strftime('%Y-%m-%d')
            d_dis = datetime.strptime(d_dis_raw, '%d/%m/%Y').strftime('%Y-%m-%d')
            los = (datetime.strptime(d_dis, '%Y-%m-%d') - datetime.strptime(d_adm, '%Y-%m-%d')).days
            
            doc = r['Doctor'].strip()
            hosp = r['Hospital'].strip()
            payer = r['Insurance Provider'].strip()
            billing = float(r['Billing Amount'])
            room = int(r['Room Number']) if r.get('Room Number') else None
            urgency = r['Admission Type'].strip()
            med = r['Medication'].strip()
            outcome = r['Test Results'].strip()
            
            # Check duplicate
            dedup_key = (p_name.lower(), d_adm, doc, hosp, round(billing, 2))
            is_dup = 0
            if dedup_key in seen_admissions:
                is_dup = 1
                duplicates_count += 1
            else:
                seen_admissions.add(dedup_key)
                
            is_adj = 1 if billing < 0 else 0
            if is_adj:
                adjustments_count += 1

            rec_id = f"ADM-{total_raw:06d}"
            tx_ref = f"CHG-TX-{d_adm.replace('-','')}-{total_raw:06d}"
            
            records_to_insert.append((
                rec_id, tx_ref, p_name, age, gender, blood, dept_id, cond,
                d_adm, d_dis, los, doc, hosp, payer, billing, room,
                urgency, med, outcome, is_dup, is_adj, "usr-admin-01", batch_id
            ))
            
            if len(records_to_insert) >= 5000:
                cursor.executemany("""
                INSERT OR REPLACE INTO financial_admissions (
                    id, transaction_reference, patient_name, age, gender, blood_type,
                    department_id, medical_condition, admission_date, discharge_date,
                    length_of_stay_days, attending_physician, hospital_branch, insurance_payer,
                    gross_billing_amount, room_number, admission_urgency, prescribed_medication,
                    diagnostic_outcome, is_duplicate_flag, is_adjustment_flag, uploaded_by, import_batch_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, records_to_insert)
                conn.commit()
                records_to_insert = []
                print(f"Processed {total_raw} records...")

        if records_to_insert:
            cursor.executemany("""
            INSERT OR REPLACE INTO financial_admissions (
                id, transaction_reference, patient_name, age, gender, blood_type,
                department_id, medical_condition, admission_date, discharge_date,
                length_of_stay_days, attending_physician, hospital_branch, insurance_payer,
                gross_billing_amount, room_number, admission_urgency, prescribed_medication,
                diagnostic_outcome, is_duplicate_flag, is_adjustment_flag, uploaded_by, import_batch_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, records_to_insert)
            conn.commit()

        # Record in import audit logs
        cursor.execute("""
        INSERT INTO import_logs (id, file_name, file_type, total_records, imported_records, duplicate_records, rejected_records, imported_by, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (batch_id, "healthcare_dataset.csv", "CSV", total_raw, total_raw - duplicates_count, duplicates_count, 0, "usr-admin-01", "SUCCESS"))
        conn.commit()

    conn.close()
    print(f"Ingestion Complete: {total_raw} raw rows imported. {duplicates_count} duplicates flagged. {adjustments_count} adjustments flagged.")

if __name__ == "__main__":
    init_database()
    seed_admissions_data()
