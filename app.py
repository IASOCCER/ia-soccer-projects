import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import io
import json
import shutil

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="IA Soccer Projects Pro V8",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path("ia_soccer_projects.db")
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

PROJECT_TYPES = [
    "Camp", "Voyage", "Tryout", "Événement",
    "Partenariat", "Formation", "Projet interne", "Autre"
]

PROJECT_STATUS = [
    "Idée", "En préparation", "En vente", "Confirmé",
    "En exécution", "Fermé", "Annulé"
]

TASK_STATUS = ["À faire", "En cours", "Terminé", "Bloqué"]
PRIORITIES = ["Haute", "Moyenne", "Basse"]
ENTRY_TYPES = ["Revenue", "Cost"]
PAYMENT_STATUS = ["Prévu", "Confirmé", "Payé", "Partiel", "En attente"]

st.markdown("""
<style>
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}
div[data-testid="stMetric"] {
    background: #f7f9fc;
    border: 1px solid #e6ebf2;
    padding: 12px 16px;
    border-radius: 14px;
}
.card {
    background: white;
    border: 1px solid #e6ebf2;
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
}
.kanban-col {
    background: #fafbfc;
    border: 1px solid #dde4ee;
    border-radius: 16px;
    padding: 12px;
    min-height: 280px;
}
.task-card {
    background: white;
    border: 1px solid #e6ebf2;
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE
# =========================================================

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_df(query, params=()):
    conn = get_conn()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
    return df


def execute(query, params=()):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        lastrowid = cur.lastrowid
    finally:
        conn.close()
    return lastrowid


def executescript(script):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.executescript(script)
        conn.commit()
    finally:
        conn.close()


def init_db():
    executescript("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        project_type TEXT,
        city TEXT,
        country TEXT,
        main_location TEXT,
        start_date TEXT,
        end_date TEXT,
        main_responsible TEXT,
        project_status TEXT DEFAULT 'Idée',
        priority TEXT DEFAULT 'Moyenne',
        short_description TEXT,
        expected_revenue REAL DEFAULT 0,
        expected_cost REAL DEFAULT 0,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS phases (
        phase_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        phase_name TEXT NOT NULL,
        phase_order INTEGER DEFAULT 1,
        phase_start_date TEXT,
        phase_end_date TEXT,
        phase_status TEXT DEFAULT 'À faire'
    );

    CREATE TABLE IF NOT EXISTS tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        phase_id INTEGER,
        task_name TEXT NOT NULL,
        task_responsible TEXT,
        task_due_date TEXT,
        task_status TEXT DEFAULT 'À faire',
        task_priority TEXT DEFAULT 'Moyenne',
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS budget (
        budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        entry_type TEXT NOT NULL,
        category TEXT,
        description TEXT,
        budget_scope TEXT DEFAULT 'Général',
        unit_count REAL DEFAULT 1,
        unit_amount REAL DEFAULT 0,
        expected_amount REAL DEFAULT 0,
        real_amount REAL DEFAULT 0,
        payment_status TEXT DEFAULT 'Prévu'
    );

    CREATE TABLE IF NOT EXISTS people (
        person_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        role_title TEXT,
        email TEXT,
        phone TEXT,
        project_id INTEGER
    );
    """)


init_db()

# =========================================================
# HELPERS
# =========================================================

def fmt_money(v):
    try:
        return f"${float(v):,.0f}"
    except Exception:
        return "$0"


def parse_date_or_none(value):
    if value in (None, "", "None"):
        return None
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def create_db_backup():
    if DB_PATH.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"ia_soccer_projects_backup_{ts}.db"
        shutil.copy2(DB_PATH, backup_file)
        return backup_file
    return None


def auto_backup_once_per_day():
    today_key = datetime.now().strftime("%Y%m%d")
    marker = BACKUP_DIR / f".last_backup_{today_key}"
    if DB_PATH.exists() and not marker.exists():
        create_db_backup()
        marker.write_text("ok", encoding="utf-8")


def list_backups():
    return sorted(BACKUP_DIR.glob("*.db"), reverse=True)


