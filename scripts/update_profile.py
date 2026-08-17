import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

OWNER = os.environ.get("PROFILE_OWNER", "artyomliske")
README = Path("README.md")
START = "<!-- PROFILE-DATA:START -->"
END = "<!-- PROFILE-DATA:END -->"


def github_json(path: str):
    request = Request(f"https://api.github.com{path}")
    request.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def main() -> None:
    repositories = github_json(
        f"/users/{OWNER}/repos?per_page=100&sort=updated"
    )
    public_projects = [
        repo
        for repo in repositories
        if not repo.get("fork")
        and repo.get("name") not in {OWNER, f"{OWNER}.github.io"}
    ]
    latest = public_projects[0] if public_projects else None
    updated = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    lines = [
        START,
        f"> Обновлено автоматически: **{updated}**",
        "",
        f"- Публичных проектов: **{len(public_projects)}**",
    ]
    if latest:
        description = latest.get("description") or "Публичный технический проект"
        lines.append(
            f"- Последний обновлённый проект: "
            f"[{latest['name']}]({latest['html_url']}) — {description}"
        )
    lines.append(END)

    text = README.read_text(encoding="utf-8")
    replacement = "\n".join(lines)
    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        flags=re.DOTALL,
    )
    updated_text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit("README markers were not found exactly once")
    README.write_text(updated_text, encoding="utf-8")


if __name__ == "__main__":
    main()
