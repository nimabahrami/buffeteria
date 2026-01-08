# ANTIGRAVITY TERMINAL // O&G ANALYZER

## Overview

The Antigravity Terminal is a specialized financial analysis tool designed for the Oil & Gas sector. It combines automated quantitative analysis with a high-fidelity, Bloomberg Terminal-inspired user interface to provide rapid insights into energy equities.

The system leverages Natural Language Processing (NLP) to parse SEC 10-K filings and integrates real-time market data to perform a battery of 18 rigorous financial health checks, covering cost structure, profitability, capital discipline, and valuation.

## Key Features

- **Automated Diagnostic Scorecard**: Instantly evaluates companies against 18 specific criteria tailored to the O&G industry (e.g., LOE/BOE, ROIC vs WACC, Reserve Replacement).
- **SEC 10-K NLP Parsing**: automatically extracts production figures, operational metrics, and management commentary directly from official SEC filings.
- **Real-Time Market Data**: Integrates live pricing, market cap, and volume data via Yahoo Finance.
- **Interactive Terminal UI**: A Streamlit-based dashboard featuring a retro-modern aesthetic, dark mode, and spectral color schemes optimized for data readability.
- **Dual Interface Modes**:
  - **Terminal Dashboard**: A fully interactive web application for visual analysis.
  - **REST API**: A JSON-based API endpoint for integration with other systems.

## Architecture

The application is built on a robust Python stack:

- **Frontend**: Streamlit
- **Backend**: Flask
- **Data Processing**: Pandas, NumPy
- **Visualization**: Altair
- **Data Sources**: YFinance (Market Data), SEC EDGAR (Filings)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/nimabahrami/buffeteria.git
    cd buffeteria
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Running the Terminal Dashboard

To launch the interactive dashboard:

```bash
streamlit run main.py
```

Access the dashboard in your browser at `http://localhost:8501`.

### Running the API

To start the backend API server:

```bash
python app.py
```

The API will be available at `http://localhost:8502`.

**Endpoint:** `GET /api/analyze?ticker=XOM`

**Response:**
```json
{
  "summary": "Analysis complete for XOM. Score: 16/18 OK.",
  "scorecard": [...],
  "ledger": {...}
}
```

## Deployment

The application includes a `Procfile` configured for deployment on platforms like Heroku or Render using Gunicorn:

```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```
