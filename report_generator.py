import json
from collections import defaultdict


def generate_report(audit_file):
    stats = defaultdict(lambda: {"total": 0, "sum_score": 0, "violations": 0})

    with open(audit_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            t_type = data['tutor_type']
            score = data['audit_results']['socratic_score']
            violation = 1 if data['audit_results']['violation'].lower() == "yes" else 0

            stats[t_type]["total"] += 1
            stats[t_type]["sum_score"] += score
            stats[t_type]["violations"] += violation

    print("\n--- EDU-GUARD PEDAGOGICAL REPORT ---")
    print(f"{'Tutor Type':<25} | {'Avg Score':<10} | {'Violation Rate':<15}")
    print("-" * 55)

    for t_type, data in stats.items():
        avg = data['sum_score'] / data['total']
        v_rate = (data['violations'] / data['total']) * 100
        print(f"{t_type:<25} | {avg:<10.2f} | {v_rate:>13.1f}%")


if __name__ == "__main__":
    generate_report("data/audit_results.jsonl")