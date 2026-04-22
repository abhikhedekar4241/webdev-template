# Deployment

This project uses **Kamal** for zero-downtime deployments to any VPS.

## Prerequisites

- A server with Docker installed.
- SSH access to the server.
- A Docker registry (e.g., Docker Hub, GitHub Packages).

## Initial Setup

1. Install Kamal:
   `gem install kamal`
2. Configure your secrets in `.env.deploy`.
3. Run setup:
   `kamal setup`

## Deploying

Simply run:
`kamal deploy`

This will:
1. Build the Docker images locally (or on a remote builder).
2. Push them to the registry.
3. Pull them onto the server.
4. Start the new containers and run health checks.
5. Swap the traffic to the new containers and stop the old ones.
