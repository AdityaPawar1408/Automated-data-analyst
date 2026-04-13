from __future__ import annotations

import io
import os
from typing import Any, Dict, List, Tuple

import pandas as pd

try:
    from crewai import Crew, Task
except Exception:  # pragma: no cover - dependency/runtime fallback
    Crew = None
    Task = None

from agents import ai_is_configured, build_agents


os.environ.setdefault("CREWAI_STORAGE_DIR", os.path.abspath(".crewai_storage"))
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.makedirs(os.environ["CREWAI_STORAGE_DIR"], exist_ok=True)


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    chosen_plural = plural or f"{singular}s"
    return singular if count == 1 else chosen_plural


def load_dataset(file) -> pd.DataFrame:
    file_bytes = file.read()
    file_name = file.name.lower()

    if file_name.endswith(".csv"):
        for options in (
            {"encoding": "utf-8"},
            {"encoding": "latin1"},
            {"encoding": "utf-8", "sep": ";"},
        ):
            try:
                return pd.read_csv(io.BytesIO(file_bytes), **options)
            except Exception:
                continue
        raise ValueError("The CSV file could not be parsed with the supported formats.")

    if file_name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_bytes))

    raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, List[str]]:
    cleaned = df.copy()
    notes: List[str] = []

    duplicate_count = int(cleaned.duplicated().sum())
    if duplicate_count:
        cleaned = cleaned.drop_duplicates()
        notes.append(
            f"Removed {duplicate_count} {pluralize(duplicate_count, 'duplicate row')}."
        )

    missing_cells = int(cleaned.isna().sum().sum())
    if missing_cells:
        object_columns = cleaned.select_dtypes(include="object").columns
        numeric_columns = cleaned.select_dtypes(include="number").columns

        if len(object_columns):
            cleaned[object_columns] = cleaned[object_columns].ffill().bfill()
        if len(numeric_columns):
            cleaned[numeric_columns] = cleaned[numeric_columns].apply(
                lambda column: column.fillna(column.median())
            )

        remaining_missing = int(cleaned.isna().sum().sum())
        notes.append(
            f"Handled missing values: {missing_cells - remaining_missing} cells filled, "
            f"{remaining_missing} still missing."
        )

    cleaned.columns = [str(column).strip() for column in cleaned.columns]
    notes.append(f"Dataset ready with {cleaned.shape[0]} rows and {cleaned.shape[1]} columns.")

    return cleaned, notes


def choose_visuals(df: pd.DataFrame) -> List[Dict[str, str]]:
    visuals: List[Dict[str, str]] = []
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    categorical_columns = df.select_dtypes(exclude="number").columns.tolist()

    if numeric_columns:
        visuals.append(
            {
                "kind": "histogram",
                "title": f"Distribution of {numeric_columns[0]}",
                "x": numeric_columns[0],
            }
        )

    if len(numeric_columns) >= 2:
        visuals.append(
            {
                "kind": "scatter",
                "title": f"{numeric_columns[0]} vs {numeric_columns[1]}",
                "x": numeric_columns[0],
                "y": numeric_columns[1],
            }
        )

    if categorical_columns and numeric_columns:
        visuals.append(
            {
                "kind": "bar",
                "title": f"Average {numeric_columns[0]} by {categorical_columns[0]}",
                "x": categorical_columns[0],
                "y": numeric_columns[0],
            }
        )

    return visuals[:3]


