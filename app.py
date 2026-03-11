import sqlite3
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).with_name("ia_soccer_projects.db")

st.set_page_config(
    page_title="IA Soccer Projects Pro V3",
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
            ("Revenue", "Inscriptions", "Camp fees", 58800),
            ("Revenue", "Sponsors", "Sponsors", 0),
            ("Cost", "Terrain", "Location terrain", 8000),
            ("Cost", "Staff", "Entraîneurs et staff", 12000),
            ("Cost", "Marketing", "Publicité", 4000),
            ("Cost", "Équipements", "Kits et matériel", 6500),
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
            ("Revenue", "Paiements familles", "Paiements familles", 0),
            ("Cost", "Vol", "Billets d'avion", 0),
            ("Cost", "Hôtel", "Hébergement", 0),
            ("Cost", "Transport", "Transport local", 0),
            ("Cost", "Staff", "Staff", 0),
            ("Cost", "Autre", "Activités", 0),
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
            ("Revenue", "Inscriptions", "Frais d'inscription", 0),
            ("Cost", "Terrain", "Location terrain", 0),
            ("Cost", "Staff", "Évaluateurs", 0),
            ("Cost", "Marketing", "Promotion", 0),
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
            ("Revenue", "Partenariats", "Revenus du partenariat", 0),
            ("Cost", "Administratif", "Déplacements / réunions", 0),
            ("Cost", "Marketing", "Matériel de présentation", 0),
        ],
    },
}

st.markdown(
    """
    <style>
    .main .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
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
    </style>
    """,
    unsafe_allow_html=True
)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_df(query, params=()):
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

def executescript(script):
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(script)
    conn.commit()
    conn.close()

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

    for entry_type, category, description, amount in TEMPLATES["Camp"]["budget"]:
        execute(
            "INSERT INTO budget (project_id, entry_type, category, description, expected_amount, payment_status) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, entry_type, category, description, amount, "Prévu")
        )

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
        for entry_type, category, description, amount in template.get("budget", []):
            execute(
                "INSERT INTO budget (project_id, entry_type, category, description, expected_amount, payment_status) VALUES (?, ?, ?, ?, ?, ?)",
                (project_id, entry_type, category, description, amount, "Prévu")
            )
    refresh_project_totals(project_id)
    return project_id

def refresh_project_totals(project_id):
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

def metrics():
    projects = fetch_df("SELECT * FROM projects")
    if projects.empty:
        return 0, 0, 0, 0
    rev = projects["expected_revenue"].fillna(0).sum()
    cost = projects["expected_cost"].fillna(0).sum()
    return len(projects), rev, cost, rev - cost

init_db()
seed_demo()

st.sidebar.title("⚽ IA Soccer Projects Pro V3")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Projets", "Nouveau projet", "Timeline", "Budget", "Tâches", "Équipe"]
)

if page == "Dashboard":
    st.title("Dashboard")
    count, rev, cost, profit = metrics()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Projets actifs", count)
    m2.metric("Revenu prévu", f"${rev:,.0f}")
    m3.metric("Coût prévu", f"${cost:,.0f}")
    m4.metric("Profit prévu", f"${profit:,.0f}")

    projects = fetch_df("SELECT * FROM projects ORDER BY start_date")
    tasks = fetch_df("""
        SELECT t.task_name, t.task_due_date, t.task_status, t.task_priority, p.project_name
        FROM tasks t
        JOIN projects p ON p.project_id = t.project_id
        ORDER BY t.task_due_date
    """)

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

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.subheader("Projets")
        if filtered_projects.empty:
            st.info("Aucun projet avec ces filtres.")
        else:
            st.dataframe(
                filtered_projects[[
                    "project_name", "project_type", "city", "start_date", "end_date",
                    "project_status", "priority", "expected_revenue", "expected_cost"
                ]],
                use_container_width=True,
                hide_index=True
            )

    with c2:
        st.subheader("Tâches à suivre")
        st.dataframe(tasks.head(12), use_container_width=True, hide_index=True)

    if not filtered_projects.empty:
        st.subheader("Répartition des projets par type")
        type_counts = filtered_projects.groupby("project_type").size().reset_index(name="count")
        type_counts = type_counts.set_index("project_type")
        st.bar_chart(type_counts)

        st.subheader("Revenus et coûts par projet")
        finance = filtered_projects[["project_name", "expected_revenue", "expected_cost"]].copy()
        finance = finance.set_index("project_name")
        st.bar_chart(finance)

