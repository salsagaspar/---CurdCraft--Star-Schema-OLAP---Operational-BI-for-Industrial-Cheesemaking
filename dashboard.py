"""
Plotly Dash Interactive Dashboard
Project: Cheese & Milk Factory Advanced Analytics Dashboard
Date: 2026-06-02

This script runs a premium, production-grade interactive dashboard using Plotly Dash.
It connects to the SQLite Star Schema database, providing real-time data filters, 
dynamic charts, OEE metrics, and maintenance scheduling visual alerts.
"""

import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, dash_table

# Initialize Dash App
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    title="Cheese & Milk Factory Analytics Dashboard"
)

workspace_path = r"c:\Users\hpvic\OneDrive\Documents\Cheese & Milk Factory"
db_path = os.path.join(workspace_path, "factory_operations.db")

# Standard dark theme chart template
chart_layout_theme = dict(
    paper_bgcolor='rgba(17, 24, 39, 0.7)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#F3F4F6', family='Inter, sans-serif'),
    xaxis=dict(gridcolor='#1F2937', zerolinecolor='#1F2937'),
    yaxis=dict(gridcolor='#1F2937', zerolinecolor='#1F2937')
)

# Fetch static dropdown values
conn = sqlite3.connect(db_path)
cheese_types = pd.read_sql("SELECT DISTINCT cheese_type FROM dim_recipes ORDER BY cheese_type", conn)['cheese_type'].tolist()
equipment_statuses = pd.read_sql("SELECT DISTINCT status FROM dim_equipment ORDER BY status", conn)['status'].tolist()
conn.close()

# Premium CSS Styles for inline injection (Space Dark Theme)
STYLES = {
    'body': {
        'backgroundColor': '#0B0F19',
        'color': '#F3F4F6',
        'fontFamily': 'Inter, system-ui, -apple-system, sans-serif',
        'margin': '0',
        'padding': '20px',
        'minHeight': '100vh'
    },
    'container': {
        'maxWidth': '1400px',
        'margin': '0 auto'
    },
    'header_card': {
        'background': 'linear-gradient(135deg, rgba(17, 24, 39, 0.8), rgba(31, 41, 55, 0.8))',
        'border': '1px solid rgba(75, 85, 99, 0.4)',
        'borderRadius': '16px',
        'padding': '24px',
        'marginBottom': '24px',
        'boxShadow': '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
        'display': 'flex',
        'justifyContent': 'space-between',
        'alignItems': 'center'
    },
    'title': {
        'margin': '0',
        'fontSize': '28px',
        'fontWeight': '800',
        'letterSpacing': '-0.025em',
        'background': 'linear-gradient(to right, #60A5FA, #34D399)',
        'WebkitBackgroundClip': 'text',
        'WebkitTextFillColor': 'transparent'
    },
    'subtitle': {
        'margin': '4px 0 0 0',
        'color': '#9CA3AF',
        'fontSize': '14px'
    },
    'kpi_row': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fit, minmax(240px, 1fr))',
        'gap': '20px',
        'marginBottom': '24px'
    },
    'kpi_card': {
        'backgroundColor': 'rgba(17, 24, 39, 0.8)',
        'border': '1px solid #1F2937',
        'borderRadius': '12px',
        'padding': '20px',
        'boxShadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        'position': 'relative',
        'overflow': 'hidden'
    },
    'kpi_value': {
        'fontSize': '32px',
        'fontWeight': '800',
        'margin': '8px 0 0 0'
    },
    'kpi_label': {
        'color': '#9CA3AF',
        'fontSize': '12px',
        'textTransform': 'uppercase',
        'letterSpacing': '0.05em',
        'fontWeight': '600'
    },
    'filter_row': {
        'backgroundColor': 'rgba(17, 24, 39, 0.8)',
        'border': '1px solid #1F2937',
        'borderRadius': '12px',
        'padding': '16px 20px',
        'marginBottom': '24px',
        'display': 'flex',
        'flexWrap': 'wrap',
        'gap': '20px',
        'alignItems': 'center'
    },
    'filter_group': {
        'flex': '1',
        'minWidth': '200px'
    },
    'filter_label': {
        'display': 'block',
        'color': '#9CA3AF',
        'fontSize': '12px',
        'marginBottom': '8px',
        'fontWeight': '600'
    },
    'charts_grid': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fit, minmax(580px, 1fr))',
        'gap': '24px',
        'marginBottom': '24px'
    },
    'chart_card': {
        'backgroundColor': 'rgba(17, 24, 39, 0.8)',
        'border': '1px solid #1F2937',
        'borderRadius': '12px',
        'padding': '20px',
        'boxShadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
    },
    'chart_title': {
        'margin': '0 0 16px 0',
        'fontSize': '16px',
        'fontWeight': '700',
        'color': '#F3F4F6'
    },
    'alert_card': {
        'backgroundColor': 'rgba(17, 24, 39, 0.8)',
        'border': '1px solid #1F2937',
        'borderRadius': '12px',
        'padding': '20px',
        'boxShadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
    }
}

