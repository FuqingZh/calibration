def select_for(change_area: str) -> str:
    if change_area in {"validation", "dependencies", "harness"}:
        return "focused_test"
    return "focused_test"
