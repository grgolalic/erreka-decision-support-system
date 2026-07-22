import os
import pandas as pd
from sqlalchemy import create_engine, text

# ------------------------------------------------------------------
# Database configuration
# Update these values according to your local MySQL installation.
# ------------------------------------------------------------------
LOZINKA = "your_password"
BAZA = "erreka_dss"

CSV_FOLDER = os.path.join(
    os.path.dirname(__file__),
    "data"
)

DB_USER = "root"
DB_HOST = "127.0.0.1"

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{LOZINKA}@{DB_HOST}/{BAZA}"
)

DELETE_ORDER = [
    "maintenance_recommendations",
    "garage_operations_log",
    "pedestrian_operations_log",
    "industrial_operations_log",
    "incident_events",
    "erreka_maintenance_history",
    "doors_registry",
    "installed_base",
    "risk_factors",
    "response_actions_catalog",
    "door_type_usage_catalog",
    "context_criticality",
    "alert_types",
]

LOAD_ORDER = [
    "alert_types",
    "context_criticality",
    "door_type_usage_catalog",
    "response_actions_catalog",
    "risk_factors",
    "installed_base",
    "doors_registry",
    "incident_events",
    "erreka_maintenance_history",
    "garage_operations_log",
    "pedestrian_operations_log",
    "industrial_operations_log",
    "maintenance_recommendations",
]

