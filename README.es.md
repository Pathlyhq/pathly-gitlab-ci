# Componentes GitLab CI/CD Pathly

[English](README.md) · [Français](README.fr.md) · **Español**


[![Powered by Pathly](https://img.shields.io/badge/Powered%20by-Pathly-0B5FFF?style=flat-square)](https://pathlyhq.com)
[![Website](https://img.shields.io/badge/Website-pathlyhq.com-111827?style=flat-square)](https://pathlyhq.com)
[![API docs](https://img.shields.io/badge/API-developers-2563eb?style=flat-square)](https://pathlyhq.com/es/developers)
[![Start free](https://img.shields.io/badge/Solo-start%20free-16a34a?style=flat-square)](https://pathlyhq.com/es/login?mode=signup)

> **Empiece en un clic.** Cree una cuenta gratuita en [Pathly](https://pathlyhq.com) ([registro](https://pathlyhq.com/es/login?mode=signup)), genere una clave API en la consola y exporte `PATHLY_API_TOKEN`. Este repositorio es el puente oficial hacia [la monitorización Pathly](https://pathlyhq.com): comprobaciones HTTP y de navegador (carrito, login, disponibilidad), con datos en la UE. Referencia API: [pathlyhq.com/es/developers](https://pathlyhq.com/es/developers).

[Componentes CI/CD de GitLab](https://docs.gitlab.com/ee/ci/components/) reutilizables para añadir visibilidad de monitoreo [Pathly](https://pathlyhq.com) a sus pipelines.

**Autor:** Simon Raynaud / keyral · **Empresa:** [Pathly](https://pathlyhq.com)

> La versión en inglés ([`README.md`](README.md)) es la canónica.

## Componentes

| Componente | Propósito |
|------------|-----------|
| `pathly-ping` | Verifica `PATHLY_API_TOKEN` con `GET /v1/usage` (403 = ok) |
| `pathly-scenario` | Crea o asegura un escenario HTTP por nombre |

Las plantillas están en [`templates/`](./templates/). Los helpers en [`scripts/`](./scripts/) tienen cobertura unitaria al 100 %.

## Inclusión

```yaml
include:
  - remote: https://raw.githubusercontent.com/Pathlyhq/pathly-gitlab-ci/v0.1.0/templates/pathly-ping.yml
    inputs:
      stage: test
  - remote: https://raw.githubusercontent.com/Pathlyhq/pathly-gitlab-ci/v0.1.0/templates/pathly-scenario.yml
    inputs:
      stage: deploy
      scenario_name: "Inicio producción"
      scenario_url: "https://www.ejemplo.com/"
      interval_sec: "300"
```

Las plantillas son autónomas (no se descarga ningún archivo de este repositorio en la ejecución), así que `include: remote` funciona desde cualquier instancia de GitLab. Fije una etiqueta de release en la URL (`v0.1.0` arriba), nunca `main`. Para usarlas como componentes CI/CD, copie este repositorio en su propia instancia de GitLab e incluya `component: $CI_SERVER_FQDN/<grupo>/pathly-gitlab-ci/pathly-ping@<versión>`.

Defina la variable CI/CD **enmascarada** `PATHLY_API_TOKEN` (`sp_…`) en Ajustes → CI/CD → Variables. Nunca haga commit del token.

Ejemplo completo: [`examples/.gitlab-ci.yml`](./examples/.gitlab-ci.yml).

## Entradas (pathly-scenario)

| Entrada | Por defecto | Descripción |
|---------|-------------|-------------|
| `scenario_url` | *(obligatoria)* | URL HTTPS pública a monitorear |
| `scenario_name` | `CI HTTP check` | Nombre en la consola Pathly |
| `interval_sec` | `300` | Intervalo de comprobación |
| `severity` | `major` | `minor` \| `major` \| `critical` |
| `api_url` | `https://api.pathlyhq.com` | Base de la API |
| `api_token` | `$PATHLY_API_TOKEN` | Token |

## Helpers locales

```bash
pip install -r requirements-dev.txt
pytest -q --cov=scripts --cov-fail-under=100

export PATHLY_API_TOKEN=sp_…
python scripts/pathly_cli.py ping
python scripts/pathly_cli.py ensure-scenario --scenario-json '{"name":"Inicio","url":"https://ejemplo.com/"}'
# o: sh scripts/pathly.sh ping
```

Referencia API: [desarrolladores Pathly](https://pathlyhq.com/es/developers).

## Seguridad

- Menor privilegio: `scenarios:read` / `scenarios:write`.
- Solo HTTPS hacia hosts remotos (http localhost permitido para API local).
- Las escrituras envían `Idempotency-Key`.


## Paquetes relacionados

| Package | Role |
|---|---|
| [pathly-github-action](https://github.com/pathlyhq/pathly-github-action) | GitHub Action |
| [pathly-sdk-python](https://github.com/pathlyhq/pathly-sdk-python) | Python SDK |
| [pathly-sdk-go](https://github.com/pathlyhq/pathly-sdk-go) | Go SDK |
| [pathly-postman](https://github.com/pathlyhq/pathly-postman) | Postman collection |
| [Pathly product](https://pathlyhq.com) | [Pathly monitoring](https://pathlyhq.com) |
## Acerca de Pathly

[Pathly](https://pathlyhq.com) es monitorización sintética para agencias y e-commerce: reproduce el recorrido del cliente, detecta un checkout roto antes de la llamada, y deja la prueba (captura, paso, runbook) lista para la factura. Producto: [pathlyhq.com](https://pathlyhq.com) · Desarrolladores: [pathlyhq.com/es/developers](https://pathlyhq.com/es/developers) · Precios: [pathlyhq.com/es/pricing](https://pathlyhq.com/es/pricing).

## Autor

Empresa: [Pathly](https://pathlyhq.com)  
Autor: Simon Raynaud / keyral  

Ver [AUTHORS](./AUTHORS), [NOTICE](./NOTICE), [CHANGELOG](./CHANGELOG.md).

## Licencia

Apache License 2.0 — ver [LICENSE](./LICENSE).
