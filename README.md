# Electro Cupid

## Build and run

```docker compose up --build```

The app will be available on http://localhost:8080

## Rebuild

After a change to the frontend:
```docker compose build frontend```

After a change to the backend:
```docker compose build backend```

## Development mode
To avoid rebuild on every change to the frontend:

```
cd frontend
pnpm dev
```

All calls to /api/... will be proxied to the backend in the running docker container.
