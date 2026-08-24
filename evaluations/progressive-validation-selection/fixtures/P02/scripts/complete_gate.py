from check_event import run


def check() -> None:
    import generate_docs
    import artifact_readback
    import docs_only


run("complete_gate", "repository-complete-gate", check)
