# Campus Lost and Found

[![Secure build and package](https://github.com/MAvinash24/Campus-Lost-and-Found/actions/workflows/ci.yml/badge.svg)](https://github.com/MAvinash24/Campus-Lost-and-Found/actions/workflows/ci.yml)

A working secure-software-engineering lab by **Marisetti Avinash**, **CH.SC.U4CYS23024**, **Amrita Vishwa Vidyapeetham Chennai**.

Students and faculty report lost/found items, search verified reports, contact a reporter privately, reply through an inbox and mark their own item recovered. Administrators verify/remove reports and review security activity. Self-registration cannot create an administrator.

The academic reports use the title **College Lost and Found**. This repository includes the application source, tests, deployment configuration, editable diagrams, reports and recorded lab evidence.

![Browse verified campus reports](deliverables/images/ui_browse.jpg)

## Features and technology

- Student and faculty registration, login and logout with hashed passwords.
- Lost/found reporting, category and location filters, and administrator moderation.
- Private reporter contact and participant-only replies.
- Creator-only recovery updates and security audit events.
- Session-bound CSRF validation, parameterized SQL, escaped templates and role checks.
- Flask, Jinja2 and SQLite; Gunicorn behind Caddy for the Docker TLS lab.
- Docker Compose, Kubernetes, GitHub Actions and local SonarQube configuration.

Browser templates call Flask routes, routes enforce authentication and authorization, and database operations use the SQLite schema. See the [security invariants](SECURITY.md) and [architecture diagram](deliverables/detailed_diagrams/08_application_architecture.svg).

## Repository contents

| Path | Contents |
| --- | --- |
| `app.py`, `wsgi.py`, `schema.sql` | Application, deployment entry point and schema |
| `templates/`, `static/` | Web pages and styles |
| `tests/` | Application and authorization tests |
| `scripts/` | Demo setup, verification, packaging, reports and analysis tools |
| `Dockerfile`, `compose.yaml`, `deploy/` | Containers, TLS and Kubernetes |
| `.github/workflows/ci.yml` | Tests, static checks, dependency audit and container build |
| `deliverables/` | Reports, screenshots, tables, editable models and evidence |
| `diagram_work/` | Diagram/report editing utilities and alternate PDF layout |
| `SONARQUBE.md` | Local analysis and coverage instructions |

Python **3.12** and Git are required for local setup. Docker Desktop with Linux containers is needed for the container lab; kind and kubectl are optional for Kubernetes. Report-generation tools use additional libraries such as Pillow, python-docx, lxml and PyMuPDF, separate from the application dependencies.

## Submission

- `deliverables/College_Lost_and_Found_Report.docx`: all sixteen phases.
- `deliverables/images/`: black-and-white diagrams and actual application screenshots.
- `deliverables/editable/`: editable draw.io models and chart data.
- `deliverables/catalog.json` and `tables/`: synchronized requirements, use cases, stories, sprints and security analysis.
- `deliverables/evidence/`: actual test, audit, Jira, container and Kubernetes records.
- [Updated report (PDF)](deliverables/updated_reports/College_Lost_and_Found_Report_Updated_Diagrams.pdf) and [Word report](deliverables/updated_reports/College_Lost_and_Found_Report_Updated_Diagrams.docx).
- [Detailed diagrams](deliverables/detailed_diagrams/README.md): twelve independent PNG/SVG diagrams.
- Jira: [CLF24 Scrum board](https://mavinash.atlassian.net/jira/software/c/projects/CLF24/boards/236).

The two nominal fifteen-day sprint plans are 8–23 October and 23 October–7 November 2026, at 09:00 Asia/Kolkata. Execution and Jira transitions are a compressed lab demonstration. Forecast charts are not historical observations.

## Run locally on Windows

Clone the repository and create an isolated Python environment:

```powershell
git clone https://github.com/MAvinash24/Campus-Lost-and-Found.git
cd Campus-Lost-and-Found
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.lock
.\.venv\Scripts\python.exe scripts/setup_local.py
$localDemo = Get-Content .local-secrets.json -Raw | ConvertFrom-Json
$env:APP_SECRET = $localDemo.APP_SECRET
.\.venv\Scripts\python.exe app.py
```

Open [the local application](http://127.0.0.1:8090). This loopback development server is for the local lab. Use the Docker/Gunicorn TLS deployment for secure communication. The ignored `.local-secrets.json` holds randomly generated demo login credentials; inspect it privately to sign in. Do not include it or `.env` in your submission or Git.

After first-time setup, the helper loads your generated application secret and starts the app:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_local.ps1
```

## Run locally on Linux or macOS

From the cloned repository, using Python 3.12:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python scripts/setup_local.py
export APP_SECRET="$(.venv/bin/python -c 'import json; print(json.load(open(".local-secrets.json"))["APP_SECRET"])')"
.venv/bin/python app.py
```

Open <http://127.0.0.1:8090>. Setup creates student, faculty and administrator demo accounts with random passwords in `.local-secrets.json`. Database initialization is automatic. Each deployment has its own database and must be seeded separately.

## Run Docker and TLS

Initialize `.env` and the local demo credentials with `scripts/setup_local.py` first.

```powershell
docker compose build
docker compose up -d
Get-Content .local-secrets.json -Raw | docker compose exec -T app python /app/scripts/seed_demo.py
docker compose ps
```

Open [the Docker TLS application](https://localhost:8443). The lab proxy uses its own internal CA. Browser trust must be configured by the user; do not bypass certificate warnings. Retrieve its **public** CA certificate with:

```powershell
docker compose exec -T tls cat /data/caddy/pki/authorities/local/root.crt > campus-lab-root.crt
```

The automated network test trusts this certificate only in its test process and verifies the hostname. It does not change Windows trust or turn off TLS verification. A production campus endpoint requires a valid campus/public certificate, campus identity verification, centrally revocable sessions and operational logging/backup controls.

If old Caddy volumes are root-owned after an earlier image run, initialize only their ownership (the tested deployment already did this):

```powershell
docker run --rm --user 0 --cap-drop ALL --cap-add CHOWN --entrypoint chown -v sse_caddy-data:/data -v sse_caddy-config:/config caddy:2.10.2-alpine -R 10001:10001 /data /config
```

No volume contents are deleted. The TLS image removes the upstream executable's low-port file capability because the proxy binds high port 8443 with all process capabilities dropped.

## Kubernetes lab

The completed lab uses a dedicated kind cluster named `campus-lab` and task-local kubeconfig `.tools/kubeconfig`. It does not change another cluster. To recreate with an official kind installation:

```powershell
kind create cluster --name campus-lab --kubeconfig .tools/kubeconfig
kind load docker-image campus-lost-found:1.0.0 campus-tls:1.0.0 --name campus-lab
$env:KUBECONFIG = (Resolve-Path .tools/kubeconfig).Path
kubectl apply -f deploy/kubernetes.yaml
kubectl create secret generic campus-secret -n campus-lost-found --from-env-file=.env --dry-run=client -o json | kubectl apply -f -
kubectl rollout status deployment/campus-app -n campus-lost-found --timeout=180s
Get-Content .local-secrets.json -Raw | kubectl exec -i deployment/campus-app -n campus-lost-found -c app -- python /app/scripts/seed_demo.py
kubectl port-forward --address 127.0.0.1 -n campus-lost-found svc/campus-app 18443:8443
```

Open [the Kubernetes TLS application](https://localhost:18443) after trusting that deployment's public lab CA. The app and TLS sidecar are both non-root with read-only root filesystems, dropped capabilities and limits. The app service is ClusterIP, credentials are in a Secret, and storage uses PVCs. Default kind networking does **not** prove NetworkPolicy enforcement; use a network-policy-capable CNI and test it before production.

Docker, Kubernetes and local demonstrations use separate private data stores and the same application source and demo identities. Their test records can differ. No production deployment is claimed.

## Verify

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip install bandit==1.9.4 pip-audit==2.10.1 requests
.\.venv\Scripts\python.exe -m bandit -r app.py wsgi.py scripts/bootstrap.py
.\.venv\Scripts\python.exe scripts/check_security.py
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
.\.venv\Scripts\python.exe scripts/network_e2e.py https://localhost:8443 deliverables/evidence/campus-lab-root.crt docker
```

GitHub Actions runs on pushes to `main` and pull requests. Check the [Actions page](https://github.com/MAvinash24/Campus-Lost-and-Found/actions) for the current hosted result. Evidence files describe recorded local lab runs and do not establish a new hosted run's status. Use feature branches, reviewed pull requests and passing checks for future changes; configure protected branches in repository settings.

## Jira synchronization

`scripts/jira_sync.py` reads `JIRA_URL`, `JIRA_EMAIL` and `JIRA_TOKEN` from process environment. It never stores the token. Current Jira IDs are in the evidence state; do not rerun setup with stale state because this can create duplicates. The dedicated project has six epics, sixteen stories, sixteen subtasks and two fifteen-day plans. Only Marisetti Avinash is assigned.

## SonarQube security analysis

The project is configured for the existing local SonarQube project `College-Lost-and-Found`. See [SONARQUBE.md](SONARQUBE.md) for scanner verification, masked token input, test coverage, quality gates, security hotspots and before/after issue snapshots. Run `scripts/sonar-scan.ps1`; analysis evidence stays in the ignored `.sonar-evidence` directory.

## Stop the lab

```powershell
docker compose stop
```

Stop any `kubectl port-forward` terminal with Ctrl+C. The application, source, data volumes and evidence are retained. Deleting the lab cluster or volumes is a separate destructive operation and is not needed to stop the application.

## Troubleshooting and publication scope

- `APP_SECRET` error: run setup and load the generated secret using the startup commands above.
- Login failure: use your own `.local-secrets.json`; local, Docker and Kubernetes databases must each be seeded.
- Certificate warning: retrieve the public Caddy CA certificate and configure trust for this local lab before signing in over HTTPS.
- Port conflict: stop the other listener or change the matching port mapping and URL.

Runtime dependencies, databases, `.env`, generated credentials, private keys, scanner installations and temporary reference-report extracts are excluded from Git. Reports, screenshots, diagrams, tables and evidence are included. These academic records retain the limitations they state; production campus identity, logging and operations remain future work.

Some optional report-editing and analysis utilities retain Windows paths from the original authoring environment. Adapt those paths before regenerating artifacts; they are not needed to run the application. No redistribution license has been selected.
