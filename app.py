import sqlite3
from pathlib import Path
from datetime import date, datetime
import pandas as pd
import streamlit as st
import shutil
import io
import json

DB_PATH = Path(__file__).with_name("ia_soccer_projects.db")
BACKUP_DIR = Path(__file__).with_name("backups")
BACKUP_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="IA Soccer Projects Pro V7",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_TYPES = [
    "Camp", "Voyage", "Tryout", "Événement",
    "Partenariat", "Formation", "Projet interne", "Autre"
]
PROJECT_STATUS = ["Idée", "En préparation", "En vente", "Confirmé", "En exécution", "Fermé", "Annulé"]
PRIORITIES = ["Haute", "Moyenne", "Basse"]
TASK_STATUS = ["À faire", "En cours", "Terminé", "Bloqué"]
PAYMENT_STATUS = ["Prévu", "Confirmé", "Payé", "Partiel", "En attente"]
ENTRY_TYPES = ["Revenue", "Cost"]
BUDGET_SCOPE = ["Général", "Par personne"]

TEMPLATES = {
    "Camp": {
        "phases": [
            ("Planification", 1),
            ("Marketing", 2),
            ("Inscriptions", 3),
            ("Staff", 4),
            ("Logistique", 5),
            ("Exécution", 6),
            ("Clôture", 7),
        ],
        "tasks": {
            "Planification": [
                "Confirmer les dates",
                "Confirmer le terrain",
                "Définir le prix",
                "Créer le formulaire",
            ],
            "Marketing": [
                "Créer Meta Ads",
                "Créer les flyers",
                "Envoyer l'email marketing",
                "Contacter les clubs",
            ],
            "Inscriptions": [
                "Suivre les inscriptions",
                "Recevoir les dépôts",
                "Confirmer les paiements",
                "Mettre à jour la liste",
            ],
            "Staff": [
                "Confirmer les entraîneurs",
                "Créer les groupes",
            ],
            "Logistique": [
                "Commander le matériel",
                "Préparer les kits",
                "Créer les groupes WhatsApp",
            ],
            "Exécution": [
                "Check-in",
                "Sessions d'entraînement",
                "Photos et vidéos",
            ],
            "Clôture": [
                "Envoyer les certificats",
                "Rapport final",
            ],
        },
        "budget": [
            ("Revenue", "Inscriptions", "Camp fees", "Général", 1, 58800),
            ("Revenue", "Sponsors", "Sponsors", "Général", 1, 0),
            ("Cost", "Terrain", "Location terrain", "Général", 1, 8000),
            ("Cost", "Staff", "Entraîneurs et staff", "Général", 1, 12000),
            ("Cost", "Marketing", "Publicité", "Général", 1, 4000),
            ("Cost", "Équipements", "Kits et matériel", "Général", 1, 6500),
        ],
    },
    "Voyage": {
        "phases": [
            ("Planification", 1),
            ("Vente", 2),
            ("Réservations", 3),
            ("Paiements", 4),
            ("Logistique", 5),
            ("Exécution", 6),
            ("Rapport final", 7),
        ],
        "tasks": {
            "Planification": ["Définir programme", "Estimer budget", "Fixer prix"],
            "Vente": ["Créer présentation", "Promouvoir voyage", "Recevoir dépôts"],
            "Réservations": ["Réserver vols", "Réserver hôtels", "Confirmer matchs"],
            "Paiements": ["Suivre paiements finaux", "Payer fournisseurs"],
            "Logistique": ["Préparer documents", "Créer groupe familles", "Finaliser itinéraire"],
            "Exécution": ["Gestion du groupe", "Transport", "Matchs / visites"],
            "Rapport final": ["Bilan financier", "Photos / vidéos", "Évaluation finale"],
        },
        "budget": [
            ("Revenue", "Paiements familles", "Paiements familles", "Par personne", 1, 0),
            ("Cost", "Vol", "Billets d'avion", "Par personne", 1, 0),
            ("Cost", "Hôtel", "Hébergement", "Par personne", 1, 0),
            ("Cost", "Transport", "Transport local", "Général", 1, 0),
            ("Cost", "Staff", "Staff", "Général", 1, 0),
            ("Cost", "Autre", "Activités", "Général", 1, 0),
        ],
    },
    "Tryout": {
        "phases": [
            ("Planification", 1),
            ("Promotion", 2),
            ("Inscriptions", 3),
            ("Logistique", 4),
            ("Exécution", 5),
            ("Évaluation", 6),
            ("Clôture", 7),
        ],
        "tasks": {
            "Planification": ["Définir date et lieu", "Confirmer staff", "Créer formulaire"],
            "Promotion": ["Posts réseaux sociaux", "Contacter clubs", "Email marketing"],
            "Inscriptions": ["Recevoir inscriptions", "Confirmer paiements"],
            "Logistique": ["Préparer terrain", "Préparer matériel", "Créer groupes"],
            "Exécution": ["Check-in", "Évaluations terrain"],
            "Évaluation": ["Analyser résultats", "Sélection joueurs"],
            "Clôture": ["Envoyer réponses", "Rapport final"],
        },
        "budget": [
            ("Revenue", "Inscriptions", "Frais d'inscription", "Général", 1, 0),
            ("Cost", "Terrain", "Location terrain", "Général", 1, 0),
            ("Cost", "Staff", "Évaluateurs", "Général", 1, 0),
            ("Cost", "Marketing", "Promotion", "Général", 1, 0),
        ],
    },
    "Partenariat": {
        "phases": [
            ("Identification", 1),
            ("Contact", 2),
            ("Négociation", 3),
            ("Proposition", 4),
            ("Accord", 5),
            ("Implémentation", 6),
            ("Évaluation", 7),
        ],
        "tasks": {
            "Identification": ["Identifier partenaire", "Collecter informations"],
            "Contact": ["Envoyer email initial", "Réunion exploratoire"],
            "Négociation": ["Définir modèle", "Discuter conditions"],
            "Proposition": ["Créer proposition", "Présenter projet"],
            "Accord": ["Rédiger contrat", "Signer partenariat"],
            "Implémentation": ["Planifier activités", "Fixer calendrier"],
            "Évaluation": ["Évaluer résultats"],
        },
        "budget": [
            ("Revenue", "Partenariats", "Revenus du partenariat", "Général", 1, 0),
            ("Cost", "Administratif", "Déplacements / réunions", "Général", 1, 0),
            ("Cost", "Marketing", "Matériel de présentation", "Général", 1, 0),
        ],
    },
}

st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        font-weight: 700;
    }
    div[data-testid="stMetric"] {
        background-color: #f7f9fc;
        border: 1px solid #e6ebf2;
        padding: 12px 16px;
        border-radius: 14px;
    }
    .section-card {
        background: #ffffff;
        border: 1px solid #e6ebf2;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .status-card {
        background: #fafbfc;
        border: 1px solid #dde4ee;
        border-radius: 16px;
        padding: 14px;
        min-height: 260px;
    }
    .task-pill {
        border: 1px solid #e6ebf2;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 8px;
        background: white;
    }
    .stButton button {
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def get_conn():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
        timeout=30
    )
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


def column_exists(table_name, column_name):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        cols = [row[1] for row in cur.fetchall()]
    finally:
        conn.close()
    return column_name in cols


def safe_add_column(table_name, column_def):
    col_name = column_def.split()[0]
    if not column_exists(table_name, col_name):
        execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")


def parse_date_or_none(value):
    if value is None or value == "":
        return None
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def fmt_money(v):
    try:
        return f"${float(v):,.0f}"
    except Exception:
        return "$0"


def ensure_backup_dir():
    BACKUP_DIR.mkdir(exist_ok=True)
    return BACKUP_DIR


