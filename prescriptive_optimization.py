"""
Prescriptive Decision Engine

This module generates maintenance recommendations based on
risk classification, business rules, and technician capacity
constraints.

Pipeline:
1. Read risk classification from the Data Warehouse
2. Apply business decision rules
3. Optimize maintenance scheduling
4. Store recommendations
5. Validate results
"""

import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# CONFIGURATION
LOZINKA = "your_password"
BAZA    = "erreka_dss"
engine  = create_engine(f"mysql+pymysql://root:{LOZINKA}@127.0.0.1/{BAZA}")

# Capacity constraints (per country, per optimization run)
MAX_IMMEDIATE_PER_COUNTRY  = 10   # max technician dispatches today
MAX_SCHEDULED_PER_COUNTRY  = 30   # max planned visits this week

# Environments where High risk ALWAYS triggers immediate on-site
CRITICAL_ENVIRONMENTS = {"hospital", "industrial dock", "logistics center", "emergency"}

# STEP 1 — CREATE OUTPUT TABLE
def create_output_table(con):
    print("\n[STEP 1] Creating prescriptive_maintenance_schedule table...")
    con.execute(text("""
        CREATE TABLE IF NOT EXISTS prescriptive_maintenance_schedule (
            recommendation_id        INT AUTO_INCREMENT PRIMARY KEY,
            door_id                  VARCHAR(20),
            door_type                VARCHAR(100),
            country_id               VARCHAR(10),
            country_name             VARCHAR(100),
            installation_environment VARCHAR(100),
            customer_type            VARCHAR(50),
            usage_scenario           VARCHAR(50),
            risk_level               VARCHAR(20),
            risk_score               INT,
            recommended_action       VARCHAR(50),
            action_priority          INT,
            reason                   TEXT,
            generated_at             DATETIME
        )
    """))
    # Clear previous run so Grafana always shows latest recommendations
    con.execute(text("TRUNCATE TABLE prescriptive_maintenance_schedule"))
    con.commit()
    print("  ✓ Table ready (previous recommendations cleared)")

# STEP 2 — READ INPUT DATA
def read_risk_data(con):
    print("\n[STEP 2] Reading door_risk_classification from DW...")
    df = pd.read_sql("""
        SELECT
            door_id,
            door_type,
            country_id,
            country_name,
            installation_environment,
            customer_type,
            usage_scenario,
            criticality_level,
            sla_category,
            failures,
            days_since_last,
            risk_level,
            risk_score
        FROM door_risk_classification
        ORDER BY risk_score DESC
    """, con=con)
    print(f"  ✓ Loaded {len(df)} doors from risk classification")
    print(f"  Risk distribution:\n{df['risk_level'].value_counts().to_string()}")
    return df

# STEP 3 — DECISION MODEL
def assign_action(row, country_immediate_counts, country_scheduled_counts):
    """
    Core decision logic — maps risk profile to a prescriptive action.

    Rules (ordered by priority):
    1. risk_score == 0  → MONITOR_ONLY
    2. risk_level == High AND critical environment
                        → IMMEDIATE_ONSITE (if capacity allows, else SCHEDULED)
    3. risk_level == High → IMMEDIATE_ONSITE (if capacity allows, else SCHEDULED)
    4. risk_level == Medium → SCHEDULED_VISIT (if capacity allows, else REMOTE)
    5. risk_level == Low  → REMOTE_INTERVENTION
    """
    country = row["country_id"]
    env     = str(row["installation_environment"]).lower()
    risk    = str(row["risk_level"]).lower()
    score   = int(row["risk_score"]) if pd.notna(row["risk_score"]) else 0

    # Initialise country counters if not seen yet
    if country not in country_immediate_counts:
        country_immediate_counts[country] = 0
    if country not in country_scheduled_counts:
        country_scheduled_counts[country] = 0

    # Rule 1: no risk → just monitor
    if score == 0:
        return "MONITOR_ONLY", "Risk score is 0 — no intervention needed at this time"

    # Rule 2 & 3: High risk
    if risk == "high":
        is_critical_env = any(ce in env for ce in CRITICAL_ENVIRONMENTS)
        base_reason = (
            f"High risk (score={score}): {int(row['failures'])} past failures, "
            f"{int(row['days_since_last'])} days since last failure"
        )
        if is_critical_env:
            base_reason += f" — critical environment ({row['installation_environment']})"

        if country_immediate_counts[country] < MAX_IMMEDIATE_PER_COUNTRY:
            country_immediate_counts[country] += 1
            return "IMMEDIATE_ONSITE", base_reason + " → dispatch technician today"
        elif country_scheduled_counts[country] < MAX_SCHEDULED_PER_COUNTRY:
            country_scheduled_counts[country] += 1
            return "SCHEDULED_VISIT", base_reason + " → capacity full, scheduled within 7 days"
        else:
            return "REMOTE_INTERVENTION", base_reason + " → all slots full, remote triage first"

    # Rule 4: Medium risk
    if risk == "medium":
        reason = (
            f"Medium risk (score={score}): {int(row['failures'])} past failures — "
            f"preventive visit recommended"
        )
        if country_scheduled_counts[country] < MAX_SCHEDULED_PER_COUNTRY:
            country_scheduled_counts[country] += 1
            return "SCHEDULED_VISIT", reason + " → plan within 7 days"
        else:
            return "REMOTE_INTERVENTION", reason + " → scheduled slots full, remote check first"

    # Rule 5: Low risk (default)
    return "REMOTE_INTERVENTION", (
        f"Low risk (score={score}) — remote monitoring sufficient, "
        f"no on-site visit required"
    )

