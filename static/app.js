/**
 * CLEOPATRA HOSPITALS GROUP (CHG) - EXECUTIVE INTELLIGENCE PLATFORM
 * Core Frontend Application & Interactive Analytics Engine
 */

// Application Global State
const state = {
    token: localStorage.getItem('chg_auth_token') || sessionStorage.getItem('chg_auth_token') || null,
    user: null,
    departments: [],
    filters: {
        startDate: null,
        endDate: null,
        departmentId: 'all',
        payer: 'all',
        urgency: 'all',
        includeDuplicates: false
    },
    txPagination: {
        page: 1,
        limit: 20,
        total: 0,
        pages: 1,
        search: ''
    },
    charts: {
        monthlyTrends: null,
        departmentDonut: null,
        payers: null,
        urgency: null,
        diagnostics: null
    },
    activeTab: 'overview',
    pendingUpload: null,
    lang: localStorage.getItem('chg_lang') || 'en'
};

// Comprehensive Localization Dictionary (English & Arabic)
const I18N = {
    en: {
        brand_title: "CLEOPATRA HOSPITALS GROUP",
        brand_subtitle: "Enterprise Intelligence & RLS Analytics Platform",
        nav_overview: "Overview",
        nav_departments: "Department Matrix",
        nav_transactions: "Admissions Ledger",
        nav_import: "Data Import Engine",
        nav_users: "User Management",
        tab_executive_badge: "Executive",
        rls_protected_badge: "Department-Level RLS Protected",
        date_all_time: "All Time",
        all_departments: "All Clinical Departments",
        all_payers: "All Payers / Insurers",
        all_urgencies: "All Urgency Types",
        include_duplicates: "Include Raw Duplicates (5,500)",
        btn_reset: "Reset",
        reporting_period_prefix: "Reporting Period:",
        reporting_period_default: "May 2019 – May 2024 (5 Operating Years)",
        kpi_revenue_title: "Total Billed Revenue",
        kpi_admissions_title: "Total Admissions",
        kpi_avg_revenue_title: "Avg Billing / Patient",
        kpi_alos_title: "Avg Length of Stay (ALOS)",
        kpi_margin_title: "Gross Operating Margin",
        kpi_margin_note: "Benchmark Cost Ratio: 68%",
        kpi_target_title: "Annual Target Achievement",
        kpi_network_title: "Active Medical Network",
        kpi_adjustments_title: "Billing Adjustments / Refunds",
        chart_trends_title: "Monthly Revenue & Profitability Trajectory",
        chart_trends_sub: "Billed revenue vs estimated operating costs and gross margin over 5 operating years",
        chart_donut_title: "Specialty Contribution",
        chart_donut_sub: "Revenue split across clinical specialties",
        chart_payers_title: "Payer Market Share & Receivables",
        chart_payers_sub: "Revenue distribution by major insurance carrier",
        chart_urgency_title: "Admission Urgency Triage",
        chart_urgency_sub: "Elective vs Urgent vs Emergency patient admissions",
        chart_diagnostics_title: "Diagnostic Outcomes Quality",
        chart_diagnostics_sub: "Normal, Inconclusive, and Abnormal diagnostic rates",
        insights_title: "Executive Intelligence & Actionable Directives",
        insights_sub: "Automated diagnosis generated directly from live clinical & billing statistics",
        insights_badge: "CEO Briefing",
        tx_title: "Inpatient Admissions Financial Ledger",
        tx_new_btn: "New Admission",
        tx_export_btn: "Export CSV",
        tx_search_placeholder: "Search patient, doctor, unit...",
        login_email: "Corporate Email",
        login_password: "Password",
        login_remember: "Remember session",
        login_forgot: "Forgot password?",
        login_btn: "Sign In Securely",
        login_demo_title: "Fast Login Demo Accounts"
    },
    ar: {
        brand_title: "مجموعة مستشفيات كليوباترا",
        brand_subtitle: "منصة الذكاء التنفيذي والتحليلات المقيدة بالأقسام",
        nav_overview: "نظرة عامة",
        nav_departments: "مصفوفة الأقسام الطبية",
        nav_transactions: "سجل المرضى والمعاملات",
        nav_import: "محرك استيراد البيانات",
        nav_users: "إدارة المستخدمين والصلاحيات",
        tab_executive_badge: "تنفيذي",
        rls_protected_badge: "نظام حماية البيانات على مستوى الأقسام (RLS)",
        date_all_time: "كافة الفترات",
        all_departments: "كافة الأقسام الطبية",
        all_payers: "كافة شركات التأمين",
        all_urgencies: "كافة مستويات الاستعجال",
        include_duplicates: "تضمين السجلات المكررة الخام (5,500)",
        btn_reset: "إعادة تعيين",
        reporting_period_prefix: "فترة التقرير:",
        reporting_period_default: "مايو 2019 – مايو 2024 (5 سنوات تشغيلية)",
        kpi_revenue_title: "إجمالي الإيرادات المفوترة",
        kpi_admissions_title: "إجمالي حالات التنويم",
        kpi_avg_revenue_title: "متوسط الفاتورة لكل مريض",
        kpi_alos_title: "متوسط مدة الإقامة (ALOS)",
        kpi_margin_title: "هامش التشغيل الإجمالي",
        kpi_margin_note: "نسبة التكلفة المعيارية: 68%",
        kpi_target_title: "نسبة تحقيق المستهدف السنوي",
        kpi_network_title: "الشبكة الطبية النشطة",
        kpi_adjustments_title: "التسويات وفروق الفواتير",
        chart_trends_title: "مسار الإيرادات الشهرية والربحية",
        chart_trends_sub: "مقارنة الإيرادات المفوترة بالتكاليف التشغيلية وهامش الربح على مدار 5 سنوات",
        chart_donut_title: "نسبة مساهمة التخصصات الطبية",
        chart_donut_sub: "توزيع الإيرادات عبر التخصصات الطبية الستة",
        chart_payers_title: "الحصص السوقية لشركات التأمين",
        chart_payers_sub: "توزيع الإيرادات والمستحقات حسب كبرى جهات التأمين",
        chart_urgency_title: "تصنيف الحالات حسب درجة الاستعجال",
        chart_urgency_sub: "مقارنة حالات الطوارئ والعاجلة والاختيارية",
        chart_diagnostics_title: "جودة النتائج التشخيصية والمختبرية",
        chart_diagnostics_sub: "نسب النتائج الطبيعية وغير الحاسمة وغير الطبيعية",
        insights_title: "الرؤى التنفيذية والتوصيات الاستراتيجية",
        insights_sub: "تشخيص وتحليل آلي مشتق مباشرة من الإحصاءات السريرية والمالية الحية",
        insights_badge: "إحاطة الرئيس التنفيذي",
        tx_title: "سجل المرضى وحسابات الإقامة السريرية",
        tx_new_btn: "إضافة حالة جديدة",
        tx_export_btn: "تصدير CSV",
        tx_search_placeholder: "ابحث بالاسم، الطبيب، المستشفى...",
        login_email: "البريد الإلكتروني للشركة",
        login_password: "كلمة المرور",
        login_remember: "تذكر الجلسة",
        login_forgot: "نسيت كلمة المرور؟",
        login_btn: "تسجيل الدخول الآمن",
        login_demo_title: "حسابات تجريبية سريعة"
    }
};