def create_db_backup():
    backup_dir = ensure_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"ia_soccer_projects_backup_{timestamp}.db"
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_file)
        return backup_file
    return None


def auto_backup_once_per_day():
    today_key = datetime.now().strftime("%Y%m%d")
    marker = BACKUP_DIR / f".last_auto_backup_{today_key}"
    if DB_PATH.exists() and not marker.exists():
        create_db_backup()
        marker.write_text("ok", encoding="utf-8")


def list_backups():
    backup_dir = ensure_backup_dir()
    return sorted(backup_dir.glob("*.db"), reverse=True)


def restore_db_backup(uploaded_file):
    try:
        with open(DB_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True, "Backup restauré avec succès."
    except Exception as e:
        return False, f"Erreur pendant la restauration : {e}"


def get_db_download_bytes():
    if DB_PATH.exists():
        return DB_PATH.read_bytes()
    return None


def export_all_to_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        fetch_df("SELECT * FROM projects").to_excel(writer, sheet_name="projects", index=False)
        fetch_df("SELECT * FROM phases").to_excel(writer, sheet_name="phases", index=False)
        fetch_df("SELECT * FROM tasks").to_excel(writer, sheet_name="tasks", index=False)
        fetch_df("SELECT * FROM budget").to_excel(writer, sheet_name="budget", index=False)
        fetch_df("SELECT * FROM people").to_excel(writer, sheet_name="people", index=False)
    output.seek(0)
    return output.getvalue()


def export_all_to_json():
    data = {
        "projects": fetch_df("SELECT * FROM projects").to_dict(orient="records"),
        "phases": fetch_df("SELECT * FROM phases").to_dict(orient="records"),
        "tasks": fetch_df("SELECT * FROM tasks").to_dict(orient="records"),
        "budget": fetch_df("SELECT * FROM budget").to_dict(orient="records"),
        "people": fetch_df("SELECT * FROM people").to_dict(orient="records"),
    }
    return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")


def init_db():
    executescript("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        project_type TEXT NOT NULL,
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
        expected_amount REAL DEFAULT 0,
        real_amount REAL DEFAULT 0,
        payment_status TEXT DEFAULT 'Prévu'
    );

    CREATE TABLE IF NOT EXISTS people (
        person_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        role_title TEXT,
        email TEXT,
        phone TEXT
    );
    """)

    safe_add_column("budget", "budget_scope TEXT DEFAULT 'Général'")
    safe_add_column("budget", "unit_count REAL DEFAULT 1")
    safe_add_column("budget", "unit_amount REAL DEFAULT 0")


def recalc_budget_line_amounts(project_id):
    budget = fetch_df(
        "SELECT budget_id, budget_scope, unit_count, unit_amount FROM budget WHERE project_id = ?",
        (project_id,)
    )
    if budget.empty:
        return

    for _, row in budget.iterrows():
        scope = row["budget_scope"] if pd.notna(row["budget_scope"]) else "Général"
        unit_count = float(row["unit_count"]) if pd.notna(row["unit_count"]) else 1
        unit_amount = float(row["unit_amount"]) if pd.notna(row["unit_amount"]) else 0

        expected_amount = unit_count * unit_amount if scope == "Par personne" else unit_amount

        execute(
            "UPDATE budget SET expected_amount = ? WHERE budget_id = ?",
            (float(expected_amount), int(row["budget_id"]))
        )


def refresh_project_totals(project_id):
    recalc_budget_line_amounts(project_id)
    budget = fetch_df("SELECT * FROM budget WHERE project_id = ?", (project_id,))
    if budget.empty:
        rev = 0
        cost = 0
    else:
        rev = budget.loc[budget["entry_type"] == "Revenue", "expected_amount"].fillna(0).sum()
        cost = budget.loc[budget["entry_type"] == "Cost", "expected_amount"].fillna(0).sum()

    execute(
        "UPDATE projects SET expected_revenue = ?, expected_cost = ?, updated_at = CURRENT_TIMESTAMP WHERE project_id = ?",
        (float(rev), float(cost), int(project_id))
    )


def seed_demo():
    df = fetch_df("SELECT COUNT(*) AS c FROM projects")
    if int(df.iloc[0]["c"]) > 0:
        return

    project_id = execute(
        """INSERT INTO projects
        (project_name, project_type, city, country, main_location, start_date, end_date,
         main_responsible, project_status, priority, short_description, expected_revenue, expected_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
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
            58800,
            33500
        )
    )

    for phase_name, phase_order in TEMPLATES["Camp"]["phases"]:
        phase_id = execute(
            "INSERT INTO phases (project_id, phase_name, phase_order, phase_status) VALUES (?, ?, ?, ?)",
            (project_id, phase_name, phase_order, "À faire")
        )
        for task_name in TEMPLATES["Camp"]["tasks"][phase_name]:
            execute(
                "INSERT INTO tasks (project_id, phase_id, task_name, task_status, task_priority) VALUES (?, ?, ?, ?, ?)",
                (project_id, phase_id, task_name, "À faire", "Moyenne")
            )

    for entry_type, category, description, budget_scope, unit_count, unit_amount in TEMPLATES["Camp"]["budget"]:
        expected_amount = unit_count * unit_amount if budget_scope == "Par personne" else unit_amount
        execute(
            """INSERT INTO budget
            (project_id, entry_type, category, description, budget_scope, unit_count, unit_amount, expected_amount, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (project_id, entry_type, category, description, budget_scope, unit_count, unit_amount, expected_amount, "Prévu")
        )

    refresh_project_totals(project_id)


def create_project_with_template(name, ptype, city, country, location, start_date, end_date, responsible, status, priority, desc):
    project_id = execute(
        """INSERT INTO projects
        (project_name, project_type, city, country, main_location, start_date, end_date,
         main_responsible, project_status, priority, short_description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, ptype, city, country, location, str(start_date), str(end_date), responsible, status, priority, desc)
    )

    template = TEMPLATES.get(ptype)
    if template:
        for phase_name, phase_order in template["phases"]:
            phase_id = execute(
                "INSERT INTO phases (project_id, phase_name, phase_order, phase_status) VALUES (?, ?, ?, ?)",
                (project_id, phase_name, phase_order, "À faire")
            )
            for task_name in template["tasks"].get(phase_name, []):
                execute(
                    "INSERT INTO tasks (project_id, phase_id, task_name, task_status, task_priority) VALUES (?, ?, ?, ?, ?)",
                    (project_id, phase_id, task_name, "À faire", "Moyenne")
                )

        for entry_type, category, description, budget_scope, unit_count, unit_amount in template.get("budget", []):
            expected_amount = unit_count * unit_amount if budget_scope == "Par personne" else unit_amount
            execute(
                """INSERT INTO budget
                (project_id, entry_type, category, description, budget_scope, unit_count, unit_amount, expected_amount, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (project_id, entry_type, category, description, budget_scope, unit_count, unit_amount, expected_amount, "Prévu")
            )

    refresh_project_totals(project_id)
    return project_id


def duplicate_project(source_project_id, new_project_name, new_city=None):
    source = fetch_df("SELECT * FROM projects WHERE project_id = ?", (source_project_id,))
    if source.empty:
        return None

    row = source.iloc[0]

    new_pid = execute(
        """INSERT INTO projects
        (project_name, project_type, city, country, main_location, start_date, end_date,
         main_responsible, project_status, priority, short_description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            new_project_name,
            row["project_type"],
            new_city if new_city is not None else (row["city"] or ""),
            row["country"] or "",
            row["main_location"] or "",
            row["start_date"] or "",
            row["end_date"] or "",
            row["main_responsible"] or "",
            "En préparation",
            row["priority"] or "Moyenne",
            row["short_description"] or "",
        )
    )

    old_phases = fetch_df("SELECT * FROM phases WHERE project_id = ? ORDER BY phase_order", (source_project_id,))
    phase_map = {}

    for _, ph in old_phases.iterrows():
        new_phase_id = execute(
            """INSERT INTO phases
            (project_id, phase_name, phase_order, phase_start_date, phase_end_date, phase_status)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                new_pid,
                ph["phase_name"],
                int(ph["phase_order"] or 1),
                ph["phase_start_date"] or "",
                ph["phase_end_date"] or "",
                ph["phase_status"] or "À faire",
            )
        )
        phase_map[int(ph["phase_id"])] = int(new_phase_id)

    old_tasks = fetch_df("SELECT * FROM tasks WHERE project_id = ?", (source_project_id,))
    for _, t in old_tasks.iterrows():
        new_phase_id = phase_map.get(int(t["phase_id"])) if pd.notna(t["phase_id"]) else None
        execute(
            """INSERT INTO tasks
            (project_id, phase_id, task_name, task_responsible, task_due_date, task_status, task_priority, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                new_pid,
                new_phase_id,
                t["task_name"],
                t["task_responsible"] or "",
                t["task_due_date"] or "",
                "À faire",
                t["task_priority"] or "Moyenne",
                t["notes"] or "",
            )
        )

    old_budget = fetch_df("SELECT * FROM budget WHERE project_id = ?", (source_project_id,))
    for _, b in old_budget.iterrows():
        scope = b["budget_scope"] if "budget_scope" in b.index and pd.notna(b["budget_scope"]) else "Général"
        unit_count = float(b["unit_count"]) if "unit_count" in b.index and pd.notna(b["unit_count"]) else 1
        unit_amount = float(b["unit_amount"]) if "unit_amount" in b.index and pd.notna(b["unit_amount"]) else float(b["expected_amount"] or 0)

        execute(
            """INSERT INTO budget
            (project_id, entry_type, category, description, budget_scope, unit_count, unit_amount, expected_amount, real_amount, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                new_pid,
                b["entry_type"],
                b["category"] or "",
                b["description"] or "",
                scope,
                unit_count,
                unit_amount,
                float(b["expected_amount"] or 0),
                0,
                "Prévu",
            )
        )

    refresh_project_totals(new_pid)
    return new_pid


def copy_budget_only(source_project_id, target_project_id):
    execute("DELETE FROM budget WHERE project_id = ?", (int(target_project_id),))
    old_budget = fetch_df("SELECT * FROM budget WHERE project_id = ?", (source_project_id,))

    for _, b in old_budget.iterrows():
        scope = b["budget_scope"] if "budget_scope" in b.index and pd.notna(b["budget_scope"]) else "Général"
        unit_count = float(b["unit_count"]) if "unit_count" in b.index and pd.notna(b["unit_count"]) else 1
        unit_amount = float(b["unit_amount"]) if "unit_amount" in b.index and pd.notna(b["unit_amount"]) else float(b["expected_amount"] or 0)

        execute(
            """INSERT INTO budget
            (project_id, entry_type, category, description, budget_scope, unit_count, unit_amount, expected_amount, real_amount, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                target_project_id,
                b["entry_type"],
                b["category"] or "",
                b["description"] or "",
                scope,
                unit_count,
                unit_amount,
                float(b["expected_amount"] or 0),
                0,
                "Prévu",
            )
        )

    refresh_project_totals(target_project_id)


