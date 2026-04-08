from __future__ import annotations

from datetime import date, timedelta


STAGE_LABELS = [
    ("civil", "Construção civil"),
    ("eletrica", "Construção elétrica"),
    ("hidraulica", "Construção hidráulica"),
    ("acabamento", "Acabamento final"),
]

COST_CATEGORIES = [
    "Materiais",
    "Mão de obra",
    "Equipamentos",
    "Transporte",
    "Acabamento",
    "Instalações elétricas",
    "Instalações hidráulicas",
    "Outros",
]


def build_seed_payload() -> list[dict]:
    clients = [
        {
            "client_name": "Alfa Empreendimentos",
            "project_name": "Residencial Horizonte",
            "address": "Av. das Palmeiras, 1200 - Goiânia/GO",
            "phone": "(62) 99111-1200",
            "email": "contato@alfaempreendimentos.com",
            "technical_manager": "Eng. Carla Menezes",
        },
        {
            "client_name": "Brisa Engenharia",
            "project_name": "Centro Comercial Brisa Sul",
            "address": "Rua 7, 845 - Brasília/DF",
            "phone": "(61) 99222-8450",
            "email": "obras@brisaengenharia.com",
            "technical_manager": "Eng. Rafael Castro",
        },
        {
            "client_name": "Construtora Aurora",
            "project_name": "Condomínio Aurora Park",
            "address": "Av. Central, 450 - Uberlândia/MG",
            "phone": "(34) 98888-4500",
            "email": "engenharia@aurora.com.br",
            "technical_manager": "Eng. Beatriz Lima",
        },
        {
            "client_name": "Delta Infra",
            "project_name": "Hospital Vida Nova",
            "address": "Rua das Acácias, 98 - Ribeirão Preto/SP",
            "phone": "(16) 99777-0098",
            "email": "projetos@deltainfra.com",
            "technical_manager": "Eng. Marcelo Duarte",
        },
        {
            "client_name": "EcoBuild",
            "project_name": "Escola Parque Verde",
            "address": "Av. Ecológica, 321 - Curitiba/PR",
            "phone": "(41) 99666-0321",
            "email": "planejamento@ecobuild.com",
            "technical_manager": "Eng. Helena Prado",
        },
        {
            "client_name": "Futura Obras",
            "project_name": "Galpão Logístico Futura",
            "address": "Rod. BR-153 Km 18 - Anápolis/GO",
            "phone": "(62) 99333-1818",
            "email": "controles@futuraobras.com.br",
            "technical_manager": "Eng. Vinicius Rocha",
        },
        {
            "client_name": "Grupo Solaris",
            "project_name": "Hotel Solaris Prime",
            "address": "Orla Azul, 56 - Vitória/ES",
            "phone": "(27) 99444-0056",
            "email": "gestao@gruposolaris.com",
            "technical_manager": "Eng. Fernanda Alves",
        },
        {
            "client_name": "Habitar Engenharia",
            "project_name": "Residencial Jardim dos Ipês",
            "address": "Rua dos Ipês, 230 - Campo Grande/MS",
            "phone": "(67) 99123-0230",
            "email": "obras@habitar.eng.br",
            "technical_manager": "Eng. Paulo Victor",
        },
        {
            "client_name": "Ícone Projetos",
            "project_name": "Centro Médico Ícone",
            "address": "Av. Saúde, 110 - Campinas/SP",
            "phone": "(19) 99881-0110",
            "email": "adm@iconeprojetos.com",
            "technical_manager": "Eng. Larissa Faria",
        },
        {
            "client_name": "Jatobá Construções",
            "project_name": "Parque Industrial Jatobá",
            "address": "Distrito Industrial, Quadra 9 - Cuiabá/MT",
            "phone": "(65) 99990-0909",
            "email": "producao@jatobaconstr.com",
            "technical_manager": "Eng. André Gusmão",
        },
    ]

    project_statuses = [
        "Em andamento",
        "Em andamento",
        "Pausada",
        "Em andamento",
        "Concluída",
        "Em andamento",
        "Não iniciada",
        "Em andamento",
        "Em andamento",
        "Concluída",
    ]

    payload = []
    base_start = date(2025, 1, 6)

    for index, client in enumerate(clients, start=1):
        start_date = base_start + timedelta(days=index * 14)
        planned_days = 150 + index * 8
        planned_end = start_date + timedelta(days=planned_days)
        executed_days = max(0, planned_days - 28 + index * 5)
        if project_statuses[index - 1] == "Concluída":
            executed_days = planned_days - (6 - index % 4)
        if project_statuses[index - 1] == "Não iniciada":
            executed_days = 0
        if project_statuses[index - 1] == "Pausada":
            executed_days = planned_days - 20

        today_reference = date(2026, 4, 8)
        delay_days = (today_reference - planned_end).days if today_reference > planned_end else 0
        overall_progress = min(
            100,
            0 if project_statuses[index - 1] == "Não iniciada" else 32 + index * 6,
        )
        if project_statuses[index - 1] == "Concluída":
            overall_progress = 100

        base_budget = 420000 + index * 65000
        actual_budget = int(base_budget * (0.92 + ((index % 5) * 0.05)))
        if project_statuses[index - 1] == "Não iniciada":
            actual_budget = 0

        stages = []
        stage_window = planned_days // 4
        for stage_index, (_, stage_name) in enumerate(STAGE_LABELS, start=1):
            stage_start = start_date + timedelta(days=(stage_index - 1) * stage_window)
            stage_end = stage_start + timedelta(days=stage_window - 2)
            if project_statuses[index - 1] == "Não iniciada":
                stage_progress = 0
                stage_status = "Não iniciada"
            else:
                stage_progress = min(100, max(0, overall_progress - (stage_index - 1) * 18 + 10))
                stage_status = (
                    "Concluída"
                    if stage_progress >= 100
                    else "Em andamento"
                    if stage_progress > 0
                    else "Não iniciada"
                )
                if project_statuses[index - 1] == "Pausada" and stage_index >= 3:
                    stage_status = "Pausada"
            stage_planned = base_budget * [0.34, 0.23, 0.19, 0.24][stage_index - 1]
            stage_actual = stage_planned * (
                0.9 if stage_progress == 0 else (1.0 + ((index + stage_index) % 4) * 0.05)
            )

            stages.append(
                {
                    "name": stage_name,
                    "description": f"Execução da etapa de {stage_name.lower()} com acompanhamento técnico e controle de qualidade.",
                    "start_date": stage_start.isoformat(),
                    "end_date": stage_end.isoformat(),
                    "progress": stage_progress,
                    "status": stage_status,
                    "notes": f"Checklist semanal ativo, inspeções quinzenais e apontamentos fotográficos para {stage_name.lower()}.",
                    "planned_cost": round(stage_planned, 2),
                    "actual_cost": round(stage_actual, 2),
                    "labor": _build_labor_entries(index, stage_index, stage_name),
                    "costs": _build_cost_entries(stage_planned, stage_actual, stage_name),
                }
            )

        payload.append(
            {
                **client,
                "start_date": start_date.isoformat(),
                "planned_end_date": planned_end.isoformat(),
                "status": project_statuses[index - 1],
                "planned_budget": round(base_budget, 2),
                "actual_budget": round(actual_budget, 2),
                "general_notes": "Monitoramento com atualização semanal de custos, produtividade e riscos operacionais.",
                "timeline_notes": f"Prazo previsto de {planned_days} dias com {executed_days} dias executados até o momento.",
                "planned_days": planned_days,
                "executed_days": executed_days,
                "delay_days": delay_days if project_statuses[index - 1] != "Concluída" else 0,
                "overall_progress": overall_progress,
                "stages": stages,
            }
        )

    return payload


