# ERREKA Decision Support System

A Decision Support System (DSS) developed for the **Decision Support Systems** course at the **University of Deusto**.

The project focuses on predictive and prescriptive maintenance for ERREKA automatic doors by combining an ETL pipeline, a relational MySQL database, simulation models, and a rule-based decision engine that generates maintenance recommendations.

---

# Project Overview

The objective of this project is to support maintenance planning by transforming operational and maintenance data into actionable decisions.

The workflow consists of four main stages:

1. **ETL Pipeline**
   - Creates the database schema
   - Extracts and transforms CSV datasets
   - Loads validated data into MySQL

2. **Simulation**
   - Simulates operational scenarios
   - Generates maintenance-related events

3. **Prescriptive Decision Engine**
   - Reads risk classifications
   - Applies business rules
   - Considers technician capacity constraints
   - Generates maintenance recommendations

4. **Visualization**
   - Produces output tables
   - Supports dashboard visualization using Grafana

---

# Features

- ETL pipeline for structured data loading
- Relational MySQL Data Warehouse
- Risk classification support
- Rule-based maintenance recommendations
- Capacity-aware scheduling
- Simulation of maintenance scenarios
- Grafana-ready output
- Modular project structure

---

# Technologies

- Python
- Pandas
- SQLAlchemy
- PyMySQL
- MySQL
- HTML / CSS
- Grafana

---

# Project Structure

```text
erreka-decision-support-system/

├── data/
│   ├── *.csv
│
├── docs/
│   ├── Activity_6_Report.pdf
│   ├── Activity_7_Report.pdf
│   └── Technical_Report.pdf
│
├── interface/
│   ├── index.html
│   └── style.css
│
├── simulation/
│   └── erreka_simulation.py
│
├── output/
│   ├── simulation_results.csv
│   └── simulation_results.json
│
├── etl_pipeline.py
├── prescriptive_optimization.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

# Dataset

The project uses multiple datasets describing automatic door installations, maintenance history and operational behaviour.

The datasets include information such as:

- Installed base
- Door registry
- Maintenance history
- Incident events
- Operational logs
- Alert types
- Risk factors
- Response actions
- Context criticality

The data is included for educational purposes within the scope of the course project.

---

# How to Run

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure MySQL

Update the database connection settings inside:

- `etl_pipeline.py`
- `prescriptive_optimization.py`

with your local MySQL credentials.

## 3. Execute the ETL pipeline

```bash
python etl_pipeline.py
```

## 4. Run the decision engine

```bash
python prescriptive_optimization.py
```

---

# Results

The project produces:

- A populated relational database
- Validated ETL process
- Risk-based maintenance recommendations
- Optimized maintenance schedules
- Output files for visualization
- Data ready for Grafana dashboards

---

# Documentation

Additional documentation is available in the **docs/** folder:

- Activity 6 Report
- Activity 7 Report
- Technical Report

These reports describe the design decisions, implementation process and evaluation of the project.

---

# Academic Context

This repository contains the final project developed for the **Decision Support Systems** course at the **University of Deusto**.

It is shared for educational and portfolio purposes.