def metrics():
    projects = fetch_df("SELECT * FROM projects")
    if projects.empty:
        return 0, 0, 0, 0
    rev = projects["expected_revenue"].fillna(0).sum()
    cost = projects["expected_cost"].fillna(0).sum()
    return len(projects), rev, cost, rev - cost


def get_all_tasks():
    return fetch_df("""
        SELECT t.task_id, t.project_id, p.project_name, ph.phase_name, t.task_name, t.task_responsible,
               t.task_due_date, t.task_status, t.task_priority, t.notes
        FROM tasks t
        JOIN projects p ON p.project_id = t.project_id
        LEFT JOIN phases ph ON ph.phase_id = t.phase_id
        ORDER BY t.task_due_date, t.task_priority
    """)


def get_real_totals():
    budget = fetch_df("SELECT * FROM budget")
    if budget.empty:
        return 0, 0, 0
    real_rev = budget.loc[budget["entry_type"] == "Revenue", "real_amount"].fillna(0).sum()
    real_cost = budget.loc[budget["entry_type"] == "Cost", "real_amount"].fillna(0).sum()
    return real_rev, real_cost, real_rev - real_cost


def get_urgent_tasks(project_ids=None, limit=20):
    query = """
        SELECT
            t.task_id,
            p.project_name,
            COALESCE(ph.phase_name, '-') AS phase_name,
            t.task_name,
            t.task_responsible,
            t.task_due_date,
            t.task_status,
            t.task_priority,
            t.notes
        FROM tasks t
        JOIN projects p ON p.project_id = t.project_id
        LEFT JOIN phases ph ON ph.phase_id = t.phase_id
        WHERE t.task_status != 'Terminé'
    """
    params = []

    if project_ids:
        placeholders = ",".join(["?"] * len(project_ids))
        query += f" AND t.project_id IN ({placeholders})"
        params.extend(project_ids)

    df = fetch_df(query, tuple(params))
    if df.empty:
        return df

    today = pd.to_datetime(date.today())
    df["due_dt"] = pd.to_datetime(df["task_due_date"], errors="coerce")
    df["days_left"] = (df["due_dt"] - today).dt.days

    def alert_label(x):
        if pd.isna(x):
            return "À suivre"
        if x < 0:
            return "En retard"
        if x == 0:
            return "Aujourd’hui"
        if x <= 7:
            return "Urgent"
        return "À suivre"

    df["alert"] = df["days_left"].apply(alert_label)
    priority_order = {"Haute": 0, "Moyenne": 1, "Basse": 2}
    df["priority_sort"] = df["task_priority"].map(priority_order).fillna(1)
    df["days_sort"] = df["days_left"].fillna(9999)
    df = df.sort_values(["days_sort", "priority_sort", "project_name"])
    return df.head(limit)


def get_overdue_and_urgent_counts():
    tasks_all = get_all_tasks()
    if tasks_all.empty:
        return 0, 0

    tasks_all["due"] = pd.to_datetime(tasks_all["task_due_date"], errors="coerce")
    overdue = len(
        tasks_all[
            (tasks_all["due"].notna()) &
            (tasks_all["due"].dt.date < date.today()) &
            (tasks_all["task_status"] != "Terminé")
        ]
    )
    urgent = len(
        tasks_all[
            (tasks_all["due"].notna()) &
            (tasks_all["due"].dt.date <= date.today()) &
            (tasks_all["task_status"] != "Terminé")
        ]
    )
    return overdue, urgent


def get_project_progress():
    projects = fetch_df("SELECT project_id, project_name FROM projects ORDER BY start_date")
    tasks = fetch_df("SELECT project_id, task_status FROM tasks")
    rows = []

    for _, p in projects.iterrows():
        p_tasks = tasks[tasks["project_id"] == p["project_id"]]
        total = len(p_tasks)
        done = len(p_tasks[p_tasks["task_status"] == "Terminé"])
        progress = round((done / total) * 100, 1) if total > 0 else 0
        rows.append({
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "tasks_total": total,
            "tasks_done": done,
            "progress_pct": progress
        })

    return pd.DataFrame(rows)


