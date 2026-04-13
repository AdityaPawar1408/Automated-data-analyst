from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from pipeline import run_pipeline
from report import generate_pdf


st.set_page_config(page_title="AI Data Analyst", layout="wide")
sns.set_theme(style="whitegrid")


def render_visual(df, visual):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    kind = visual.get("kind")
    title = visual.get("title", "Chart")

    if kind == "histogram":
        sns.histplot(df[visual["x"]].dropna(), kde=True, ax=ax, color="#1f77b4")
        ax.set_xlabel(visual["x"])
    elif kind == "scatter":
        sns.scatterplot(data=df, x=visual["x"], y=visual["y"], ax=ax, color="#ff7f0e")
    elif kind == "bar":
        grouped = (
            df.groupby(visual["x"], dropna=False)[visual["y"]]
            .mean()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        sns.barplot(data=grouped, x=visual["x"], y=visual["y"], ax=ax, color="#2ca02c")
        ax.tick_params(axis="x", rotation=30)
    else:
        plt.close(fig)
        return

    ax.set_title(title)
    ax.grid(alpha=0.2)
    st.pyplot(fig)
    plt.close(fig)


st.title("Automated Data Analyst")
st.caption("Upload a CSV or Excel file to get a cleaned dataset, clear insights, charts, and a PDF report.")

uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])

if uploaded_file:
    with st.spinner("Analyzing your dataset..."):
        try:
            df, report_data = run_pipeline(uploaded_file)
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
        else:
            st.success("Analysis completed successfully.")
            st.write(f"File name: `{uploaded_file.name}`")

            metric_columns = st.columns(4)
            metric_columns[0].metric("Rows", f"{df.shape[0]:,}")
            metric_columns[1].metric("Columns", f"{df.shape[1]:,}")
            metric_columns[2].metric("Missing Cells", f"{int(df.isna().sum().sum()):,}")
            metric_columns[3].metric("Duplicates", f"{int(df.duplicated().sum()):,}")

            st.subheader("Data Preview")
            st.dataframe(df.head(20), use_container_width=True)

            st.subheader("Overview")
            for item in report_data["overview"]:
                st.write(f"- {item}")

            st.subheader("Cleaning Summary")
            for item in report_data["cleaning_notes"]:
                st.write(f"- {item}")

            st.subheader("Key Insights")
            for item in report_data["insights"]:
                st.write(f"- {item}")

            st.subheader("Correlations")
            for item in report_data["correlations"]:
                st.write(f"- {item}")

            st.subheader("Recommended Visuals")
            visuals = report_data.get("visuals", [])
            if visuals:
                for visual in visuals:
                    render_visual(df, visual)
            else:
                st.info("No suitable charts were identified for this dataset.")

            st.subheader("AI Enhancement")
            st.info(report_data.get("ai_status", "No AI status available."))
            if report_data.get("ai_summary"):
                st.write(report_data["ai_summary"])

            st.subheader("Download Report")
            pdf_file = generate_pdf(report_data)
            with open(pdf_file, "rb") as file_handle:
                st.download_button(
                    label="Download PDF Report",
                    data=file_handle,
                    file_name="AI_Report.pdf",
                    mime="application/pdf",
                )