# Dash App Layout
app.layout = html.Div(style=STYLES['body'], children=[
    html.Div(style=STYLES['container'], children=[
        
        # HEADER CARD
        html.Div(style=STYLES['header_card'], children=[
            html.Div([
                html.H1("OPERATIONAL & OEE DASHBOARD", style=STYLES['title']),
                html.P("Cheese & Milk Factory Analytics Suite • Plotly Dash Edition", style=STYLES['subtitle'])
            ]),
            html.Div(children=[
                html.Span("● LIVE CONNECTED", style={
                    'color': '#34D399', 
                    'fontWeight': '700', 
                    'fontSize': '12px',
                    'letterSpacing': '0.05em',
                    'border': '1px solid rgba(52, 211, 153, 0.3)',
                    'padding': '6px 12px',
                    'borderRadius': '20px',
                    'backgroundColor': 'rgba(52, 211, 153, 0.1)'
                })
            ])
        ]),

        # KPI CARDS ROW
        html.Div(id="kpi-cards-row", style=STYLES['kpi_row']),

        # FILTERS CARD
        html.Div(style=STYLES['filter_row'], children=[
            # Filter 1: Cheese Type Selection
            html.Div(style=STYLES['filter_group'], children=[
                html.Label("FILTER TIPE KEJU", style=STYLES['filter_label']),
                dcc.Dropdown(
                    id='cheese-type-dropdown',
                    options=[{'label': 'Semua Tipe Keju', 'value': 'ALL'}] + [{'label': t, 'value': t} for t in cheese_types],
                    value='ALL',
                    clearable=False,
                    style={'backgroundColor': '#1F2937', 'color': '#000'}
                )
            ]),
            
            # Filter 2: Equipment Status
            html.Div(style=STYLES['filter_group'], children=[
                html.Label("STATUS MESIN PENGOLAHAN", style=STYLES['filter_label']),
                dcc.Dropdown(
                    id='equipment-status-dropdown',
                    options=[{'label': 'Semua Status Mesin', 'value': 'ALL'}] + [{'label': s, 'value': s} for s in equipment_statuses],
                    value='ALL',
                    clearable=False,
                    style={'backgroundColor': '#1F2937', 'color': '#000'}
                )
            ])
        ]),

        # CHARTS GRID
        html.Div(style=STYLES['charts_grid'], children=[
            # Chart 1: Actual vs Target Yield Boxplot
            html.Div(style=STYLES['chart_card'], children=[
                html.H3("Analisis Distribusi Yield Keju Aktual vs Target Resep", style=STYLES['chart_title']),
                dcc.Graph(id='yield-distribution-chart', config={'displayModeBar': False})
            ]),
            
            # Chart 2: QC Quality Tests Pie Chart
            html.Div(style=STYLES['chart_card'], children=[
                html.H3("Persentase Kelulusan Hasil Kontrol Kualitas (QC Test)", style=STYLES['chart_title']),
                dcc.Graph(id='qc-outcomes-chart', config={'displayModeBar': False})
            ]),
            
            # Chart 3: Productive Volume Trends
            html.Div(style=STYLES['chart_card'], children=[
                html.H3("Tren Volume Susu Terolah & Yield Keju (Bulanan)", style=STYLES['chart_title']),
                dcc.Graph(id='production-volume-chart', config={'displayModeBar': False})
            ]),
            
            # Chart 4: Power Load vs Capacity
            html.Div(style=STYLES['chart_card'], children=[
                html.H3("Efisiensi Energi: Beban Daya vs Kapasitas Operasional", style=STYLES['chart_title']),
                dcc.Graph(id='energy-efficiency-chart', config={'displayModeBar': False})
            ])
        ]),

        # MAINTENANCE ALERT TABLE
        html.Div(style=STYLES['alert_card'], children=[
            html.H3("⚠️ DAFTAR TUNGGU PEMELIHARAAN KRITIS MESIN OPERASIONAL (MAINTENANCE BACKLOG)", style={
                'margin': '0 0 16px 0', 'fontSize': '16px', 'fontWeight': '700', 'color': '#F87171'
            }),
            html.Div(id="backlog-table-container")
        ])
    ])
])


