# Automated Data Analyst

`Automated Data Analyst` is a Streamlit app that accepts CSV or Excel files, cleans the dataset, generates quick insights, recommends charts, and exports a PDF report.

The project is designed to stay useful even when AI services are unavailable. Core analysis runs locally with `pandas`, while CrewAI-based enhancement is used only when the environment is configured.

## Features

- Upload `.csv`, `.xlsx`, or `.xls` files
- Automatic duplicate removal and missing-value handling
- Local summary of dataset shape, trends, and correlations
- Auto-generated chart recommendations with rendered visuals
- Optional CrewAI enhancement using a Groq model
- One-click PDF report export

## Project Structure

- [app.py](/f:/Projects/automated-data-analyst/app.py:1): Streamlit interface and chart rendering
- [pipeline.py](/f:/Projects/automated-data-analyst/pipeline.py:1): file loading, cleaning, analysis, and optional AI enhancement
- [agents.py](/f:/Projects/automated-data-analyst/agents.py:1): CrewAI agent setup
- [report.py](/f:/Projects/automated-data-analyst/report.py:1): PDF report generation
- [requirements.txt](/f:/Projects/automated-data-analyst/requirements.txt:1): Python dependencies

## Requirements

- Python 3.10+
- Windows PowerShell, Command Prompt, or any shell that can activate the virtual environment

## Installation

1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.

Example on Windows:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root if you want AI enhancement:

```env
GROQ_API_KEY=your_groq_api_key_here
DATA_ANALYST_MODEL=groq/llama-3.3-70b-versatile
```

Notes:

- `GROQ_API_KEY` enables CrewAI-powered analysis enhancement.
- `DATA_ANALYST_MODEL` is optional. If omitted, the default Groq model is used.
- Without `GROQ_API_KEY`, the app still works using the built-in local analysis path.

## Run the App

```powershell
.\venv\Scripts\streamlit.exe run app.py
```

Then open the local Streamlit URL shown in the terminal.

## How It Works

1. The user uploads a CSV or Excel file.
2. The pipeline loads the file and normalizes basic formatting.
3. Duplicate rows are removed.
4. Missing text values are forward/back filled.
5. Missing numeric values are filled with the median.
6. The app generates local insights, correlation notes, and chart suggestions.
7. If AI is configured, CrewAI adds an enhancement summary.
8. A PDF report is generated for download.

## Output

The app displays:

- Dataset metrics such as rows, columns, missing cells, and duplicates
- A preview of the cleaned dataset
- Cleaning notes
- Key insights
- Correlation highlights
- Recommended charts rendered in the UI
- AI status and optional AI-generated summary
- A downloadable PDF report

## Dependencies

Main libraries used in this project:

- `streamlit`
- `pandas`
- `matplotlib`
- `seaborn`
- `reportlab`
- `python-dotenv`
- `crewai`
- `crewai-tools`
- `litellm`
- `openpyxl`

## Troubleshooting

### App runs but AI summary is skipped

Make sure `.env` contains a valid `GROQ_API_KEY`.

### CSV fails to load

The loader tries common encodings and separators, but malformed files may still fail. Re-save the file as UTF-8 CSV or Excel and try again.

### PDF report does not look updated

The report is written to `report.pdf` in the project root each time a new analysis is generated.

## Future Improvements

- Smarter chart selection for time-series datasets
- Better statistical summaries for larger datasets
- Multiple-page PDF layout with tables and embedded plots
- File-based test coverage for upload and analysis flows

## License

No license file is currently included in this repository. Add one if you plan to distribute the project.
