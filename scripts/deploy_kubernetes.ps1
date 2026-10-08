$ErrorActionPreference = 'Stop'
$clusterConfig = Join-Path $PSScriptRoot '../.tools/kubeconfig'
$env:KUBECONFIG = $clusterConfig
.tools/kind.exe load docker-image campus-tls:1.0.0 --name campus-lab
kubectl apply -f deploy/kubernetes.yaml
if ($LASTEXITCODE -ne 0) { throw 'Manifest application failed' }
# Pipe the generated secret directly; do not print it or write a Secret YAML.
kubectl create secret generic campus-secret --namespace campus-lost-found --from-env-file=.env --dry-run=client -o json | kubectl apply -f -
kubectl rollout status deployment/campus-app -n campus-lost-found --timeout=180s
if ($LASTEXITCODE -ne 0) { throw 'Kubernetes rollout failed' }
Get-Content .local-secrets.json -Raw | kubectl exec -i deployment/campus-app -n campus-lost-found -c app -- python /app/scripts/seed_demo.py
kubectl get pods,svc,pvc,networkpolicy -n campus-lost-found -o wide
kubectl get deployment campus-app -n campus-lost-found -o json | Set-Content -Encoding UTF8 deliverables/evidence/kubernetes-deployment.json
kubectl get pods -n campus-lost-found -o json | Set-Content -Encoding UTF8 deliverables/evidence/kubernetes-pods.json
kubectl exec deployment/campus-app -n campus-lost-found -c tls -- cat /data/caddy/pki/authorities/local/root.crt | Set-Content -Encoding ASCII deliverables/evidence/kubernetes-lab-root.crt