elif page == "Projets":
    st.title("Projets")
    projects = fetch_df("SELECT * FROM projects ORDER BY start_date")

    st.dataframe(
        projects[[
            "project_id", "project_name", "project_type", "city", "country",
            "start_date", "end_date", "main_responsible", "project_status",
            "priority", "expected_revenue", "expected_cost"
        ]],
        use_container_width=True,
        hide_index=True
    )

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

            c1, c2 = st.columns(2)
            start_date = c1.text_input("Date début (YYYY-MM-DD)", value=row["start_date"] or "")
            end_date = c2.text_input("Date fin (YYYY-MM-DD)", value=row["end_date"] or "")

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
                        start_date, end_date, main_responsible, project_status,
                        priority, short_description, int(selected)
                    )
                )
                st.success("Projet mis à jour.")

        st.markdown("### Zone de suppression")
        if st.button("Supprimer ce projet"):
            execute("DELETE FROM tasks WHERE project_id = ?", (int(selected),))
            execute("DELETE FROM phases WHERE project_id = ?", (int(selected),))
            execute("DELETE FROM budget WHERE project_id = ?", (int(selected),))
            execute("DELETE FROM projects WHERE project_id = ?", (int(selected),))
            st.success("Projet supprimé.")

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
        st.dataframe(phases, use_container_width=True, hide_index=True)

        with st.form("add_phase"):
            st.subheader("Ajouter une phase")
            a1, a2 = st.columns(2)
            phase_name_new = a1.text_input("Nom de la phase")
            phase_order_new = a2.number_input("Ordre", min_value=1, step=1, value=1)
            b1, b2 = st.columns(2)
            phase_start_new = b1.text_input("Début (YYYY-MM-DD)")
            phase_end_new = b2.text_input("Fin (YYYY-MM-DD)")
            phase_status_new = st.selectbox("Status phase", TASK_STATUS, index=0)
            add_phase_btn = st.form_submit_button("Ajouter phase")
            if add_phase_btn and phase_name_new:
                execute(
                    "INSERT INTO phases (project_id, phase_name, phase_order, phase_start_date, phase_end_date, phase_status) VALUES (?, ?, ?, ?, ?, ?)",
                    (int(selected), phase_name_new, int(phase_order_new), phase_start_new, phase_end_new, phase_status_new)
                )
                st.success("Phase ajoutée.")

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
                phase_start = d1.text_input("Début (YYYY-MM-DD)", value=phase_row["phase_start_date"] or "")
                phase_end = d2.text_input("Fin (YYYY-MM-DD)", value=phase_row["phase_end_date"] or "")
                phase_status = st.selectbox(
                    "Status",
                    TASK_STATUS,
                    index=TASK_STATUS.index(phase_row["phase_status"]) if phase_row["phase_status"] in TASK_STATUS else 0
                )
                save_phase = st.form_submit_button("Enregistrer phase")
                if save_phase:
                    execute(
                        "UPDATE phases SET phase_name=?, phase_order=?, phase_start_date=?, phase_end_date=?, phase_status=? WHERE phase_id=?",
                        (phase_name, int(phase_order), phase_start, phase_end, phase_status, int(edit_phase_id))
                    )
                    st.success("Phase mise à jour.")

            if st.button("Supprimer la phase sélectionnée"):
                execute("DELETE FROM phases WHERE phase_id = ?", (int(edit_phase_id),))
                st.success("Phase supprimée.")

