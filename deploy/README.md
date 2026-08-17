# Deployment configuration (GitOps via Flux)

This folder contains everything **Flux** needs to deploy the application to Bedag's Kubernetes platform. No pipeline talks to the cluster directly: GitHub Actions only updates the image tag in the stage values files, Flux watches this repo and applies the change.

| Environment | Values file | Read by Flux from branch |
|---|---|---|
| **test** | `stages/test/geo-metadata-engine/values.yaml` | `develop` |
| **prod** | `stages/prod/geo-metadata-engine/values.yaml` | `main` |

## Layout

```
stages/
├── base/    # shared config: HelmRelease (Bedag "common" chart) + shared values
├── test/    # test overrides: hostname, image tag, env vars, patches, secrets
└── prod/    # prod overrides: same layout as test
```

Secrets (`secrets/secret-values.yaml` per stage) are SOPS-encrypted with the public key `.sops.pub.asc`. Never commit plain-text secrets — this repo is public.

## Full documentation

- [Deployment](https://github.com/kanton-bern/geo-metadata-engine/wiki/Deployment) — how Flux, the values layering and the secrets work
- [GitHub Actions Workflows](https://github.com/kanton-bern/geo-metadata-engine/wiki/GitHub-Actions-Workflows) — how images are built and how a deployment is triggered
