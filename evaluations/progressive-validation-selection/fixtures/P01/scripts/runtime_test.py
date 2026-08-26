from check_event import run


def check() -> None:
    if "release:stable".split(":", 1) != ["release", "stable"]:
        raise ValueError("sample parser contract failed")


run("runtime_test", "runtime-parser", check)
