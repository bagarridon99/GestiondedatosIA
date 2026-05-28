import sqlite3
from html import escape

import pandas as pd

from config import DASHBOARD_FILE, DATABASE_FILE, ERROR_REPORT_FILE, TABLE_NAME


def generate_charts(total_processed, logger):
    logger.info("Etapa 5: generación de dashboard HTML de KPIs")

    DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    error_report = pd.read_csv(ERROR_REPORT_FILE)
    row_errors = error_report[error_report["fila"] > 0]
    rows_with_errors = row_errors["fila"].nunique()
    total_errors = len(row_errors)

    with sqlite3.connect(DATABASE_FILE) as connection:
        table = TABLE_NAME
        valid_rows = read_single_value(
            connection,
            """
            SELECT COUNT(*) AS valor
            FROM {table}
            """.format(table=table),
        )

        warning_summary = pd.read_sql_query(
            """
            SELECT 'Score crediticio bajo' AS warning, COUNT(*) AS cantidad
            FROM {table}
            WHERE credit_score < 580
            UNION ALL
            SELECT 'Tasa de interes alta', COUNT(*)
            FROM {table}
            WHERE loan_int_rate > 20
            UNION ALL
            SELECT 'Prestamo mayor al 40% del ingreso', COUNT(*)
            FROM {table}
            WHERE loan_percent_income > 0.40
            UNION ALL
            SELECT 'Historial crediticio corto', COUNT(*)
            FROM {table}
            WHERE cb_person_cred_hist_length < 2
            """.format(table=table),
            connection,
        )

        rows_with_warnings = read_single_value(
            connection,
            """
            SELECT COUNT(*) AS valor
            FROM {table}
            WHERE credit_score < 580
               OR loan_int_rate > 20
               OR loan_percent_income > 0.40
               OR cb_person_cred_hist_length < 2
            """.format(table=table),
        )

        warning_examples = pd.read_sql_query(
            """
            SELECT
                rowid AS fila_sqlite,
                person_age,
                person_income,
                loan_amnt,
                loan_int_rate,
                loan_percent_income,
                cb_person_cred_hist_length,
                credit_score,
                TRIM(
                    CASE WHEN credit_score < 580 THEN 'Score crediticio bajo; ' ELSE '' END ||
                    CASE WHEN loan_int_rate > 20 THEN 'Tasa de interes alta; ' ELSE '' END ||
                    CASE WHEN loan_percent_income > 0.40 THEN 'Prestamo mayor al 40% del ingreso; ' ELSE '' END ||
                    CASE WHEN cb_person_cred_hist_length < 2 THEN 'Historial crediticio corto; ' ELSE '' END
                ) AS motivo_warning
            FROM loan_data
            WHERE credit_score < 580
               OR loan_int_rate > 20
               OR loan_percent_income > 0.40
               OR cb_person_cred_hist_length < 2
            LIMIT 3
            """.replace("FROM loan_data", f"FROM {table}"),
            connection,
        )

        valid_examples = pd.read_sql_query(
            """
            SELECT
                rowid AS fila_sqlite,
                person_age,
                person_emp_exp,
                person_income,
                loan_amnt,
                loan_percent_income,
                credit_score,
                previous_loan_defaults_on_file,
                loan_status,
                'Cumple rangos obligatorios, valores positivos y categorias permitidas' AS motivo_valido
            FROM {table}
            WHERE person_age BETWEEN 18 AND 100
              AND person_emp_exp BETWEEN 0 AND 80
              AND person_income > 0
              AND loan_amnt > 0
              AND loan_int_rate > 0
              AND loan_percent_income BETWEEN 0 AND 1
              AND cb_person_cred_hist_length >= 0
              AND credit_score BETWEEN 300 AND 850
              AND previous_loan_defaults_on_file IN ('Yes', 'No')
              AND loan_status IN (0, 1)
            LIMIT 3
            """.format(table=table),
            connection,
        )

    error_by_field = (
        row_errors.groupby("campo")
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
    )

    html = build_dashboard_html(
        total_processed,
        valid_rows,
        rows_with_errors,
        total_errors,
        rows_with_warnings,
        warning_summary,
        error_by_field,
        warning_examples,
        row_errors.head(3),
        valid_examples,
    )
    DASHBOARD_FILE.write_text(html, encoding="utf-8")

    logger.info("Dashboard HTML guardado en: %s", DASHBOARD_FILE)
    print(f"Dashboard HTML de KPIs guardado en: {DASHBOARD_FILE}")

    return DASHBOARD_FILE