def summarize_dataset(df: pd.DataFrame, cleaning_notes: List[str]) -> Dict[str, Any]:
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    categorical_columns = df.select_dtypes(exclude="number").columns.tolist()

    overview = [
        f"Rows: {df.shape[0]}",
        f"Columns: {df.shape[1]}",
        f"Numeric columns: {len(numeric_columns)}",
        f"Categorical/date-like columns: {len(categorical_columns)}",
    ]

    insights: List[str] = []

    if numeric_columns:
        summary = df[numeric_columns].describe().T
        top_variability = summary["std"].dropna().sort_values(ascending=False)
        if not top_variability.empty:
            column = top_variability.index[0]
            insights.append(
                f"`{column}` shows the highest variability, so it is a good candidate for trend and anomaly checks."
            )

        for column in numeric_columns[:3]:
            series = df[column].dropna()
            if series.empty:
                continue
            insights.append(
                f"`{column}` ranges from {series.min():,.2f} to {series.max():,.2f}, with an average of {series.mean():,.2f}."
            )

    if categorical_columns:
        for column in categorical_columns[:2]:
            top_values = df[column].astype(str).value_counts().head(3)
            joined = ", ".join([f"{index} ({value})" for index, value in top_values.items()])
            insights.append(f"Most common values in `{column}`: {joined}.")

    correlations: List[str] = []
    if len(numeric_columns) >= 2:
        corr = df[numeric_columns].corr(numeric_only=True)
        pairs: List[Tuple[float, str, str]] = []
        for left_index, left in enumerate(numeric_columns):
            for right in numeric_columns[left_index + 1 :]:
                value = corr.loc[left, right]
                if pd.notna(value):
                    pairs.append((abs(float(value)), left, right))
        pairs.sort(reverse=True)
        for magnitude, left, right in pairs[:3]:
            value = float(corr.loc[left, right])
            direction = "positive" if value >= 0 else "negative"
            correlations.append(
                f"`{left}` and `{right}` have a {direction} correlation of {value:.2f}."
            )

    if not insights:
        insights.append("The dataset loaded successfully, but it does not contain enough numeric detail for deeper statistical commentary.")

    return {
        "overview": overview,
        "cleaning_notes": cleaning_notes,
        "insights": insights,
        "correlations": correlations or ["No strong numeric correlation analysis was available for this dataset."],
        "visuals": choose_visuals(df),
    }


def generate_ai_summary(df: pd.DataFrame, base_report: Dict[str, Any]) -> str | None:
    if Crew is None or Task is None or not ai_is_configured():
        return None

    agents = build_agents()
    if len(agents) != 3:
        return None

    data_sample = df.head(8).to_string()
    cleaning_agent, analysis_agent, visualization_agent = agents

    tasks = [
        Task(
            description=(
                "Review this dataset sample and explain the main cleaning steps already applied.\n\n"
                f"{data_sample}\n\n"
                f"Existing cleaning notes: {base_report['cleaning_notes']}"
            ),
            agent=cleaning_agent,
            expected_output="A concise cleaning summary.",
        ),
        Task(
            description=(
                "Analyze this dataset sample and provide concise, practical business insights.\n\n"
                f"{data_sample}\n\n"
                f"Current local insights: {base_report['insights']}\n"
                f"Current correlation notes: {base_report['correlations']}"
            ),
            agent=analysis_agent,
            expected_output="A concise list of insights.",
        ),
        Task(
            description=(
                "Recommend up to three charts for this dataset and explain why each helps.\n\n"
                f"{data_sample}\n\n"
                f"Current chart plan: {base_report['visuals']}"
            ),
            agent=visualization_agent,
            expected_output="A concise visualization recommendation.",
        ),
    ]

    crew = Crew(agents=agents, tasks=tasks, verbose=False)
    return str(crew.kickoff())


def run_pipeline(file) -> tuple[pd.DataFrame, Dict[str, Any]]:
    df = load_dataset(file)
    cleaned_df, cleaning_notes = clean_dataset(df)
    report = summarize_dataset(cleaned_df, cleaning_notes)

    try:
        ai_summary = generate_ai_summary(cleaned_df, report)
    except Exception as exc:
        ai_summary = None
        report["ai_status"] = f"AI enhancement unavailable: {exc}"
    else:
        report["ai_status"] = (
            "AI enhancement generated successfully."
            if ai_summary
            else "AI enhancement skipped because the model runtime is not configured."
        )

    report["ai_summary"] = ai_summary
    return cleaned_df, report
