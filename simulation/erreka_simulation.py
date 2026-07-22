import pandas as pd
import numpy as np
import json
import os
import random

# CONFIGURATION

RANDOM_SEED = 42
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) 

DATA_PATH = os.path.join(PROJECT_ROOT, "data", "door_risk_clasification.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
SIMULATION_MONTHS = 12  # can be changed to 3 or 6

TRANSITION_PROBS = {
    "Reactive": {
        "ok_to_degrading":      0.15,
        "degrading_to_failed":  0.40,
        "failed_to_repaired":   0.60,
    },
    "Preventive": {
        "ok_to_degrading":      0.08,
        "degrading_to_failed":  0.20,
        "failed_to_repaired":   0.80,
    },
    "Risk_SLA": {
        "ok_to_degrading":      0.05,
        "degrading_to_failed":  0.10,
        "failed_to_repaired":   0.95,
    }
}

COST_PER_ACTION = {
    "Reactive":   {"repair": 850,  "inspection": 0,   "preventive": 0},
    "Preventive": {"repair": 500,  "inspection": 120, "preventive": 200},
    "Risk_SLA":   {"repair": 600,  "inspection": 150, "preventive": 350},
}

# SLA breach penalty (€) - assumption
SLA_BREACH_PENALTY = {
    "Critical":      2000,
    "High Priority": 1000,
    "Standard":       300,
    "Basic":            0,
}

# INITIAL STATE ASSIGNMENT
#
# Based on the existing risk classification from Activity 5:
# - High risk (score=3)   -> start in Degrading state (already at risk)
# - Medium risk (score=2) -> 50% chance Degrading, 50% OK
# - Low risk (score=1)    -> start in OK state

def assign_initial_state(risk_level, risk_score):
    if risk_level == "High":
        return "Degrading"
    elif risk_level == "Medium":
        return "Degrading" if random.random() < 0.5 else "OK"
    else:
        return "OK"

# CORE SIMULATION FUNCTION

def run_simulation(doors_df, strategy_name, months):
    """
    Runs the simulation for a given strategy over the specified number of months.
    Returns a dictionary with monthly metrics and per-door final states.
    """
    probs = TRANSITION_PROBS[strategy_name]
    costs = COST_PER_ACTION[strategy_name]

    # Initialise door states
    states = {}
    for _, door in doors_df.iterrows():
        states[door["door_id"]] = assign_initial_state(
            door["risk_level"], door["risk_score"]
        )

    # Monthly metrics storage
    monthly_failures = []
    monthly_sla_breaches = []
    monthly_costs = []
    monthly_state_counts = []

    for month in range(1, months + 1):
        month_failures = 0
        month_sla_breaches = 0
        month_cost = 0
        state_counts = {"OK": 0, "Degrading": 0, "Failed": 0, "Repaired": 0}

        for _, door in doors_df.iterrows():
            door_id = door["door_id"]
            current_state = states[door_id]
            p_ok_deg = probs["ok_to_degrading"]
            p_deg_fail = probs["degrading_to_failed"]
            p_fail_rep = probs["failed_to_repaired"]

            if strategy_name == "Risk_SLA":
                if door["sla_category"] == "Critical" and door["risk_score"] >= 2:
                    p_deg_fail *= 0.7   # 30% further reduction for critical SLA doors
                    p_fail_rep = min(p_fail_rep * 1.1, 1.0)
                if door["criticality_level"] == "very high":
                    p_ok_deg *= 0.8     # 20% reduction for very high criticality
            elif strategy_name == "Preventive":
                if door["usage_scenario"] == "intensive":
                    p_ok_deg *= 1.2     # intensive use increases degradation slightly
                    p_ok_deg = min(p_ok_deg, 1.0)

            # State transition logic
            new_state = current_state

            if current_state == "OK":
                if random.random() < p_ok_deg:
                    new_state = "Degrading"

            elif current_state == "Degrading":
                if random.random() < p_deg_fail:
                    new_state = "Failed"
                    month_failures += 1

                    # Check SLA breach
                    if door["sla_category"] in ["Critical", "High Priority"]:
                        month_sla_breaches += 1
                        month_cost += SLA_BREACH_PENALTY[door["sla_category"]]

                    month_cost += costs["repair"]

            elif current_state == "Failed":
                if random.random() < p_fail_rep:
                    new_state = "OK"  # repaired, back to OK
                    if strategy_name == "Preventive":
                        month_cost += costs["inspection"]
                else:
                    # Still failed - another SLA breach if critical
                    if door["sla_category"] == "Critical":
                        month_sla_breaches += 1
                        month_cost += SLA_BREACH_PENALTY["Critical"] * 0.5

            elif current_state == "Repaired":
                # Repaired doors go back to OK next month
                new_state = "OK"

            # Apply preventive inspection cost (Preventive strategy)
            if strategy_name == "Preventive" and current_state in ["OK", "Degrading"]:
                month_cost += costs["inspection"]

            # Apply Risk & SLA targeted inspection cost
            if strategy_name == "Risk_SLA" and door["risk_score"] >= 2:
                month_cost += costs["preventive"]

            states[door_id] = new_state
            state_counts[new_state] = state_counts.get(new_state, 0) + 1

        monthly_failures.append(month_failures)
        monthly_sla_breaches.append(month_sla_breaches)
        monthly_costs.append(round(month_cost, 2))
        monthly_state_counts.append(state_counts)

        print(f"  [{strategy_name}] Month {month}: "
              f"Failures={month_failures}, "
              f"SLA Breaches={month_sla_breaches}, "
              f"Cost=€{month_cost:,.0f}")

    return {
        "strategy": strategy_name,
        "months": list(range(1, months + 1)),
        "failures": monthly_failures,
        "sla_breaches": monthly_sla_breaches,
        "costs": monthly_costs,
        "state_counts": monthly_state_counts,
        "totals": {
            "total_failures": sum(monthly_failures),
            "total_sla_breaches": sum(monthly_sla_breaches),
            "total_cost": round(sum(monthly_costs), 2),
            "avg_monthly_failures": round(sum(monthly_failures) / months, 1),
        }
    }

def compute_top_priority_doors(doors_df, strategy_name, n=5):
    df = doors_df.copy()

    sla_priority = {"Critical": 4, "High Priority": 3, "Standard": 2, "Basic": 1}
    df["sla_rank"] = df["sla_category"].map(sla_priority).fillna(0)

    usage_priority = {"intensive": 3, "moderate": 2, "low": 1}
    df["usage_rank"] = df["usage_scenario"].map(usage_priority).fillna(0)

    crit_priority = {"very high": 4, "high": 3, "medium": 2, "low": 1}
    df["crit_rank"] = df["criticality_level"].map(crit_priority).fillna(0)

    df["is_failing_now"] = (df["days_since_last"] == 0).astype(int)

    if strategy_name == "Reactive":
        # Reactive ONLY considers doors that are currently in failure
        # (days_since_last == 0). A reactive team does not pre-emptively
        # intervene on healthy doors. Ranking inside this subset is by
        # raw failure count.
        eligible = df[df["is_failing_now"] == 1].copy()
        eligible["score"] = (
            eligible["failures"] * 10
            + eligible["sla_rank"] * 2
        )

    elif strategy_name == "Preventive":
        # Preventive ONLY scans doors that are operational (not currently
        # failing) — preventive maintenance is about avoiding the next
        # failure, not fixing the current one. Inside this subset, doors
        # with intensive usage and many past failures come first because
        # they consume the inspection cycle fastest.
        eligible = df[df["is_failing_now"] == 0].copy()
        eligible["score"] = (
            eligible["usage_rank"] * 30
            + eligible["failures"] * 8
            + eligible["crit_rank"] * 5
            + eligible["risk_score"] * 2
        )

    elif strategy_name == "Risk_SLA":
        # Risk & SLA considers ALL doors but ranks strictly by business
        # impact: risk score × SLA criticality. The result is the worst-
        # case business risk regardless of current operational state.
        eligible = df.copy()
        eligible["score"] = (
            eligible["risk_score"] * 30
            + eligible["sla_rank"] * 25
            + eligible["failures"] * 3
            + eligible["is_failing_now"] * 2
        )

    else:
        eligible = df.copy()
        eligible["score"] = 0

    if len(eligible) < n:
        eligible = df.copy()
        eligible["score"] = eligible["risk_score"] * 10 + eligible["failures"]

    df_sorted = eligible.sort_values(by="score", ascending=False)
    top = df_sorted.head(n)

    result = []
    for _, row in top.iterrows():
        result.append({
            "door_id":          row["door_id"],
            "door_type":        row["door_type"],
            "country":          row["country_name"],
            "risk_level":       row["risk_level"],
            "sla_category":     row["sla_category"],
            "failures":         int(row["failures"]),
            "days_since_last":  int(row["days_since_last"]),
            "usage_scenario":   row["usage_scenario"],
        })

    return result

# MAIN

def main():
    print("=" * 60)
    print("ERREKA DSS - Activity 7: Maintenance Strategy Simulation")
    print("=" * 60)

    # Set random seed for reproducibility
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # Load data
    print(f"\nLoading data from {DATA_PATH}...")
    doors_df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(doors_df)} doors.")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Run simulation for all 3 strategies
    strategies = ["Reactive", "Preventive", "Risk_SLA"]
    results = []

    print(f"\nRunning {SIMULATION_MONTHS}-month simulation...\n")

    for strategy in strategies:
        print(f"Strategy: {strategy}")
        result = run_simulation(doors_df, strategy, SIMULATION_MONTHS)
        # Compute top 5 priority doors for this strategy
        result["top_priority_doors"] = compute_top_priority_doors(
            doors_df, strategy, n=5
        )
        results.append(result)
        print()
        
    # SUMMARY TABLE

    print("=" * 60)
    print("SIMULATION SUMMARY")
    print("=" * 60)
    print(f"{'Strategy':<15} {'Total Failures':>15} {'SLA Breaches':>13} {'Total Cost':>12}")
    print("-" * 60)
    for r in results:
        print(f"{r['strategy']:<15} "
              f"{r['totals']['total_failures']:>15} "
              f"{r['totals']['total_sla_breaches']:>13} "
              f"€{r['totals']['total_cost']:>11,.0f}")


    # JSON for HTML interface
    output_json = {
        "simulation_config": {
            "months": SIMULATION_MONTHS,
            "total_doors": len(doors_df),
            "random_seed": RANDOM_SEED,
            "assumption_note": (
                "Transition probabilities are modelling assumptions, "
                "not empirically validated values. They reflect the "
                "conceptual effectiveness of each maintenance strategy."
            )
        },
        "strategies": results,
        "transition_probabilities": TRANSITION_PROBS,
    }

    json_path = os.path.join(OUTPUT_DIR, "simulation_results.json")
    with open(json_path, "w") as f:
        json.dump(output_json, f, indent=2)
    print(f"\nJSON saved to {json_path}")

    # CSV summary for documentation
    csv_rows = []
    for r in results:
        for i, month in enumerate(r["months"]):
            csv_rows.append({
                "strategy": r["strategy"],
                "month": month,
                "failures": r["failures"][i],
                "sla_breaches": r["sla_breaches"][i],
                "cost": r["costs"][i],
            })

    csv_df = pd.DataFrame(csv_rows)
    csv_path = os.path.join(OUTPUT_DIR, "simulation_results.csv")
    csv_df.to_csv(csv_path, index=False)
    print(f"CSV saved to {csv_path}")

    print("\nSimulation complete.")
    return output_json


if __name__ == "__main__":
    main()