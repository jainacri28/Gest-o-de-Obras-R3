from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from .seed_data import build_seed_payload


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "gestao_obras.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                address TEXT,
                technical_manager TEXT,
                start_date TEXT,
                planned_end_date TEXT,
                status TEXT,
                planned_budget REAL DEFAULT 0,
                actual_budget REAL DEFAULT 0,
                planned_days INTEGER DEFAULT 0,
                executed_days INTEGER DEFAULT 0,
                delay_days INTEGER DEFAULT 0,
                overall_progress REAL DEFAULT 0,
                general_notes TEXT,
                timeline_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                start_date TEXT,
                end_date TEXT,
                progress REAL DEFAULT 0,
                status TEXT,
                notes TEXT,
                planned_cost REAL DEFAULT 0,
                actual_cost REAL DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                stage_id INTEGER,
                planned_start TEXT,
                planned_end TEXT,
                planned_days INTEGER DEFAULT 0,
                executed_days INTEGER DEFAULT 0,
                variance_days INTEGER DEFAULT 0,
                progress REAL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (stage_id) REFERENCES stages(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS labor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                stage_id INTEGER NOT NULL,
                professional_name TEXT NOT NULL,
                role TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                daily_rate REAL DEFAULT 0,
                days_worked INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (stage_id) REFERENCES stages(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                stage_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                planned_cost REAL DEFAULT 0,
                actual_cost REAL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (stage_id) REFERENCES stages(id) ON DELETE CASCADE
            );
            """
        )

    if get_projects_df().empty:
        seed_demo_data()


def seed_demo_data() -> None:
    with get_connection() as conn:
        for client in build_seed_payload():
            client_id = conn.execute(
                "INSERT INTO clients (name, phone, email) VALUES (?, ?, ?)",
                (client["client_name"], client["phone"], client["email"]),
            ).lastrowid

            project_id = conn.execute(
                """
                INSERT INTO projects (
                    client_id, name, address, technical_manager, start_date, planned_end_date,
                    status, planned_budget, actual_budget, planned_days, executed_days, delay_days,
                    overall_progress, general_notes, timeline_notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    client_id,
                    client["project_name"],
                    client["address"],
                    client["technical_manager"],
                    client["start_date"],
                    client["planned_end_date"],
                    client["status"],
                    client["planned_budget"],
                    client["actual_budget"],
                    client["planned_days"],
                    client["executed_days"],
                    client["delay_days"],
                    client["overall_progress"],
                    client["general_notes"],
                    client["timeline_notes"],
                ),
            ).lastrowid

            for stage in client["stages"]:
                stage_id = conn.execute(
                    """
                    INSERT INTO stages (
                        project_id, name, description, start_date, end_date,
                        progress, status, notes, planned_cost, actual_cost
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        stage["name"],
                        stage["description"],
                        stage["start_date"],
                        stage["end_date"],
                        stage["progress"],
                        stage["status"],
                        stage["notes"],
                        stage["planned_cost"],
                        stage["actual_cost"],
                    ),
                ).lastrowid

                planned_days = max(
                    (
                        pd.to_datetime(stage["end_date"]) - pd.to_datetime(stage["start_date"])
                    ).days,
                    0,
                )
                executed_days = int(planned_days * (stage["progress"] / 100))
                variance_days = executed_days - planned_days
                conn.execute(
                    """
                    INSERT INTO schedules (
                        project_id, stage_id, planned_start, planned_end,
                        planned_days, executed_days, variance_days, progress, notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        stage_id,
                        stage["start_date"],
                        stage["end_date"],
                        planned_days,
                        executed_days,
                        variance_days,
                        stage["progress"],
                        stage["notes"],
                    ),
                )

                conn.executemany(
                    """
                    INSERT INTO labor (
                        project_id, stage_id, professional_name, role, quantity,
                        daily_rate, days_worked, total_cost, notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            project_id,
                            stage_id,
                            item["name"],
                            item["role"],
                            item["quantity"],
                            item["daily_rate"],
                            item["days_worked"],
                            item["total_cost"],
                            item["notes"],
                        )
                        for item in stage["labor"]
                    ],
                )

                conn.executemany(
                    """
                    INSERT INTO costs (
                        project_id, stage_id, category, planned_cost, actual_cost, notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            project_id,
                            stage_id,
                            item["category"],
                            item["planned_cost"],
                            item["actual_cost"],
                            item["notes"],
                        )
                        for item in stage["costs"]
                    ],
                )