// Brand Colors
const CHG_COLORS = {
    primary: '#0697A8',
    navy: '#023D4F',
    cyan: '#00B4D8',
    emerald: '#0D9488',
    amber: '#F59E0B',
    rose: '#EF4444',
    indigo: '#6366F1',
    palette: ['#0697A8', '#00B4D8', '#023D4F', '#0D9488', '#6366F1', '#F59E0B']
};

// -----------------------------------------------------------------------------
// INITIALIZATION
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
    initDarkMode();
    initLanguage();
    if (state.token) {
        try {
            await fetchCurrentUser();
            await initApp();
        } catch (e) {
            console.warn('Session expired or invalid token:', e);
            showLoginModal();
        }
    } else {
        showLoginModal();
    }

    // Window resize handler for ECharts
    window.addEventListener('resize', () => {
        Object.values(state.charts).forEach(c => c && c.resize());
    });
});

function initDarkMode() {
    if (localStorage.getItem('chg_theme') === 'dark' || 
        (!localStorage.getItem('chg_theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

function toggleDarkMode() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('chg_theme', isDark ? 'dark' : 'light');
    // Re-render charts with appropriate theme
    refreshAllCharts();
}

function initLanguage() {
    state.lang = localStorage.getItem('chg_lang') || 'en';
    applyLanguage();
}

function toggleLanguage() {
    state.lang = state.lang === 'ar' ? 'en' : 'ar';
    localStorage.setItem('chg_lang', state.lang);
    applyLanguage();
    refreshAllCharts();
    if (state.activeTab === 'departments') loadDepartmentDeepDive();
    if (state.activeTab === 'transactions') loadTransactions(state.txPagination.page);
}

function applyLanguage() {
    const isAr = state.lang === 'ar';
    document.documentElement.lang = state.lang;
    document.documentElement.dir = isAr ? 'rtl' : 'ltr';

    // Update Language Toggle Button Labels
    document.querySelectorAll('.lang-label-text').forEach(el => {
        el.innerText = isAr ? 'English' : 'العربية';
    });

    const dict = I18N[state.lang] || I18N.en;

    // Direct mapping to IDs or text
    const textMap = {
        'tab-btn-overview': `<i class="fa-solid fa-chart-line"></i> ${dict.nav_overview}`,
        'tab-btn-departments': `<i class="fa-solid fa-hospital-user"></i> ${dict.nav_departments}`,
        'tab-btn-transactions': `<i class="fa-solid fa-receipt"></i> ${dict.nav_transactions}`,
        'tab-btn-import': `<i class="fa-solid fa-cloud-arrow-up"></i> ${dict.nav_import}`,
        'tab-btn-users': `<i class="fa-solid fa-users-gear"></i> ${dict.nav_users}`,
    };

    Object.entries(textMap).forEach(([id, html]) => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
    });

    // Translate data-i18n elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            el.innerText = dict[key];
        }
    });

    // Update filter dropdown initial options
    const deptFirstOpt = document.querySelector('#filter-department option[value="all"]');
    if (deptFirstOpt) deptFirstOpt.text = dict.all_departments;
    const payerFirstOpt = document.querySelector('#filter-payer option[value="all"]');
    if (payerFirstOpt) payerFirstOpt.text = dict.all_payers;
    const urgencyFirstOpt = document.querySelector('#filter-urgency option[value="all"]');
    if (urgencyFirstOpt) urgencyFirstOpt.text = dict.all_urgencies;

    // Search placeholder
    const searchInput = document.getElementById('tx-search-input');
    if (searchInput) searchInput.placeholder = dict.tx_search_placeholder;
}

// -----------------------------------------------------------------------------
// AUTHENTICATION & SESSION
// -----------------------------------------------------------------------------
function showLoginModal() {
    document.getElementById('login-modal').classList.remove('hidden');
}

function hideLoginModal() {
    document.getElementById('login-modal').classList.add('hidden');
}

function togglePasswordVisibility(fieldId) {
    const input = document.getElementById(fieldId);
    const eye = document.getElementById('eye-' + fieldId);
    if (input.type === 'password') {
        input.type = 'text';
        eye.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        input.type = 'password';
        eye.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

function fillLogin(email, password) {
    document.getElementById('login-email').value = email;
    document.getElementById('login-password').value = password;
}

function showForgotPasswordInfo() {
    alert("For security in executive compliance, password resets must be issued by a Super Administrator from the User Management panel.");
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const remember = document.getElementById('remember-me').checked;
    const errorBox = document.getElementById('login-error');
    const submitBtn = document.getElementById('login-submit-btn');

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Authenticating...';
    errorBox.classList.add('hidden');

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Authentication failed');
        }

        const data = await res.json();
        state.token = data.access_token;
        state.user = data.user;

        if (remember) {
            localStorage.setItem('chg_auth_token', state.token);
            sessionStorage.removeItem('chg_auth_token');
        } else {
            sessionStorage.setItem('chg_auth_token', state.token);
            localStorage.removeItem('chg_auth_token');
        }

        hideLoginModal();
        await initApp();
    } catch (err) {
        errorBox.classList.remove('hidden');
        document.getElementById('login-error-text').innerText = err.message;
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Sign In Securely</span><i class="fa-solid fa-arrow-right text-xs"></i>';
    }
}

async function fetchCurrentUser() {
    const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch profile');
    state.user = await res.json();
}

function handleLogout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem('chg_auth_token');
    sessionStorage.removeItem('chg_auth_token');
    window.location.reload();
}

// -----------------------------------------------------------------------------
// APP INITIALIZATION & ROLE-BASED ACCESS CONTROL (RBAC & RLS)
// -----------------------------------------------------------------------------
async function initApp() {
    updateUserBadge();
    await loadDepartments();
    enforceRLSConstraints();
    await loadDashboardData();
}

