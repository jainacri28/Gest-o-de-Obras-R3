from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.database import (
    add_client_and_project,
    get_clients_df,
    get_costs_df,
    get_labor_df,
    get_projects_df,
    get_schedules_df,
    get_stages_df,
    init_db,
)


st.set_page_config(
    page_title="Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top right, rgba(15,118,110,0.12), transparent 20%),
                    linear-gradient(180deg, #f7f5ef 0%, #eef3ee 100%);
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #17332d 0%, #0f766e 100%);
            }
            [data-testid="stSidebar"] * {
                color: #f8fafc !important;
            }
            .hero {
                padding: 1.4rem 1.5rem;
                border-radius: 24px;
                background: linear-gradient(130deg, #17332d 0%, #0f766e 58%, #d97706 100%);
                color: white;
                box-shadow: 0 18px 40px rgba(23, 51, 45, 0.16);
                margin-bottom: 1rem;
            }
            .hero h1 {
                margin: 0;
                font-size: 2rem;
                line-height: 1.1;
            }
            .hero p {
                margin: 0.55rem 0 0;
                font-size: 1rem;
                max-width: 880px;
            }
            .metric-card {
                background: rgba(255, 255, 255, 0.82);
                border: 1px solid rgba(15, 118, 110, 0.12);
                border-radius: 22px;
                padding: 1rem 1.1rem;
                box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
            }
            .section-card {
                background: rgba(255, 255, 255, 0.84);
                border: 1px solid rgba(23, 51, 45, 0.08);
                border-radius: 22px;
                padding: 1rem 1.1rem;
                box-shadow: 0 12px 25px rgba(15, 23, 42, 0.05);
            }
            .pill {
                display: inline-block;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                background: rgba(217, 119, 6, 0.12);
                color: #92400e;
                font-weight: 600;
                font-size: 0.82rem;
                margin-right: 0.45rem;
                margin-bottom: 0.4rem;
            }
            .small-note {
                color: #475569;
                font-size: 0.92rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, pd.DataFrame]:
    return {
        "clients": get_clients_df(),
        "projects": get_projects_df(),
        "stages": get_stages_df(),
        "schedules": get_schedules_df(),
        "labor": get_labor_df(),
        "costs": get_costs_df(),
    }


def apply_filters(data: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    projects = data["projects"].copy()
    stages = data["stages"].copy()
    schedules = data["schedules"].copy()
    labor = data["labor"].copy()
    costs = data["costs"].copy()
    clients = data["clients"].copy()

    st.sidebar.markdown("## Filtros")
    selected_client = st.sidebar.selectbox("Cliente", ["Todos"] + sorted(projects["cliente"].dropna().unique().tolist()))
    selected_stage = st.sidebar.selectbox("Etapa", ["Todas"] + sorted(stages["etapa"].dropna().unique().tolist()))
    selected_status = st.sidebar.selectbox("Status", ["Todos"] + sorted(projects["status"].dropna().unique().tolist()))

    if selected_client != "Todos":
        projects = projects[projects["cliente"] == selected_client]
        stages = stages[stages["cliente"] == selected_client]
        schedules = schedules[schedules["cliente"] == selected_client]
        labor = labor[labor["cliente"] == selected_client]
        costs = costs[costs["cliente"] == selected_client]
        clients = clients[clients["cliente"] == selected_client]

    if selected_stage != "Todas":
        stages = stages[stages["etapa"] == selected_stage]
        project_names = stages["obra"].unique().tolist()
        projects = projects[projects["obra"].isin(project_names)]
        schedules = schedules[schedules["obra"].isin(project_names) & (schedules["etapa"] == selected_stage)]
        labor = labor[labor["obra"].isin(project_names) & (labor["etapa"] == selected_stage)]
        costs = costs[costs["obra"].isin(project_names) & (costs["etapa"] == selected_stage)]
        clients = clients[clients["obra"].isin(project_names)]

    if selected_status != "Todos":
        projects = projects[projects["status"] == selected_status]
        valid_projects = projects["obra"].tolist()
        stages = stages[stages["obra"].isin(valid_projects)]
        schedules = schedules[schedules["obra"].isin(valid_projects)]
        labor = labor[labor["obra"].isin(valid_projects)]
        costs = costs[costs["obra"].isin(valid_projects)]
        clients = clients[clients["obra"].isin(valid_projects)]

    return (
        {
            "clients": clients,
            "projects": projects,
            "stages": stages,
            "schedules": schedules,
            "labor": labor,
            "costs": costs,
        },
        {"client": selected_client, "stage": selected_stage, "status": selected_status},
    )


def render_sidebar() -> str:
    st.sidebar.markdown("# Gestão de Obras")
    st.sidebar.caption("Controle operacional, financeiro e gerencial em um só painel.")
    return st.sidebar.radio(
        "Navegação",
        [
            "Dashboard",
            "Clientes e Obras",
            "Etapas",
            "Mão de Obra",
            "Cronograma",
            "Custos e Relatórios",
        ],
        label_visibility="collapsed",
    )


def render_header(filters: dict[str, str]) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div>
                <span class="pill">Cliente: {filters['client']}</span>
                <span class="pill">Etapa: {filters['stage']}</span>
                <span class="pill">Status: {filters['status']}</span>
            </div>
            <h1>Plataforma de Gestão de Obras</h1>
            <p>
                Acompanhe 10 obras com visão executiva do andamento, custos previstos x realizados,
                equipes, cronogramas, alertas e relatórios por cliente e etapa.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(data: dict[str, pd.DataFrame]) -> None:
    projects = data["projects"]
    stages = data["stages"]

    if projects.empty:
        st.info("Nenhuma obra encontrada para os filtros selecionados.")
        return

    total_projects = int(len(projects))
    in_progress = int((projects["status"] == "Em andamento").sum())
    completed = int((projects["status"] == "Concluída").sum())
    delayed = int(((projects["delay_days"] > 0) & (projects["status"] != "Concluída")).sum())
    total_planned = float(projects["planned_budget"].sum())
    total_actual = float(projects["actual_budget"].sum())
    avg_progress = float(projects["overall_progress"].mean()) if total_projects else 0

    metrics = st.columns(6)
    for col, (label, value) in zip(
        metrics,
        [
            ("Total de obras", total_projects),
            ("Em andamento", in_progress),
            ("Concluídas", completed),
            ("Atrasadas", delayed),
            ("Custo previsto", format_currency(total_planned)),
            ("Custo real", format_currency(total_actual)),
        ],
    ):
        with col:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(label, value)
            st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1.5, 1])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Indicadores executivos")
        k1, k2, k3 = st.columns(3)
        k1.metric("Execução média", f"{avg_progress:.1f}%")
        k2.metric("Diferença orçamentária", format_currency(float(total_actual - total_planned)))
        k3.metric("Obras dentro do orçamento", int((projects["budget_delta"] <= 0).sum()))

        progress_chart = px.bar(
            projects.sort_values("overall_progress", ascending=False),
            x="obra",
            y="overall_progress",
            color="status",
            text_auto=".0f",
            title="Andamento por cliente / obra",
            labels={"overall_progress": "% executado", "obra": "Obra"},
            color_discrete_sequence=["#0f766e", "#d97706", "#b91c1c", "#64748b"],
        )
        progress_chart.update_layout(height=360, margin=dict(l=10, r=10, t=48, b=10))
        st.plotly_chart(progress_chart, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Alertas automáticos")
        delayed_projects = projects[(projects["delay_days"] > 0) & (projects["status"] != "Concluída")]
        over_budget = projects[projects["budget_delta"] > 0]
        if delayed_projects.empty:
            st.success("Nenhuma obra em atraso no filtro atual.")
        else:
            for _, row in delayed_projects.nlargest(5, "delay_days").iterrows():
                st.warning(f"{row['obra']}: atraso de {int(row['delay_days'])} dias.")
        if over_budget.empty:
            st.success("Nenhuma obra estourando o orçamento no filtro atual.")
        else:
            for _, row in over_budget.nlargest(5, "budget_delta").iterrows():
                st.error(f"{row['obra']}: {format_currency(row['budget_delta'])} acima do previsto.")
        st.markdown("</div>", unsafe_allow_html=True)

    row_two = st.columns(3)
    with row_two[0]:
        chart = px.pie(
            projects,
            names="status",
            title="Status das obras",
            hole=0.56,
            color_discrete_sequence=["#0f766e", "#d97706", "#b91c1c", "#64748b"],
        )
        chart.update_layout(height=330, margin=dict(l=10, r=10, t=48, b=10))
        st.plotly_chart(chart, width="stretch")

    with row_two[1]:
        stage_costs = stages.groupby("etapa", as_index=False)[["custo_previsto", "custo_real"]].sum()
        chart = go.Figure()
        chart.add_bar(x=stage_costs["etapa"], y=stage_costs["custo_previsto"], name="Previsto", marker_color="#0f766e")
        chart.add_bar(x=stage_costs["etapa"], y=stage_costs["custo_real"], name="Real", marker_color="#d97706")
        chart.update_layout(title="Custos por etapa", barmode="group", height=330, margin=dict(l=10, r=10, t=48, b=10))
        st.plotly_chart(chart, width="stretch")

    with row_two[2]:
        ranking = projects.nlargest(7, "actual_budget")[["obra", "actual_budget"]]
        chart = px.bar(
            ranking.sort_values("actual_budget"),
            x="actual_budget",
            y="obra",
            orientation="h",
            title="Ranking das obras mais caras",
            color="actual_budget",
            color_continuous_scale=["#dbeafe", "#0f766e"],
        )
        chart.update_layout(height=330, margin=dict(l=10, r=10, t=48, b=10), coloraxis_showscale=False)
        st.plotly_chart(chart, width="stretch")

    timeline = projects[["obra", "start_date", "planned_end_date", "status"]].copy()
    if not timeline.empty:
        timeline["start_date"] = pd.to_datetime(timeline["start_date"])
        timeline["planned_end_date"] = pd.to_datetime(timeline["planned_end_date"])
        chart = px.timeline(
            timeline,
            x_start="start_date",
            x_end="planned_end_date",
            y="obra",
            color="status",
            title="Linha do tempo das obras",
            color_discrete_sequence=["#0f766e", "#d97706", "#b91c1c", "#64748b"],
        )
        chart.update_yaxes(autorange="reversed")
        chart.update_layout(height=420, margin=dict(l=10, r=10, t=48, b=10))
        st.plotly_chart(chart, width="stretch")

    st.markdown(
        '<div class="small-note">Indicadores calculados automaticamente com base em cronograma, percentual executado e variação de custos.</div>',
        unsafe_allow_html=True,
    )


def render_clients_projects(data: dict[str, pd.DataFrame]) -> None:
    clients = data["clients"].copy()
    projects = data["projects"].copy()

    st.subheader("Cadastro de clientes e obras")
    left, right = st.columns([1.05, 1.35])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### Novo cadastro")
        with st.form("client_project_form", clear_on_submit=True):
            client_name = st.text_input("Nome do cliente")
            project_name = st.text_input("Nome da obra")
            address = st.text_input("Endereço da obra")
            phone = st.text_input("Telefone")
            email = st.text_input("E-mail")
            technical_manager = st.text_input("Responsável técnico")
            start_date = st.date_input("Data de início da obra", value=date.today())
            planned_end_date = st.date_input("Data prevista de término", value=date.today())
            status = st.selectbox("Status da obra", ["Não iniciada", "Em andamento", "Pausada", "Concluída"])
            planned_budget = st.number_input("Custo previsto da obra", min_value=0.0, step=1000.0)
            actual_budget = st.number_input("Custo real da obra", min_value=0.0, step=1000.0)
            overall_progress = st.slider("Percentual executado", 0, 100, 0)
            general_notes = st.text_area("Observações gerais", height=90)
            submitted = st.form_submit_button("Salvar cadastro", width="stretch")

        if submitted:
            if not client_name or not project_name:
                st.error("Preencha pelo menos o nome do cliente e o nome da obra.")
            else:
                planned_days = max((planned_end_date - start_date).days, 0)
                executed_days = int(planned_days * (overall_progress / 100))
                delay_days = max((date.today() - planned_end_date).days, 0) if status != "Concluída" else 0
                add_client_and_project(
                    {"name": client_name, "phone": phone, "email": email},
                    {
                        "name": project_name,
                        "address": address,
                        "technical_manager": technical_manager,
                        "start_date": start_date.isoformat(),
                        "planned_end_date": planned_end_date.isoformat(),
                        "status": status,
                        "planned_budget": planned_budget,
                        "actual_budget": actual_budget,
                        "planned_days": planned_days,
                        "executed_days": executed_days,
                        "delay_days": delay_days,
                        "overall_progress": overall_progress,
                        "general_notes": general_notes,
                        "timeline_notes": "Cadastro realizado diretamente pelo painel.",
                    },
                )
                load_data.clear()
                st.success("Cliente e obra cadastrados com sucesso.")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### Lista geral de clientes")
        st.dataframe(
            clients[
                [
                    "cliente",
                    "obra",
                    "endereco",
                    "responsavel_tecnico",
                    "inicio",
                    "termino_previsto",
                    "status",
                    "percentual_executado",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### Resumo das obras")
    project_view = projects[
        [
            "cliente",
            "obra",
            "status",
            "planned_budget",
            "actual_budget",
            "planned_days",
            "executed_days",
            "delay_days",
            "overall_progress",
            "general_notes",
        ]
    ].copy()
    project_view.columns = [
        "Cliente",
        "Obra",
        "Status",
        "Custo previsto",
        "Custo real",
        "Dias previstos",
        "Dias executados",
        "Atraso (dias)",
        "% executado",
        "Observações",
    ]
    st.dataframe(project_view, width="stretch", hide_index=True)


def render_stages(data: dict[str, pd.DataFrame]) -> None:
    stages = data["stages"].copy()
    st.subheader("Etapas da obra")

    if stages.empty:
        st.info("Nenhuma etapa encontrada para os filtros selecionados.")
        return

    selected_project = st.selectbox("Selecione a obra", ["Todas"] + sorted(stages["obra"].unique().tolist()))
    view = stages if selected_project == "Todas" else stages[stages["obra"] == selected_project]

    for _, row in view.iterrows():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        header_col, stat_col = st.columns([2.6, 1])
        with header_col:
            st.markdown(f"### {row['obra']} • {row['etapa']}")
            st.write(row["descricao"])
            st.caption(f"Início: {row['inicio']} | Fim: {row['fim']} | Status: {row['status_etapa']}")
        with stat_col:
            st.metric("% concluído", f"{row['percentual_concluido']:.0f}%")
            st.metric("Dentro do orçamento", "Sim" if row["diferenca"] <= 0 else "Não", format_currency(row["diferenca"]))
        st.progress(min(max(row["percentual_concluido"] / 100, 0.0), 1.0))
        st.write(f"Observações: {row['observacoes']}")
        st.markdown("</div>", unsafe_allow_html=True)


def render_labor(data: dict[str, pd.DataFrame]) -> None:
    labor = data["labor"].copy()
    st.subheader("Mão de obra necessária")

    if labor.empty:
        st.info("Nenhum registro de mão de obra encontrado.")
        return

    summary = labor.groupby("funcao", as_index=False)[["quantidade_necessaria", "custo_total_mao_de_obra"]].sum()
    c1, c2 = st.columns([1.1, 1.4])
    with c1:
        chart = px.bar(
            summary.sort_values("custo_total_mao_de_obra", ascending=False),
            x="funcao",
            y="custo_total_mao_de_obra",
            text_auto=".2s",
            title="Custos por função",
            color="quantidade_necessaria",
            color_continuous_scale=["#d97706", "#0f766e"],
        )
        chart.update_layout(height=360, margin=dict(l=10, r=10, t=48, b=10))
        st.plotly_chart(chart, width="stretch")

    with c2:
        labor_view = labor.copy()
        labor_view.columns = [
            "ID",
            "Cliente",
            "Obra",
            "Etapa",
            "Nome",
            "Função",
            "Quantidade necessária",
            "Valor da diária",
            "Dias trabalhados",
            "Custo total",
            "Observações",
        ]
        st.dataframe(labor_view.drop(columns=["ID"]), width="stretch", hide_index=True)


def render_schedule(data: dict[str, pd.DataFrame]) -> None:
    projects = data["projects"].copy()
    stages = data["stages"].copy()
    schedules = data["schedules"].copy()
    st.subheader("Cronograma da obra")

    if projects.empty or schedules.empty:
        st.info("Nenhuma obra encontrada para exibir cronograma.")
        return

    schedule_view = schedules.copy()
    schedule_view.columns = [
        "ID",
        "Cliente",
        "Obra",
        "Etapa",
        "Prazo de início",
        "Prazo de fim",
        "Dias previstos",
        "Dias executados",
        "Atraso/adiantamento",
        "Andamento por etapa",
        "Observações",
    ]
    st.dataframe(schedule_view.drop(columns=["ID"]), width="stretch", hide_index=True)

    stage_timeline = stages[["obra", "etapa", "inicio", "fim", "status_etapa"]].copy()
    stage_timeline["inicio"] = pd.to_datetime(stage_timeline["inicio"])
    stage_timeline["fim"] = pd.to_datetime(stage_timeline["fim"])
    chart = px.timeline(
        stage_timeline,
        x_start="inicio",
        x_end="fim",
        y="obra",
        color="etapa",
        text="etapa",
        title="Andamento por etapa",
        color_discrete_sequence=["#0f766e", "#15803d", "#0284c7", "#d97706"],
    )
    chart.update_yaxes(autorange="reversed")
    chart.update_layout(height=480, margin=dict(l=10, r=10, t=48, b=10))
    st.plotly_chart(chart, width="stretch")

    st.markdown("#### Barra de progresso por obra")
    for _, row in projects.iterrows():
        st.write(f"**{row['obra']}**")
        st.progress(min(max(row["overall_progress"] / 100, 0.0), 1.0), text=f"{row['overall_progress']:.0f}% executado")


def render_costs_reports(data: dict[str, pd.DataFrame]) -> None:
    projects = data["projects"].copy()
    costs = data["costs"].copy()
    stages = data["stages"].copy()

    st.subheader("Controle de custos e relatórios")

    if projects.empty:
        st.info("Nenhum dado de custo encontrado.")
        return

    top_left, top_right = st.columns([1.1, 1.4])
    with top_left:
        category_summary = costs.groupby("categoria", as_index=False)[["custo_previsto", "custo_real"]].sum()
        chart = go.Figure()
        chart.add_scatterpolar(r=category_summary["custo_previsto"], theta=category_summary["categoria"], fill="toself", name="Previsto", line_color="#0f766e")
        chart.add_scatterpolar(r=category_summary["custo_real"], theta=category_summary["categoria"], fill="toself", name="Real", line_color="#d97706")
        chart.update_layout(height=420, title="Categorias de custo", margin=dict(l=10, r=10, t=48, b=10))
        st.plotly_chart(chart, width="stretch")

    with top_right:
        report = projects[
            ["cliente", "obra", "planned_budget", "actual_budget", "budget_delta", "budget_delta_pct", "overall_progress", "status"]
        ].copy()
        report.columns = [
            "Cliente",
            "Obra",
            "Custo previsto",
            "Custo real",
            "Diferença",
            "% estouro/economia",
            "% executado",
            "Status",
        ]
        st.dataframe(report, width="stretch", hide_index=True)

    st.markdown("#### Relatórios detalhados")
    tabs = st.tabs(["Por cliente", "Por etapa", "Resumo geral"])
    with tabs[0]:
        client_report = costs.groupby(["cliente", "obra"], as_index=False)[["custo_previsto", "custo_real"]].sum()
        client_report["diferença"] = client_report["custo_real"] - client_report["custo_previsto"]
        st.dataframe(client_report, width="stretch", hide_index=True)
    with tabs[1]:
        stage_report = stages.groupby(["cliente", "obra", "etapa"], as_index=False)[["custo_previsto", "custo_real", "percentual_concluido"]].sum()
        stage_report["orçamento"] = stage_report.apply(
            lambda row: "Dentro do orçamento" if row["custo_real"] <= row["custo_previsto"] else "Fora do orçamento",
            axis=1,
        )
        st.dataframe(stage_report, width="stretch", hide_index=True)
    with tabs[2]:
        total_prev = projects["planned_budget"].sum()
        total_real = projects["actual_budget"].sum()
        summary_cols = st.columns(4)
        summary_cols[0].metric("Custo total previsto", format_currency(float(total_prev)))
        summary_cols[1].metric("Custo total real", format_currency(float(total_real)))
        summary_cols[2].metric("Diferença acumulada", format_currency(float(total_real - total_prev)))
        summary_cols[3].metric("Execução média", f"{projects['overall_progress'].mean():.1f}%")
        st.dataframe(costs, width="stretch", hide_index=True)


def main() -> None:
    init_db()
    inject_styles()
    page = render_sidebar()
    raw_data = load_data()
    filtered_data, selected_filters = apply_filters(raw_data)
    render_header(selected_filters)

    if page == "Dashboard":
        render_dashboard(filtered_data)
    elif page == "Clientes e Obras":
        render_clients_projects(filtered_data)
    elif page == "Etapas":
        render_stages(filtered_data)
    elif page == "Mão de Obra":
        render_labor(filtered_data)
    elif page == "Cronograma":
        render_schedule(filtered_data)
    elif page == "Custos e Relatórios":
        render_costs_reports(filtered_data)


if __name__ == "__main__":
    main()
