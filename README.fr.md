# Composants GitLab CI/CD Pathly

[English](README.md) · **Français** · [Español](README.es.md)


[![Powered by Pathly](https://img.shields.io/badge/Powered%20by-Pathly-0B5FFF?style=flat-square)](https://pathlyhq.com)
[![Website](https://img.shields.io/badge/Website-pathlyhq.com-111827?style=flat-square)](https://pathlyhq.com)
[![API docs](https://img.shields.io/badge/API-developers-2563eb?style=flat-square)](https://pathlyhq.com/fr/developers)
[![Start free](https://img.shields.io/badge/Solo-start%20free-16a34a?style=flat-square)](https://pathlyhq.com/fr/login?mode=signup)

> **Démarrage en un clic.** Créez un compte gratuit sur [Pathly](https://pathlyhq.com) ([inscription](https://pathlyhq.com/fr/login?mode=signup)), générez une clé API dans la console, puis exportez `PATHLY_API_TOKEN`. Ce dépôt est le pont officiel vers [la surveillance Pathly](https://pathlyhq.com) — contrôles HTTP et parcours navigateur (panier, connexion, disponibilité), données hébergées dans l’UE. Référence API : [pathlyhq.com/fr/developers](https://pathlyhq.com/fr/developers).

[Composants CI/CD GitLab](https://docs.gitlab.com/ee/ci/components/) réutilisables pour ajouter la visibilité monitoring [Pathly](https://pathlyhq.com) à vos pipelines.

[Développeurs (FR)](https://pathlyhq.com/fr/developers) · [Developers (EN)](https://pathlyhq.com/en/developers) · [pathlyhq.com](https://pathlyhq.com)

> La version anglaise ([`README.md`](README.md)) fait référence.

**Auteur :** Simon Raynaud / keyral · **Société :** [Pathly](https://pathlyhq.com)

## Composants

| Composant | Rôle |
|-----------|------|
| `pathly-ping` | Vérifie `PATHLY_API_TOKEN` via `GET /v1/usage` (403 = ok) |
| `pathly-scenario` | Crée ou garantit un scénario HTTP par nom |

Modèles dans [`templates/`](./templates/). Helpers dans [`scripts/`](./scripts/), tests à 100 % de couverture.

## Inclusion

```yaml
include:
  - remote: https://raw.githubusercontent.com/Pathlyhq/pathly-gitlab-ci/v0.1.0/templates/pathly-ping.yml
    inputs:
      stage: test
  - remote: https://raw.githubusercontent.com/Pathlyhq/pathly-gitlab-ci/v0.1.0/templates/pathly-scenario.yml
    inputs:
      stage: deploy
      scenario_name: "Accueil production"
      scenario_url: "https://www.exemple.fr/"
      interval_sec: "300"
```

Les modèles sont autonomes (aucun fichier de ce dépôt n'est téléchargé à l'exécution), donc `include: remote` fonctionne depuis toute instance GitLab. Épinglez un tag de release dans l'URL (`v0.1.0` ci-dessus), jamais `main`. Pour les utiliser comme composants CI/CD, recopiez ce dépôt dans votre propre instance GitLab et incluez `component: $CI_SERVER_FQDN/<groupe>/pathly-gitlab-ci/pathly-ping@<version>`.

Définir la variable CI/CD **masquée** `PATHLY_API_TOKEN` (`sp_…`) dans Paramètres → CI/CD → Variables. Ne jamais committer le jeton.

Exemple complet : [`examples/.gitlab-ci.yml`](./examples/.gitlab-ci.yml).

## Entrées (pathly-scenario)

| Entrée | Défaut | Description |
|--------|--------|-------------|
| `scenario_url` | *(requis)* | URL HTTPS publique à surveiller |
| `scenario_name` | `CI HTTP check` | Nom dans la console Pathly |
| `interval_sec` | `300` | Intervalle de contrôle |
| `severity` | `major` | `minor` \| `major` \| `critical` |
| `api_url` | `https://api.pathlyhq.com` | Base de l’API |
| `api_token` | `$PATHLY_API_TOKEN` | Jeton |

## Helpers locaux

```bash
pip install -r requirements-dev.txt
pytest -q --cov=scripts --cov-fail-under=100

export PATHLY_API_TOKEN=sp_…
python scripts/pathly_cli.py ping
python scripts/pathly_cli.py ensure-scenario --scenario-json '{"name":"Accueil","url":"https://exemple.fr/"}'
# ou : sh scripts/pathly.sh ping
```

Référence API : [développeurs Pathly](https://pathlyhq.com/fr/developers).

## Sécurité

- Moindre privilège : `scenarios:read` / `scenarios:write`.
- HTTPS obligatoire hors localhost.
- Les écritures portent `Idempotency-Key`.


## Packages associés

| Package | Role |
|---|---|
| [pathly-github-action](https://github.com/pathlyhq/pathly-github-action) | GitHub Action |
| [pathly-sdk-python](https://github.com/pathlyhq/pathly-sdk-python) | Python SDK |
| [pathly-sdk-go](https://github.com/pathlyhq/pathly-sdk-go) | Go SDK |
| [pathly-postman](https://github.com/pathlyhq/pathly-postman) | Postman collection |
| [Pathly product](https://pathlyhq.com) | [Pathly monitoring](https://pathlyhq.com) |
## À propos de Pathly

[Pathly](https://pathlyhq.com) surveille les parcours clients des agences et e-commerçants : rejoue le tunnel, détecte un checkout cassé avant l’appel du client, et joint la preuve (capture, étape, consigne) à la facture de maintenance. Produit : [pathlyhq.com](https://pathlyhq.com) · Développeurs : [pathlyhq.com/fr/developers](https://pathlyhq.com/fr/developers) · Tarifs : [pathlyhq.com/fr/pricing](https://pathlyhq.com/fr/pricing).

## Auteur

Société : [Pathly](https://pathlyhq.com)  
Auteur : Simon Raynaud / keyral  

Voir [AUTHORS](./AUTHORS), [NOTICE](./NOTICE), [CHANGELOG](./CHANGELOG.md).

## Licence

Apache License 2.0 — voir [LICENSE](./LICENSE).