function updateUserBadge() {
    const nameEl = document.getElementById('user-display-name');
    const roleEl = document.getElementById('user-display-role');
    const badgeContainer = document.getElementById('rls-badge-container');
    const badgeText = document.getElementById('rls-badge-text');
    const rlsIcon = document.getElementById('rls-icon');

    if (!state.user) return;

    nameEl.innerText = state.user.full_name;
    roleEl.innerText = `${state.user.role.replace('_', ' ')}`;

    // Show/hide Admin-only navigation
    const isAdmin = state.user.role === 'SUPER_ADMIN';
    document.querySelectorAll('.admin-only').forEach(el => {
        if (isAdmin) el.classList.remove('hidden');
        else el.classList.add('hidden');
    });

    // RLS Status Badge
    badgeContainer.classList.remove('hidden');
    const isAr = state.lang === 'ar';
    if (state.user.role === 'SUPER_ADMIN') {
        badgeContainer.className = 'hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border border-purple-200 dark:border-purple-800';
        badgeText.innerText = isAr ? 'مدير النظام (صلاحيات كاملة)' : 'Super Admin (Unrestricted)';
        rlsIcon.className = 'fa-solid fa-crown text-[10px]';
    } else if (state.user.role === 'CEO') {
        badgeContainer.className = 'hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-teal-50 text-chg-primary dark:bg-teal-950/60 dark:text-teal-300 border border-chg-primary/20';
        badgeText.innerText = isAr ? 'رؤية موحدة لكافة الأقسام' : 'Company-Wide Consolidated';
        rlsIcon.className = 'fa-solid fa-globe text-[10px]';
    } else {
        badgeContainer.className = 'hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800';
        badgeText.innerText = isAr ? `مقيد أمنياً: ${state.user.department_name || 'القسم'}` : `RLS Locked: ${state.user.department_name || 'Department'}`;
        rlsIcon.className = 'fa-solid fa-lock text-[10px]';
    }
}

async function loadDepartments() {
    try {
        const res = await fetch('/api/departments', {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        state.departments = await res.json();
        
        const select = document.getElementById('filter-department');
        select.innerHTML = '';
        
        if (state.user.role === 'SUPER_ADMIN' || state.user.role === 'CEO') {
            const allOpt = document.createElement('option');
            allOpt.value = 'all';
            allOpt.text = 'All Clinical Departments';
            select.appendChild(allOpt);
        }

        state.departments.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.id;
            opt.text = `${d.department_name} (${d.clinical_specialty})`;
            select.appendChild(opt);
        });

        // Also populate modal department dropdown
        const modalSelect = document.getElementById('user-modal-department');
        modalSelect.innerHTML = '<option value="">No Department (Company-wide / Admin)</option>';
        state.departments.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.id;
            opt.text = `${d.department_name} (${d.clinical_specialty})`;
            modalSelect.appendChild(opt);
        });

    } catch (e) {
        console.error('Error loading departments:', e);
    }
}

function enforceRLSConstraints() {
    const deptSelect = document.getElementById('filter-department');
    const lockIcon = document.getElementById('dept-lock-icon');

    if (state.user.role === 'DEPARTMENT_MANAGER' || state.user.role === 'VIEWER') {
        // Enforce lock on UI
        deptSelect.value = state.user.department_id;
        deptSelect.disabled = true;
        lockIcon.classList.remove('hidden');
        state.filters.departmentId = state.user.department_id;
    } else {
        deptSelect.disabled = false;
        lockIcon.classList.add('hidden');
        state.filters.departmentId = 'all';
    }
}

// -----------------------------------------------------------------------------
// TAB NAVIGATION
// -----------------------------------------------------------------------------
function switchTab(tabName) {
    state.activeTab = tabName;

    // Toggle active tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('text-chg-primary', 'bg-teal-50', 'dark:bg-slate-800', 'dark:text-teal-400');
        btn.classList.add('text-slate-600', 'dark:text-slate-400');
    });
    const activeBtn = document.getElementById(`tab-btn-${tabName}`);
    if (activeBtn) {
        activeBtn.classList.remove('text-slate-600', 'dark:text-slate-400');
        activeBtn.classList.add('text-chg-primary', 'bg-teal-50', 'dark:bg-slate-800', 'dark:text-teal-400');
    }

    // Toggle views
    ['overview', 'departments', 'transactions', 'import', 'users'].forEach(view => {
        const viewEl = document.getElementById(`view-${view}`);
        if (viewEl) {
            if (view === tabName) viewEl.classList.remove('hidden');
            else viewEl.classList.add('hidden');
        }
    });

    if (tabName === 'overview') {
        refreshAllCharts();
    } else if (tabName === 'departments') {
        loadDepartmentDeepDive();
    } else if (tabName === 'transactions') {
        loadTransactions(1);
    } else if (tabName === 'users') {
        loadUsersTable();
    } else if (tabName === 'import') {
        loadImportHistory();
    }
}

// -----------------------------------------------------------------------------
// FILTER CONTROLS & EVENT HANDLERS
// -----------------------------------------------------------------------------
function setDateRange(year) {
    document.querySelectorAll('.date-chip').forEach(btn => {
        btn.classList.remove('bg-white', 'dark:bg-slate-700', 'text-chg-primary', 'shadow-xs');
        btn.classList.add('text-slate-600', 'dark:text-slate-400');
    });
    event.target.classList.add('bg-white', 'dark:bg-slate-700', 'text-chg-primary', 'shadow-xs');

    const periodLabel = document.getElementById('active-period-label');
    if (year === 'all') {
        state.filters.startDate = null;
        state.filters.endDate = null;
        periodLabel.innerText = 'May 2019 – May 2024 (5 Operating Years)';
    } else {
        state.filters.startDate = `${year}-01-01`;
        state.filters.endDate = `${year}-12-31`;
        periodLabel.innerText = `Calendar Operating Year ${year}`;
    }
    applyFilters();
}

function applyFilters() {
    if (state.user.role === 'SUPER_ADMIN' || state.user.role === 'CEO') {
        state.filters.departmentId = document.getElementById('filter-department').value;
    } else {
        state.filters.departmentId = state.user.department_id;
    }
    state.filters.payer = document.getElementById('filter-payer').value;
    state.filters.urgency = document.getElementById('filter-urgency').value;
    state.filters.includeDuplicates = document.getElementById('toggle-duplicates').checked;

    loadDashboardData();
    if (state.activeTab === 'departments') loadDepartmentDeepDive();
    if (state.activeTab === 'transactions') loadTransactions(1);
}

