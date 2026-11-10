-- ==============================================================================
-- CLEOPATRA HOSPITALS GROUP (CHG) - EXECUTIVE INTELLIGENCE DATABASE SCHEMA
-- PostgreSQL & Supabase Row Level Security (RLS) Implementation
-- ==============================================================================

-- 1. EXTENSIONS & ENUMS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM ('SUPER_ADMIN', 'CEO', 'DEPARTMENT_MANAGER', 'VIEWER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE admission_urgency_enum AS ENUM ('Elective', 'Urgent', 'Emergency');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE test_result_enum AS ENUM ('Normal', 'Inconclusive', 'Abnormal');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. DEPARTMENTS TABLE
CREATE TABLE IF NOT EXISTS public.departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_code VARCHAR(32) UNIQUE NOT NULL,
    department_name VARCHAR(128) NOT NULL,
    clinical_specialty VARCHAR(128) NOT NULL,
    head_of_department VARCHAR(128),
    budget_annual NUMERIC(15, 2) DEFAULT 0.00,
    target_annual NUMERIC(15, 2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed CHG Clinical Departments based on data discovery
INSERT INTO public.departments (department_code, department_name, clinical_specialty, budget_annual, target_annual)
VALUES 
    ('ONC', 'Department of Oncology', 'Cancer', 300000000.00, 320000000.00),
    ('CARD', 'Department of Cardiology', 'Hypertension', 300000000.00, 320000000.00),
    ('ENDO', 'Department of Endocrinology & Diabetes', 'Diabetes', 300000000.00, 320000000.00),
    ('PULM', 'Department of Pulmonology & Respiratory', 'Asthma', 300000000.00, 310000000.00),
    ('ORTHO', 'Department of Orthopedics & Rheumatology', 'Arthritis', 300000000.00, 320000000.00),
    ('BARI', 'Department of Bariatrics & Metabolic Health', 'Obesity', 300000000.00, 310000000.00)
ON CONFLICT (department_code) DO NOTHING;

-- 3. USER PROFILES TABLE (Linked with Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role_enum NOT NULL DEFAULT 'VIEWER',
    department_id UUID REFERENCES public.departments(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. ADMISSIONS FINANCIAL DATA TABLE (Extended from Dataset)
CREATE TABLE IF NOT EXISTS public.financial_admissions_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_reference VARCHAR(64) UNIQUE NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    age INT NOT NULL CHECK (age >= 0 AND age <= 130),
    gender VARCHAR(16) NOT NULL,
    blood_type VARCHAR(8) NOT NULL,
    department_id UUID NOT NULL REFERENCES public.departments(id) ON DELETE RESTRICT,
    medical_condition VARCHAR(128) NOT NULL,
    admission_date DATE NOT NULL,
    discharge_date DATE NOT NULL,
    length_of_stay_days INT GENERATED ALWAYS AS ((discharge_date - admission_date)) STORED,
    attending_physician VARCHAR(255) NOT NULL,
    hospital_branch VARCHAR(255) NOT NULL,
    insurance_payer VARCHAR(128) NOT NULL,
    gross_billing_amount NUMERIC(12, 2) NOT NULL,
    room_number INT,
    admission_urgency admission_urgency_enum NOT NULL DEFAULT 'Elective',
    prescribed_medication VARCHAR(128),
    diagnostic_test_outcome test_result_enum NOT NULL DEFAULT 'Normal',
    is_duplicate_flag BOOLEAN DEFAULT FALSE,
    is_adjustment_flag BOOLEAN GENERATED ALWAYS AS (gross_billing_amount < 0) STORED,
    uploaded_by UUID REFERENCES auth.users(id),
    import_batch_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for Executive Performance
CREATE INDEX IF NOT EXISTS idx_fad_dept ON public.financial_admissions_data(department_id);
CREATE INDEX IF NOT EXISTS idx_fad_admission_date ON public.financial_admissions_data(admission_date);
CREATE INDEX IF NOT EXISTS idx_fad_payer ON public.financial_admissions_data(insurance_payer);
CREATE INDEX IF NOT EXISTS idx_fad_urgency ON public.financial_admissions_data(admission_urgency);

-- 5. DATA IMPORT AUDIT LOG TABLE
CREATE TABLE IF NOT EXISTS public.import_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(32) NOT NULL,
    file_size_bytes BIGINT,
    total_records INT NOT NULL DEFAULT 0,
    imported_records INT NOT NULL DEFAULT 0,
    duplicate_records INT NOT NULL DEFAULT 0,
    rejected_records INT NOT NULL DEFAULT 0,
    column_mapping_json JSONB,
    imported_by UUID REFERENCES auth.users(id),
    import_status VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- 6. SECURITY HELPER FUNCTIONS
-- ==============================================================================

-- Get authenticated user role
CREATE OR REPLACE FUNCTION public.get_auth_role()
RETURNS user_role_enum AS $$
    SELECT role FROM public.user_profiles WHERE id = auth.uid() AND is_active = TRUE;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Get authenticated user assigned department
CREATE OR REPLACE FUNCTION public.get_auth_department_id()
RETURNS UUID AS $$
    SELECT department_id FROM public.user_profiles WHERE id = auth.uid() AND is_active = TRUE;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- ==============================================================================
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

-- Enable RLS on all tables
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.financial_admissions_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.import_audit_logs ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- A. DEPARTMENTS POLICIES
-- ------------------------------------------------------------------------------
-- Everyone authenticated can view departments
CREATE POLICY "Allow authenticated read departments"
    ON public.departments FOR SELECT
    TO authenticated
    USING (TRUE);

-- Only SUPER_ADMIN can modify departments
CREATE POLICY "Allow admin manage departments"
    ON public.departments FOR ALL
    TO authenticated
    USING (public.get_auth_role() = 'SUPER_ADMIN')
    WITH CHECK (public.get_auth_role() = 'SUPER_ADMIN');

-- ------------------------------------------------------------------------------
-- B. USER PROFILES POLICIES
-- ------------------------------------------------------------------------------
-- Users can read their own profile; SUPER_ADMIN and CEO can read all profiles
CREATE POLICY "Read user profiles"
    ON public.user_profiles FOR SELECT
    TO authenticated
    USING (
        id = auth.uid() 
        OR public.get_auth_role() IN ('SUPER_ADMIN', 'CEO')
    );

-- Only SUPER_ADMIN can insert, update, or delete profiles
CREATE POLICY "Super admin manage user profiles"
    ON public.user_profiles FOR ALL
    TO authenticated
    USING (public.get_auth_role() = 'SUPER_ADMIN')
    WITH CHECK (public.get_auth_role() = 'SUPER_ADMIN');

-- ------------------------------------------------------------------------------
-- C. FINANCIAL DATA ROW LEVEL SECURITY (CORE REQUIREMENT)
-- ------------------------------------------------------------------------------
-- SELECT:
-- 1. SUPER_ADMIN and CEO can access ALL financial records across all departments.
-- 2. DEPARTMENT_MANAGER and VIEWER can strictly access records where department_id = their assigned department_id.
CREATE POLICY "RLS Select Financial Admissions Data"
    ON public.financial_admissions_data FOR SELECT
    TO authenticated
    USING (
        public.get_auth_role() IN ('SUPER_ADMIN', 'CEO')
        OR (
            public.get_auth_role() IN ('DEPARTMENT_MANAGER', 'VIEWER')
            AND department_id = public.get_auth_department_id()
        )
    );

-- INSERT / UPDATE / DELETE:
-- Only SUPER_ADMIN (or designated DEPARTMENT_MANAGER for their own department if permitted)
CREATE POLICY "RLS Insert Financial Admissions Data"
    ON public.financial_admissions_data FOR INSERT
    TO authenticated
    WITH CHECK (
        public.get_auth_role() = 'SUPER_ADMIN'
        OR (
            public.get_auth_role() = 'DEPARTMENT_MANAGER'
            AND department_id = public.get_auth_department_id()
        )
    );

CREATE POLICY "RLS Update Financial Admissions Data"
    ON public.financial_admissions_data FOR UPDATE
    TO authenticated
    USING (
        public.get_auth_role() = 'SUPER_ADMIN'
        OR (
            public.get_auth_role() = 'DEPARTMENT_MANAGER'
            AND department_id = public.get_auth_department_id()
        )
    )
    WITH CHECK (
        public.get_auth_role() = 'SUPER_ADMIN'
        OR (
            public.get_auth_role() = 'DEPARTMENT_MANAGER'
            AND department_id = public.get_auth_department_id()
        )
    );

CREATE POLICY "RLS Delete Financial Admissions Data"
    ON public.financial_admissions_data FOR DELETE
    TO authenticated
    USING (public.get_auth_role() = 'SUPER_ADMIN');

-- ------------------------------------------------------------------------------
-- D. AUDIT LOGS POLICIES
-- ------------------------------------------------------------------------------
CREATE POLICY "Admin view and manage audit logs"
    ON public.import_audit_logs FOR ALL
    TO authenticated
    USING (public.get_auth_role() = 'SUPER_ADMIN');

CREATE POLICY "CEO view audit logs"
    ON public.import_audit_logs FOR SELECT
    TO authenticated
    USING (public.get_auth_role() = 'CEO');