def _build_labor_entries(client_index: int, stage_index: int, stage_name: str) -> list[dict]:
    profiles = [
        ("João Ferreira", "Pedreiro", 2 + (client_index % 2), 220),
        ("Carlos Souza", "Servente", 2, 140),
        ("Marcos Silva", "Mestre de obras", 1, 320),
        ("Ana Ribeiro", "Engenheiro civil", 1, 650),
        ("Paulo Nunes", "Eletricista", 1 + (stage_index == 2), 290),
        ("Diego Lima", "Encanador", 1 + (stage_index == 3), 275),
        ("Renato Prado", "Pintor", 1 + (stage_index == 4), 210),
        ("Felipe Costa", "Gesseiro", 1 if stage_index == 4 else 0, 230),
        ("Bruno Melo", "Azulejista", 1 if stage_index >= 3 else 0, 240),
        ("Equipe Complementar", "Outros profissionais", 1, 180),
    ]
    days = 12 + client_index + stage_index * 2
    entries = []
    for name, role, qty, daily_rate in profiles:
        if qty <= 0:
            continue
        days_worked = max(4, days - (3 if role in {"Pintor", "Gesseiro"} else 0))
        entries.append(
            {
                "name": name,
                "role": role,
                "quantity": qty,
                "daily_rate": float(daily_rate),
                "days_worked": days_worked,
                "total_cost": float(qty * daily_rate * days_worked),
                "notes": f"Equipe alocada na etapa de {stage_name.lower()} com acompanhamento diário.",
            }
        )
    return entries


def _build_cost_entries(stage_planned: float, stage_actual: float, stage_name: str) -> list[dict]:
    weights = [0.24, 0.21, 0.1, 0.08, 0.12, 0.11, 0.08, 0.06]
    entries = []
    for idx, category in enumerate(COST_CATEGORIES):
        planned = round(stage_planned * weights[idx], 2)
        variance_factor = 0.94 + (idx % 4) * 0.06
        actual = round(planned * variance_factor * (stage_actual / stage_planned), 2)
        entries.append(
            {
                "category": category,
                "planned_cost": planned,
                "actual_cost": actual,
                "notes": f"Lançamentos de {category.lower()} vinculados à etapa de {stage_name.lower()}.",
            }
        )
    return entries
