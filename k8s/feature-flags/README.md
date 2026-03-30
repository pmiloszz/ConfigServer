# Feature-flags Kubernetes (Kustomize)

This folder contains the Kubernetes manifests for the feature-flags application using Kustomize:

- Base: `k8s/feature-flags/base/`
- Overlays: `k8s/feature-flags/overlays/dev` and `k8s/feature-flags/overlays/prod`

## Quick apply

```bash
# Development overlay
kubectl apply -k k8s/feature-flags/overlays/dev

# Production overlay
kubectl apply -k k8s/feature-flags/overlays/prod
```

## Key services

- Backend (FastAPI): `feature-flags-api-svc` (ClusterIP, internal)
- Frontend (NGINX): `feature-flags-svc` (ClusterIP in base; dev/prod overlays patch to **LoadBalancer** — on Docker Desktop use `kubectl get svc -n feature-flags feature-flags-svc` then `http://<EXTERNAL-IP>`)

For clusters where only Ingress should be public (typical cloud prod), remove the `patch-frontend-svc-loadbalancer.yaml` patch from `overlays/prod/kustomization.yaml`.

## Notes

- The frontend NGINX config is mounted via ConfigMap (`feature-flags-nginx-config`).
- Image tags are controlled by the overlay `kustomization.yaml` (`images:` section).

