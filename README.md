## Academic ERP Leave Management API

### Run the backend

```bash
uv sync --extra dev
uv run uvicorn main:app --reload
```

Open the interactive API documentation at `http://127.0.0.1:8000/docs`.

The detailed frontend integration contract is in [FRONTEND_API.md](FRONTEND_API.md).

### Authentication

Set these Supabase values in `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-public-anon-key
SUPABASE_JWT_SECRET=your-project-jwt-secret
SUPABASE_JWT_AUDIENCE=authenticated
```

Available endpoints:

```text
POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Signup request:

```json
{
	"email": "employee@example.com",
	"password": "at-least-8-characters",
	"employee_id": 101
}
```

Signup intentionally requires an existing active employee. The email must match
the employee record, then the new Supabase user is linked to that employee with
the `EMPLOYEE` role. Department Head and Admin roles should be assigned by an
administrator in `user_role`.

Login returns a Supabase access token. Send it on protected requests:

```http
Authorization: Bearer <access_token>
```

The local development fallback user is used only when no bearer token is sent
and `ENVIRONMENT=development`. A supplied token is always validated.
