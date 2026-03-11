import sqlite3
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st

DB_PATH = Path("ia_soccer_projects.db")

st.set_page_config(page_title="IA Soccer Projects", page_icon="⚽", layout="wide")

PROJECT_TYPES = [
    "Camp", "Voyage", "Tryout", "Événement",
    "Partenariat", "Formation", "Projet interne", "Autre"
]
PROJECT_STATUS = ["Idée", "En préparation", "En vente", "Confirmé", "En exécution", "Fermé", "Annulé"]
PRIORITIES = ["Haute", "Moyenne", "Basse"]
PAYMENT_STATUS = ["Prévu", "Confirmé", "Payé", "Partiel", "En attente"]
ENTRY_TYPES = ["Revenue", "Cost"]

TEMPLATES = {
    "Camp": {
        "phases": [
            ("Planification", 1), ("Marketing", 2), ("Inscriptions", 3),
            ("Staff", 4), ("Logistique", 5), ("Exécution", 6), ("Clôture", 7)
        ],
        "tasks": {
            "Planification": [
                "Confirmer les dates",
                "Confirmer le terrain / installations",
                "Définir le prix",
                "Créer le formulaire d'inscription",
            ],
            "Marketing": [
                "Créer la campagne Meta Ads",
                "Créer les flyers",
                "Envoyer l'email marketing",
                "Contacter les clubs locaux",
            ],
            "Inscriptions": [
                "Suivre les inscriptions",
                "Recevoir les dépôts",
                "Confirmer les paiements",
                "Mettre à jour la liste des joueurs",
            ],
            "Staff": [
                "Confirmer les entraîneurs",
                "Créer les groupes par âge",
            ],
            "Logistique": [
                "Commander le matériel",
                "Préparer les kits",
                "Créer les groupes WhatsApp",
            ],
            "Exécution": [
                "Check-in des joueurs",
                "Sessions d'entraînement",
                "Photos et vidéos",
            ],
            "Clôture": [
                "Envoyer les certificats",
                "Rapport final",
            ],
        },
        "budget": [
            ("Revenue", "Inscriptions", "Camp fees"),
            ("Revenue", "Sponsors", "Sponsors"),
            ("Cost", "Terrain", "Location terrain"),
            ("Cost", "Staff", "Entraîneurs et staff"),
            ("Cost", "Marketing", "Publicité"),
            ("Cost", "Équipements", "Kits et matériel"),
        ],
    },
    "Voyage": {
        "phases": [
            ("Planification", 1), ("Vente", 2), ("Réservations", 3),
            ("Paiements", 4), ("Logistique", 5), ("Exécution", 6), ("Rapport final", 7)
        ],
        "tasks": {
            "Planification": ["Définir le programme", "Estimer le budget", "Fixer le prix"],
            "Vente": ["Créer la présentation", "Promouvoir le voyage", "Recevoir les dépôts"],
            "Réservations": ["Réserver vols", "Réserver hôtels", "Confirmer matchs / visites"],
            "Paiements": ["Suivre les paiements finaux", "Payer fournisseurs"],
            "Logistique": ["Préparer les documents", "Créer le groupe familles", "Finaliser l'itinéraire"],
            "Exécution": ["Gestion du groupe", "Transport", "Matchs / visites"],
            "Rapport final": ["Bilan financier", "Photos / vidéos", "Évaluation finale"],
        },
        "budget": [
            ("Revenue", "Paiements familles", "Paiements familles"),
            ("Cost", "Vol", "Billets d'avion"),
            ("Cost", "Hôtel", "Hébergement"),
            ("Cost", "Transport", "Transport local"),
            ("Cost", "Staff", "Staff"),
            ("Cost", "Autre", "Activités"),
        ],
    },
    "Tryout": {
        "phases": [
            ("Planification", 1), ("Promotion", 2), ("Inscriptions", 3),
            ("Logistique", 4), ("Exécution", 5), ("Évaluation", 6), ("Clôture", 7)
        ],
        "tasks": {
            "Planification": ["Définir date et lieu", "Confirmer le staff", "Créer le formulaire"],
            "Promotion": ["Posts réseaux sociaux", "Contacter clubs", "Email marketing"],
            "Inscriptions": ["Recevoir inscriptions", "Confirmer paiements"],
            "Logistique": ["Préparer terrain", "Préparer matériel", "Créer groupes"],
            "Exécution": ["Check-in", "Évaluations terrain"],
            "Évaluation": ["Analyser résultats", "Sélection joueurs"],
            "Clôture": ["Envoyer réponses", "Rapport final"],
        },
        "budget": [
            ("Revenue", "Inscriptions", "Frais d'inscription"),
            ("Cost", "Terrain", "Location terrain"),
            ("Cost", "Staff", "Évaluateurs"),
            ("Cost", "Marketing", "Promotion"),
        ],
    },
    "Partenariat": {
        "phases": [
            ("Identification", 1), ("Contact", 2), ("Négociation", 3),
            ("Proposition", 4), ("Accord", 5), ("Implémentation", 6), ("Évaluation", 7)
        ],
        "tasks": {
            "Identification": ["Identifier le partenaire", "Collecter les informations"],
            "Contact": ["Envoyer l'email initial", "Réunion exploratoire"],
            "Négociation": ["Définir le modèle", "Discuter les conditions"],
            "Proposition": ["Créer la proposition", "Présenter le projet"],
            "Accord": ["Rédiger contrat", "Signer partenariat"],
            "Implémentation": ["Planifier activités", "Fixer calendrier"],
            "Évaluation": ["Évaluer résultats"],
        },
        "budget": [
            ("Revenue", "Partenariats", "Revenus du partenariat"),
            ("Cost", "Administratif", "Déplacements / réunions"),
            ("Cost", "Marketing", "Matériel de présentation"),
        ],
    }
}

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
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
        phase_status TEXT DEFAULT 'À faire',
        FOREIGN KEY(project_id) REFERENCES projects(project_id)
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
        notes TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(project_id),
        FOREIGN KEY(phase_id) REFERENCES phases(phase_id)
    );

    CREATE TABLE IF NOT EXISTS budget (
        budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        entry_type TEXT NOT NULL,
        category TEXT,
        description TEXT,
        expected_amount REAL DEFAULT 0,
        real_amount REAL DEFAULT 0,
        payment_status TEXT DEFAULT 'Prévu',
        FOREIGN KEY(project_id) REFERENCES projects(project_id)
    );

    CREATE TABLE IF NOT EXISTS people (
        person_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        role_title TEXT,
        email TEXT,
        phone TEXT
    );
    """)
    conn.commit()
    conn.close()

def seed_demo():
    conn = get_conn()
    cur = conn.cursor()
    exists = cur.execute("SELECT COUNT(*) AS c FROM projects").fetchone()["c"]
    if exists == 0:
        cur.execute("""
            INSERT INTO projects
            (project_name, project_type, city, country, main_location, start_date, end_date,
             main_responsible, project_status, priority, short_description, expected_revenue, expected_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "FC Porto World Camp Brossard", "Camp", "Brossard", "Canada", "Complexe CN",
            "2026-06-29", "2026-07-03", "Rogerio Crespo", "En vente", "Haute",
            "Camp officiel de développement", 58800, 33500
        ))
        project_id = cur.lastrowid

        for name, order in TEMPLATES["Camp"]["phases"]:
            cur.execute(
                "INSERT INTO phases (project_id, phase_name, phase_order, phase_status) VALUES (?, ?, ?, ?)",
                (project_id, name, order, "À faire")
            )
            phase_id = cur.lastrowid
            for task in TEMPLATES["Camp"]["tasks"][name]:
                cur.execute(
                    "INSERT INTO tasks (project_id, phase_id, task_name, task_status, task_priority) VALUES (?, ?, ?, ?, ?)",
                    (project_id, phase_id, task, "À faire", "Moyenne")
                )

        for entry_type, category, description in TEMPLATES["Camp"]["budget"]:
            amount = 0
            if description == "Camp fees":
                amount = 58800
            elif description == "Location terrain":
                amount = 8000
            elif description == "Entraîneurs et staff":
                amount = 12000
            elif description == "Publicité":
                amount = 4000
            elif description == "Kits et matériel":
                amount = 6500
            cur.execute(
                "INSERT INTO budget (project_id, entry_type, category, description, expected_amount, payment_status) VALUES (?, ?, ?, ?, ?, ?)",
                (project_id, entry_type, category, description, amount, "Prévu")
            )
        conn.commit()
    conn.close()

