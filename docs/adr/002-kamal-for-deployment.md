# ADR 002: Kamal for Deployment

- **Status:** Accepted
- **Deciders:** [Team Name]
- **Date:** 2024-04-22

## Context and Problem Statement
We need a robust, simple, and cloud-agnostic way to deploy our containerized application.

## Decision Drivers
- **Simplicity:** Avoiding the complexity of Kubernetes for small to medium-sized projects.
- **Zero-Downtime:** Ensuring application availability during deployments.
- **Cloud-Agnostic:** Not being locked into a specific vendor's platform.
- **Infrastructure as Code (IaC):** Version-controlled deployment configuration.

## Considered Options
1.  **Kamal (formerly MRSK):** Uses Docker and SSH to deploy to any Linux server.
2.  **Kubernetes (K8s):** The industry standard for container orchestration at scale.
3.  **Managed PaaS (Heroku, Render, Fly.io):** Easy to use but often more expensive and comes with platform lock-in.

## Decision Outcome
**Kamal** was chosen for its simplicity and "no-nonsense" approach. It provides zero-downtime deployments by managing Docker containers directly via SSH, without requiring a complex control plane like Kubernetes.

### Positive Consequences
- Low operational overhead.
- Simple, versioned configuration in `config/deploy.yml`.
- Works on any basic virtual private server (VPS).

### Negative Consequences
- Requires some server management knowledge compared to a fully managed PaaS.
- Less built-in scaling logic than Kubernetes (though easy to scale vertically).