# STEP 4 — OPTIMIZATION (greedy assignment)
def optimize(df):
    """
    Greedy optimization:
    - Doors already sorted by risk_score DESC (highest risk first)
    - For each door, assign best available action given remaining capacity
    - Constraints: MAX_IMMEDIATE and MAX_SCHEDULED per country
    - Objective: maximize coverage of highest-risk doors with strongest actions
    """
    print("\n[STEP 3] Running optimization (greedy assignment)...")

    country_immediate_counts = {}
    country_scheduled_counts = {}

    actions   = []
    priorities = []
    reasons   = []

    for _, row in df.iterrows():
        action, reason = assign_action(row, country_immediate_counts, country_scheduled_counts)
        actions.append(action)
        reasons.append(reason)
        
    priority_map = {
        "IMMEDIATE_ONSITE":    1,
        "SCHEDULED_VISIT":     2,
        "REMOTE_INTERVENTION": 3,
        "MONITOR_ONLY":        4,
    }
    priorities = [priority_map[a] for a in actions]

    df = df.copy()
    df["recommended_action"] = actions
    df["action_priority"]    = priorities
    df["reason"]             = reasons
    df["generated_at"]       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Summary
    print(f"  Optimization complete. Action distribution:")
    print(df["recommended_action"].value_counts().to_string())
    print(f"\n  Capacity used per country (IMMEDIATE):")
    for c, n in sorted(country_immediate_counts.items()):
        if n > 0:
            print(f"    {c}: {n}/{MAX_IMMEDIATE_PER_COUNTRY}")

    return df

# STEP 5 — WRITE TO DATA WAREHOUSE

def write_recommendations(df, con):
    print("\n[STEP 4] Writing recommendations to DW...")

    output_cols = [
        "door_id", "door_type", "country_id", "country_name",
        "installation_environment", "customer_type", "usage_scenario",
        "risk_level", "risk_score",
        "recommended_action", "action_priority", "reason", "generated_at"
    ]

    output_df = df[output_cols]
    output_df.to_sql(
        name="prescriptive_maintenance_schedule",
        con=con,
        if_exists="append",
        index=False
    )
    print(f"  ✓ {len(output_df)} recommendations written to prescriptive_maintenance_schedule")

# STEP 6 — VALIDATE
def validate(con):
    print("\n[STEP 5] Validation — sample output from DW:")

    result = pd.read_sql("""
        SELECT
            door_id,
            country_id,
            installation_environment,
            risk_level,
            risk_score,
            recommended_action,
            action_priority,
            LEFT(reason, 80) AS reason_preview
        FROM prescriptive_maintenance_schedule
        ORDER BY action_priority ASC, risk_score DESC
        LIMIT 10
    """, con=con)

    print(result.to_string(index=False))

    # Summary counts
    summary = pd.read_sql("""
        SELECT recommended_action, COUNT(*) as doors, AVG(risk_score) as avg_risk
        FROM prescriptive_maintenance_schedule
        GROUP BY recommended_action
        ORDER BY MIN(action_priority)
    """, con=con)
    print("\n  Summary by action:")
    print(summary.to_string(index=False))

# MAIN
if __name__ == "__main__":
    print("=" * 60)
    print("ERREKA DSS — Prescriptive Optimization Pipeline")
    print(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    with engine.connect() as con:
        create_output_table(con)
        df_risk = read_risk_data(con)
        df_optimized = optimize(df_risk)
        write_recommendations(df_optimized, con)
        validate(con)

    print("\n" + "=" * 60)
    print("Pipeline completed successfully.")
    print("Recommendations are now stored in: prescriptive_maintenance_schedule")
    print("Open Grafana to view the Prescriptive Dashboard.")
    print("=" * 60)