def restore_db(uploaded_file):
    try:
        with open(DB_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True, "Backup restauré avec succès."
    except Exception as e:
        return False, str(e)


def export_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        fetch_df("SELECT * FROM projects").to_excel(writer, sheet_name="projects", index=False)
        fetch_df("SELECT * FROM phases").to_excel(writer, sheet_name="phases", index=False)
        fetch_df("SELECT * FROM tasks").to_excel(writer, sheet_name="tasks", index=False)
        fetch_df("SELECT * FROM budget").to_excel(writer, sheet_name="budget", index=False)
        fetch_df("SELECT * FROM people").to_excel(writer, sheet_name="people", index=False)
    output.seek(0)
    return output.getvalue()


def export_json():
    data = {
        "projects": fetch_df("SELECT * FROM projects").to_dict(orient="records"),
        "phases": fetch_df("SELECT * FROM phases").to_dict(orient="records"),
        "tasks": fetch_df("SELECT * FROM tasks").to_dict(orient="records"),
        "budget": fetch_df("SELECT * FROM budget").to_dict(orient="records"),
        "people": fetch_df("SELECT * FROM people").to_dict(orient="records"),
    }
    return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")


def recalc_project_totals(project_id):
    budget = fetch_df("SELECT * FROM budget WHERE project_id = ?", (project_id,))
    if budget.empty:
        rev = 0
        cost = 0
    else:
        budget["expected_amount"] = pd.to_numeric(budget["expected_amount"], errors="coerce").fillna(0)
        rev = budget.loc[budget["entry_type"] == "Revenue", "expected_amount"].sum()
        cost = budget.loc[budget["entry_type"] == "Cost", "expected_amount"].sum()

    execute(
        "UPDATE projects SET expected_revenue = ?, expected_cost = ?, updated_at = CURRENT_TIMESTAMP WHERE project_id = ?",
        (float(rev), float(cost), int(project_id))
    )


def get_project_progress():
    projects = fetch_df("SELECT project_id, project_name FROM projects ORDER BY start_date")
    tasks = fetch_df("SELECT project_id, task_status FROM tasks")
    rows = []

    for _, p in projects.iterrows():
        pt = tasks[tasks["project_id"] == p["project_id"]]
        total = len(pt)
        done = len(pt[pt["task_status"] == "Terminé"])
        progress = round((done / total) * 100, 1) if total > 0 else 0
        rows.append({
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "tasks_total": total,
            "tasks_done": done,
            "progress_pct": progress,
        })

    return pd.DataFrame(rows)


def get_real_totals():
    budget = fetch_df("SELECT * FROM budget")
    if budget.empty:
        return 0, 0, 0
    budget["real_amount"] = pd.to_numeric(budget["real_amount"], errors="coerce").fillna(0)
    real_rev = budget.loc[budget["entry_type"] == "Revenue", "real_amount"].sum()
    real_cost = budget.loc[budget["entry_type"] == "Cost", "real_amount"].sum()
    return real_rev, real_cost, real_rev - real_cost


def get_overdue_urgent_counts():
    tasks = fetch_df("SELECT task_due_date, task_status FROM tasks")
    if tasks.empty:
        return 0, 0

    tasks["due_dt"] = pd.to_datetime(tasks["task_due_date"], errors="coerce")
    today_ts = pd.Timestamp.today().normalize()

    overdue = len(tasks[
        (tasks["due_dt"].notna()) &
        (tasks["due_dt"] < today_ts) &
        (tasks["task_status"] != "Terminé")
    ])

    urgent = len(tasks[
        (tasks["due_dt"].notna()) &
        (tasks["due_dt"] <= today_ts) &
        (tasks["task_status"] != "Terminé")
    ])

    return overdue, urgent


def get_urgent_tasks(limit=15):
    df = fetch_df("""
        SELECT t.task_id, p.project_name, COALESCE(ph.phase_name, '-') AS phase_name,
               t.task_name, t.task_responsible, t.task_due_date, t.task_status, t.task_priority
        FROM tasks t
        JOIN projects p ON p.project_id = t.project_id
        LEFT JOIN phases ph ON ph.phase_id = t.phase_id
        WHERE t.task_status != 'Terminé'
    """)
    if df.empty:
        return df

    df["due_dt"] = pd.to_datetime(df["task_due_date"], errors="coerce")
    today_ts = pd.Timestamp.today().normalize()
    df["days_left"] = (df["due_dt"] - today_ts).dt.days

    def tag(x):
        if pd.isna(x):
            return "À suivre"
        if x < 0:
            return "En retard"
        if x == 0:
            return "Aujourd’hui"
        if x <= 7:
            return "Urgent"
        return "À suivre"

    df["alert"] = df["days_left"].apply(tag)
    priority_map = {"Haute": 0, "Moyenne": 1, "Basse": 2}
    df["p_sort"] = df["task_priority"].map(priority_map).fillna(1)
    df["d_sort"] = df["days_left"].fillna(9999)
    df = df.sort_values(["d_sort", "p_sort", "project_name"])
    return df.head(limit)


def global_search(term):
    like = f"%{term}%"
    p = fetch_df("""
        SELECT 'Projet' AS source, project_name AS title, city AS subinfo
        FROM projects
        WHERE project_name LIKE ? OR city LIKE ? OR main_location LIKE ? OR short_description LIKE ?
    """, (like, like, like, like))

    t = fetch_df("""
        SELECT 'Tâche' AS source, task_name AS title, task_responsible AS subinfo
        FROM tasks
        WHERE task_name LIKE ? OR task_responsible LIKE ? OR notes LIKE ?
    """, (like, like, like))

    b = fetch_df("""
        SELECT 'Budget' AS source, description AS title, category AS subinfo
        FROM budget
        WHERE description LIKE ? OR category LIKE ?
    """, (like, like))

    pe = fetch_df("""
        SELECT 'Équipe' AS source, full_name AS title, role_title AS subinfo
        FROM people
        WHERE full_name LIKE ? OR role_title LIKE ? OR email LIKE ?
    """, (like, like, like))

    return pd.concat([p, t, b, pe], ignore_index=True)


def seed_demo_if_empty():
    df = fetch_df("SELECT COUNT(*) AS c FROM projects")
    if int(df.iloc[0]["c"]) > 0:
        return

    pid = execute("""
        INSERT INTO projects
        (project_name, project_type, city, country, main_location, start_date, end_date,
         main_responsible, project_status, priority, short_description, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "FC Porto World Camp Brossard",
        "Camp",
        "Brossard",
        "Canada",
        "Complexe CN",
        "2026-06-29",
        "2026-07-03",
        "Rogerio Crespo",
        "En vente",
        "Haute",
        "Camp officiel de développement",
        "Projet démo"
    ))

    phase1 = execute("""
        INSERT INTO phases (project_id, phase_name, phase_order, phase_start_date, phase_end_date, phase_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (pid, "Planification", 1, "2026-03-01", "2026-04-01", "En cours"))

    phase2 = execute("""
        INSERT INTO phases (project_id, phase_name, phase_order, phase_start_date, phase_end_date, phase_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (pid, "Marketing", 2, "2026-04-02", "2026-05-15", "À faire"))

    execute("""
        INSERT INTO tasks (project_id, phase_id, task_name, task_responsible, task_due_date, task_status, task_priority, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (pid, phase1, "Confirmer les dates", "Rogerio", "2026-03-20", "En cours", "Haute", ""))

    execute("""
        INSERT INTO tasks (project_id, phase_id, task_name, task_responsible, task_due_date, task_status, task_priority, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (pid, phase2, "Créer les flyers", "Marketing", "2026-04-10", "À faire", "Moyenne", ""))

    execute("""
        INSERT INTO budget
        (project_id, entry_type, category, description, budget_scope, unit_count, unit_amount, expected_amount, real_amount, payment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pid, "Revenue", "Inscriptions", "Camp fees", "Général", 1, 58800, 58800, 0, "Prévu"))

    execute("""
        INSERT INTO budget
        (project_id, entry_type, category, description, budget_scope, unit_count, unit_amount, expected_amount, real_amount, payment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pid, "Cost", "Terrain", "Location terrain", "Général", 1, 8000, 8000, 0, "Prévu"))

    execute("""
        INSERT INTO people (full_name, role_title, email, phone, project_id)
        VALUES (?, ?, ?, ?, ?)
    """, ("Rogerio Crespo", "Directeur technique", "", "", pid))

    recalc_project_totals(pid)


seed_demo_if_empty()
auto_backup_once_per_day()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚽ IA Soccer Projects Pro V8")
search_term = st.sidebar.text_input("Recherche globale")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Projets", "Nouveau projet", "Timeline", "Tâches", "Board", "Budget", "Équipe", "Analytics", "Backup"]
)

if search_term:
    st.sidebar.markdown("### Résultats")
    results = global_search(search_term)
    if results.empty:
        st.sidebar.info("Aucun résultat")
    else:
        st.sidebar.dataframe(results.head(12), use_container_width=True, hide_index=True)

# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":
    st.title("Dashboard exécutif")

    count, rev, cost, profit = metrics()
    real_rev, real_cost, real_profit = get_real_totals()
    overdue, urgent = get_overdue_urgent_counts()

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Projets", count)
    m2.metric("Revenue prévu", fmt_money(rev))
    m3.metric("Cost prévu", fmt_money(cost))
    m4.metric("Profit prévu", fmt_money(profit))
    m5.metric("Tâches urgentes", urgent)
    m6.metric("En retard", overdue)

    x1, x2, x3 = st.columns(3)
    x1.metric("Revenue réel", fmt_money(real_rev))
    x2.metric("Cost réel", fmt_money(real_cost))
    x3.metric("Profit réel", fmt_money(real_profit))

    projects = fetch_df("SELECT * FROM projects ORDER BY start_date")
    progress = get_project_progress()

    if not projects.empty and not progress.empty:
        projects = projects.merge(progress[["project_id", "progress_pct"]], on="project_id", how="left")

    c1, c2 = st.columns([1.2, 1])

    with c1:
        st.subheader("Vue projets")
        if projects.empty:
            st.info("Aucun projet.")
        else:
            st.dataframe(
                projects[[
                    "project_name", "project_type", "city", "start_date", "end_date",
                    "project_status", "priority", "expected_revenue", "expected_cost", "progress_pct"
                ]],
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Finance par projet")
            chart_df = projects[["project_name", "expected_revenue", "expected_cost"]].copy().set_index("project_name")
            st.bar_chart(chart_df)

    with c2:
        st.subheader("Tâches urgentes")
        urgent_tasks = get_urgent_tasks()
        if urgent_tasks.empty:
            st.success("Aucune tâche urgente.")
        else:
            st.dataframe(
                urgent_tasks[[
                    "project_name", "phase_name", "task_name", "task_responsible",
                    "task_due_date", "task_priority", "alert"
                ]],
                use_container_width=True,
                hide_index=True
            )

# =========================================================
# PROJECTS
# =========================================================

elif page == "Projets":
    st.title("Projets")

    projects = fetch_df("SELECT * FROM projects ORDER BY start_date")
    progress = get_project_progress()

    if not projects.empty and not progress.empty:
        projects = projects.merge(progress[["project_id", "progress_pct"]], on="project_id", how="left")

    st.dataframe(projects, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Modifier un projet")

    if not projects.empty:
        selected = st.selectbox(
            "Projet",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )

        row = projects[projects["project_id"] == selected].iloc[0]

        with st.form("edit_project"):
            c1, c2 = st.columns(2)
            project_name = c1.text_input("Nom du projet", value=row["project_name"])
            project_type = c2.selectbox(
                "Type",
                PROJECT_TYPES,
                index=PROJECT_TYPES.index(row["project_type"]) if row["project_type"] in PROJECT_TYPES else 0
            )

            c3, c4 = st.columns(2)
            city = c3.text_input("Ville", value=row["city"] or "")
            country = c4.text_input("Pays", value=row["country"] or "")

            main_location = st.text_input("Lieu principal", value=row["main_location"] or "")

            c5, c6 = st.columns(2)
            start_date = c5.date_input("Date début", value=parse_date_or_none(row["start_date"]) or date.today())
            end_date = c6.date_input("Date fin", value=parse_date_or_none(row["end_date"]) or date.today())

            c7, c8, c9 = st.columns(3)
            main_responsible = c7.text_input("Responsable", value=row["main_responsible"] or "")
            project_status = c8.selectbox(
                "Statut",
                PROJECT_STATUS,
                index=PROJECT_STATUS.index(row["project_status"]) if row["project_status"] in PROJECT_STATUS else 0
            )
            priority = c9.selectbox(
                "Priorité",
                PRIORITIES,
                index=PRIORITIES.index(row["priority"]) if row["priority"] in PRIORITIES else 1
            )

            short_description = st.text_area("Description", value=row["short_description"] or "")
            notes = st.text_area("Notes internes", value=row["notes"] or "")

            if st.form_submit_button("Enregistrer projet"):
                execute("""
                    UPDATE projects SET
                        project_name=?,
                        project_type=?,
                        city=?,
                        country=?,
                        main_location=?,
                        start_date=?,
                        end_date=?,
                        main_responsible=?,
                        project_status=?,
                        priority=?,
                        short_description=?,
                        notes=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE project_id=?
                """, (
                    project_name, project_type, city, country, main_location,
                    str(start_date), str(end_date), main_responsible,
                    project_status, priority, short_description, notes, int(selected)
                ))
                st.success("Projet mis à jour.")
                st.rerun()

        confirm_delete = st.checkbox("Je confirme la suppression du projet")
        if st.button("Supprimer le projet"):
            if not confirm_delete:
                st.error("Confirme la suppression.")
            else:
                execute("DELETE FROM tasks WHERE project_id = ?", (int(selected),))
                execute("DELETE FROM phases WHERE project_id = ?", (int(selected),))
                execute("DELETE FROM budget WHERE project_id = ?", (int(selected),))
                execute("DELETE FROM people WHERE project_id = ?", (int(selected),))
                execute("DELETE FROM projects WHERE project_id = ?", (int(selected),))
                st.success("Projet supprimé.")
                st.rerun()

# =========================================================
# NEW PROJECT
# =========================================================

elif page == "Nouveau projet":
    st.title("Nouveau projet")

    with st.form("new_project"):
        c1, c2 = st.columns(2)
        project_name = c1.text_input("Nom du projet")
        project_type = c2.selectbox("Type", PROJECT_TYPES)

        c3, c4 = st.columns(2)
        city = c3.text_input("Ville")
        country = c4.text_input("Pays", value="Canada")

        main_location = st.text_input("Lieu principal")

        c5, c6 = st.columns(2)
        start_date = c5.date_input("Date début", value=date.today())
        end_date = c6.date_input("Date fin", value=date.today())

        c7, c8, c9 = st.columns(3)
        main_responsible = c7.text_input("Responsable")
        project_status = c8.selectbox("Statut", PROJECT_STATUS, index=1)
        priority = c9.selectbox("Priorité", PRIORITIES, index=1)

        short_description = st.text_area("Description")
        notes = st.text_area("Notes internes")

        if st.form_submit_button("Créer le projet"):
            if not project_name:
                st.error("Le nom du projet est obligatoire.")
            else:
                execute("""
                    INSERT INTO projects
                    (project_name, project_type, city, country, main_location,
                     start_date, end_date, main_responsible, project_status,
                     priority, short_description, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_name, project_type, city, country, main_location,
                    str(start_date), str(end_date), main_responsible,
                    project_status, priority, short_description, notes
                ))
                st.success("Projet créé avec succès.")
                st.rerun()

# =========================================================
# TIMELINE
# =========================================================

elif page == "Timeline":
    st.title("Timeline")

    projects = fetch_df("SELECT project_id, project_name FROM projects ORDER BY start_date")
    if projects.empty:
        st.info("Aucun projet.")
    else:
        selected = st.selectbox(
            "Projet",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )

        phases = fetch_df("""
            SELECT phase_id, phase_name, phase_order, phase_start_date, phase_end_date, phase_status
            FROM phases
            WHERE project_id = ?
            ORDER BY phase_order
        """, (int(selected),))

        if phases.empty:
            st.info("Aucune phase.")
        else:
            st.dataframe(phases, use_container_width=True, hide_index=True)

            ph = phases.copy()
            ph["phase_start_date"] = pd.to_datetime(ph["phase_start_date"], errors="coerce")
            ph["phase_end_date"] = pd.to_datetime(ph["phase_end_date"], errors="coerce")
            ph["duration_days"] = (ph["phase_end_date"] - ph["phase_start_date"]).dt.days.fillna(0)
            st.subheader("Durée des phases")
            st.bar_chart(ph.set_index("phase_name")[["duration_days"]])

        with st.form("add_phase"):
            st.subheader("Ajouter une phase")
            a1, a2 = st.columns(2)
            phase_name = a1.text_input("Nom de la phase")
            phase_order = a2.number_input("Ordre", min_value=1, value=1, step=1)
            a3, a4 = st.columns(2)
            phase_start = a3.date_input("Début", value=date.today())
            phase_end = a4.date_input("Fin", value=date.today())
            phase_status = st.selectbox("Statut", TASK_STATUS)

            if st.form_submit_button("Ajouter phase"):
                if phase_name:
                    execute("""
                        INSERT INTO phases (project_id, phase_name, phase_order, phase_start_date, phase_end_date, phase_status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (int(selected), phase_name, int(phase_order), str(phase_start), str(phase_end), phase_status))
                    st.success("Phase ajoutée.")
                    st.rerun()

# =========================================================
# TASKS
# =========================================================

elif page == "Tâches":
    st.title("Tâches")

    tasks = fetch_df("""
        SELECT t.task_id, p.project_name, COALESCE(ph.phase_name, '-') AS phase_name,
               t.task_name, t.task_responsible, t.task_due_date,
               t.task_status, t.task_priority, t.notes, t.project_id
        FROM tasks t
        JOIN projects p ON p.project_id = t.project_id
        LEFT JOIN phases ph ON ph.phase_id = t.phase_id
        ORDER BY t.task_due_date, t.task_priority
    """)

    if not tasks.empty:
        f1, f2, f3, f4 = st.columns(4)
        project_filter = f1.selectbox("Projet", ["Tous"] + sorted(tasks["project_name"].dropna().unique().tolist()))
        status_filter = f2.selectbox("Statut", ["Tous"] + TASK_STATUS)
        priority_filter = f3.selectbox("Priorité", ["Tous"] + PRIORITIES)
        only_overdue = f4.checkbox("Seulement en retard")

        filtered = tasks.copy()
        if project_filter != "Tous":
            filtered = filtered[filtered["project_name"] == project_filter]
        if status_filter != "Tous":
            filtered = filtered[filtered["task_status"] == status_filter]
        if priority_filter != "Tous":
            filtered = filtered[filtered["task_priority"] == priority_filter]
        if only_overdue:
            filtered["due_dt"] = pd.to_datetime(filtered["task_due_date"], errors="coerce")
            today_ts = pd.Timestamp.today().normalize()
            filtered = filtered[
                (filtered["due_dt"].notna()) &
                (filtered["due_dt"] < today_ts) &
                (filtered["task_status"] != "Terminé")
            ]

        st.dataframe(filtered, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune tâche.")

    projects = fetch_df("SELECT project_id, project_name FROM projects ORDER BY start_date")
    if not projects.empty:
        selected_project = st.selectbox(
            "Projet pour nouvelle tâche",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )
        phases = fetch_df("SELECT phase_id, phase_name FROM phases WHERE project_id = ? ORDER BY phase_order", (int(selected_project),))

        with st.form("add_task"):
            st.subheader("Ajouter une tâche")
            t1, t2 = st.columns(2)
            task_name = t1.text_input("Nom de la tâche")
            task_responsible = t2.text_input("Responsable")

            t3, t4 = st.columns(2)
            task_due_date = t3.date_input("Date limite", value=date.today())
            task_status = t4.selectbox("Statut", TASK_STATUS)

            t5, t6 = st.columns(2)
            task_priority = t5.selectbox("Priorité", PRIORITIES)
            phase_options = [None] + phases["phase_id"].tolist() if not phases.empty else [None]
            phase_id = t6.selectbox(
                "Phase",
                phase_options,
                format_func=lambda x: "Sans phase" if x is None else phases.loc[phases.phase_id == x, "phase_name"].iloc[0]
            )

            notes = st.text_input("Notes")

            if st.form_submit_button("Ajouter tâche"):
                if task_name:
                    execute("""
                        INSERT INTO tasks
                        (project_id, phase_id, task_name, task_responsible, task_due_date, task_status, task_priority, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        int(selected_project), phase_id, task_name, task_responsible,
                        str(task_due_date), task_status, task_priority, notes
                    ))
                    st.success("Tâche ajoutée.")
                    st.rerun()

# =========================================================
# BOARD
# =========================================================

elif page == "Board":
    st.title("Board des tâches")

    df = fetch_df("""
        SELECT t.task_id, p.project_name, t.task_name, t.task_responsible,
               t.task_due_date, t.task_status, t.task_priority, t.notes
        FROM tasks t
        JOIN projects p ON p.project_id = t.project_id
        ORDER BY t.task_due_date
    """)

    if df.empty:
        st.info("Aucune tâche.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        cols = {
            "À faire": c1,
            "En cours": c2,
            "Bloqué": c3,
            "Terminé": c4,
        }

        for status_name, col in cols.items():
            with col:
                st.markdown(f'<div class="kanban-col"><h4>{status_name}</h4>', unsafe_allow_html=True)
                subset = df[df["task_status"] == status_name]
                if subset.empty:
                    st.caption("Aucune tâche")
                else:
                    for _, r in subset.iterrows():
                        due = r["task_due_date"] if pd.notna(r["task_due_date"]) else "-"
                        st.markdown(
                            f"""
                            <div class="task-card">
                                <b>{r['task_name']}</b><br>
                                Projet: {r['project_name']}<br>
                                Responsable: {r['task_responsible'] or '-'}<br>
                                Date: {due}<br>
                                Priorité: {r['task_priority']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# BUDGET
# =========================================================

elif page == "Budget":
    st.title("Budget")

    projects = fetch_df("SELECT project_id, project_name FROM projects ORDER BY start_date")
    if projects.empty:
        st.info("Aucun projet.")
    else:
        selected = st.selectbox(
            "Projet",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )

        budget = fetch_df("""
            SELECT budget_id, entry_type, category, description, budget_scope,
                   unit_count, unit_amount, expected_amount, real_amount, payment_status
            FROM budget
            WHERE project_id = ?
            ORDER BY entry_type DESC, category, description
        """, (int(selected),))

        if not budget.empty:
            rev = pd.to_numeric(budget.loc[budget["entry_type"] == "Revenue", "expected_amount"], errors="coerce").fillna(0).sum()
            cost = pd.to_numeric(budget.loc[budget["entry_type"] == "Cost", "expected_amount"], errors="coerce").fillna(0).sum()
            real_rev = pd.to_numeric(budget.loc[budget["entry_type"] == "Revenue", "real_amount"], errors="coerce").fillna(0).sum()
            real_cost = pd.to_numeric(budget.loc[budget["entry_type"] == "Cost", "real_amount"], errors="coerce").fillna(0).sum()

            a1, a2, a3, a4 = st.columns(4)
            a1.metric("Revenue prévu", fmt_money(rev))
            a2.metric("Cost prévu", fmt_money(cost))
            a3.metric("Profit prévu", fmt_money(rev - cost))
            a4.metric("Profit réel", fmt_money(real_rev - real_cost))

            st.dataframe(budget, use_container_width=True, hide_index=True)

            st.subheader("Prévu par type")
            chart_df = budget.groupby("entry_type")["expected_amount"].sum().reset_index().set_index("entry_type")
            st.bar_chart(chart_df)

        with st.form("add_budget"):
            st.subheader("Ajouter ligne budget")
            b1, b2, b3 = st.columns(3)
            entry_type = b1.selectbox("Type", ENTRY_TYPES)
            category = b2.text_input("Catégorie")
            description = b3.text_input("Description")

            c1, c2 = st.columns(2)
            unit_count = c1.number_input("Quantité", min_value=1.0, value=1.0, step=1.0)
            unit_amount = c2.number_input("Montant unitaire", min_value=0.0, value=0.0, step=50.0)

            expected_amount = float(unit_count * unit_amount)

            d1, d2 = st.columns(2)
            real_amount = d1.number_input("Montant réel", min_value=0.0, value=0.0, step=50.0)
            payment_status = d2.selectbox("État", PAYMENT_STATUS)

            if st.form_submit_button("Ajouter ligne"):
                execute("""
                    INSERT INTO budget
                    (project_id, entry_type, category, description, budget_scope, unit_count, unit_amount, expected_amount, real_amount, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(selected), entry_type, category, description, "Général",
                    float(unit_count), float(unit_amount), float(expected_amount),
                    float(real_amount), payment_status
                ))
                recalc_project_totals(int(selected))
                st.success("Ligne ajoutée.")
                st.rerun()

# =========================================================
# PEOPLE
# =========================================================

elif page == "Équipe":
    st.title("Équipe")

    people = fetch_df("""
        SELECT person_id, full_name, role_title, email, phone, project_id
        FROM people
        ORDER BY full_name
    """)
    st.dataframe(people, use_container_width=True, hide_index=True)

    projects = fetch_df("SELECT project_id, project_name FROM projects ORDER BY start_date")

    with st.form("add_person"):
        st.subheader("Ajouter une personne")
        p1, p2 = st.columns(2)
        full_name = p1.text_input("Nom complet")
        role_title = p2.text_input("Rôle")

        p3, p4 = st.columns(2)
        email = p3.text_input("Email")
        phone = p4.text_input("Téléphone")

        project_id = st.selectbox(
            "Projet lié",
            [None] + projects["project_id"].tolist() if not projects.empty else [None],
            format_func=lambda x: "Aucun projet" if x is None else projects.loc[projects.project_id == x, "project_name"].iloc[0]
        )

        if st.form_submit_button("Ajouter personne"):
            if full_name:
                execute("""
                    INSERT INTO people (full_name, role_title, email, phone, project_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (full_name, role_title, email, phone, project_id))
                st.success("Personne ajoutée.")
                st.rerun()

# =========================================================
# ANALYTICS
# =========================================================

elif page == "Analytics":
    st.title("Analytics")

    projects = fetch_df("SELECT * FROM projects")
    tasks = fetch_df("SELECT * FROM tasks")
    budget = fetch_df("SELECT * FROM budget")
    progress = get_project_progress()

    if not projects.empty:
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Projets par statut")
            chart1 = projects.groupby("project_status").size().reset_index(name="count").set_index("project_status")
            st.bar_chart(chart1)

        with c2:
            st.subheader("Projets par type")
            chart2 = projects.groupby("project_type").size().reset_index(name="count").set_index("project_type")
            st.bar_chart(chart2)

    if not tasks.empty:
        c3, c4 = st.columns(2)

        with c3:
            st.subheader("Tâches par statut")
            chart3 = tasks.groupby("task_status").size().reset_index(name="count").set_index("task_status")
            st.bar_chart(chart3)

        with c4:
            st.subheader("Tâches par priorité")
            chart4 = tasks.groupby("task_priority").size().reset_index(name="count").set_index("task_priority")
            st.bar_chart(chart4)

    if not progress.empty:
        st.subheader("Progression des projets")
        st.bar_chart(progress.set_index("project_name")[["progress_pct"]])

    if not budget.empty:
        st.subheader("Budget par catégorie")
        chart5 = budget.groupby("category")["expected_amount"].sum().reset_index().set_index("category")
        st.bar_chart(chart5)

# =========================================================
# BACKUP
# =========================================================

elif page == "Backup":
    st.title("Backup et restauration")

    if DB_PATH.exists():
        st.download_button(
            "Télécharger la base .db",
            data=DB_PATH.read_bytes(),
            file_name="ia_soccer_projects.db",
            mime="application/octet-stream"
        )

    if st.button("Créer un backup maintenant"):
        b = create_db_backup()
        if b:
            st.success(f"Backup créé: {b.name}")

    backups = list_backups()
    if backups:
        st.subheader("Backups locaux")
        st.dataframe(pd.DataFrame({"backup": [b.name for b in backups]}), use_container_width=True, hide_index=True)

    uploaded = st.file_uploader("Restaurer un fichier .db", type=["db"])
    if uploaded is not None:
        if st.button("Restaurer ce backup"):
            ok, msg = restore_db(uploaded)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.subheader("Exports")
    st.download_button(
        "Télécharger export Excel",
        data=export_excel(),
        file_name="ia_soccer_projects_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        "Télécharger export JSON",
        data=export_json(),
        file_name="ia_soccer_projects_export.json",
        mime="application/json"
    )
