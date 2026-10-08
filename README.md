# College Lost and Found

A working secure-software-engineering lab by **Marisetti Avinash**, **CH.SC.U4CYS23024**, **Amrita Vishwa Vidyapeetham Chennai**.

Students and faculty report lost/found items, search verified reports, contact a reporter privately, reply through an inbox and mark their own item recovered. Administrators verify/remove reports and review security activity. Self-registration cannot create an administrator.

## Submission

- `deliverables/College_Lost_and_Found_Report.docx`: all sixteen phases.
- `deliverables/images/`: black-and-white diagrams and actual application screenshots.
- `deliverables/editable/`: editable draw.io models and chart data.
- `deliverables/catalog.json` and `tables/`: synchronized requirements, use cases, stories, sprints and security analysis.
- `deliverables/evidence/`: actual test, audit, Jira, container and Kubernetes records.
- Jira: [CLF24 Scrum board](https://mavinash.atlassian.net/jira/software/c/projects/CLF24/boards/236).

The two nominal fifteen-day sprint plans are 8–23 October and 23 October–7 November 2026, at 09:00 Asia/Kolkata. Execution and Jira transitions are a compressed lab demonstration. Forecast charts are not historical observations.

## Run locally on Windows

From this directory, with Python 3.12 available:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.lock
.\.venv\Scripts\python.exe scripts/setup_local.py
$localDemo = Get-Content .local-secrets.json -Raw | ConvertFrom-Json
$env:APP_SECRET = $localDemo.APP_SECRET
.\.venv\Scripts\python.exe app.py
```

Open [the local application](http://127.0.0.1:8090). This loopback development server is for the local lab. Use the Docker/Gunicorn TLS deployment for secure communication. The ignored `.local-secrets.json` holds randomly generated demo login credentials; inspect it privately to sign in. Do not include it or `.env` in your submission or Git.

For this Codex workspace, the prepared runtime also supports:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_local.ps1
```

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

GitHub Actions is configured in `.github/workflows/ci.yml`. Local equivalent pipeline evidence is retained; a hosted Actions run requires a GitHub remote and is not invented. Intended workflow: a short feature branch, reviewed pull request, passing checks, then main; configure hosted protected branches when publishing a remote.

## Jira synchronization

`scripts/jira_sync.py` reads `JIRA_URL`, `JIRA_EMAIL` and `JIRA_TOKEN` from process environment. It never stores the token. Current Jira IDs are in the evidence state; do not rerun setup with stale state because this can create duplicates. The dedicated project has six epics, sixteen stories, sixteen subtasks and two fifteen-day plans. Only Marisetti Avinash is assigned.

## Stop the lab

```powershell
docker compose stop
```

Stop any `kubectl port-forward` terminal with Ctrl+C. The application, source, data volumes and evidence are retained. Deleting the lab cluster or volumes is a separate destructive operation and is not needed to stop the application.
