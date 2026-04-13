import os
from typing import List

from dotenv import load_dotenv

try:
    from crewai import Agent
except Exception:  # pragma: no cover - dependency/runtime fallback
    Agent = None


load_dotenv()

MODEL = os.getenv("DATA_ANALYST_MODEL", "groq/llama-3.3-70b-versatile")


def ai_is_configured() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))


def build_agents() -> List["Agent"]:
    """Create CrewAI agents only when the runtime is fully configured."""
    if Agent is None or not ai_is_configured():
        return []

    cleaning_agent = Agent(
        role="Data Cleaning Expert",
        goal="Explain how the dataset should be cleaned and what quality issues exist.",
        backstory="A careful data quality specialist who communicates clearly.",
        llm=MODEL,
        verbose=False,
    )

    analysis_agent = Agent(
        role="Data Analyst",
        goal="Find trends, patterns, anomalies, and business-relevant insights.",
        backstory="An analyst who translates statistics into plain English.",
        llm=MODEL,
        verbose=False,
    )

    visualization_agent = Agent(
        role="Visualization Expert",
        goal="Recommend useful charts and explain what each one would show.",
        backstory="A visualization designer focused on clarity over decoration.",
        llm=MODEL,
        verbose=False,
    )

    return [cleaning_agent, analysis_agent, visualization_agent]
