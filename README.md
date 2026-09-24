# Pathly GitLab CI/CD Components

**English** · [Français](README.fr.md) · [Español](README.es.md)


[![Powered by Pathly](https://img.shields.io/badge/Powered%20by-Pathly-0B5FFF?style=flat-square)](https://pathlyhq.com)
[![Website](https://img.shields.io/badge/Website-pathlyhq.com-111827?style=flat-square)](https://pathlyhq.com)
[![API docs](https://img.shields.io/badge/API-developers-2563eb?style=flat-square)](https://pathlyhq.com/en/developers)
[![Start free](https://img.shields.io/badge/Solo-start%20free-16a34a?style=flat-square)](https://pathlyhq.com/en/login?mode=signup)

> **Get started in one click.** Create a free account on [Pathly](https://pathlyhq.com) ([sign up](https://pathlyhq.com/en/login?mode=signup)), create an API key in the console, then export `PATHLY_API_TOKEN`. This project is the official bridge to [Pathly monitoring](https://pathlyhq.com) — real-browser and HTTP checks for checkout, login and availability, with data hosted in the EU. Full API reference: [pathlyhq.com/en/developers](https://pathlyhq.com/en/developers).

Reusable [GitLab CI/CD Components](https://docs.gitlab.com/ee/ci/components/) to add [Pathly](https://pathlyhq.com) monitoring visibility to your pipelines.

[Developers (EN)](https://pathlyhq.com/en/developers) · [Développeurs (FR)](https://pathlyhq.com/fr/developers) · [pathlyhq.com](https://pathlyhq.com)

> English is the default / canonical documentation language.

**Author:** Simon Raynaud / keyral · **Company:** [Pathly](https://pathlyhq.com)

## Components

| Component | Purpose |
|-----------|---------|
| `pathly-ping` | Verify `PATHLY_API_TOKEN` against `GET /v1/usage` (403 = ok) |
| `pathly-scenario` | Create or ensure an HTTP scenario by name |

Templates live under [`templates/`](./templates/). Helpers under [`scripts/`](./scripts/) are unit-tested at 100% coverage.

## Include

```yaml
include:
  - component: $CI_SERVER_FQDN/pathlyhq/pathly-gitlab-ci/pathly-ping@~latest
    inputs:
      stage: test
  - component: $CI_SERVER_FQDN/pathlyhq/pathly-gitlab-ci/pathly-scenario@~latest
    inputs:
      stage: deploy
      scenario_name: "Production home"
      scenario_url: "https://www.example.com/"
      interval_sec: "300"
```

Pin a version tag instead of `~latest` in production (for example `@1.0.0`).

Set a **masked** CI/CD variable `PATHLY_API_TOKEN` (`sp_…`) under Settings → CI/CD → Variables. Never commit the token.

Full sample: [`examples/.gitlab-ci.yml`](./examples/.gitlab-ci.yml).

## Inputs (pathly-scenario)

| Input | Default | Description |
|-------|---------|-------------|
| `scenario_url` | *(required)* | Public HTTPS URL to monitor |
| `scenario_name` | `CI HTTP check` | Name in the Pathly console |
| `interval_sec` | `300` | Check interval |
| `severity` | `major` | `minor` \| `major` \| `critical` |
| `api_url` | `https://api.pathlyhq.com` | API base |
| `api_token` | `$PATHLY_API_TOKEN` | Token |

## Local helpers

```bash
pip install -r requirements-dev.txt
pytest -q --cov=scripts --cov-fail-under=100

export PATHLY_API_TOKEN=sp_…
python scripts/pathly_cli.py ping
python scripts/pathly_cli.py ensure-scenario --scenario-json '{"name":"Home","url":"https://example.com/"}'
# or: sh scripts/pathly.sh ping
```

API reference: [Pathly developers](https://pathlyhq.com/en/developers).

## Security

- Least privilege scopes: `scenarios:read` / `scenarios:write`.
- HTTPS only toward remote hosts (localhost http allowed for local API).
- Writes send `Idempotency-Key`.


## Related packages

| Package | Role |
|---|---|
| [pathly-github-action](https://github.com/pathlyhq/pathly-github-action) | GitHub Action |
| [pathly-sdk-python](https://github.com/pathlyhq/pathly-sdk-python) | Python SDK |
| [pathly-sdk-go](https://github.com/pathlyhq/pathly-sdk-go) | Go SDK |
| [pathly-postman](https://github.com/pathlyhq/pathly-postman) | Postman collection |
| [Pathly product](https://pathlyhq.com) | [Pathly monitoring](https://pathlyhq.com) |
## About Pathly

[Pathly](https://pathlyhq.com) is synthetic monitoring for agencies and e-commerce: replay the customer journey, catch broken checkouts before your clients call, and keep evidence (screenshot, step, runbook) ready for the invoice. Product: [pathlyhq.com](https://pathlyhq.com) · Developers: [pathlyhq.com/en/developers](https://pathlyhq.com/en/developers) · Status & pricing: [pathlyhq.com/en/pricing](https://pathlyhq.com/en/pricing).

## Author

Company: [Pathly](https://pathlyhq.com)  
Author: Simon Raynaud / keyral  

See [AUTHORS](./AUTHORS), [NOTICE](./NOTICE), [CHANGELOG](./CHANGELOG.md).

## License

Apache License 2.0 — see [LICENSE](./LICENSE).