def global_search(term):
    term_like = f"%{term}%"
    projects = fetch_df("""
        SELECT 'Projet' AS source, project_name AS title, city AS subinfo, CAST(project_id AS TEXT) AS ref
        FROM projects
        WHERE project_name LIKE ? OR city LIKE ? OR country LIKE ? OR main_location LIKE ? OR short_description LIKE ?
    """, (term_like, term_like, term_like, term_like, term_like))

    tasks = fetch_df("""
        SELECT 'Tâche' AS source, task_name AS title, task_responsible AS subinfo, CAST(task_id AS TEXT) AS ref
        FROM tasks
        WHERE task_name LIKE ? OR task_responsible LIKE ? OR notes LIKE ?
    """, (term_like, term_like, term_like))

    people = fetch_df("""
        SELECT 'Équipe' AS source, full_name AS title, role_title AS subinfo, CAST(person_id AS TEXT) AS ref
        FROM people
        WHERE full_name LIKE ? OR role_title LIKE ? OR email LIKE ? OR phone LIKE ?
    """, (term_like, term_like, term_like, term_like))

    budget = fetch_df("""
        SELECT 'Budget' AS source, description AS title, category AS subinfo, CAST(budget_id AS TEXT) AS ref
        FROM budget
        WHERE description LIKE ? OR category LIKE ?
    """, (term_like, term_like))

    return pd.concat([projects, tasks, people, budget], ignore_index=True)


def render_task_card(row):
    due = row["task_due_date"] if pd.notna(row["task_due_date"]) and row["task_due_date"] != "" else "-"
    responsible = row["task_responsible"] if pd.notna(row["task_responsible"]) and row["task_responsible"] != "" else "-"
    priority = row["task_priority"] if pd.notna(row["task_priority"]) else "-"
    project_name = row["project_name"] if pd.notna(row["project_name"]) else "-"
    notes = row["notes"] if pd.notna(row["notes"]) and row["notes"] != "" else ""
    st.markdown(
        f"""
        <div class="task-pill">
            <b>{row["task_name"]}</b><br>
            Projet: {project_name}<br>
            Responsable: {responsible}<br>
            Date: {due}<br>
            Priorité: {priority}<br>
            {notes}
        </div>
        """,
        unsafe_allow_html=True
    )


init_db()
seed_demo()
auto_backup_once_per_day()

st.sidebar.title("⚽ IA Soccer Projects Pro V7")
search_term = st.sidebar.text_input("Recherche globale")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Projets", "Nouveau projet", "Timeline", "Budget", "Tâches", "Board", "Équipe", "Analytics", "Backup"]
)

if search_term:
    st.sidebar.markdown("### Résultats")
    results = global_search(search_term)
    if results.empty:
        st.sidebar.info("Aucun résultat")
    else:
        st.sidebar.dataframe(results.head(12), use_container_width=True, hide_index=True)

if page == "Dashboard":
    st.title("Dashboard exécutif")

    count, rev, cost, profit = metrics()
    real_rev, real_cost, real_profit = get_real_totals()
    overdue, urgent = get_overdue_and_urgent_counts()

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
    progress_df = get_project_progress()

    if projects.empty:
        st.info("Aucun projet disponible.")
    else:
        st.subheader("Filtres")
        f1, f2, f3 = st.columns(3)
        type_filter = f1.selectbox("Type de projet", ["Tous"] + PROJECT_TYPES)
        status_filter = f2.selectbox("Status projet", ["Tous"] + PROJECT_STATUS)
        city_list = ["Tous"] + sorted([c for c in projects["city"].dropna().unique().tolist()])
        city_filter = f3.selectbox("Ville", city_list)

        filtered_projects = projects.copy()
        if type_filter != "Tous":
            filtered_projects = filtered_projects[filtered_projects["project_type"] == type_filter]
        if status_filter != "Tous":
            filtered_projects = filtered_projects[filtered_projects["project_status"] == status_filter]
        if city_filter != "Tous":
            filtered_projects = filtered_projects[filtered_projects["city"] == city_filter]

        if not filtered_projects.empty and not progress_df.empty:
            filtered_projects = filtered_projects.merge(
                progress_df[["project_id", "progress_pct", "tasks_total", "tasks_done"]],
                on="project_id",
                how="left"
            )

        c1, c2 = st.columns([1.2, 1])

        with c1:
            st.subheader("Vue projets")
            if filtered_projects.empty:
                st.info("Aucun projet avec ces filtres.")
            else:
                display_cols = [
                    "project_name", "project_type", "city", "start_date", "end_date",
                    "project_status", "priority", "expected_revenue", "expected_cost",
                    "progress_pct"
                ]
                existing_cols = [c for c in display_cols if c in filtered_projects.columns]
                st.dataframe(filtered_projects[existing_cols], use_container_width=True, hide_index=True)

                st.subheader("Finance par projet")
                finance = filtered_projects[["project_name", "expected_revenue", "expected_cost"]].copy()
                finance = finance.set_index("project_name")
                st.bar_chart(finance)

        with c2:
            st.subheader("Tâches urgentes")
            filtered_ids = filtered_projects["project_id"].tolist() if not filtered_projects.empty else []
            urgent_tasks = get_urgent_tasks(filtered_ids, limit=15)

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

        if not filtered_projects.empty:
            a1, a2 = st.columns(2)

            with a1:
                st.subheader("Répartition par type")
                type_counts = filtered_projects.groupby("project_type").size().reset_index(name="count")
                type_counts = type_counts.set_index("project_type")
                st.bar_chart(type_counts)

            with a2:
                st.subheader("Répartition par status")
                status_counts = filtered_projects.groupby("project_status").size().reset_index(name="count")
                status_counts = status_counts.set_index("project_status")
                st.bar_chart(status_counts)

            st.subheader("Progression des projets")
            prog_chart = filtered_projects[["project_name", "progress_pct"]].copy().set_index("project_name")
            st.bar_chart(prog_chart)