function resetFilters() {
    state.filters.startDate = null;
    state.filters.endDate = null;
    state.filters.payer = 'all';
    state.filters.urgency = 'all';
    state.filters.includeDuplicates = false;

    document.getElementById('filter-payer').value = 'all';
    document.getElementById('filter-urgency').value = 'all';
    document.getElementById('toggle-duplicates').checked = false;
    document.getElementById('active-period-label').innerText = 'May 2019 – May 2024 (5 Operating Years)';

    if (state.user.role === 'SUPER_ADMIN' || state.user.role === 'CEO') {
        document.getElementById('filter-department').value = 'all';
        state.filters.departmentId = 'all';
    }

    applyFilters();
}

function buildQueryString() {
    const params = new URLSearchParams();
    if (state.filters.startDate) params.append('start_date', state.filters.startDate);
    if (state.filters.endDate) params.append('end_date', state.filters.endDate);
    if (state.filters.departmentId && state.filters.departmentId !== 'all') params.append('department_id', state.filters.departmentId);
    if (state.filters.payer && state.filters.payer !== 'all') params.append('payer', state.filters.payer);
    if (state.filters.urgency && state.filters.urgency !== 'all') params.append('urgency', state.filters.urgency);
    if (state.filters.includeDuplicates) params.append('include_duplicates', 'true');
    return params.toString();
}

// -----------------------------------------------------------------------------
// DATA LOADING & DASHBOARD LOGIC
// -----------------------------------------------------------------------------
async function loadDashboardData() {
    const qs = buildQueryString();
    try {
        // Fetch KPIs, Trends, Breakdowns, Insights in parallel
        const [kpiRes, trendsRes, breakdownsRes, insightsRes] = await Promise.all([
            fetch(`/api/analytics/kpis?${qs}`, { headers: { 'Authorization': `Bearer ${state.token}` } }),
            fetch(`/api/analytics/monthly-trends?${qs}`, { headers: { 'Authorization': `Bearer ${state.token}` } }),
            fetch(`/api/analytics/operational-breakdowns?${qs}`, { headers: { 'Authorization': `Bearer ${state.token}` } }),
            fetch(`/api/analytics/executive-insights?${qs}`, { headers: { 'Authorization': `Bearer ${state.token}` } })
        ]);

        if (kpiRes.ok) {
            const kpiData = await kpiRes.json();
            renderKPIs(kpiData);
        }
        if (trendsRes.ok) {
            const trendsData = await trendsRes.json();
            renderMonthlyTrendsChart(trendsData);
        }
        if (breakdownsRes.ok) {
            const breakdownData = await breakdownsRes.json();
            renderOperationalCharts(breakdownData);
        }
        if (insightsRes.ok) {
            const insightsData = await insightsRes.json();
            renderExecutiveInsights(insightsData);
        }

        // Also fetch department breakdown for Donut chart
        const deptRes = await fetch(`/api/analytics/department-breakdown?${qs}`, { headers: { 'Authorization': `Bearer ${state.token}` } });
        if (deptRes.ok) {
            const deptData = await deptRes.json();
            renderDepartmentDonut(deptData);
        }

    } catch (e) {
        console.error('Error fetching dashboard metrics:', e);
    }
}

function formatCurrency(num) {
    if (Math.abs(num) >= 1e9) return '$' + (num / 1e9).toFixed(2) + ' B';
    if (Math.abs(num) >= 1e6) return '$' + (num / 1e6).toFixed(2) + ' M';
    if (Math.abs(num) >= 1e3) return '$' + (num / 1e3).toFixed(1) + ' K';
    return '$' + Number(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function renderKPIs(data) {
    document.getElementById('kpi-revenue').innerText = formatCurrency(data.total_revenue);
    document.getElementById('kpi-admissions').innerText = Number(data.total_admissions).toLocaleString();
    document.getElementById('kpi-avg-revenue').innerText = formatCurrency(data.avg_revenue_per_patient);
    document.getElementById('kpi-alos').innerText = `${data.avg_length_of_stay} Days`;

    document.getElementById('kpi-margin').innerText = `${data.profit_margin_pct}%`;
    document.getElementById('kpi-target-pct').innerText = `${data.target_achievement_pct}%`;
    document.getElementById('kpi-budget-note').innerText = `Target: ${formatCurrency(data.annual_target)}`;

    document.getElementById('kpi-network').innerText = `${Number(data.active_physicians).toLocaleString()} Doctors`;
    document.getElementById('kpi-facilities-note').innerText = `In ${Number(data.active_facilities).toLocaleString()} Clinical Units`;

    document.getElementById('kpi-adjustments').innerText = formatCurrency(data.total_adjustments);
    document.getElementById('kpi-adjustments-count').innerText = `${data.adjustment_count} negative audit records`;
}

// -----------------------------------------------------------------------------
// APACHE ECHARTS VISUALIZATIONS
// -----------------------------------------------------------------------------
function isDarkTheme() {
    return document.documentElement.classList.contains('dark');
}

function refreshAllCharts() {
    setTimeout(() => {
        Object.values(state.charts).forEach(c => c && c.resize());
    }, 50);
}

function renderMonthlyTrendsChart(trends) {
    const dom = document.getElementById('chart-monthly-trends');
    if (!dom) return;
    if (state.charts.monthlyTrends) state.charts.monthlyTrends.dispose();

    state.charts.monthlyTrends = echarts.init(dom, isDarkTheme() ? 'dark' : null);

    const periods = trends.map(t => t.period);
    const revenues = trends.map(t => t.revenue);
    const profits = trends.map(t => t.profit);

    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross', label: { backgroundColor: '#023D4F' } },
            formatter: (params) => {
                let html = `<div class="font-bold mb-1">${params[0].axisValue}</div>`;
                params.forEach(p => {
                    html += `<div class="flex items-center justify-between gap-4 text-xs">
                        <span>${p.marker} ${p.seriesName}:</span>
                        <strong>$${Number(p.value).toLocaleString('en-US', {minimumFractionDigits: 2})}</strong>
                    </div>`;
                });
                return html;
            }
        },
        grid: { top: 20, right: 20, bottom: 40, left: 60 },
        xAxis: {
            type: 'category',
            data: periods,
            axisLine: { lineStyle: { color: isDarkTheme() ? '#334155' : '#E2E8F0' } },
            axisLabel: { color: isDarkTheme() ? '#94A3B8' : '#64748B', fontSize: 10 }
        },
        yAxis: {
            type: 'value',
            splitLine: { lineStyle: { color: isDarkTheme() ? '#1E293B' : '#F1F5F9' } },
            axisLabel: {
                color: isDarkTheme() ? '#94A3B8' : '#64748B',
                fontSize: 10,
                formatter: (val) => '$' + (val / 1e6).toFixed(0) + 'M'
            }
        },
        series: [
            {
                name: 'Gross Revenue',
                type: 'bar',
                data: revenues,
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#0697A8' },
                        { offset: 1, color: '#023D4F' }
                    ]),
                    borderRadius: [4, 4, 0, 0]
                }
            },
            {
                name: 'Gross Profit',
                type: 'line',
                smooth: true,
                data: profits,
                itemStyle: { color: '#00B4D8' },
                lineStyle: { width: 3 },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(0, 180, 216, 0.35)' },
                        { offset: 1, color: 'rgba(0, 180, 216, 0.0)' }
                    ])
                }
            }
        ]
    };

    state.charts.monthlyTrends.setOption(option);
}