#  STEP 1 — CREATE TABLES (IF NOT EXISTS)
def create_tables(con):
    print("\n[STEP 1] Provjera / kreiranje tablica (IF NOT EXISTS)...")

    statements = [
        """CREATE TABLE IF NOT EXISTS alert_types (
            alert_type_id                VARCHAR(10)  PRIMARY KEY,
            alert_type                   VARCHAR(100),
            description                  TEXT,
            technical_severity           VARCHAR(20),
            potential_operational_impact VARCHAR(20),
            safety_related               VARCHAR(5)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS context_criticality (
            context_criticality_id VARCHAR(10)  PRIMARY KEY,
            customer_type          VARCHAR(50),
            environment_type       VARCHAR(100),
            criticality_level      VARCHAR(20),
            sla_category           VARCHAR(50)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS door_type_usage_catalog (
            door_type_id             INT          AUTO_INCREMENT PRIMARY KEY,
            door_type                VARCHAR(100),
            usage_scenario           VARCHAR(50),
            installation_environment VARCHAR(100),
            criticality_level        VARCHAR(20),
            operational_complexity   VARCHAR(20),
            maintenance_intensity    VARCHAR(20),
            estimated_cycles_day     INT
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS response_actions_catalog (
            response_action_id     VARCHAR(10)  PRIMARY KEY,
            response_action        VARCHAR(100),
            description            TEXT,
            response_time_category VARCHAR(50),
            resource_intensity     VARCHAR(20)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS risk_factors (
            risk_factor_id VARCHAR(10)  PRIMARY KEY,
            risk_factor    VARCHAR(100),
            description    TEXT,
            door_type      VARCHAR(100),
            usage_scenario VARCHAR(50),
            risk_dimension VARCHAR(50)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS installed_base (
            installed_base_id        INT          AUTO_INCREMENT PRIMARY KEY,
            country_id               VARCHAR(10),
            country_name             VARCHAR(100),
            door_type                VARCHAR(100),
            usage_scenario           VARCHAR(50),
            installation_environment VARCHAR(100),
            installed_doors          INT,
            customer_type            VARCHAR(50)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS doors_registry (
            doors_registry_id        INT          AUTO_INCREMENT PRIMARY KEY,
            door_id                  VARCHAR(20),
            country_id               VARCHAR(10),
            country_name             VARCHAR(100),
            door_type                VARCHAR(100),
            usage_scenario           VARCHAR(50),
            installation_environment VARCHAR(100),
            customer_type            VARCHAR(50),
            context_criticality_id   VARCHAR(10),
            FOREIGN KEY (context_criticality_id)
                REFERENCES context_criticality(context_criticality_id)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS erreka_maintenance_history (
            door_id                 VARCHAR(20)  PRIMARY KEY,
            last_maintenance_date   DATE,
            maintenance_type        VARCHAR(50),
            number_of_past_failures INT,
            days_since_last_failure INT,
            days_to_next_failure    INT,
            failed_next_30_days     VARCHAR(5)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS incident_events (
            incident_id              VARCHAR(50)  PRIMARY KEY,
            timestamp                DATETIME,
            door_id                  VARCHAR(20),
            country_id               VARCHAR(10),
            door_type                VARCHAR(100),
            usage_scenario           VARCHAR(50),
            installation_environment VARCHAR(100),
            customer_type            VARCHAR(50),
            context_criticality_id   VARCHAR(10),
            alert_type_id            VARCHAR(10),
            FOREIGN KEY (alert_type_id)
                REFERENCES alert_types(alert_type_id),
            FOREIGN KEY (context_criticality_id)
                REFERENCES context_criticality(context_criticality_id)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS garage_operations_log (
            garage_id                       INT         AUTO_INCREMENT PRIMARY KEY,
            timestamp                       DATETIME,
            door_id                         VARCHAR(20),
            country_id                      VARCHAR(10),
            door_type                       VARCHAR(100),
            usage_scenario                  VARCHAR(50),
            operating_mode                  VARCHAR(20),
            open_limit_switch_state         VARCHAR(10),
            closed_limit_switch_state       VARCHAR(10),
            encoder_position                FLOAT,
            encoder_speed                   FLOAT,
            motor_torque                    FLOAT,
            safety_photocell_blocked        VARCHAR(10),
            sensitive_edge_triggered        VARCHAR(10),
            motor_temperature               FLOAT,
            motor_command                   VARCHAR(20),
            electromechanical_brake_engaged VARCHAR(10),
            electric_lock_state             VARCHAR(20),
            courtesy_light_active           VARCHAR(10),
            rf_remote_control_activated     VARCHAR(10),
            wall_button_pressed             VARCHAR(10),
            emergency_stop_activated        VARCHAR(10),
            iot_app_command_received        VARCHAR(10),
            iot_telemetry_status            VARCHAR(20)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS pedestrian_operations_log (
            pedestrian_id                   INT         AUTO_INCREMENT PRIMARY KEY,
            timestamp                       DATETIME,
            door_id                         VARCHAR(20),
            country_id                      VARCHAR(10),
            door_type                       VARCHAR(100),
            usage_scenario                  VARCHAR(50),
            operating_mode                  VARCHAR(20),
            open_limit_switch_state         VARCHAR(10),
            closed_limit_switch_state       VARCHAR(10),
            encoder_position                FLOAT,
            encoder_speed                   FLOAT,
            motor_torque                    FLOAT,
            safety_photocell_blocked        VARCHAR(10),
            sensitive_edge_triggered        VARCHAR(10),
            motor_temperature               FLOAT,
            motor_command                   VARCHAR(20),
            electromechanical_brake_engaged VARCHAR(10),
            electric_lock_state             VARCHAR(20),
            courtesy_light_active           VARCHAR(10),
            rf_remote_control_activated     VARCHAR(10),
            wall_button_pressed             VARCHAR(10),
            emergency_stop_activated        VARCHAR(10),
            iot_app_command_received        VARCHAR(10),
            iot_telemetry_status            VARCHAR(20)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS industrial_operations_log (
            industrial_operations_id        INT         AUTO_INCREMENT PRIMARY KEY,
            timestamp                       DATETIME,
            door_id                         VARCHAR(20),
            country_id                      VARCHAR(10),
            door_type                       VARCHAR(100),
            usage_scenario                  VARCHAR(50),
            operating_mode                  VARCHAR(20),
            upper_limit_switch_state        VARCHAR(10),
            lower_limit_switch_state        VARCHAR(10),
            encoder_position                FLOAT,
            encoder_speed                   FLOAT,
            cycle_counter                   INT,
            anti_fall_triggered             VARCHAR(10),
            industrial_radar_detected       VARCHAR(10),
            inductive_loop_triggered        VARCHAR(10),
            photoelectric_barrier_blocked   VARCHAR(10),
            infrared_curtain_triggered      VARCHAR(10),
            bottom_sensitive_edge_triggered VARCHAR(10),
            motor_current                   FLOAT,
            motor_torque                    FLOAT,
            vibration_level                 FLOAT,
            motor_temperature               FLOAT,
            motor_command                   VARCHAR(20),
            electromagnetic_brake_engaged   VARCHAR(10),
            automatic_latch_state           VARCHAR(20),
            traffic_light_state             VARCHAR(20),
            audible_warning_active          VARCHAR(10),
            manual_open_button_pressed      VARCHAR(10),
            emergency_stop_activated        VARCHAR(10),
            iot_telemetry_status            VARCHAR(20)
        ) ENGINE=InnoDB""",

        """CREATE TABLE IF NOT EXISTS maintenance_recommendations (
            door_id                  VARCHAR(32)   NOT NULL,
            country                  VARCHAR(64)   NOT NULL,
            door_type                VARCHAR(64)   NOT NULL,
            usage_scenario           VARCHAR(16)   NOT NULL,
            predicted_failure_risk   DECIMAL(5,3)  NOT NULL,
            business_impact_score    DECIMAL(6,2)  NOT NULL,
            estimated_service_hours  DECIMAL(6,2)  NOT NULL,
            recommended_action       VARCHAR(128)  NOT NULL,
            selected_this_week       TINYINT(1)    NOT NULL,
            priority_rank            INT           NULL,
            expected_avoided_downtime INT          NOT NULL,
            criticality_level        VARCHAR(16)   NOT NULL,
            sla_category             VARCHAR(32)   NOT NULL,
            justification_tag        VARCHAR(128)  NOT NULL,
            PRIMARY KEY (door_id)
        ) ENGINE=InnoDB""",
    ]

    for sql in statements:
        con.execute(text(sql))
    con.commit()
    print("  ✓ Sve tablice postoje")