def read_single_value(connection, query):
    result = pd.read_sql_query(query, connection)
    return int(result.loc[0, "valor"])


def build_dashboard_html(
    total_processed,
    valid_rows,
    rows_with_errors,
    total_errors,
    rows_with_warnings,
    warning_summary,
    error_by_field,
    warning_examples,
    error_examples,
    valid_examples,
):
    valid_percent = calculate_percent(valid_rows, total_processed)
    error_percent = calculate_percent(rows_with_errors, total_processed)
    warning_percent = calculate_percent(rows_with_warnings, valid_rows)
    warning_total = int(warning_summary["cantidad"].sum())

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Calidad del Pipeline</title>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            color: #1f2933;
        }}
        header {{
            background: #263238;
            color: white;
            padding: 24px 40px;
        }}
        main {{
            padding: 28px 40px;
            max-width: 1380px;
            margin: 0 auto;
        }}
        h1, h2, p {{
            margin-top: 0;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: white;
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 20px;
            overflow: hidden;
        }}
        .metric-card {{
            display: flex;
            flex-direction: column;
            min-height: 150px;
        }}
        .value {{
            font-size: 32px;
            font-weight: bold;
            margin-top: 8px;
        }}
        .metric-button {{
            margin-top: auto;
            border: 1px solid #b6c2cf;
            background: #ffffff;
            border-radius: 6px;
            padding: 9px 12px;
            cursor: pointer;
            font-weight: bold;
            color: #1f2933;
            text-align: center;
        }}
        .metric-button:hover {{
            background: #eef2f7;
        }}
        .ok {{ color: #207a4c; }}
        .warning {{ color: #a16207; }}
        .error {{ color: #b42318; }}
        .bar-row {{
            display: grid;
            grid-template-columns: 180px 1fr 80px;
            gap: 12px;
            align-items: center;
            margin: 14px 0;
        }}
        .bar-bg {{
            background: #e5e7eb;
            border-radius: 4px;
            height: 26px;
            overflow: hidden;
        }}
        .bar {{
            height: 100%;
            background: #2e86ab;
        }}
        .bar.warning {{
            background: #d97706;
        }}
        .bar.error {{
            background: #c73e1d;
        }}
        .note {{
            color: #52606d;
            font-size: 14px;
        }}
        .examples {{
            align-items: start;
            margin-top: 20px;
        }}
        .example-list {{
            display: grid;
            gap: 10px;
        }}
        .example-item {{
            border: 1px solid #d9e2ec;
            border-left: 5px solid #2e86ab;
            border-radius: 8px;
            padding: 12px 14px;
            background: #fbfcfd;
        }}
        .example-item.warning-border {{
            border-left-color: #d97706;
        }}
        .example-item.error-border {{
            border-left-color: #c73e1d;
        }}
        .example-title {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            font-weight: bold;
        }}
        .example-summary {{
            color: #52606d;
            font-size: 14px;
            margin: 8px 0 0;
        }}
        .modal-backdrop {{
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.55);
            z-index: 20;
            padding: 24px;
        }}
        .modal-backdrop.open {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .modal {{
            width: min(720px, 100%);
            max-height: 82vh;
            overflow: auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.25);
        }}
        .modal-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 18px 22px;
            border-bottom: 1px solid #d9e2ec;
        }}
        .modal-header h2 {{
            margin: 0;
            font-size: 22px;
        }}
        .modal-body {{
            padding: 20px 22px;
        }}
        .template-content {{
            display: none;
        }}
        .close-button {{
            border: 0;
            background: #eef2f7;
            border-radius: 6px;
            padding: 8px 12px;
            cursor: pointer;
            font-weight: bold;
        }}
        .detail-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            margin: 12px 0;
        }}
        .detail-field {{
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 10px;
            background: #fbfcfd;
        }}
        .detail-label {{
            color: #52606d;
            display: block;
            font-size: 12px;
            margin-bottom: 4px;
        }}
        .detail-reason {{
            border-top: 1px solid #e5e7eb;
            padding-top: 14px;
            line-height: 1.4;
        }}
        @media (max-width: 900px) {{
            main {{
                padding: 20px;
            }}
            .grid {{
                grid-template-columns: 1fr;
            }}
            .bar-row {{
                grid-template-columns: 140px 1fr 60px;
            }}
            .detail-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>Dashboard de Calidad del Pipeline</h1>
        <p>KPIs de errores y warnings generados al ejecutar main.py.</p>
    </header>
    <main>
        <section class="summary">
            <div class="card metric-card">
                <p>Registros procesados</p>
                <div class="value">{total_processed:,}</div>
                <p class="note">Total leido desde el archivo limpio</p>
            </div>
            <div class="card metric-card">
                <p>Registros validos</p>
                <div class="value ok">{valid_percent}%</div>
                <p class="note">{valid_rows:,} registros cargados a SQLite</p>
                <button class="metric-button" onclick="openListModal('Ejemplos de registros validos', 'validExamples')">Ver ejemplos</button>
            </div>
            <div class="card metric-card">
                <p>Registros con errores</p>
                <div class="value error">{error_percent}%</div>
                <p class="note">{rows_with_errors:,} registros rechazados</p>
                <button class="metric-button" onclick="openListModal('Ejemplos de registros con errores', 'errorExamples')">Ver ejemplos</button>
            </div>
            <div class="card metric-card">
                <p>Registros con warnings</p>
                <div class="value warning">{warning_percent}%</div>
                <p class="note">{rows_with_warnings:,} registros validos con alertas</p>
                <button class="metric-button" onclick="openListModal('Ejemplos de registros con warnings', 'warningExamples')">Ver ejemplos</button>
            </div>
        </section>

        <section class="grid">
            <div class="card">
                <h2>Resumen de calidad</h2>
                {build_quality_bars(valid_percent, error_percent, warning_percent)}
            </div>

            <div class="card">
                <h2>Warnings detectados</h2>
                <p class="note">Total de eventos de warning: {warning_total:,}</p>
                {build_bar_chart(warning_summary, "warning", "cantidad", "warning")}
            </div>

            <div class="card">
                <h2>Errores por campo</h2>
                <p class="note">Total de errores semanticos: {total_errors:,}</p>
                {build_bar_chart(error_by_field, "campo", "cantidad", "error")}
            </div>
        </section>

        <div class="template-content" id="validExamples">
            <p class="note">Son registros que pasaron todas las reglas estructurales y semanticas.</p>
            {build_valid_examples_table(valid_examples)}
        </div>
        <div class="template-content" id="warningExamples">
            <p class="note">Son registros validos que se cargaron a SQLite, pero tienen condiciones que conviene monitorear.</p>
            {build_warning_examples_table(warning_examples)}
        </div>
        <div class="template-content" id="errorExamples">
            <p class="note">Son registros rechazados por incumplir reglas semanticas del pipeline.</p>
            {build_error_examples_table(error_examples)}
        </div>
    </main>
    <div class="modal-backdrop" id="detailModal" onclick="closeModalOnBackdrop(event)">
        <div class="modal">
            <div class="modal-header">
                <h2 id="modalTitle">Detalle</h2>
                <button class="close-button" onclick="closeModal()">Cerrar</button>
            </div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>
    <script>
        function openListModal(title, templateId) {{
            const template = document.getElementById(templateId);
            document.getElementById("modalTitle").textContent = title;
            document.getElementById("modalBody").innerHTML = template.innerHTML;
            document.getElementById("detailModal").classList.add("open");
        }}

        function closeModal() {{
            document.getElementById("detailModal").classList.remove("open");
        }}

        function closeModalOnBackdrop(event) {{
            if (event.target.id === "detailModal") {{
                closeModal();
            }}
        }}

        document.addEventListener("keydown", function(event) {{
            if (event.key === "Escape") {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>
"""


def calculate_percent(value, total):
    if total == 0:
        return 0
    return round(100 * value / total, 2)


def build_quality_bars(valid_percent, error_percent, warning_percent):
    rows = [
        ("Datos validos", valid_percent, "ok"),
        ("Errores", error_percent, "error"),
        ("Warnings", warning_percent, "warning"),
    ]
    return "\n".join(
        f"""
        <div class="bar-row">
            <strong>{label}</strong>
            <div class="bar-bg"><div class="bar {style}" style="width: {percent}%"></div></div>
            <span>{percent}%</span>
        </div>
        """
        for label, percent, style in rows
    )


def build_bar_chart(df, label_column, value_column, style):
    if df.empty:
        return "<p>No hay datos para mostrar.</p>"

    max_value = max(int(df[value_column].max()), 1)
    rows = []
    for _, row in df.iterrows():
        label = row[label_column]
        value = int(row[value_column])
        width = round(value / max_value * 100, 2)
        rows.append(
            f"""
            <div class="bar-row">
                <strong>{label}</strong>
                <div class="bar-bg"><div class="bar {style}" style="width: {width}%"></div></div>
                <span>{value:,}</span>
            </div>
            """
        )
    return "\n".join(rows)


def build_valid_examples_table(df):
    if df.empty:
        return "<p>No hay ejemplos de registros validos.</p>"

    rows = []
    for _, row in df.iterrows():
        title = f"Registro valido - Fila SQLite {int(row['fila_sqlite'])}"
        rows.append(
            f"""
            <div class="example-item">
                <div class="example-title">
                    <span>{escape(title)}</span>
                </div>
                <p class="example-summary">Edad {row["person_age"]}, score {row["credit_score"]}, monto {row["loan_amnt"]}</p>
                <div class="detail-grid">
                    {detail_field("Edad", row["person_age"])}
                    {detail_field("Experiencia laboral", row["person_emp_exp"])}
                    {detail_field("Ingreso", row["person_income"])}
                    {detail_field("Monto prestamo", row["loan_amnt"])}
                    {detail_field("% ingreso", row["loan_percent_income"])}
                    {detail_field("Credit score", row["credit_score"])}
                </div>
                <div class="detail-reason"><strong>Por que es valido:</strong> {escape(str(row["motivo_valido"]))}.</div>
            </div>
            """
        )

    return f"""<div class="example-list">{"".join(rows)}</div>"""


def build_warning_examples_table(df):
    if df.empty:
        return "<p>No hay ejemplos de warnings.</p>"

    rows = []
    for _, row in df.iterrows():
        title = f"Registro con warning - Fila SQLite {int(row['fila_sqlite'])}"
        rows.append(
            f"""
            <div class="example-item warning-border">
                <div class="example-title">
                    <span>{escape(title)}</span>
                </div>
                <p class="example-summary">Score {row["credit_score"]}, tasa {row["loan_int_rate"]}, % ingreso {row["loan_percent_income"]}</p>
                <div class="detail-grid">
                    {detail_field("Credit score", row["credit_score"])}
                    {detail_field("Tasa interes", row["loan_int_rate"])}
                    {detail_field("% ingreso", row["loan_percent_income"])}
                    {detail_field("Historial crediticio", row["cb_person_cred_hist_length"])}
                    {detail_field("Ingreso", row["person_income"])}
                    {detail_field("Monto prestamo", row["loan_amnt"])}
                </div>
                <div class="detail-reason"><strong>Por que tiene warning:</strong> {escape(str(row["motivo_warning"]))}</div>
            </div>
            """
        )

    return f"""<div class="example-list">{"".join(rows)}</div>"""


def build_error_examples_table(df):
    if df.empty:
        return "<p>No hay ejemplos de errores.</p>"

    rows = []
    for _, row in df.iterrows():
        title = f"Registro con error - Fila CSV {int(row['fila'])}"
        rows.append(
            f"""
            <div class="example-item error-border">
                <div class="example-title">
                    <span>{escape(title)}</span>
                </div>
                <p class="example-summary">Campo {escape(str(row["campo"]))}, valor detectado {escape(str(row["valor_detectado"]))}</p>
                <div class="detail-grid">
                    {detail_field("Campo", row["campo"])}
                    {detail_field("Valor detectado", row["valor_detectado"])}
                    {detail_field("Fila CSV", int(row["fila"]))}
                    {detail_field("Fecha validacion", row["fecha_validacion"])}
                </div>
                <div class="detail-reason"><strong>Por que tiene error:</strong> {escape(str(row["regla_incumplida"]))}.</div>
            </div>
            """
        )

    return f"""<div class="example-list">{"".join(rows)}</div>"""


def detail_field(label, value):
    return f"""
    <div class="detail-field">
        <span class="detail-label">{escape(str(label))}</span>
        <strong>{escape(str(value))}</strong>
    </div>
    """