def add_client_and_project(client_data: dict, project_data: dict) -> None:
    with get_connection() as conn:
        client_id = conn.execute(
            "INSERT INTO clients (name, phone, email) VALUES (?, ?, ?)",
            (client_data["name"], client_data["phone"], client_data["email"]),
        ).lastrowid
        conn.execute(
            """
            INSERT INTO projects (
                client_id, name, address, technical_manager, start_date, planned_end_date,
                status, planned_budget, actual_budget, planned_days, executed_days, delay_days,
                overall_progress, general_notes, timeline_notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                project_data["name"],
                project_data["address"],
                project_data["technical_manager"],
                project_data["start_date"],
                project_data["planned_end_date"],
                project_data["status"],
                project_data["planned_budget"],
                project_data["actual_budget"],
                project_data["planned_days"],
                project_data["executed_days"],
                project_data["delay_days"],
                project_data["overall_progress"],
                project_data["general_notes"],
                project_data["timeline_notes"],
            ),
        )


def get_clients_df() -> pd.DataFrame:
    return _read_sql(
        """
        SELECT
            c.id AS client_id,
            c.name AS cliente,
            c.phone AS telefone,
            c.email AS email,
            p.id AS project_id,
            p.name AS obra,
            p.address AS endereco,
            p.technical_manager AS responsavel_tecnico,
            p.start_date AS inicio,
            p.planned_end_date AS termino_previsto,
            p.status AS status,
            p.overall_progress AS percentual_executado,
            p.general_notes AS observacoes
        FROM clients c
        LEFT JOIN projects p ON p.client_id = c.id
        ORDER BY c.id
        """
    )


def get_projects_df() -> pd.DataFrame:
    return _read_sql(
        """
        SELECT
            p.id AS project_id,
            c.name AS cliente,
            p.name AS obra,
            p.address AS endereco,
            p.technical_manager AS responsavel_tecnico,
            p.start_date,
            p.planned_end_date,
            p.status,
            p.planned_budget,
            p.actual_budget,
            p.planned_days,
            p.executed_days,
            p.delay_days,
            p.overall_progress,
            p.general_notes,
            p.timeline_notes,
            ROUND(p.actual_budget - p.planned_budget, 2) AS budget_delta,
            CASE
                WHEN p.planned_budget = 0 THEN 0
                ELSE ROUND(((p.actual_budget - p.planned_budget) / p.planned_budget) * 100, 2)
            END AS budget_delta_pct
        FROM projects p
        JOIN clients c ON c.id = p.client_id
        ORDER BY p.id
        """
    )


def get_stages_df() -> pd.DataFrame:
    return _read_sql(
        """
        SELECT
            s.id AS stage_id,
            p.id AS project_id,
            c.name AS cliente,
            p.name AS obra,
            s.name AS etapa,
            s.description AS descricao,
            s.start_date AS inicio,
            s.end_date AS fim,
            s.progress AS percentual_concluido,
            s.status AS status_etapa,
            s.notes AS observacoes,
            s.planned_cost AS custo_previsto,
            s.actual_cost AS custo_real,
            ROUND(s.actual_cost - s.planned_cost, 2) AS diferenca
        FROM stages s
        JOIN projects p ON p.id = s.project_id
        JOIN clients c ON c.id = p.client_id
        ORDER BY p.id, s.id
        """
    )


def get_labor_df() -> pd.DataFrame:
    return _read_sql(
        """
        SELECT
            l.id AS labor_id,
            c.name AS cliente,
            p.name AS obra,
            s.name AS etapa,
            l.professional_name AS nome,
            l.role AS funcao,
            l.quantity AS quantidade_necessaria,
            l.daily_rate AS valor_diaria,
            l.days_worked AS dias_trabalhados,
            l.total_cost AS custo_total_mao_de_obra,
            l.notes AS observacoes
        FROM labor l
        JOIN projects p ON p.id = l.project_id
        JOIN clients c ON c.id = p.client_id
        JOIN stages s ON s.id = l.stage_id
        ORDER BY p.id, s.id, l.role
        """
    )


def get_schedules_df() -> pd.DataFrame:
    return _read_sql(
        """
        SELECT
            sc.id AS schedule_id,
            c.name AS cliente,
            p.name AS obra,
            COALESCE(s.name, 'Cronograma geral') AS etapa,
            sc.planned_start AS prazo_inicio,
            sc.planned_end AS prazo_fim,
            sc.planned_days AS dias_previstos,
            sc.executed_days AS dias_executados,
            sc.variance_days AS atraso_ou_adiantamento,
            sc.progress AS andamento_etapa,
            sc.notes AS observacoes
        FROM schedules sc
        JOIN projects p ON p.id = sc.project_id
        JOIN clients c ON c.id = p.client_id
        LEFT JOIN stages s ON s.id = sc.stage_id
        ORDER BY p.id, sc.id
        """
    )


def get_costs_df() -> pd.DataFrame:
    return _read_sql(
        """
        SELECT
            ct.id AS cost_id,
            c.name AS cliente,
            p.name AS obra,
            s.name AS etapa,
            ct.category AS categoria,
            ct.planned_cost AS custo_previsto,
            ct.actual_cost AS custo_real,
            ROUND(ct.actual_cost - ct.planned_cost, 2) AS diferenca,
            CASE
                WHEN ct.planned_cost = 0 THEN 0
                ELSE ROUND(((ct.actual_cost - ct.planned_cost) / ct.planned_cost) * 100, 2)
            END AS variacao_percentual,
            ct.notes AS observacoes
        FROM costs ct
        JOIN projects p ON p.id = ct.project_id
        JOIN clients c ON c.id = p.client_id
        JOIN stages s ON s.id = ct.stage_id
        ORDER BY p.id, s.id, ct.category
        """
    )


def get_project_options() -> list[str]:
    df = get_projects_df()
    return df["obra"].dropna().tolist()


def _read_sql(query: str) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)
