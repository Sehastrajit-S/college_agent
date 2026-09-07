def build_notes(overview: str, steps: list) -> str:
    lines = []
    if overview:
        lines.append(overview)
    if steps:
        lines.append("")
        lines.append("What needs to be done:")
        for step in steps:
            lines.append(f"☐ {step}")
    return "\n".join(lines)
