# chart_maker.py — Powerful Edition (Fixed)
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io


def make_chart(df, chart_type="auto", x_col=None, y_col=None, title=""):
    """Single chart बनाउने"""
    if df.empty:
        return None
    
    numeric_cols, text_cols = _detect_columns(df)
    
    if not numeric_cols:
        return None
    
    y_col = y_col or numeric_cols[0]
    x_col = x_col or (text_cols[0] if text_cols else df.columns[0])
    
    if chart_type == "auto":
        chart_type = _auto_chart_type(df, numeric_cols)
    
    try:
        fig = _create_chart(df, chart_type, x_col, y_col, title)
        if fig:
            fig.update_layout(
                height=450,
                margin=dict(l=20, r=20, t=50, b=20),
                template="plotly_white"
            )
        return fig
    except Exception as e:
        print(f"Chart error: {e}")
        return None


def make_all_charts(df, title=""):
    """एउटै table बाट सबै chart types बनाउने"""
    if df.empty:
        return {}
    
    numeric_cols, text_cols = _detect_columns(df)
    if not numeric_cols:
        return {}
    
    x_col = text_cols[0] if text_cols else df.columns[0]
    charts = {}
    
    for y_col in numeric_cols[:3]:  # पहिलो 3 numeric
        for chart_type in ["bar", "line", "pie"]:
            fig = _create_chart(
                df, chart_type, x_col, y_col,
                f"{y_col} — {chart_type.capitalize()}"
            )
            if fig:
                fig.update_layout(height=400, template="plotly_white")
                charts[f"{chart_type}_{y_col}"] = fig
    
    return charts


def make_summary_chart(df, title=""):
    """सबै numeric columns को summary chart"""
    numeric_cols, text_cols = _detect_columns(df)
    if not numeric_cols:
        return None
    
    x_col = text_cols[0] if text_cols else df.columns[0]
    
    try:
        fig = px.bar(
            df, x=x_col, y=numeric_cols,
            title=title or "All Numeric Columns",
            barmode="group"
        )
        fig.update_layout(height=450, template="plotly_white")
        return fig
    except Exception:
        return None


def get_summary_stats(df):
    """Table को Statistics (Sum, Mean, Min, Max, Median) निकाल्ने"""
    if df.empty:
        return {}
    
    numeric_cols, _ = _detect_columns(df)
    stats = {}
    
    for col in numeric_cols:
        try:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(series) == 0:
                continue
            
            stats[col] = {
                "count": int(len(series)),
                "sum": float(series.sum()),
                "mean": float(series.mean()),
                "min": float(series.min()),
                "max": float(series.max()),
                "median": float(series.median())
            }
        except Exception:
            pass
    
    return stats


def df_to_csv_bytes(df):
    """DataFrame → CSV bytes (download को लागि)"""
    return df.to_csv(index=False).encode("utf-8")


def df_to_excel_bytes(df):
    """DataFrame → Excel bytes (download को लागि)"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Table Data")
    return buffer.getvalue()


# ============================================================
# Helper Functions
# ============================================================
def _detect_columns(df):
    """Numeric + Text columns detect"""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    text_cols = df.select_dtypes(include=["object"]).columns.tolist()
    
    # यदि numeric फेला परेन भने $ र , हटाएर try गर्ने
    if not numeric_cols:
        for col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r'[$,]', '', regex=True),
                errors="coerce"
            )
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        text_cols = [c for c in df.columns if c not in numeric_cols]
    
    return numeric_cols, text_cols


def _auto_chart_type(df, numeric_cols):
    """Auto chart type"""
    if len(df) <= 6 and len(numeric_cols) == 1:
        return "pie"
    elif len(df) > 20:
        return "line"
    return "bar"


def _create_chart(df, chart_type, x_col, y_col, title):
    """Chart create गर्ने"""
    try:
        if chart_type == "bar":
            return px.bar(df, x=x_col, y=y_col, title=title or f"{y_col} by {x_col}")
        elif chart_type == "line":
            return px.line(df, x=x_col, y=y_col, title=title or f"{y_col} trend")
        elif chart_type == "pie":
            return px.pie(df, names=x_col, values=y_col, title=title or f"{y_col} distribution")
        elif chart_type == "scatter":
            return px.scatter(df, x=x_col, y=y_col, title=title or f"{x_col} vs {y_col}")
        elif chart_type == "area":
            return px.area(df, x=x_col, y=y_col, title=title or f"{y_col} area")
        elif chart_type == "histogram":
            return px.histogram(df, x=x_col, title=title or f"{x_col} distribution")
        else:
            return px.bar(df, x=x_col, y=y_col, title=title)
    except Exception:
        return None