function renderDepartmentDonut(deptData) {
    const dom = document.getElementById('chart-department-donut');
    if (!dom) return;
    if (state.charts.departmentDonut) state.charts.departmentDonut.dispose();

    state.charts.departmentDonut = echarts.init(dom, isDarkTheme() ? 'dark' : null);

    const pieData = deptData.map(d => ({
        name: d.clinical_specialty,
        value: d.revenue
    }));

    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'item',
            formatter: (p) => `<strong>${p.name}</strong><br/>Revenue: $${Number(p.value).toLocaleString()}<br/>Share: <strong>${p.percent}%</strong>`
        },
        color: CHG_COLORS.palette,
        series: [
            {
                name: 'Specialty Share',
                type: 'pie',
                radius: ['45%', '75%'],
                center: ['50%', '50%'],
                avoidLabelOverlap: true,
                itemStyle: {
                    borderRadius: 6,
                    borderColor: isDarkTheme() ? '#0f172a' : '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false,
                    position: 'center'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 12,
                        fontWeight: 'bold',
                        formatter: '{b}\n{d}%'
                    }
                },
                data: pieData
            }
        ]
    };

    state.charts.departmentDonut.setOption(option);
}

function renderOperationalCharts(data) {
    // 1. Payers
    const payersDom = document.getElementById('chart-payers-breakdown');
    if (payersDom) {
        if (state.charts.payers) state.charts.payers.dispose();
        state.charts.payers = echarts.init(payersDom, isDarkTheme() ? 'dark' : null);
        state.charts.payers.setOption({
            backgroundColor: 'transparent',
            tooltip: { trigger: 'item', formatter: '{b}: ${c} ({d}%)' },
            color: ['#0697A8', '#00B4D8', '#0D9488', '#6366F1', '#38BDF8'],
            series: [{
                type: 'pie',
                radius: '65%',
                data: data.payers.map(p => ({ name: p.name, value: p.revenue }))
            }]
        });
    }

    // 2. Admission Urgency
    const urgencyDom = document.getElementById('chart-urgency-breakdown');
    if (urgencyDom) {
        if (state.charts.urgency) state.charts.urgency.dispose();
        state.charts.urgency = echarts.init(urgencyDom, isDarkTheme() ? 'dark' : null);
        state.charts.urgency.setOption({
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis' },
            xAxis: {
                type: 'category',
                data: data.urgencies.map(u => u.urgency),
                axisLabel: { color: isDarkTheme() ? '#94A3B8' : '#64748B', fontSize: 10 }
            },
            yAxis: {
                type: 'value',
                axisLabel: { color: isDarkTheme() ? '#94A3B8' : '#64748B', fontSize: 10 }
            },
            series: [{
                type: 'bar',
                data: data.urgencies.map(u => u.count),
                itemStyle: { color: '#0697A8', borderRadius: [4, 4, 0, 0] }
            }]
        });
    }

    // 3. Diagnostics Quality
    const diagDom = document.getElementById('chart-diagnostics-breakdown');
    if (diagDom) {
        if (state.charts.diagnostics) state.charts.diagnostics.dispose();
        state.charts.diagnostics = echarts.init(diagDom, isDarkTheme() ? 'dark' : null);
        state.charts.diagnostics.setOption({
            backgroundColor: 'transparent',
            tooltip: { trigger: 'item', formatter: '{b}: {c} patients ({d}%)' },
            color: ['#0D9488', '#F59E0B', '#EF4444'],
            series: [{
                type: 'pie',
                radius: ['35%', '65%'],
                data: data.diagnostics.map(d => ({ name: d.outcome, value: d.count }))
            }]
        });
    }
}

// -----------------------------------------------------------------------------
// EXECUTIVE INSIGHTS COMPONENT
// -----------------------------------------------------------------------------
function renderExecutiveInsights(insights) {
    const container = document.getElementById('executive-insights-container');
    if (!insights || !insights.length) {
        container.innerHTML = '<div class="text-xs text-slate-400">No active alerts detected.</div>';
        return;
    }

    container.innerHTML = insights.map(i => {
        let borderClass = 'border-l-4 border-l-chg-primary';
        let badgeBg = 'bg-teal-50 dark:bg-teal-950/60 text-chg-primary';
        let icon = 'fa-lightbulb';

        if (i.type === 'warning') {
            borderClass = 'border-l-4 border-l-amber-500';
            badgeBg = 'bg-amber-50 dark:bg-amber-950/60 text-amber-600';
            icon = 'fa-triangle-exclamation';
        } else if (i.type === 'positive') {
            borderClass = 'border-l-4 border-l-emerald-500';
            badgeBg = 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600';
            icon = 'fa-circle-arrow-up';
        }

        const isAr = state.lang === 'ar';
        const lblFinding = isAr ? 'الملاحظة:' : 'Finding:';
        const lblImpact = isAr ? 'الأثر المالي / التشغيلي:' : 'Impact:';
        const lblAction = isAr ? 'الإجراء التنفيذي المقترح:' : 'Recommended Action:';

        return `
            <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 ${borderClass} space-y-2">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-xs text-slate-900 dark:text-white flex items-center gap-2">
                        <i class="fa-solid ${icon}"></i> ${i.title}
                    </span>
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded ${badgeBg}">${i.affected_unit}</span>
                </div>
                <p class="text-xs text-slate-600 dark:text-slate-300"><strong>${lblFinding}</strong> ${i.what_happened}</p>
                <div class="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2">
                    <span>${lblImpact} <strong class="text-slate-800 dark:text-slate-200">${i.numerical_impact}</strong></span>
                </div>
                <div class="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
                    <strong class="text-chg-primary">${lblAction}</strong> ${i.action_required}
                </div>
            </div>
        `;
    }).join('');
}

