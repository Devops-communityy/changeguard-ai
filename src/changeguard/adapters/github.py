import httpx

from changeguard.domain.models import ChangeContext, ChangedFile


class GitHubAdapter:
    def __init__(self, token: str, repository: str) -> None:
        self.repository = repository
        self.client = httpx.Client(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10.0,
        )

    def pull_request(self, number: int) -> ChangeContext:
        pull = self.client.get(f"/repos/{self.repository}/pulls/{number}")
        pull.raise_for_status()
        files = self.client.get(f"/repos/{self.repository}/pulls/{number}/files")
        files.raise_for_status()
        payload = pull.json()
        changed_files = [
            ChangedFile(
                path=item["filename"],
                additions=item["additions"],
                deletions=item["deletions"],
                patch=item.get("patch", ""),
            )
            for item in files.json()
        ]
        services = sorted(
            {
                item.path.split("/")[1]
                for item in changed_files
                if item.path.startswith("services/") and len(item.path.split("/")) > 2
            }
        )
        return ChangeContext(
            repository=self.repository,
            commit_sha=payload["head"]["sha"],
            pull_request=number,
            author=payload["user"]["login"],
            title=payload["title"],
            files=changed_files,
            services=services,
        )

    def close(self) -> None:
        self.client.close()