def load_df(query, params=()):
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute(query, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    lastrowid = cur.lastrowid
    conn.close()
    return lastrowid

def project_metrics():
    projects = load_df("SELECT * FROM projects")
    if projects.empty:
        return {"projects_count": 0, "expected_revenue": 0, "expected_cost": 0, "expected_profit": 0}
    rev = projects["expected_revenue"].fillna(0).sum()
    cost = projects["expected_cost"].fillna(0).sum()
    return {
        "projects_count": len(projects),
        "expected_revenue": rev,
        "expected_cost": cost,
        "expected_profit": rev - cost
    }

def create_project_with_template(name, ptype, city, country, location, start_date, end_date, responsible, status, priority, desc):
    project_id = execute("""
        INSERT INTO projects
        (project_name, project_type, city, country, main_location, start_date, end_date, main_responsible, project_status, priority, short_description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, ptype, city, country, location, str(start_date), str(end_date), responsible, status, priority, desc))

    template = TEMPLATES.get(ptype)
    if template:
        for phase_name, phase_order in template["phases"]:
            phase_id = execute("""
                INSERT INTO phases (project_id, phase_name, phase_order, phase_status)
                VALUES (?, ?, ?, ?)
            """, (project_id, phase_name, phase_order, "À faire"))
            for task_name in template["tasks"].get(phase_name, []):
                execute("""
                    INSERT INTO tasks (project_id, phase_id, task_name, task_status, task_priority)
                    VALUES (?, ?, ?, ?, ?)
                """, (project_id, phase_id, task_name, "À faire", "Moyenne"))
        for entry_type, category, description in template.get("budget", []):
            execute("""
                INSERT INTO budget (project_id, entry_type, category, description, expected_amount, payment_status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, entry_type, category, description, 0, "Prévu"))
    return project_id

init_db()
seed_demo()

st.sidebar.title("⚽ IA Soccer Projects")
page = st.sidebar.radio("Navigation", ["Dashboard", "Projets", "Nouveau projet", "Timeline", "Budget", "Tâches", "Équipe"])

if page == "Dashboard":
    st.title("Dashboard")
    m = project_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Projets actifs", m["projects_count"])
    c2.metric("Revenu prévu", f"${m['expected_revenue']:,.0f}")
    c3.metric("Coût prévu", f"${m['expected_cost']:,.0f}")
    c4.metric("Profit prévu", f"${m['expected_profit']:,.0f}")

    projects = load_df("SELECT project_id, project_name, project_type, city, start_date, end_date, project_status, priority, expected_revenue, expected_cost FROM projects ORDER BY start_date")
    tasks = load_df("""
        SELECT t.task_id, p.project_name, t.task_name, t.task_due_date, t.task_status, t.task_priority
        FROM tasks t
        JOIN projects p ON p.project_id = t.project_id
        ORDER BY t.task_due_date
    """)
    col1, col2 = st.columns([1.4, 1])
    with col1:
        st.subheader("Projets")
        st.dataframe(projects, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Tâches")
        st.dataframe(tasks.head(12), use_container_width=True, hide_index=True)

elif page == "Projets":
    st.title("Projets")
    projects = load_df("""
        SELECT project_id, project_name, project_type, city, country, start_date, end_date,
               main_responsible, project_status, priority, expected_revenue, expected_cost
        FROM projects ORDER BY start_date
    """)
    st.dataframe(projects, use_container_width=True, hide_index=True)

    if not projects.empty:
        selected = st.selectbox(
            "Voir le détail d'un projet",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )
        proj = load_df("SELECT * FROM projects WHERE project_id = ?", (selected,))
        phases = load_df("SELECT * FROM phases WHERE project_id = ? ORDER BY phase_order", (selected,))
        tasks = load_df("SELECT * FROM tasks WHERE project_id = ?", (selected,))
        budget = load_df("SELECT * FROM budget WHERE project_id = ?", (selected,))

        st.subheader("Résumé")
        st.dataframe(proj, use_container_width=True, hide_index=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Phases", len(phases))
        c2.metric("Tâches", len(tasks))
        rev = budget.loc[budget.entry_type == "Revenue", "expected_amount"].fillna(0).sum()
        cost = budget.loc[budget.entry_type == "Cost", "expected_amount"].fillna(0).sum()
        c3.metric("Profit budget", f"${rev - cost:,.0f}")

        st.subheader("Phases")
        st.dataframe(phases[["phase_name", "phase_order", "phase_status", "phase_start_date", "phase_end_date"]], use_container_width=True, hide_index=True)
        st.subheader("Budget")
        st.dataframe(budget[["entry_type", "category", "description", "expected_amount", "real_amount", "payment_status"]], use_container_width=True, hide_index=True)

elif page == "Nouveau projet":
    st.title("Nouveau projet")
    with st.form("new_project"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Nom du projet")
        ptype = c2.selectbox("Type de projet", PROJECT_TYPES)
        c3, c4 = st.columns(2)
        city = c3.text_input("Ville")
        country = c4.text_input("Pays", value="Canada")
        location = st.text_input("Lieu principal")
        c5, c6 = st.columns(2)
        start_date = c5.date_input("Date de début", value=date.today())
        end_date = c6.date_input("Date de fin", value=date.today())
        c7, c8, c9 = st.columns(3)
        responsible = c7.text_input("Responsable")
        status = c8.selectbox("Status", PROJECT_STATUS, index=1)
        priority = c9.selectbox("Priorité", PRIORITIES, index=1)
        desc = st.text_area("Description courte")
        submitted = st.form_submit_button("Créer le projet")
        if submitted:
            if not name:
                st.error("Le nom du projet est obligatoire.")
            else:
                pid = create_project_with_template(name, ptype, city, country, location, start_date, end_date, responsible, status, priority, desc)
                st.success(f"Projet créé avec succès. ID: {pid}")

elif page == "Timeline":
    st.title("Timeline")
    projects = load_df("SELECT project_id, project_name FROM projects ORDER BY start_date")
    if projects.empty:
        st.info("Aucun projet pour le moment.")
    else:
        selected = st.selectbox(
            "Projet",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )
        phases = load_df("""
            SELECT phase_name, phase_order, phase_start_date, phase_end_date, phase_status
            FROM phases
            WHERE project_id = ?
            ORDER BY phase_order
        """, (selected,))
        tasks = load_df("""
            SELECT t.task_name, p.phase_name, t.task_responsible, t.task_due_date, t.task_status, t.task_priority
            FROM tasks t
            LEFT JOIN phases p ON p.phase_id = t.phase_id
            WHERE t.project_id = ?
            ORDER BY p.phase_order, t.task_due_date
        """, (selected,))
        st.subheader("Phases")
        st.dataframe(phases, use_container_width=True, hide_index=True)
        st.subheader("Tâches liées")
        st.dataframe(tasks, use_container_width=True, hide_index=True)

elif page == "Budget":
    st.title("Budget")
    projects = load_df("SELECT project_id, project_name FROM projects ORDER BY start_date")
    if projects.empty:
        st.info("Aucun projet pour le moment.")
    else:
        selected = st.selectbox(
            "Projet",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )
        budget = load_df("""
            SELECT entry_type, category, description, expected_amount, real_amount, payment_status
            FROM budget
            WHERE project_id = ?
            ORDER BY entry_type DESC, category
        """, (selected,))
        rev = budget.loc[budget.entry_type == "Revenue", "expected_amount"].fillna(0).sum()
        cost = budget.loc[budget.entry_type == "Cost", "expected_amount"].fillna(0).sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Revenu prévu", f"${rev:,.0f}")
        c2.metric("Coût prévu", f"${cost:,.0f}")
        c3.metric("Profit prévu", f"${rev - cost:,.0f}")
        st.dataframe(budget, use_container_width=True, hide_index=True)

        with st.form("add_budget"):
            st.subheader("Ajouter une ligne de budget")
            b1, b2, b3 = st.columns(3)
            entry_type = b1.selectbox("Type", ENTRY_TYPES)
            category = b2.text_input("Catégorie")
            description = b3.text_input("Description")
            a1, a2 = st.columns(2)
            expected_amount = a1.number_input("Montant prévu", min_value=0.0, step=100.0)
            real_amount = a2.number_input("Montant réel", min_value=0.0, step=100.0)
            payment_status = st.selectbox("État", PAYMENT_STATUS)
            add_b = st.form_submit_button("Ajouter")
            if add_b:
                execute("""
                    INSERT INTO budget (project_id, entry_type, category, description, expected_amount, real_amount, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (selected, entry_type, category, description, expected_amount, real_amount, payment_status))
                st.success("Ligne de budget ajoutée.")

elif page == "Tâches":
    st.title("Tâches")
    tasks = load_df("""
        SELECT t.task_id, p.project_name, ph.phase_name, t.task_name, t.task_responsible,
               t.task_due_date, t.task_status, t.task_priority
        FROM tasks t
        JOIN projects p ON p.project_id = t.project_id
        LEFT JOIN phases ph ON ph.phase_id = t.phase_id
        ORDER BY t.task_due_date, t.task_priority
    """)
    st.dataframe(tasks, use_container_width=True, hide_index=True)

elif page == "Équipe":
    st.title("Équipe")
    people = load_df("SELECT * FROM people ORDER BY full_name")
    st.dataframe(people, use_container_width=True, hide_index=True)
    with st.form("add_person"):
        st.subheader("Ajouter une personne")
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Nom complet")
        role_title = c2.text_input("Rôle")
        c3, c4 = st.columns(2)
        email = c3.text_input("Email")
        phone = c4.text_input("Téléphone")
        add_p = st.form_submit_button("Ajouter")
        if add_p:
            if full_name:
                execute("INSERT INTO people (full_name, role_title, email, phone) VALUES (?, ?, ?, ?)", (full_name, role_title, email, phone))
                st.success("Personne ajoutée.")
            else:
                st.error("Le nom est obligatoire.")
