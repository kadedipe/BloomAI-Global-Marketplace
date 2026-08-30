# Railway deployment

This directory uses Railway's current project-level Infrastructure as Code format.

```bash
npm --prefix .railway install
railway login
railway link
railway config plan
railway config apply
```

Set `JWT_SECRET`, `CORS_ORIGINS`, `VITE_API_URL`, and `VITE_AI_API_URL` when prompted. Generate public domains for the web and both APIs. Keep PostgreSQL, Redis, and Event Worker private.