elif page == "Projets":
    st.title("Projets")
    projects = fetch_df("SELECT * FROM projects ORDER BY start_date")
    progress_df = get_project_progress()

    if not projects.empty and not progress_df.empty:
        projects = projects.merge(progress_df[["project_id", "progress_pct"]], on="project_id", how="left")

    st.dataframe(
        projects[[
            "project_id", "project_name", "project_type", "city", "country",
            "start_date", "end_date", "main_responsible", "project_status",
            "priority", "expected_revenue", "expected_cost", "progress_pct"
        ]] if not projects.empty else projects,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.subheader("Dupliquer un projet complet")

    if not projects.empty:
        d1, d2, d3 = st.columns(3)
        source_project_id = d1.selectbox(
            "Projet source",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}",
            key="dup_project_source"
        )
        default_name = f"{projects.loc[projects.project_id == source_project_id, 'project_name'].iloc[0]} - Copie"
        new_project_name = d2.text_input("Nom du nouveau projet", value=default_name)
        new_city = d3.text_input("Nouvelle ville (optionnel)")

        if st.button("Dupliquer le projet complet"):
            new_pid = duplicate_project(int(source_project_id), new_project_name, new_city if new_city.strip() else None)
            if new_pid:
                st.success(f"Projet dupliqué avec succès. Nouveau projet ID: {new_pid}")
                st.rerun()

    st.markdown("---")
    st.subheader("Copier seulement le budget d’un autre projet")

    if len(projects) >= 2:
        b1, b2 = st.columns(2)
        source_budget_project = b1.selectbox(
            "Projet source budget",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}",
            key="copy_budget_source"
        )
        target_budget_project = b2.selectbox(
            "Projet cible budget",
            projects["project_id"],
            index=1 if len(projects) > 1 else 0,
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}",
            key="copy_budget_target"
        )

        if st.button("Copier le budget"):
            if int(source_budget_project) == int(target_budget_project):
                st.error("Le projet source et le projet cible doivent être différents.")
            else:
                copy_budget_only(int(source_budget_project), int(target_budget_project))
                st.success("Budget copié avec succès.")
                st.rerun()

    st.markdown("---")

    if not projects.empty:
        selected = st.selectbox(
            "Choisir un projet à modifier",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )
        row = projects[projects["project_id"] == selected].iloc[0]

        with st.form("edit_project"):
            st.subheader("Modifier le projet")
            a1, a2 = st.columns(2)
            project_name = a1.text_input("Nom du projet", value=row["project_name"])
            project_type = a2.selectbox(
                "Type",
                PROJECT_TYPES,
                index=PROJECT_TYPES.index(row["project_type"]) if row["project_type"] in PROJECT_TYPES else 0
            )

            b1, b2 = st.columns(2)
            city = b1.text_input("Ville", value=row["city"] or "")
            country = b2.text_input("Pays", value=row["country"] or "")

            main_location = st.text_input("Lieu principal", value=row["main_location"] or "")

            start_default = parse_date_or_none(row["start_date"]) or date.today()
            end_default = parse_date_or_none(row["end_date"]) or date.today()

            c1, c2 = st.columns(2)
            start_date = c1.date_input("Date début", value=start_default)
            end_date = c2.date_input("Date fin", value=end_default)

            d1, d2, d3 = st.columns(3)
            main_responsible = d1.text_input("Responsable", value=row["main_responsible"] or "")
            project_status = d2.selectbox(
                "Status",
                PROJECT_STATUS,
                index=PROJECT_STATUS.index(row["project_status"]) if row["project_status"] in PROJECT_STATUS else 0
            )
            priority = d3.selectbox(
                "Priorité",
                PRIORITIES,
                index=PRIORITIES.index(row["priority"]) if row["priority"] in PRIORITIES else 1
            )

            short_description = st.text_area("Description", value=row["short_description"] or "")

            save = st.form_submit_button("Enregistrer")
            if save:
                execute(
                    """UPDATE projects SET
                    project_name=?, project_type=?, city=?, country=?, main_location=?,
                    start_date=?, end_date=?, main_responsible=?, project_status=?,
                    priority=?, short_description=?, updated_at=CURRENT_TIMESTAMP
                    WHERE project_id=?""",
                    (
                        project_name, project_type, city, country, main_location,
                        str(start_date), str(end_date), main_responsible, project_status,
                        priority, short_description, int(selected)
                    )
                )
                st.success("Projet mis à jour.")
                st.rerun()

        st.markdown("### Zone de suppression")
        confirm_delete_project = st.checkbox("Je confirme la suppression de ce projet")
        if st.button("Supprimer ce projet"):
            if not confirm_delete_project:
                st.error("Veuillez confirmer la suppression.")
            else:
                execute("DELETE FROM tasks WHERE project_id = ?", (int(selected),))
                execute("DELETE FROM phases WHERE project_id = ?", (int(selected),))
                execute("DELETE FROM budget WHERE project_id = ?", (int(selected),))
                execute("DELETE FROM projects WHERE project_id = ?", (int(selected),))
                st.success("Projet supprimé.")
                st.rerun()

elif page == "Nouveau projet":
    st.title("Nouveau projet")
    with st.form("new_project"):
        a1, a2 = st.columns(2)
        name = a1.text_input("Nom du projet")
        ptype = a2.selectbox("Type de projet", PROJECT_TYPES)

        b1, b2 = st.columns(2)
        city = b1.text_input("Ville")
        country = b2.text_input("Pays", value="Canada")

        main_location = st.text_input("Lieu principal")

        c1, c2 = st.columns(2)
        start_date = c1.date_input("Date de début", value=date.today())
        end_date = c2.date_input("Date de fin", value=date.today())

        d1, d2, d3 = st.columns(3)
        main_responsible = d1.text_input("Responsable")
        project_status = d2.selectbox("Status", PROJECT_STATUS, index=1)
        priority = d3.selectbox("Priorité", PRIORITIES, index=1)

        short_description = st.text_area("Description courte")

        submitted = st.form_submit_button("Créer le projet")
        if submitted:
            if not name:
                st.error("Le nom du projet est obligatoire.")
            else:
                pid = create_project_with_template(
                    name, ptype, city, country, main_location,
                    start_date, end_date, main_responsible,
                    project_status, priority, short_description
                )
                st.success(f"Projet créé avec succès. ID: {pid}")
                st.rerun()