#  STEP 2 — DELETE (briši podatke, NE tablice)

def delete_all_data(con):
    print("\n[STEP 2] Brisanje podataka iz tablica (TRUNCATE)...")

    con.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

    for table in DELETE_ORDER:
        try:
            con.execute(text(f"TRUNCATE TABLE {table}"))
            print(f"  ✓ {table:<40} TRUNCATE OK")
        except Exception as e:
            print(f"  ⚠  {table:<40} greška — {e}")

    con.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    con.commit()
    print("  ✓ Brisanje završeno — tablice su prazne, struktura netaknuta")

#  STEP 3 — EXTRACT & TRANSFORM

def read_csv(filename):
    path = os.path.join(CSV_FOLDER, filename)
    if not os.path.exists(path):
        print(f"  ⚠  {filename} nije pronađen — preskačem")
        return None
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    print(f"  ✓ {filename}: {len(df)} redaka učitano")
    return df


def extract_all():
    print("\n[STEP 3] Učitavanje i transformacija CSV datoteka...")

    alert_types         = read_csv("alert_types.csv")
    context_criticality = read_csv("context_criticality.csv")
    catalog             = read_csv("door_type_usage_catalog.csv")
    response_actions    = read_csv("response_actions_catalog.csv")
    risk_factors        = read_csv("risk_factors.csv")
    installed_base      = read_csv("installed_base.csv")
    doors_registry      = read_csv("doors_registry.csv")
    incident_events     = read_csv("incident_events.csv")
    maintenance         = read_csv("erreka_maintenance_history.csv")
    garage_log          = read_csv("garage_operations_log.csv")
    pedestrian_log      = read_csv("pedestrian_operations_log.csv")
    industrial_log      = read_csv("industrial_operations_log.csv")
    recommendations     = read_csv("maintenance_recommendations.csv")

    # Parse timestamps
    for df in [incident_events, garage_log, pedestrian_log, industrial_log]:
        if df is not None and "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Parse maintenance history
    if maintenance is not None:
        maintenance["last_maintenance_date"] = pd.to_datetime(
            maintenance["last_maintenance_date"], errors="coerce"
        ).dt.date
        for col in ["days_since_last_failure", "days_to_next_failure",
                    "number_of_past_failures"]:
            if col in maintenance.columns:
                maintenance[col] = pd.to_numeric(maintenance[col], errors="coerce")

    # Ukloni surrogate PK stupce koje MySQL sam generira
    if catalog is not None and "door_type_id" in catalog.columns:
        catalog = catalog.drop(columns=["door_type_id"])
    if installed_base is not None and "installed_base_id" in installed_base.columns:
        installed_base = installed_base.drop(columns=["installed_base_id"])

    # maintenance_recommendations: numeric konverzije
    if recommendations is not None:
        for col in ["predicted_failure_risk", "business_impact_score",
                    "estimated_service_hours", "expected_avoided_downtime",
                    "priority_rank", "selected_this_week"]:
            if col in recommendations.columns:
                recommendations[col] = pd.to_numeric(
                    recommendations[col], errors="coerce"
                )

    return {
        "alert_types":                alert_types,
        "context_criticality":        context_criticality,
        "door_type_usage_catalog":    catalog,
        "response_actions_catalog":   response_actions,
        "risk_factors":               risk_factors,
        "installed_base":             installed_base,
        "doors_registry":             doors_registry,
        "incident_events":            incident_events,
        "erreka_maintenance_history": maintenance,
        "garage_operations_log":      garage_log,
        "pedestrian_operations_log":  pedestrian_log,
        "industrial_operations_log":  industrial_log,
        "maintenance_recommendations": recommendations,
    }

