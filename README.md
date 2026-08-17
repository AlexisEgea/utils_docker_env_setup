# utils_docker_env_setup

## Docker

The Docker files are located in `infra/docker`.

### Build

From the project root directory:

```bash
docker compose -f ./infra/docker/compose.yml build
```

### Run

The application is interactive (keyboard input), so the service is configured with TTY enabled:

```bash
docker compose -f ./infra/docker/compose.yml run --rm app
```

If you specifically want to use `up`, run:

```bash
docker compose -f ./infra/docker/compose.yml up app
```

If you are using Git Bash on Windows and keyboard input does not work, use:

```bash
winpty docker compose -f ./infra/docker/compose.yml run --rm app
```

### Debug with Docker

A separate Docker Compose override file for debugging is available at `infra/docker/compose.debug.yml`.

1. Start with base + debug override:

```bash
docker compose -f ./infra/docker/compose.yml -f ./infra/docker/compose.debug.yml run --rm --service-ports app
```

2. In Cursor/VS Code, launch the configuration `Python: Debug Docker`.

### Cleanup / Purge

Remove stopped containers:

```bash
docker container prune -f
```

Remove dangling images only:

```bash
docker image prune -f
```

Remove all unused images (not just dangling):

```bash
docker image prune -a -f
```

Remove unused volumes:

```bash
docker volume prune -f
```

Global Docker cleanup (unused containers, networks, images):

```bash
docker system prune -f
```

Full purge of all unused Docker resources including volumes:

```bash
docker system prune -a --volumes -f
```

