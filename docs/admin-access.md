# BloomAI production administrator access

BloomAI deliberately does not expose public administrator registration. Production administrators are provisioned from the marketplace API service and then authenticate through the normal `/api/v1/auth/login` endpoint. The resulting HTTP-only auth cookie is the same session used by `/admin.html`.

## 1. Provision the first administrator

Set these variables on the Railway **marketplace API** service (not the web service):

- `BLOOMAI_ADMIN_EMAIL`
- `BLOOMAI_ADMIN_PASSWORD`
- `BLOOMAI_ADMIN_NAME`

Use a strong unique password. Do not put the password in a command-line argument or commit it to the repository.

Run the bootstrap command from the marketplace API service environment:

```bash
python scripts/bootstrap_admin.py
```

The command is idempotent. If the configured email already belongs to an administrator, it leaves the account unchanged. It refuses to silently promote an existing customer or vendor account.

To deliberately rotate the name/password for an existing administrator:

```bash
python scripts/bootstrap_admin.py --update-existing
```

After provisioning, remove `BLOOMAI_ADMIN_PASSWORD` from long-lived environment variables if your operational process allows it, or rotate it to a secret-management workflow. The application itself does not need this bootstrap password variable during normal runtime.

## 2. Sign in

Open the deployed web application at:

```text
/admin.html
```

If there is no valid administrator session, BloomAI now redirects to:

```text
/admin-login.html
```

Enter the provisioned administrator email and password. The login page calls the existing marketplace authentication API, verifies `/api/v1/auth/me`, confirms `role == admin`, and only then redirects to `/admin.html`.

If a customer or vendor tries to use the admin login, BloomAI clears the resulting session and denies access.

## 3. Railway configuration checks

The web service must have the same `VITE_API_URL` used by the marketplace application, pointing at the deployed marketplace API. The marketplace API must include the web origin in `CORS_ORIGINS` and run with its production JWT secret/database configuration.

The admin bootstrap command uses the service's configured `DATABASE_URL`, so run it from the marketplace API Railway service or another trusted environment that points at the same production database.

## Security properties

- Public registration still rejects the `admin` role.
- The bootstrap workflow will not elevate an existing non-admin account.
- Passwords are hashed with the application's configured password hasher before persistence.
- The browser session remains an HTTP-only authentication cookie.
- `/admin.html` verifies the current session before loading the analytics bundle.
- Backend admin endpoints continue to enforce `Role.admin`, so the frontend redirect is convenience and defense-in-depth rather than the authorization boundary.