#  STEP 4 — LOAD

def load_table(df, table_name, con):
    if df is None:
        print(f"  ⚠  {table_name:<40} nema podataka — preskačem")
        return
    try:
        df.to_sql(name=table_name, con=con, if_exists="append", index=False)
        print(f"  ✓ {table_name:<40} {len(df):>6} redaka upisano")
    except Exception as e:
        print(f"  ⚠  {table_name:<40} greška — {e}")


def load_all(data, con):
    print("\n[STEP 4] Punjenje tablica novim podacima...")
    for table in LOAD_ORDER:
        load_table(data.get(table), table, con)

#  STEP 5 — VALIDATE
def validate(con):
    print("\n[STEP 5] Validacija — broj redaka po tablici:")
    print(f"\n  {'Tablica':<40} {'Redaka':>8}")
    print(f"  {'-'*40} {'-'*8}")
    for table in LOAD_ORDER:
        try:
            result = con.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            status = "✓" if count > 0 else "⚠ "
            print(f"  {status} {table:<38} {count:>8}")
        except Exception:
            print(f"  ⚠  {table:<38} {'N/A':>8}")

#  MAIN

if __name__ == "__main__":
    print("=" * 60)
    print("  ERREKA DSS — Universal Reload ETL")
    print("  Briše stare podatke i puni nove iz CSV foldera")
    print("=" * 60)
    print(f"\n  Folder: {CSV_FOLDER}")
    print(f"  Baza:   {BAZA}")

    with engine.connect() as con:
        create_tables(con)
        delete_all_data(con)
        data = extract_all()
        load_all(data, con)
        validate(con)

    print("\n" + "=" * 60)
    print("  ✓ ETL završen uspješno")
    print("=" * 60)