// -----------------------------------------------------------------------------
// DEPARTMENT DEEP DIVE VIEW
// -----------------------------------------------------------------------------
async function loadDepartmentDeepDive() {
    const qs = buildQueryString();
    try {
        const res = await fetch(`/api/analytics/department-breakdown?${qs}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const depts = await res.json();

        // Cards grid
        const cardsGrid = document.getElementById('dept-cards-grid');
        cardsGrid.innerHTML = depts.map(d => `
            <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm chg-card-hover">
                <div class="flex items-center justify-between mb-3">
                    <h4 class="font-bold text-sm text-slate-900 dark:text-white">${d.department_name}</h4>
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-50 dark:bg-teal-950/60 text-chg-primary">${d.clinical_specialty}</span>
                </div>
                <div class="text-xl font-extrabold text-chg-navy dark:text-white mb-2">${formatCurrency(d.revenue)}</div>
                <div class="grid grid-cols-2 gap-2 text-xs text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <div>Admissions: <strong class="text-slate-800 dark:text-slate-200">${Number(d.admissions).toLocaleString()}</strong></div>
                    <div>Avg Stay: <strong class="text-slate-800 dark:text-slate-200">${d.avg_los} days</strong></div>
                    <div>Avg / Pt: <strong class="text-slate-800 dark:text-slate-200">${formatCurrency(d.avg_revenue)}</strong></div>
                    <div>Share: <strong class="text-chg-primary font-bold">${d.contribution_pct}%</strong></div>
                </div>
            </div>
        `).join('');

        // Table body
        const tbody = document.getElementById('dept-table-body');
        tbody.innerHTML = depts.map(d => `
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td class="p-3.5 font-bold text-slate-900 dark:text-white">${d.department_name}</td>
                <td class="p-3.5 text-slate-500">${d.clinical_specialty}</td>
                <td class="p-3.5 text-right">${Number(d.admissions).toLocaleString()}</td>
                <td class="p-3.5 text-right font-bold text-slate-900 dark:text-white">${formatCurrency(d.revenue)}</td>
                <td class="p-3.5 text-right">${formatCurrency(d.avg_revenue)}</td>
                <td class="p-3.5 text-right">${d.avg_los} d</td>
                <td class="p-3.5 text-right font-bold text-chg-primary">${d.contribution_pct}%</td>
            </tr>
        `).join('');

    } catch (e) {
        console.error('Error in department deep dive:', e);
    }
}

// -----------------------------------------------------------------------------
// DETAILED INPATIENT TRANSACTIONS LEDGER
// -----------------------------------------------------------------------------
let searchTimeout = null;
function handleTxSearch(e) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        state.txPagination.search = e.target.value.trim();
        loadTransactions(1);
    }, 300);
}

function changeTxPage(delta) {
    const newPage = state.txPagination.page + delta;
    if (newPage >= 1 && newPage <= state.txPagination.pages) {
        loadTransactions(newPage);
    }
}

async function loadTransactions(page = 1) {
    state.txPagination.page = page;
    const qs = buildQueryString();
    const searchParam = state.txPagination.search ? `&search=${encodeURIComponent(state.txPagination.search)}` : '';
    
    try {
        const res = await fetch(`/api/transactions?page=${page}&limit=${state.txPagination.limit}${searchParam}&${qs}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const data = await res.json();

        state.txPagination.total = data.total;
        state.txPagination.pages = data.pages;

        document.getElementById('transactions-count-summary').innerText = 
            `Displaying ${Number(data.records.length).toLocaleString()} of ${Number(data.total).toLocaleString()} authorized inpatient records`;
        document.getElementById('tx-page-info').innerText = `Page ${data.page} of ${Math.max(1, data.pages)}`;
        document.getElementById('tx-prev-btn').disabled = data.page <= 1;
        document.getElementById('tx-next-btn').disabled = data.page >= data.pages;

        const tbody = document.getElementById('tx-table-body');
        if (!data.records.length) {
            tbody.innerHTML = '<tr><td colspan="11" class="p-6 text-center text-slate-400">No records found matching current criteria.</td></tr>';
            return;
        }

        tbody.innerHTML = data.records.map(r => {
            const isNegative = r.gross_billing_amount < 0;
            const amountClass = isNegative ? 'text-rose-600 font-bold' : 'text-slate-900 dark:text-white font-bold';
            
            let outcomeBadge = 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300';
            if (r.diagnostic_outcome === 'Abnormal') outcomeBadge = 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300';
            else if (r.diagnostic_outcome === 'Inconclusive') outcomeBadge = 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300';

            return `
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td class="p-3 font-mono text-[11px] text-slate-400">${r.transaction_reference}</td>
                    <td class="p-3 font-bold text-slate-800 dark:text-slate-200">
                        ${r.patient_name} <span class="font-normal text-slate-400 text-[10px]">(${r.age}y, ${r.gender})</span>
                    </td>
                    <td class="p-3 text-slate-600 dark:text-slate-400">${r.department_name}</td>
                    <td class="p-3 text-slate-500">${r.admission_date}</td>
                    <td class="p-3">${r.length_of_stay_days}d</td>
                    <td class="p-3 text-slate-600 dark:text-slate-400">${r.attending_physician}</td>
                    <td class="p-3 text-slate-500 truncate max-w-[140px]" title="${r.hospital_branch}">${r.hospital_branch}</td>
                    <td class="p-3 text-slate-600 dark:text-slate-400">${r.insurance_payer}</td>
                    <td class="p-3 text-right ${amountClass}">
                        ${isNegative ? '-' : ''}$${Math.abs(r.gross_billing_amount).toLocaleString('en-US', {minimumFractionDigits: 2})}
                    </td>
                    <td class="p-3 text-center">
                        <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                            ${r.admission_urgency}
                        </span>
                    </td>
                    <td class="p-3 text-center">
                        <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${outcomeBadge}">
                            ${r.diagnostic_outcome}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (e) {
        console.error('Error loading transactions:', e);
    }
}

function exportTransactionsCSV() {
    const qs = buildQueryString();
    window.location.href = `/api/transactions/export?format=csv&${qs}`;
}

// -----------------------------------------------------------------------------
// NEW ADMISSION MODAL & REAL-TIME INTERACTIVE ENTRY
// -----------------------------------------------------------------------------
function openCreateTxModal() {
    const modal = document.getElementById('tx-modal');
    const deptSelect = document.getElementById('tx-department');
    
    // Set default dates
    const today = new Date().toISOString().split('T')[0];
    const discharge = new Date(Date.now() + 5 * 86400000).toISOString().split('T')[0];
    document.getElementById('tx-admission-date').value = today;
    document.getElementById('tx-discharge-date').value = discharge;

    // Populate departments
    deptSelect.innerHTML = '';
    state.departments.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.text = `${d.department_name} (${d.clinical_specialty})`;
        deptSelect.appendChild(opt);
    });

    // If Department Manager, lock to their assigned department (RLS)
    if (state.user.role === 'DEPARTMENT_MANAGER' || state.user.role === 'VIEWER') {
        deptSelect.value = state.user.department_id;
        deptSelect.disabled = true;
    } else {
        deptSelect.disabled = false;
    }

    modal.classList.remove('hidden');
}

function closeCreateTxModal() {
    document.getElementById('tx-modal').classList.add('hidden');
}

async function saveTransaction(e) {
    e.preventDefault();
    const saveBtn = document.getElementById('tx-save-btn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

    const payload = {
        patient_name: document.getElementById('tx-patient-name').value.trim(),
        age: parseInt(document.getElementById('tx-patient-age').value),
        gender: document.getElementById('tx-patient-gender').value,
        blood_type: document.getElementById('tx-patient-blood').value,
        department_id: document.getElementById('tx-department').value,
        admission_date: document.getElementById('tx-admission-date').value,
        discharge_date: document.getElementById('tx-discharge-date').value,
        attending_physician: document.getElementById('tx-doctor').value.trim(),
        hospital_branch: document.getElementById('tx-hospital').value.trim(),
        insurance_payer: document.getElementById('tx-payer').value,
        gross_billing_amount: parseFloat(document.getElementById('tx-billing').value),
        room_number: parseInt(document.getElementById('tx-room').value) || null,
        admission_urgency: document.getElementById('tx-urgency').value,
        prescribed_medication: "Standard Care",
        diagnostic_outcome: document.getElementById('tx-outcome').value
    };

    try {
        const res = await fetch('/api/transactions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to record admission');
        }

        const data = await res.json();
        alert(`Admission recorded successfully!\nRef: ${data.transaction_reference}\nAll dashboard KPIs & charts have been refreshed.`);
        
        closeCreateTxModal();
        // Immediately reload all interactive data
        await loadDashboardData();
        await loadTransactions(1);
        if (state.activeTab === 'departments') await loadDepartmentDeepDive();
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save & Refresh Analytics';
    }
}

// -----------------------------------------------------------------------------
// ADMIN DATA IMPORT & COLUMN MAPPING ENGINE
// -----------------------------------------------------------------------------
async function handleFileSelected(e) {
    const file = e.target.files[0];
    if (!file) return;

    state.pendingUpload = file;
    const formData = new FormData();
    formData.append('file', file);

    const mappingContainer = document.getElementById('mapping-container');
    mappingContainer.classList.remove('hidden');
    document.getElementById('mapping-file-info').innerText = `Analyzing schema for: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;

    try {
        const res = await fetch('/api/admin/upload-preview', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` },
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to inspect file');
        }

        const data = await res.json();
        renderMappingTable(data);
    } catch (err) {
        alert('File Inspection Error: ' + err.message);
    }
}

function renderMappingTable(data) {
    const tbody = document.getElementById('mapping-table-body');
    const headers = data.headers;
    const suggested = data.suggested_mapping;
    const preview = data.preview_rows || [];

    tbody.innerHTML = data.standard_targets.map(std => {
        const selectedCol = suggested[std.key] || '';
        const sampleVal = preview.length > 0 && selectedCol ? preview[0][headers.indexOf(selectedCol)] || '—' : '—';

        const optionsHtml = headers.map(h => `
            <option value="${h}" ${h === selectedCol ? 'selected' : ''}>${h}</option>
        `).join('');

        return `
            <tr>
                <td class="p-3 font-bold text-slate-800 dark:text-slate-200">
                    ${std.label}
                    <input type="hidden" class="mapping-key" value="${std.key}">
                </td>
                <td class="p-3">
                    ${std.required ? '<span class="text-rose-600 font-bold">* Required</span>' : '<span class="text-slate-400">Optional</span>'}
                </td>
                <td class="p-3">
                    <select class="mapping-select px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-800 dark:text-slate-200 outline-none w-full">
                        <option value="">-- Do Not Map --</option>
                        ${optionsHtml}
                    </select>
                </td>
                <td class="p-3 text-slate-500 font-mono text-[11px] truncate max-w-xs">${sampleVal}</td>
            </tr>
        `;
    }).join('');
}

async function commitFileImport() {
    if (!state.pendingUpload) return;

    const commitBtn = document.getElementById('commit-import-btn');
    commitBtn.disabled = true;
    commitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing & Ingesting...';

    // Collect mappings
    const mapping = {};
    const keys = document.querySelectorAll('.mapping-key');
    const selects = document.querySelectorAll('.mapping-select');
    for (let i = 0; i < keys.length; i++) {
        if (selects[i].value) {
            mapping[keys[i].value] = selects[i].value;
        }
    }

    const formData = new FormData();
    formData.append('file', state.pendingUpload);
    formData.append('column_mapping_json', JSON.stringify(mapping));
    formData.append('append_mode', 'true');

    try {
        const res = await fetch('/api/admin/import-commit', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` },
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Import failed');
        }

        const result = await res.json();
        alert(`Import Successful!\nTotal Rows: ${result.total_rows}\nImported: ${result.imported}\nDuplicates Flagged: ${result.duplicates_flagged}\nRejected (Unmapped): ${result.rejected_unmapped}`);
        
        document.getElementById('mapping-container').classList.add('hidden');
        document.getElementById('file-upload-input').value = '';
        state.pendingUpload = null;
        loadImportHistory();
        loadDashboardData();
    } catch (err) {
        alert('Ingestion Error: ' + err.message);
    } finally {
        commitBtn.disabled = false;
        commitBtn.innerHTML = '<i class="fa-solid fa-check-double"></i> Validate & Ingest Dataset';
    }
}

async function loadImportHistory() {
    try {
        const res = await fetch('/api/admin/import-history', {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const logs = await res.json();
        const tbody = document.getElementById('import-history-body');
        tbody.innerHTML = logs.map(l => `
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td class="p-3 font-mono text-[11px] text-slate-400">${l.id.slice(0, 8)}...</td>
                <td class="p-3 font-bold text-slate-800 dark:text-slate-200">${l.file_name}</td>
                <td class="p-3 text-right">${Number(l.total_records).toLocaleString()}</td>
                <td class="p-3 text-right font-bold text-emerald-600">${Number(l.imported_records).toLocaleString()}</td>
                <td class="p-3 text-right text-amber-600">${Number(l.duplicate_records).toLocaleString()}</td>
                <td class="p-3 text-right text-rose-600">${Number(l.rejected_records).toLocaleString()}</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">${l.status}</span></td>
                <td class="p-3 text-slate-400">${l.created_at}</td>
                <td class="p-3 text-center">
                    <button onclick="deleteImportBatch('${l.id}', '${l.file_name}')" class="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 dark:hover:bg-rose-900/60 rounded-lg text-xs font-semibold transition inline-flex items-center gap-1 shadow-xs" title="حذف الدفعة وسجلاتها">
                        <i class="fa-solid fa-trash-can"></i> حذف
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Error loading import history:', e);
    }
}

async function deleteImportBatch(batchId, fileName) {
    if (!confirm(`هل تريد بالتأكيد حذف ملف الاستيراد "${fileName}" وجميع السجلات (55,500) المرتبطة به؟`)) return;
    try {
        const res = await fetch(`/api/admin/import-batches/${batchId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'فشل حذف دفعة الاستيراد');
        }
        const data = await res.json();
        alert(`تم الحذف بنجاح!\n${data.message}`);
        await loadImportHistory();
        await loadDashboardData();
        await loadTransactions(1);
    } catch (e) {
        alert('حدث خطأ: ' + e.message);
    }
}

// -----------------------------------------------------------------------------
// ADMIN USER ACCESS MANAGEMENT & RLS
// -----------------------------------------------------------------------------
async function loadUsersTable() {
    try {
        const res = await fetch('/api/admin/users', {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const users = await res.json();
        const tbody = document.getElementById('users-table-body');
        
        tbody.innerHTML = users.map(u => {
            const roleBadgeClass = u.role === 'SUPER_ADMIN' ? 'bg-purple-50 text-purple-700' :
                u.role === 'CEO' ? 'bg-teal-50 text-chg-primary' : 'bg-slate-100 text-slate-700';

            return `
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td class="p-3 font-bold text-slate-900 dark:text-white">${u.full_name}</td>
                    <td class="p-3 text-slate-500">${u.email}</td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${roleBadgeClass}">${u.role}</span></td>
                    <td class="p-3 text-slate-600 dark:text-slate-300">
                        ${u.department_name ? `🔒 ${u.department_name}` : '<span class="text-slate-400">All Departments</span>'}
                    </td>
                    <td class="p-3">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${u.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}">
                            ${u.is_active ? 'Active' : 'Disabled'}
                        </span>
                    </td>
                    <td class="p-3 text-slate-400">${u.last_login_at || 'Never'}</td>
                    <td class="p-3 text-right">
                        <button onclick="editUser('${u.id}', '${u.full_name}', '${u.email}', '${u.role}', '${u.department_id || ''}', ${u.is_active})"
                            class="px-2 py-1 rounded text-xs text-chg-primary hover:bg-teal-50 dark:hover:bg-slate-800 font-semibold mr-1">
                            Edit
                        </button>
                        <button onclick="toggleUserStatus('${u.id}', ${u.is_active ? 0 : 1})"
                            class="px-2 py-1 rounded text-xs ${u.is_active ? 'text-rose-600 hover:bg-rose-50' : 'text-emerald-600 hover:bg-emerald-50'} font-semibold">
                            ${u.is_active ? 'Disable' : 'Activate'}
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Error loading users table:', e);
    }
}

function openCreateUserModal() {
    document.getElementById('user-modal-title').innerText = 'Create New Corporate User';
    document.getElementById('user-modal-id').value = '';
    document.getElementById('user-modal-name').value = '';
    document.getElementById('user-modal-email').value = '';
    document.getElementById('user-modal-email').disabled = false;
    document.getElementById('user-modal-password').value = '';
    document.getElementById('user-modal-password').required = true;
    document.getElementById('user-modal-role').value = 'VIEWER';
    document.getElementById('user-modal-department').value = '';
    document.getElementById('user-modal-active').checked = true;
    handleModalRoleChange();
    document.getElementById('user-modal').classList.remove('hidden');
}

function editUser(id, name, email, role, departmentId, isActive) {
    document.getElementById('user-modal-title').innerText = 'Edit Corporate User Profile';
    document.getElementById('user-modal-id').value = id;
    document.getElementById('user-modal-name').value = name;
    document.getElementById('user-modal-email').value = email;
    document.getElementById('user-modal-email').disabled = true; // Email immutable in edit
    document.getElementById('user-modal-password').value = '';
    document.getElementById('user-modal-password').required = false;
    document.getElementById('user-modal-password-label').innerText = 'New Password (Leave blank to keep unchanged)';
    document.getElementById('user-modal-role').value = role;
    document.getElementById('user-modal-department').value = departmentId;
    document.getElementById('user-modal-active').checked = Boolean(isActive);
    handleModalRoleChange();
    document.getElementById('user-modal').classList.remove('hidden');
}

function handleModalRoleChange() {
    const role = document.getElementById('user-modal-role').value;
    const deptSelect = document.getElementById('user-modal-department');
    if (role === 'DEPARTMENT_MANAGER' || role === 'VIEWER') {
        deptSelect.required = true;
    } else {
        deptSelect.required = false;
    }
}

function closeUserModal() {
    document.getElementById('user-modal').classList.add('hidden');
}

async function saveUser(e) {
    e.preventDefault();
    const id = document.getElementById('user-modal-id').value;
    const fullName = document.getElementById('user-modal-name').value.trim();
    const email = document.getElementById('user-modal-email').value.trim();
    const password = document.getElementById('user-modal-password').value;
    const role = document.getElementById('user-modal-role').value;
    const departmentId = document.getElementById('user-modal-department').value || null;
    const isActive = document.getElementById('user-modal-active').checked;

    try {
        if (!id) {
            // Create user
            const res = await fetch('/api/admin/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${state.token}`
                },
                body: JSON.stringify({
                    email,
                    full_name: fullName,
                    password,
                    role,
                    department_id: departmentId,
                    is_active: isActive
                })
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Could not create user');
            }
        } else {
            // Update user
            const payload = {
                full_name: fullName,
                role,
                department_id: departmentId,
                is_active: isActive
            };
            if (password) payload.password = password;

            const res = await fetch(`/api/admin/users/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${state.token}`
                },
                body: JSON.stringify(payload)
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Could not update user');
            }
        }
        closeUserModal();
        loadUsersTable();
    } catch (err) {
        alert('User Error: ' + err.message);
    }
}

async function toggleUserStatus(userId, newStatus) {
    if (!confirm(`Are you sure you want to ${newStatus ? 'activate' : 'disable'} this user account?`)) return;
    try {
        const res = await fetch(`/api/admin/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ is_active: Boolean(newStatus) })
        });
        if (!res.ok) throw new Error('Action failed');
        loadUsersTable();
    } catch (err) {
        alert(err.message);
    }
}