elif page == "Budget":
    st.title("Budget")
    projects = fetch_df("SELECT project_id, project_name FROM projects ORDER BY start_date")

    if projects.empty:
        st.info("Aucun projet pour le moment.")
    else:
        selected = st.selectbox(
            "Projet",
            projects["project_id"],
            format_func=lambda x: f"{x} - {projects.loc[projects.project_id == x, 'project_name'].iloc[0]}"
        )

        budget = fetch_df(
            "SELECT budget_id, entry_type, category, description, expected_amount, real_amount, payment_status FROM budget WHERE project_id = ? ORDER BY entry_type DESC, category",
            (int(selected),)
        )

        rev = budget.loc[budget["entry_type"] == "Revenue", "expected_amount"].fillna(0).sum() if not budget.empty else 0
        cost = budget.loc[budget["entry_type"] == "Cost", "expected_amount"].fillna(0).sum() if not budget.empty else 0

        a1, a2, a3 = st.columns(3)
        a1.metric("Revenu prévu", f"${rev:,.0f}")
        a2.metric("Coût prévu", f"${cost:,.0f}")
        a3.metric("Profit prévu", f"${rev - cost:,.0f}")

        st.dataframe(budget.drop(columns=["budget_id"]), use_container_width=True, hide_index=True)

        if not budget.empty:
            finance_chart = budget.groupby("entry_type")["expected_amount"].sum().reset_index()
            finance_chart = finance_chart.set_index("entry_type")
            st.bar_chart(finance_chart)

        with st.form("add_budget"):
            st.subheader("Ajouter une ligne de budget")
            b1, b2, b3 = st.columns(3)
            entry_type = b1.selectbox("Type", ENTRY_TYPES)
            category = b2.text_input("Catégorie")
            description = b3.text_input("Description")
            c1, c2 = st.columns(2)
            expected_amount = c1.number_input("Montant prévu", min_value=0.0, step=100.0)
            real_amount = c2.number_input("Montant réel", min_value=0.0, step=100.0)
            payment_status = st.selectbox("État", PAYMENT_STATUS)
            add_b = st.form_submit_button("Ajouter")
            if add_b:
                execute(
                    "INSERT INTO budget (project_id, entry_type, category, description, expected_amount, real_amount, payment_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (int(selected), entry_type, category, description, float(expected_amount), float(real_amount), payment_status)
                )
                refresh_project_totals(int(selected))
                st.success("Ligne de budget ajoutée.")

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
                e1, e2 = st.columns(2)
                e_expected = e1.number_input("Montant prévu", min_value=0.0, step=100.0, value=float(b_row["expected_amount"] or 0))
                e_real = e2.number_input("Montant réel", min_value=0.0, step=100.0, value=float(b_row["real_amount"] or 0))
                e_status = st.selectbox(
                    "État",
                    PAYMENT_STATUS,
                    index=PAYMENT_STATUS.index(b_row["payment_status"]) if b_row["payment_status"] in PAYMENT_STATUS else 0
                )
                save_edit = st.form_submit_button("Enregistrer modifications")
                if save_edit:
                    execute(
                        "UPDATE budget SET entry_type=?, category=?, description=?, expected_amount=?, real_amount=?, payment_status=? WHERE budget_id=?",
                        (e_type, e_cat, e_desc, float(e_expected), float(e_real), e_status, int(edit_id))
                    )
                    refresh_project_totals(int(selected))
                    st.success("Ligne de budget mise à jour.")

            if st.button("Supprimer la ligne sélectionnée"):
                execute("DELETE FROM budget WHERE budget_id = ?", (int(edit_id),))
                refresh_project_totals(int(selected))
                st.success("Ligne supprimée.")

elif page == "Tâches":
    st.title("Tâches")
    tasks = fetch_df("""
        SELECT t.task_id, p.project_name, ph.phase_name, t.task_name, t.task_responsible,
               t.task_due_date, t.task_status, t.task_priority, t.notes
        FROM tasks t
        JOIN projects p ON p.project_id = t.project_id
        LEFT JOIN phases ph ON ph.phase_id = t.phase_id
        ORDER BY t.task_due_date, t.task_priority
    """)

    st.dataframe(tasks.drop(columns=["task_id"]), use_container_width=True, hide_index=True)

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
            task_due_date_new = t3.text_input("Date limite (YYYY-MM-DD)")
            task_status_new = t4.selectbox("Status", TASK_STATUS, index=0, key="new_task_status")
            t5, t6 = st.columns(2)
            task_priority_new = t5.selectbox("Priorité", PRIORITIES, index=1, key="new_task_priority")
            phase_id_new = t6.selectbox(
                "Phase",
                phases["phase_id"].tolist() if not phases.empty else [],
                format_func=lambda x: phases.loc[phases.phase_id == x, "phase_name"].iloc[0] if not phases.empty else "",
                key="new_task_phase"
            )
            notes_new = st.text_input("Notes")
            add_task_btn = st.form_submit_button("Ajouter tâche")
            if add_task_btn and task_name_new:
                execute(
                    """INSERT INTO tasks
                    (project_id, phase_id, task_name, task_responsible, task_due_date, task_status, task_priority, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (int(add_project_id), int(phase_id_new) if phase_id_new else None, task_name_new, task_responsible_new, task_due_date_new, task_status_new, task_priority_new, notes_new)
                )
                st.success("Tâche ajoutée.")

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
            due = e3.text_input("Date limite (YYYY-MM-DD)", value=t_row["task_due_date"] or "")
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
                    (task_name, task_responsible, due, status, priority, notes, int(task_id))
                )
                st.success("Tâche mise à jour.")

        if st.button("Supprimer la tâche sélectionnée"):
            execute("DELETE FROM tasks WHERE task_id = ?", (int(task_id),))
            st.success("Tâche supprimée.")

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

        if st.button("Supprimer la personne sélectionnée"):
            execute("DELETE FROM people WHERE person_id = ?", (int(person_id),))
            st.success("Personne supprimée.")