elif page == "Timeline":
    st.title("Timeline")
    projects = fetch_df("SELECT project_id, project_name FROM projects ORDER BY start_date")

    if projects.empty:
        st.info("Aucun projet pour le moment.")
    else:
        selected = st.selectbox(
            "Projet",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )

        phases = fetch_df(
            "SELECT phase_id, phase_name, phase_order, phase_start_date, phase_end_date, phase_status FROM phases WHERE project_id = ? ORDER BY phase_order",
            (int(selected),)
        )

        if not phases.empty:
            st.dataframe(phases, use_container_width=True, hide_index=True)

            chart_df = phases.copy()
            chart_df["phase_start_date"] = pd.to_datetime(chart_df["phase_start_date"], errors="coerce")
            chart_df["phase_end_date"] = pd.to_datetime(chart_df["phase_end_date"], errors="coerce")

            duration_rows = []
            for _, row in chart_df.iterrows():
                if pd.notna(row["phase_start_date"]) and pd.notna(row["phase_end_date"]):
                    duration = max((row["phase_end_date"] - row["phase_start_date"]).days, 0)
                else:
                    duration = 0
                duration_rows.append({"phase_name": row["phase_name"], "duration_days": duration})
            duration_df = pd.DataFrame(duration_rows).set_index("phase_name")
            st.subheader("Durée estimée des phases")
            st.bar_chart(duration_df)

            st.subheader("Vue timeline")
            for _, ph in phases.iterrows():
                st.markdown(
                    f"""
                    <div class="section-card">
                        <b>{int(ph['phase_order'])}. {ph['phase_name']}</b><br>
                        Début: {ph['phase_start_date'] or '-'} | Fin: {ph['phase_end_date'] or '-'}<br>
                        Statut: {ph['phase_status']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("Aucune phase pour ce projet.")

        with st.form("add_phase"):
            st.subheader("Ajouter une phase")
            a1, a2 = st.columns(2)
            phase_name_new = a1.text_input("Nom de la phase")
            phase_order_new = a2.number_input("Ordre", min_value=1, step=1, value=1)
            b1, b2 = st.columns(2)
            phase_start_new = b1.date_input("Début", value=date.today(), key="phase_start_new")
            phase_end_new = b2.date_input("Fin", value=date.today(), key="phase_end_new")
            phase_status_new = st.selectbox("Status phase", TASK_STATUS, index=0)
            add_phase_btn = st.form_submit_button("Ajouter phase")

            if add_phase_btn and phase_name_new:
                execute(
                    "INSERT INTO phases (project_id, phase_name, phase_order, phase_start_date, phase_end_date, phase_status) VALUES (?, ?, ?, ?, ?, ?)",
                    (int(selected), phase_name_new, int(phase_order_new), str(phase_start_new), str(phase_end_new), phase_status_new)
                )
                st.success("Phase ajoutée.")
                st.rerun()

        if not phases.empty:
            edit_phase_id = st.selectbox(
                "Modifier une phase",
                phases["phase_id"],
                format_func=lambda x: f"{x} - {phases.loc[phases.phase_id == x, 'phase_name'].iloc[0]}"
            )
            phase_row = phases[phases["phase_id"] == edit_phase_id].iloc[0]

            with st.form("edit_phase"):
                c1, c2 = st.columns(2)
                phase_name = c1.text_input("Nom phase", value=phase_row["phase_name"])
                phase_order = c2.number_input("Ordre", min_value=1, step=1, value=int(phase_row["phase_order"] or 1))
                d1, d2 = st.columns(2)
                phase_start = d1.date_input("Début", value=parse_date_or_none(phase_row["phase_start_date"]) or date.today(), key="edit_phase_start")
                phase_end = d2.date_input("Fin", value=parse_date_or_none(phase_row["phase_end_date"]) or date.today(), key="edit_phase_end")
                phase_status = st.selectbox(
                    "Status",
                    TASK_STATUS,
                    index=TASK_STATUS.index(phase_row["phase_status"]) if phase_row["phase_status"] in TASK_STATUS else 0
                )
                save_phase = st.form_submit_button("Enregistrer phase")
                if save_phase:
                    execute(
                        "UPDATE phases SET phase_name=?, phase_order=?, phase_start_date=?, phase_end_date=?, phase_status=? WHERE phase_id=?",
                        (phase_name, int(phase_order), str(phase_start), str(phase_end), phase_status, int(edit_phase_id))
                    )
                    st.success("Phase mise à jour.")
                    st.rerun()

            confirm_delete_phase = st.checkbox("Je confirme la suppression de cette phase")
            if st.button("Supprimer la phase sélectionnée"):
                if not confirm_delete_phase:
                    st.error("Veuillez confirmer la suppression.")
                else:
                    execute("DELETE FROM tasks WHERE phase_id = ?", (int(edit_phase_id),))
                    execute("DELETE FROM phases WHERE phase_id = ?", (int(edit_phase_id),))
                    st.success("Phase supprimée avec ses tâches liées.")
                    st.rerun()

elif page == "Budget":
    st.title("Budget")
    projects = fetch_df("SELECT project_id, project_name, project_type FROM projects ORDER BY start_date")

    if projects.empty:
        st.info("Aucun projet pour le moment.")
    else:
        selected = st.selectbox(
            "Projet",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )

        budget = fetch_df(
            """SELECT budget_id, entry_type, category, description, budget_scope, unit_count, unit_amount,
                      expected_amount, real_amount, payment_status
               FROM budget
               WHERE project_id = ?
               ORDER BY entry_type DESC, category, description""",
            (int(selected),)
        )

        rev = budget.loc[budget["entry_type"] == "Revenue", "expected_amount"].fillna(0).sum() if not budget.empty else 0
        cost = budget.loc[budget["entry_type"] == "Cost", "expected_amount"].fillna(0).sum() if not budget.empty else 0
        real_rev = budget.loc[budget["entry_type"] == "Revenue", "real_amount"].fillna(0).sum() if not budget.empty else 0
        real_cost = budget.loc[budget["entry_type"] == "Cost", "real_amount"].fillna(0).sum() if not budget.empty else 0

        a1, a2, a3, a4, a5 = st.columns(5)
        a1.metric("Revenu prévu", fmt_money(rev))
        a2.metric("Coût prévu", fmt_money(cost))
        a3.metric("Profit prévu", fmt_money(rev - cost))
        a4.metric("Profit réel", fmt_money(real_rev - real_cost))
        a5.metric("Écart réel/prévu", fmt_money((real_rev - real_cost) - (rev - cost)))

        if not budget.empty:
            st.subheader("Lignes budgétaires")
            st.dataframe(budget, use_container_width=True, hide_index=True)

            st.subheader("Résumé budget général / individuel")
            budget_calc = budget.copy()
            budget_calc["unit_count"] = pd.to_numeric(budget_calc["unit_count"], errors="coerce").fillna(1)
            budget_calc["unit_amount"] = pd.to_numeric(budget_calc["unit_amount"], errors="coerce").fillna(0)
            budget_calc["expected_amount"] = pd.to_numeric(budget_calc["expected_amount"], errors="coerce").fillna(0)
            budget_calc["real_amount"] = pd.to_numeric(budget_calc["real_amount"], errors="coerce").fillna(0)

            revenue_total = budget_calc.loc[budget_calc["entry_type"] == "Revenue", "expected_amount"].sum()
            cost_total = budget_calc.loc[budget_calc["entry_type"] == "Cost", "expected_amount"].sum()
            profit_total = revenue_total - cost_total

            revenue_pp_rows = budget_calc[(budget_calc["entry_type"] == "Revenue") & (budget_calc["budget_scope"] == "Par personne")]
            cost_pp_rows = budget_calc[(budget_calc["entry_type"] == "Cost") & (budget_calc["budget_scope"] == "Par personne")]
            revenue_general_rows = budget_calc[(budget_calc["entry_type"] == "Revenue") & (budget_calc["budget_scope"] == "Général")]
            cost_general_rows = budget_calc[(budget_calc["entry_type"] == "Cost") & (budget_calc["budget_scope"] == "Général")]

            participants_list = budget_calc.loc[budget_calc["budget_scope"] == "Par personne", "unit_count"].tolist()
            participants = int(max(participants_list)) if participants_list else 0

            revenue_per_person_direct = revenue_pp_rows["unit_amount"].sum() if not revenue_pp_rows.empty else 0
            cost_per_person_direct = cost_pp_rows["unit_amount"].sum() if not cost_pp_rows.empty else 0
            revenue_general_per_person = revenue_general_rows["expected_amount"].sum() / participants if participants > 0 else 0
            cost_general_per_person = cost_general_rows["expected_amount"].sum() / participants if participants > 0 else 0

            revenue_per_person_full = revenue_per_person_direct + revenue_general_per_person
            cost_per_person_full = cost_per_person_direct + cost_general_per_person
            profit_per_person = revenue_per_person_full - cost_per_person_full

            summary_df = pd.DataFrame([
                {"Indicateur": "Participants", "Total projet": participants, "Par personne": participants},
                {"Indicateur": "Revenue", "Total projet": revenue_total, "Par personne": revenue_per_person_full},
                {"Indicateur": "Cost", "Total projet": cost_total, "Par personne": cost_per_person_full},
                {"Indicateur": "Profit", "Total projet": profit_total, "Par personne": profit_per_person},
            ])
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            c1, c2 = st.columns(2)
            with c1:
                finance_chart = budget.groupby("entry_type")["expected_amount"].sum().reset_index().set_index("entry_type")
                st.subheader("Prévu par type")
                st.bar_chart(finance_chart)

            with c2:
                real_chart = budget.groupby("entry_type")["real_amount"].sum().reset_index().set_index("entry_type")
                st.subheader("Réel par type")
                st.bar_chart(real_chart)

            cat_chart = budget.groupby(["category"])["expected_amount"].sum().reset_index().set_index("category")
            st.subheader("Prévu par catégorie")
            st.bar_chart(cat_chart)

        with st.form("add_budget"):
            st.subheader("Ajouter une ligne de budget")
            b1, b2, b3 = st.columns(3)
            entry_type = b1.selectbox("Type", ENTRY_TYPES)
            category = b2.text_input("Catégorie")
            description = b3.text_input("Description")

            c1, c2, c3 = st.columns(3)
            budget_scope = c1.selectbox("Mode", BUDGET_SCOPE)
            unit_count = c2.number_input("Nombre de personnes / unités", min_value=1.0, step=1.0, value=1.0)
            unit_amount = c3.number_input("Montant unitaire", min_value=0.0, step=50.0)

            expected_preview = float(unit_count * unit_amount) if budget_scope == "Par personne" else float(unit_amount)
            st.caption(f"Total prévu calculé: {fmt_money(expected_preview)}")

            d1, d2 = st.columns(2)
            real_amount = d1.number_input("Montant réel", min_value=0.0, step=100.0)
            payment_status = d2.selectbox("État", PAYMENT_STATUS)

            add_b = st.form_submit_button("Ajouter")
            if add_b:
                expected_amount = float(unit_count * unit_amount) if budget_scope == "Par personne" else float(unit_amount)
                execute(
                    """INSERT INTO budget
                    (project_id, entry_type, category, description, budget_scope, unit_count, unit_amount, expected_amount, real_amount, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        int(selected), entry_type, category, description, budget_scope,
                        float(unit_count), float(unit_amount), float(expected_amount),
                        float(real_amount), payment_status
                    )
                )
                refresh_project_totals(int(selected))
                st.success("Ligne de budget ajoutée.")
                st.rerun()

        if not budget.empty:
            edit_id = st.selectbox(
                "Modifier une ligne existante",
                budget["budget_id"],
                format_func=lambda x: f"{x} - {budget.loc[budget.budget_id == x, 'category'].iloc[0]} / {budget.loc[budget.budget_id == x, 'description'].iloc[0]}"
            )
            b_row = budget[budget["budget_id"] == edit_id].iloc[0]

            with st.form("edit_budget"):
                st.subheader("Modifier la ligne de budget")
                d1, d2, d3 = st.columns(3)
                e_type = d1.selectbox("Type", ENTRY_TYPES, index=ENTRY_TYPES.index(b_row["entry_type"]) if b_row["entry_type"] in ENTRY_TYPES else 0)
                e_cat = d2.text_input("Catégorie", value=b_row["category"] or "")
                e_desc = d3.text_input("Description", value=b_row["description"] or "")

                e1, e2, e3 = st.columns(3)
                e_scope = e1.selectbox("Mode", BUDGET_SCOPE, index=BUDGET_SCOPE.index(b_row["budget_scope"]) if b_row["budget_scope"] in BUDGET_SCOPE else 0)
                e_unit_count = e2.number_input("Nombre de personnes / unités", min_value=1.0, step=1.0, value=float(b_row["unit_count"] or 1))
                e_unit_amount = e3.number_input("Montant unitaire", min_value=0.0, step=50.0, value=float(b_row["unit_amount"] or 0))

                e_total = float(e_unit_count * e_unit_amount) if e_scope == "Par personne" else float(e_unit_amount)
                st.info(f"Total prévu calculé automatiquement: {fmt_money(e_total)}")

                f1, f2 = st.columns(2)
                e_real = f1.number_input("Montant réel", min_value=0.0, step=100.0, value=float(b_row["real_amount"] or 0))
                e_status = f2.selectbox(
                    "État",
                    PAYMENT_STATUS,
                    index=PAYMENT_STATUS.index(b_row["payment_status"]) if b_row["payment_status"] in PAYMENT_STATUS else 0
                )

                save_edit = st.form_submit_button("Enregistrer modifications")
                if save_edit:
                    execute(
                        """UPDATE budget
                           SET entry_type=?, category=?, description=?, budget_scope=?, unit_count=?, unit_amount=?, expected_amount=?, real_amount=?, payment_status=?
                           WHERE budget_id=?""",
                        (
                            e_type, e_cat, e_desc, e_scope, float(e_unit_count), float(e_unit_amount),
                            float(e_total), float(e_real), e_status, int(edit_id)
                        )
                    )
                    refresh_project_totals(int(selected))
                    st.success("Ligne de budget mise à jour.")
                    st.rerun()

            confirm_delete_budget = st.checkbox("Je confirme la suppression de cette ligne de budget")
            if st.button("Supprimer la ligne sélectionnée"):
                if not confirm_delete_budget:
                    st.error("Veuillez confirmer la suppression.")
                else:
                    execute("DELETE FROM budget WHERE budget_id = ?", (int(edit_id),))
                    refresh_project_totals(int(selected))
                    st.success("Ligne supprimée.")
                    st.rerun()

