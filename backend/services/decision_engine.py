"""Decision engine: builds the human-readable explanation (Explainable AI)."""


def build_explanation(shipment_id: str, risk_level: str, risk_score: float,
                      factors: list, best: dict, second_best: dict = None,
                      totals: dict = None) -> str:
    """Compose bullet-point reasoning shown on the dashboard."""
    lines = [f"Decision for {shipment_id}: {best['action']} (risk {risk_level} {risk_score}/100).",
             "Reason:"]
    for f in factors[:6]:
        lines.append(f"- {f}")
    lines.append(f"- {best['action']} reduces expected delay to {best['delay']:.1f} days "
                 f"at transport cost Rs {best['transport_cost']:,.0f}.")
    if best.get("penalty", 0) == 0 and totals and totals.get("penalty", 0) > 0:
        lines.append(f"- It avoids an estimated contract penalty of Rs {totals['penalty']:,.0f}.")
    if second_best:
        lines.append(f"- It scored {best['score']:,.0f} vs next-best "
                     f"'{second_best['action']}' ({second_best['score']:,.0f}) on cost/delay/risk.")
    return "\n".join(lines)
