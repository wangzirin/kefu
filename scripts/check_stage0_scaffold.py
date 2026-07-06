#!/usr/bin/env python3
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "README.md",
    ".env.example",
    "backend/pyproject.toml",
    "backend/requirements.txt",
    "backend/Dockerfile",
    "backend/app/main.py",
    "backend/app/api/health.py",
    "backend/app/api/auth.py",
    "backend/app/core/config.py",
    "backend/app/db/base.py",
    "backend/app/models/foundation.py",
    "backend/app/migrations/env.py",
    "backend/app/migrations/versions/0001_foundation.py",
    "frontend/package.json",
    "frontend/index.html",
    "frontend/vite.config.ts",
    "frontend/src/App.tsx",
    "frontend/src/main.tsx",
    "frontend/src/styles.css",
    "deploy/docker-compose.yml",
    "evals/standard_questions.csv",
    "evals/promptfoo.config.yaml",
]


def fail(message: str) -> None:
    print(f"FAIL stage0 scaffold: {message}")
    sys.exit(1)


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing files: " + ", ".join(missing))

    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    for dep in ["react", "react-dom", "vite", "typescript"]:
        if dep not in deps:
            fail(f"frontend dependency missing: {dep}")

    backend_requirements = (ROOT / "backend/requirements.txt").read_text(encoding="utf-8")
    for dep in ["fastapi", "uvicorn", "sqlalchemy", "alembic", "redis"]:
        if dep not in backend_requirements:
            fail(f"backend dependency missing: {dep}")

    compose = (ROOT / "deploy/docker-compose.yml").read_text(encoding="utf-8")
    for service in ["postgres", "redis", "backend", "frontend"]:
        if f"{service}:" not in compose:
            fail(f"compose service missing: {service}")

    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    forbidden_fragments = ["sk-", "Bearer ", "xoxb-", "AKIA"]
    for fragment in forbidden_fragments:
        if fragment in env_example:
            fail(f"possible secret in .env.example: {fragment}")

    print("PASS stage0 scaffold")


if __name__ == "__main__":
    main()