# --- DYNAMIC INTERACTIVE CALLBACKS ---

@app.callback(
    [
        Output('kpi-cards-row', 'children'),
        Output('yield-distribution-chart', 'figure'),
        Output('qc-outcomes-chart', 'figure'),
        Output('production-volume-chart', 'figure'),
        Output('energy-efficiency-chart', 'figure'),
        Output('backlog-table-container', 'children')
    ],
    [
        Input('cheese-type-dropdown', 'value'),
        Input('equipment-status-dropdown', 'value')
    ]
)
def update_dashboard(selected_cheese, selected_status):
    # Establish SQLite connection
    conn = sqlite3.connect(db_path)
    
    # 1. KPI CARDS CALCULATION
    q_kpis = """
    SELECT 
        COUNT(p.batch_id) as total_batches,
        ROUND(AVG(p.cheese_yield_kg / p.milk_volume_liters * 100), 2) as avg_yield_pct,
        ROUND(AVG(p.milk_volume_liters), 1) as avg_milk_vol
    FROM fact_cheese_production p
    JOIN dim_recipes r ON p.recipe_id = r.recipe_id
    JOIN dim_equipment e ON p.equipment_id = e.equipment_id
    WHERE 1=1
    """
    params_kpis = []
    if selected_cheese != 'ALL':
        q_kpis += " AND r.cheese_type = ?"
        params_kpis.append(selected_cheese)
    if selected_status != 'ALL':
        q_kpis += " AND e.status = ?"
        params_kpis.append(selected_status)
        
    df_kpis = pd.read_sql(q_kpis, conn, params=params_kpis)
    total_batches = df_kpis.iloc[0]['total_batches'] or 0
    avg_yield = df_kpis.iloc[0]['avg_yield_pct'] or 0.0
    avg_milk = df_kpis.iloc[0]['avg_milk_vol'] or 0.0

    # Get Pass rate
    q_qc = """
    SELECT 
        outcome,
        COUNT(*) as count
    FROM fact_quality_tests q
    JOIN fact_cheese_production p ON q.batch_id = p.batch_id
    JOIN dim_recipes r ON p.recipe_id = r.recipe_id
    JOIN dim_equipment e ON q.equipment_id = e.equipment_id
    WHERE 1=1
    """
    params_qc = []
    if selected_cheese != 'ALL':
        q_qc += " AND r.cheese_type = ?"
        params_qc.append(selected_cheese)
    if selected_status != 'ALL':
        q_qc += " AND e.status = ?"
        params_qc.append(selected_status)
    q_qc += " GROUP BY outcome"
        
    df_qc = pd.read_sql(q_qc, conn, params=params_qc)
    total_tests = df_qc['count'].sum()
    passed_tests = df_qc[df_qc['outcome'] == 'Pass']['count'].sum()
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0

    kpi_cards = [
        html.Div(style=STYLES['kpi_card'], children=[
            html.Div("TOTAL BATCH TEROLAH", style=STYLES['kpi_label']),
            html.Div(f"{total_batches:,}", style={**STYLES['kpi_value'], 'color': '#60A5FA'})
        ]),
        html.Div(style=STYLES['kpi_card'], children=[
            html.Div("RATA-RATA YIELD RASIO", style=STYLES['kpi_label']),
            html.Div(f"{avg_yield:.2f}%", style={**STYLES['kpi_value'], 'color': '#34D399'})
        ]),
        html.Div(style=STYLES['kpi_card'], children=[
            html.Div("RATA-RATA INPUT SUSU", style=STYLES['kpi_label']),
            html.Div(f"{avg_milk:,.1f} L", style={**STYLES['kpi_value'], 'color': '#FBBF24'})
        ]),
        html.Div(style=STYLES['kpi_card'], children=[
            html.Div("TINGKAT KELULUSAN (PASS RATE)", style=STYLES['kpi_label']),
            html.Div(f"{pass_rate:.1f}%", style={**STYLES['kpi_value'], 'color': '#A78BFA'})
        ])
    ]

    # 2. CHART 1: CHEESE YIELD DISTRIBUTION BOXPLOT
    q_y_chart = """
    SELECT 
        r.cheese_type,
        (p.cheese_yield_kg / p.milk_volume_liters * 100) as yield_pct,
        r.yield_ratio_pct as target_yield_pct
    FROM fact_cheese_production p
    JOIN dim_recipes r ON p.recipe_id = r.recipe_id
    JOIN dim_equipment e ON p.equipment_id = e.equipment_id
    WHERE 1=1
    """
    params_yc = []
    if selected_cheese != 'ALL':
        q_y_chart += " AND r.cheese_type = ?"
        params_yc.append(selected_cheese)
    if selected_status != 'ALL':
        q_y_chart += " AND e.status = ?"
        params_yc.append(selected_status)
        
    df_y_chart = pd.read_sql(q_y_chart, conn, params=params_yc)
    fig_yield = px.box(
        df_y_chart, 
        x='cheese_type', 
        y='yield_pct', 
        points="outliers",
        color_discrete_sequence=['#3B82F6']
    )
    fig_yield.add_hline(y=df_y_chart['target_yield_pct'].mean(), line_dash="dash", line_color="#EF4444", annotation_text="Baseline Target")
    fig_yield.update_layout(
        margin=dict(l=40, r=20, t=10, b=40),
        xaxis_title="Tipe Keju",
        yaxis_title="Yield Ratio (%)",
        **chart_layout_theme
    )

    # 3. CHART 2: QC OUTCOMES PIE / DONUT
    q_qc_chart = """
    SELECT 
        q.outcome,
        COUNT(*) as count
    FROM fact_quality_tests q
    JOIN fact_cheese_production p ON q.batch_id = p.batch_id
    JOIN dim_recipes r ON p.recipe_id = r.recipe_id
    JOIN dim_equipment e ON q.equipment_id = e.equipment_id
    WHERE 1=1
    """
    params_qcc = []
    if selected_cheese != 'ALL':
        q_qc_chart += " AND r.cheese_type = ?"
        params_qcc.append(selected_cheese)
    if selected_status != 'ALL':
        q_qc_chart += " AND e.status = ?"
        params_qcc.append(selected_status)
    q_qc_chart += " GROUP BY q.outcome"
    
    df_qcc = pd.read_sql(q_qc_chart, conn, params=params_qcc)
    
    color_map = {
        'Pass': '#10B981',
        'Borderline': '#F59E0B',
        'Fail': '#EF4444',
        'Repeat Required': '#6366F1',
        'Inconclusive': '#6B7280'
    }
    
    fig_qc = px.pie(
        df_qcc, 
        names='outcome', 
        values='count', 
        hole=0.4, 
        color='outcome',
        color_discrete_map=color_map
    )
    fig_qc.update_layout(
        margin=dict(l=20, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        **chart_layout_theme
    )

    # 4. CHART 3: PRODUCTION TRENDS LINE CHART (RESOLVED DUP KEYWORD ARGS)
    q_trend = """
    SELECT 
        d.year || '-' || printf('%02d', d.month) as year_month,
        SUM(p.milk_volume_liters) as total_milk,
        SUM(p.cheese_yield_kg) as total_cheese
    FROM fact_cheese_production p
    JOIN dim_recipes r ON p.recipe_id = r.recipe_id
    JOIN dim_equipment e ON p.equipment_id = e.equipment_id
    JOIN dim_date d ON p.production_date = d.date_str
    WHERE 1=1
    """
    params_trend = []
    if selected_cheese != 'ALL':
        q_trend += " AND r.cheese_type = ?"
        params_trend.append(selected_cheese)
    if selected_status != 'ALL':
        q_trend += " AND e.status = ?"
        params_trend.append(selected_status)
    q_trend += " GROUP BY d.year, d.month ORDER BY d.year, d.month"
    
    df_trend = pd.read_sql(q_trend, conn, params=params_trend)
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=df_trend['year_month'], y=df_trend['total_milk'],
        name='Susu Terolah (L)', mode='lines+markers', line=dict(color='#3B82F6', width=3)
    ))
    fig_trend.add_trace(go.Bar(
        x=df_trend['year_month'], y=df_trend['total_cheese'],
        name='Keju Dihasilkan (Kg)', yaxis='y2', opacity=0.6, marker_color='#10B981'
    ))
    
    # First apply standard theme
    fig_trend.update_layout(
        **chart_layout_theme
    )
    # Then apply custom layout specifications to avoid Python dict unpacking duplicate keyword error
    fig_trend.update_layout(
        margin=dict(l=40, r=40, t=10, b=40),
        yaxis=dict(title='Volume Susu (L)', gridcolor='#1F2937', zerolinecolor='#1F2937'),
        yaxis2=dict(title='Massa Keju (Kg)', overlaying='y', side='right'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # 5. CHART 4: ENERGY EFFICIENCY SCATTER
    q_energy = """
    SELECT 
        equipment_type,
        capacity_liters_hr,
        power_consumption_kw,
        plant_area
    FROM dim_equipment
    WHERE capacity_liters_hr > 0
    """
    params_energy = []
    if selected_status != 'ALL':
        q_energy += " AND status = ?"
        params_energy.append(selected_status)
        
    df_energy = pd.read_sql(q_energy, conn, params=params_energy)
    fig_energy = px.scatter(
        df_energy, 
        x='capacity_liters_hr', 
        y='power_consumption_kw',
        color='plant_area',
        size='power_consumption_kw',
        hover_data=['equipment_type'],
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig_energy.update_layout(
        margin=dict(l=40, r=20, t=10, b=40),
        xaxis_title="Kapasitas (L/Jam)",
        yaxis_title="Daya Listrik (kW)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        **chart_layout_theme
    )

    # 6. TABLE: BACKLOG MAINTENANCE ALERT
    q_table = """
    SELECT 
        equipment_name as "Nama Mesin",
        equipment_type as "Tipe Mesin",
        plant_area as "Lini Area",
        next_maintenance_due as "Tenggat Jadwal",
        status as "Status Operasional",
        responsible_team as "Tim Penanggung Jawab"
    FROM dim_equipment
    WHERE date(next_maintenance_due) < date('2026-06-02')
    """
    params_table = []
    if selected_status != 'ALL':
        q_table += " AND status = ?"
        params_table.append(selected_status)
    q_table += " ORDER BY next_maintenance_due ASC LIMIT 6"
    
    df_table = pd.read_sql(q_table, conn, params=params_table)
    
    table_element = dash_table.DataTable(
        data=df_table.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_table.columns],
        style_header={
            'backgroundColor': '#1F2937',
            'color': '#F3F4F6',
            'fontWeight': '700',
            'border': '1px solid #374151'
        },
        style_cell={
            'backgroundColor': 'rgba(17, 24, 39, 0.4)',
            'color': '#D1D5DB',
            'padding': '12px',
            'fontFamily': 'Inter, sans-serif',
            'fontSize': '12px',
            'textAlign': 'left',
            'border': '1px solid #1F2937'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Tenggat Jadwal'},
                'color': '#F87171',
                'fontWeight': '600'
            },
            {
                'if': {'column_id': 'Status Operasional'},
                'color': '#34D399',
                'fontWeight': '600'
            }
        ]
    )

    conn.close()
    
    return kpi_cards, fig_yield, fig_qc, fig_trend, fig_energy, table_element


# Run Dash App
if __name__ == '__main__':
    print("Initializing Dash Board local server on http://127.0.0.1:8050 ...")
    app.run(debug=True, port=8050)