elif page == "Tâches":
    st.title("Tâches")
    tasks = get_all_tasks()

    if not tasks.empty:
        f1, f2, f3, f4 = st.columns(4)
        project_filter = f1.selectbox("Filtre projet", ["Tous"] + sorted(tasks["project_name"].dropna().unique().tolist()))
        status_filter = f2.selectbox("Filtre status", ["Tous"] + TASK_STATUS)
        priority_filter = f3.selectbox("Filtre priorité", ["Tous"] + PRIORITIES)
        only_overdue = f4.checkbox("Seulement en retard")

        filtered_tasks = tasks.copy()
        if project_filter != "Tous":
            filtered_tasks = filtered_tasks[filtered_tasks["project_name"] == project_filter]
        if status_filter != "Tous":
            filtered_tasks = filtered_tasks[filtered_tasks["task_status"] == status_filter]
        if priority_filter != "Tous":
            filtered_tasks = filtered_tasks[filtered_tasks["task_priority"] == priority_filter]
        if only_overdue:
            filtered_tasks["due_dt"] = pd.to_datetime(filtered_tasks["task_due_date"], errors="coerce")
            filtered_tasks = filtered_tasks[
                (filtered_tasks["due_dt"].notna()) &
                (filtered_tasks["due_dt"].dt.date < date.today()) &
                (filtered_tasks["task_status"] != "Terminé")
            ]

        drop_cols = ["task_id", "project_id"]
        if "due_dt" in filtered_tasks.columns:
            drop_cols.append("due_dt")

        st.dataframe(filtered_tasks.drop(columns=drop_cols), use_container_width=True, hide_index=True)
    else:
        st.info("Aucune tâche pour le moment.")

    projects = fetch_df("SELECT project_id, project_name FROM projects ORDER BY start_date")
    if not projects.empty:
        add_project_id = st.selectbox(
            "Projet pour nouvelle tâche",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}",
            key="task_project_new"
        )
        phases = fetch_df("SELECT phase_id, phase_name FROM phases WHERE project_id = ? ORDER BY phase_order", (int(add_project_id),))

        with st.form("add_task"):
            st.subheader("Ajouter une tâche")
            t1, t2 = st.columns(2)
            task_name_new = t1.text_input("Nom de la tâche")
            task_responsible_new = t2.text_input("Responsable")
            t3, t4 = st.columns(2)
            task_due_date_new = t3.date_input("Date limite", value=date.today())
            task_status_new = t4.selectbox("Status", TASK_STATUS, index=0, key="new_task_status")
            t5, t6 = st.columns(2)
            task_priority_new = t5.selectbox("Priorité", PRIORITIES, index=1, key="new_task_priority")

            phase_options = [None] + phases["phase_id"].tolist() if not phases.empty else [None]
            phase_id_new = t6.selectbox(
                "Phase",
                phase_options,
                format_func=lambda x: "Sans phase" if x is None else phases.loc[phases.phase_id == x, "phase_name"].iloc[0],
                key="new_task_phase"
            )

            notes_new = st.text_input("Notes")
            add_task_btn = st.form_submit_button("Ajouter tâche")
            if add_task_btn and task_name_new:
                execute(
                    """INSERT INTO tasks
                    (project_id, phase_id, task_name, task_responsible, task_due_date, task_status, task_priority, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        int(add_project_id),
                        phase_id_new,
                        task_name_new,
                        task_responsible_new,
                        str(task_due_date_new),
                        task_status_new,
                        task_priority_new,
                        notes_new
                    )
                )
                st.success("Tâche ajoutée.")
                st.rerun()

    if not tasks.empty:
        task_id = st.selectbox(
            "Modifier une tâche",
            tasks["task_id"],
            format_func=lambda x: f"{x} - {tasks.loc[tasks.task_id == x, 'task_name'].iloc[0]}"
        )
        t_row = tasks[tasks["task_id"] == task_id].iloc[0]

        with st.form("edit_task"):
            e1, e2 = st.columns(2)
            task_name = e1.text_input("Nom de la tâche", value=t_row["task_name"])
            task_responsible = e2.text_input("Responsable", value=t_row["task_responsible"] or "")
            e3, e4 = st.columns(2)
            due = e3.date_input("Date limite", value=parse_date_or_none(t_row["task_due_date"]) or date.today())
            status = e4.selectbox(
                "Status",
                TASK_STATUS,
                index=TASK_STATUS.index(t_row["task_status"]) if t_row["task_status"] in TASK_STATUS else 0
            )
            e5, e6 = st.columns(2)
            priority = e5.selectbox(
                "Priorité",
                PRIORITIES,
                index=PRIORITIES.index(t_row["task_priority"]) if t_row["task_priority"] in PRIORITIES else 1
            )
            notes = e6.text_input("Notes", value=t_row["notes"] or "")
            save_task = st.form_submit_button("Enregistrer tâche")
            if save_task:
                execute(
                    "UPDATE tasks SET task_name=?, task_responsible=?, task_due_date=?, task_status=?, task_priority=?, notes=? WHERE task_id=?",
                    (task_name, task_responsible, str(due), status, priority, notes, int(task_id))
                )
                st.success("Tâche mise à jour.")
                st.rerun()

        confirm_delete_task = st.checkbox("Je confirme la suppression de cette tâche")
        if st.button("Supprimer la tâche sélectionnée"):
            if not confirm_delete_task:
                st.error("Veuillez confirmer la suppression.")
            else:
                execute("DELETE FROM tasks WHERE task_id = ?", (int(task_id),))
                st.success("Tâche supprimée.")
                st.rerun()

elif page == "Board":
    st.title("Board des tâches")
    tasks = get_all_tasks()

    if tasks.empty:
        st.info("Aucune tâche disponible.")
    else:
        project_names = ["Tous"] + sorted(tasks["project_name"].dropna().unique().tolist())
        selected_project = st.selectbox("Filtre projet", project_names)

        if selected_project != "Tous":
            tasks = tasks[tasks["project_name"] == selected_project]

        c1, c2, c3, c4 = st.columns(4)
        groups = {
            "À faire": c1,
            "En cours": c2,
            "Bloqué": c3,
            "Terminé": c4
        }

        for status_name, col in groups.items():
            with col:
                st.markdown(f'<div class="status-card"><h4>{status_name}</h4>', unsafe_allow_html=True)
                subset = tasks[tasks["task_status"] == status_name]
                if subset.empty:
                    st.caption("Aucune tâche")
                else:
                    for _, row in subset.iterrows():
                        render_task_card(row)
                st.markdown("</div>", unsafe_allow_html=True)

elif page == "Équipe":
    st.title("Équipe")
    people = fetch_df("SELECT * FROM people ORDER BY full_name")
    st.dataframe(people, use_container_width=True, hide_index=True)

    with st.form("add_person"):
        st.subheader("Ajouter une personne")
        a1, a2 = st.columns(2)
        full_name = a1.text_input("Nom complet")
        role_title = a2.text_input("Rôle")
        b1, b2 = st.columns(2)
        email = b1.text_input("Email")
        phone = b2.text_input("Téléphone")
        add_p = st.form_submit_button("Ajouter")

        if add_p:
            if full_name:
                execute(
                    "INSERT INTO people (full_name, role_title, email, phone) VALUES (?, ?, ?, ?)",
                    (full_name, role_title, email, phone)
                )
                st.success("Personne ajoutée.")
                st.rerun()
            else:
                st.error("Le nom est obligatoire.")

    if not people.empty:
        person_id = st.selectbox(
            "Modifier une personne",
            people["person_id"],
            format_func=lambda x: f"{x} - {people.loc[people.person_id == x, 'full_name'].iloc[0]}"
        )
        p_row = people[people["person_id"] == person_id].iloc[0]

        with st.form("edit_person"):
            c1, c2 = st.columns(2)
            full_name_edit = c1.text_input("Nom complet", value=p_row["full_name"])
            role_title_edit = c2.text_input("Rôle", value=p_row["role_title"] or "")
            d1, d2 = st.columns(2)
            email_edit = d1.text_input("Email", value=p_row["email"] or "")
            phone_edit = d2.text_input("Téléphone", value=p_row["phone"] or "")
            save_person = st.form_submit_button("Enregistrer")

            if save_person:
                execute(
                    "UPDATE people SET full_name=?, role_title=?, email=?, phone=? WHERE person_id=?",
                    (full_name_edit, role_title_edit, email_edit, phone_edit, int(person_id))
                )
                st.success("Personne mise à jour.")
                st.rerun()

        confirm_delete_person = st.checkbox("Je confirme la suppression de cette personne")
        if st.button("Supprimer la personne sélectionnée"):
            if not confirm_delete_person:
                st.error("Veuillez confirmer la suppression.")
            else:
                execute("DELETE FROM people WHERE person_id = ?", (int(person_id),))
                st.success("Personne supprimée.")
                st.rerun()

elif page == "Analytics":
    st.title("Analytics")
    projects = fetch_df("SELECT * FROM projects ORDER BY start_date")
    tasks = get_all_tasks()
    budget = fetch_df("SELECT * FROM budget")

    if projects.empty:
        st.info("Aucun projet disponible.")
    else:
        progress_df = get_project_progress()
        a1, a2 = st.columns(2)

        with a1:
            st.subheader("Profit par projet")
            proj_fin = projects[["project_name", "expected_revenue", "expected_cost"]].copy()
            proj_fin["profit"] = proj_fin["expected_revenue"].fillna(0) - proj_fin["expected_cost"].fillna(0)
            st.bar_chart(proj_fin.set_index("project_name")[["profit"]])

        with a2:
            st.subheader("Progression par projet")
            if not progress_df.empty:
                st.bar_chart(progress_df.set_index("project_name")[["progress_pct"]])

        if not tasks.empty:
            st.subheader("Tâches par statut")
            task_status_chart = tasks.groupby("task_status").size().reset_index(name="count").set_index("task_status")
            st.bar_chart(task_status_chart)

            st.subheader("Tâches par priorité")
            task_priority_chart = tasks.groupby("task_priority").size().reset_index(name="count").set_index("task_priority")
            st.bar_chart(task_priority_chart)

        if not budget.empty:
            st.subheader("Budget par catégorie")
            budget_cat = budget.groupby("category")["expected_amount"].sum().reset_index().set_index("category")
            st.bar_chart(budget_cat)

            st.subheader("Prévu vs Réel")
            compare_df = pd.DataFrame({
                "Prévu": [budget["expected_amount"].fillna(0).sum()],
                "Réel": [budget["real_amount"].fillna(0).sum()]
            }, index=["Global"])
            st.bar_chart(compare_df)

elif page == "Backup":
    st.title("Backup et restauration")

    st.subheader("1. Télécharger la base de données complète")
    db_bytes = get_db_download_bytes()
    if db_bytes:
        st.download_button(
            label="Télécharger le fichier .db",
            data=db_bytes,
            file_name="ia_soccer_projects.db",
            mime="application/octet-stream"
        )
    else:
        st.warning("Aucune base de données trouvée.")

    st.subheader("2. Créer un backup local")
    if st.button("Créer un backup maintenant"):
        backup_file = create_db_backup()
        if backup_file:
            st.success(f"Backup créé : {backup_file.name}")
        else:
            st.error("Impossible de créer le backup.")

    st.subheader("3. Liste des backups locaux")
    backups = list_backups()
    if backups:
        st.dataframe(
            pd.DataFrame({"Fichiers backup": [b.name for b in backups]}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aucun backup local disponible.")

    st.subheader("4. Restaurer un backup .db")
    uploaded_db = st.file_uploader("Importer un fichier backup .db", type=["db"])
    if uploaded_db is not None:
        if st.button("Restaurer ce backup"):
            ok, msg = restore_db_backup(uploaded_db)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.subheader("5. Export complet")
    excel_data = export_all_to_excel()
    st.download_button(
        label="Télécharger export Excel",
        data=excel_data,
        file_name="ia_soccer_projects_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    json_data = export_all_to_json()
    st.download_button(
        label="Télécharger export JSON",
        data=json_data,
        file_name="ia_soccer_projects_export.json",
        mime="application/json"
    )

    st.info("Conseil: garde toujours um backup .db e um export Excel.")
