import { defineRailway, github, group, postgres, preserve, project, redis, service } from "railway/iac";

export default defineRailway((ctx) => {
  const production = ctx.environment === "production";
  const database = postgres("BloomAI PostgreSQL");
  const cache = redis("BloomAI Redis");
  const marketplaceApi = service("Marketplace API", {
    source: github("kadedipe/BloomAI-Global-Marketplace", { branch: "main", rootDirectory: "services/marketplace-api" }),
    healthcheck: "/health/ready",
    replicas: 1,
    env: { ENVIRONMENT: production ? "production" : "staging", DATABASE_URL: database.env.DATABASE_URL, REDIS_URL: cache.env.REDIS_URL, JWT_SECRET: preserve(), CORS_ORIGINS: preserve() },
  });
  const aiApi = service("AI Inference API", {
    source: github("kadedipe/BloomAI-Global-Marketplace", { branch: "main", rootDirectory: "services/ai-api" }),
    healthcheck: "/health/ready",
    env: {
      ENVIRONMENT: production ? "production" : "staging",
      MODEL_PATH: "/app/models/mobilenet_v3_small_flowers102.pth",
      MODEL_GDRIVE_FILE_ID: "1CfPnSgK_UYa71EZQwve1nrxtYK1Edb60",
      MODEL_SHA256: "9ee2f29556562a14a666ad8345b850b7aa11d26dc2e73b16a735d4d33b515dc9",
      CORS_ORIGINS: preserve(),
    },
  });
  const eventWorker = service("Event Worker", {
    source: github("kadedipe/BloomAI-Global-Marketplace", { branch: "main", rootDirectory: "services/event-worker" }),
    env: { REDIS_URL: cache.env.REDIS_URL, LOG_LEVEL: "INFO" },
  });
  const web = service("BloomAI Web", {
    source: github("kadedipe/BloomAI-Global-Marketplace", { branch: "main", rootDirectory: "apps/web" }),
    healthcheck: "/",
    env: { VITE_API_URL: preserve(), VITE_AI_API_URL: preserve() },
  });
  const backend = group("Backend", [database, cache, marketplaceApi, aiApi, eventWorker]);
  return project("BloomAI Global Marketplace", { resources: [backend, web] });
});
