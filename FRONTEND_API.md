# Frontend API Integration Guide

This document is the integration contract for the React frontend of the Academic ERP Leave Management API.

It describes the API that is currently implemented in this repository. Do not invent endpoint names, fields, or status values in the frontend. Use the contracts below exactly.

## 1. Local Development

Start the backend from the repository root:

```powershell
uv sync --extra dev
uv run uvicorn main:app --reload
```

Base URL:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

All application endpoints are under:

```text
/api/v1
```

The frontend should keep the base URL in one environment variable rather than scattering URLs through components:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Example API client setup:

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(response.status, body?.detail ?? "Request failed", body);
  }

  return body as T;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public body: unknown,
  ) {
    super(message);
  }
}
```

## 2. Authentication Model

Supabase Auth owns passwords, sessions, access tokens, email confirmation, and refresh tokens. The FastAPI backend owns the relationship between a Supabase user and an ERP employee.

The backend does not accept a frontend-created employee ID as an authenticated identity. It gets the user ID from the verified JWT, then resolves:

```text
Supabase JWT sub
    -> user_account.user_id
    -> employee.employee_id
    -> user_role.role
```

### Required request header

Every protected request must include the current Supabase access token:

```http
Authorization: Bearer <access_token>
```

Do not send the refresh token as the bearer token. Do not send a password to any endpoint except `/auth/login` and `/auth/signup`.

### Token storage

Prefer the Supabase client SDK session storage and its automatic refresh behavior. Do not put access or refresh tokens in application state that is logged, persisted in arbitrary local storage, or sent to the backend as JSON.

When the access token expires:

1. Let the Supabase client refresh the session.
2. Retry the original request once with the new access token.
3. If refresh fails, clear the session and redirect to login.
4. Never retry a failed login or signup request automatically.

## 3. Auth Endpoints

### 3.1 Create user: `POST /auth/signup`

Creates a Supabase user and links that user to an existing active ERP employee.

This is an employee self-registration flow, not unrestricted user creation.

#### Preconditions

- The `employee_id` already exists in `employee`.
- The employee status is `ACTIVE`.
- The email exactly matches the employee email, ignoring case.
- The email is not already registered in Supabase.
- The email is not already linked in `user_account`.

#### Request

```json
{
  "email": "employee@example.com",
  "password": "at-least-8-characters",
  "employee_id": 101
}
```

Field rules:

| Field | Type | Required | Rules |
|---|---|---:|---|
| `email` | string | yes | Valid email format; must match the employee record |
| `password` | string | yes | 8 to 72 characters |
| `employee_id` | integer | yes | Greater than zero; must refer to an active employee |

#### Successful response: `201 Created`

If Supabase email confirmation is disabled:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_id": "8f4c0000-0000-0000-0000-000000000001",
  "requires_email_confirmation": false
}
```

If email confirmation is enabled, Supabase may return no access token:

```json
{
  "access_token": null,
  "refresh_token": null,
  "token_type": "bearer",
  "expires_in": null,
  "user_id": "8f4c0000-0000-0000-0000-000000000001",
  "requires_email_confirmation": true
}
```

Frontend behavior:

- If `requires_email_confirmation` is `true`, show a confirmation-email screen.
- Do not call protected endpoints yet.
- After confirmation, send the user through Supabase login and store the returned session.
- If an access token is present, treat signup as an authenticated session.

#### Common errors

| Status | Meaning | Frontend action |
|---:|---|---|
| `400` | Invalid signup data or Supabase rejected the request | Show the returned `detail` near the form |
| `404` | Active employee does not exist | Ask the user to contact administration |
| `409` | Email does not match employee or account already linked | Do not retry blindly; show account-linking message |
| `422` | Request failed Pydantic validation | Highlight invalid fields |
| `502` | Supabase returned an unusable response | Show temporary service error and allow retry |
| `503` | Auth configuration or Supabase service unavailable | Show service unavailable state |

### 3.2 Login: `POST /auth/login`

Authenticates through Supabase email/password authentication.

#### Request

```json
{
  "email": "employee@example.com",
  "password": "the-user-password"
}
```

#### Successful response: `200 OK`

```json
{
  "access_token": "eyJ...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_id": "8f4c0000-0000-0000-0000-000000000001",
  "requires_email_confirmation": false
}
```

The frontend should use the returned session through the Supabase client when possible. If the frontend calls this API directly, it must securely retain both tokens and refresh before expiry.

#### Common errors

- `401`: incorrect credentials or Supabase rejected the login.
- `422`: email or password field failed validation.
- `503`: Supabase Auth is not configured or unreachable.
- `502`: Supabase returned an unexpected response.

Do not distinguish “email does not exist” from “password is wrong” in custom UI messages unless the backend explicitly provides that distinction. Generic login failure messages avoid account enumeration.

### 3.3 Logout: `POST /auth/logout`

Requires a valid bearer token.

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

Response:

```json
{
  "message": "Logged out successfully."
}
```

The backend currently treats Supabase access tokens as stateless JWTs. The frontend must also call the Supabase client sign-out operation and clear all local user/session state.

### 3.4 Current auth identity: `GET /auth/me`

Requires a valid bearer token.

Response:

```json
{
  "user_id": "8f4c0000-0000-0000-0000-000000000001",
  "employee_id": 101,
  "roles": ["EMPLOYEE"]
}
```

Use this endpoint after application startup or session restoration to determine whether the backend recognizes the Supabase user. Do not infer authorization from frontend route names or editable client state.

## 4. Employee Endpoints

### 4.1 Profile: `GET /me/profile`

Requires authentication.

Response:

```json
{
  "employee_id": 101,
  "employee_code": "EMP001",
  "first_name": "Rahul",
  "last_name": "Sharma",
  "email": "employee@example.com",
  "department_id": 3,
  "designation": "Assistant Professor"
}
```

Possible responses:

- `200`: profile returned.
- `401`: token missing, invalid, or expired.
- `403`: token is valid but not linked to an active ERP employee.
- `404`: linked employee profile no longer exists.

### 4.2 Leave balance: `GET /me/leave-balance`

Requires authentication.

Response:

```json
[
  {
    "leave_type_id": 1,
    "leave_type": "Casual Leave",
    "entitled": 12,
    "carry_forward": 2,
    "used": 8,
    "remaining": 6
  }
]
```

The calculation is:

```text
remaining = entitled + carry_forward - used
```

Only `TAKEN` leave records count toward `used`. Pending applications do not reduce this balance.

The current academic year uses a June-to-May cycle:

- June 1, 2026 through May 31, 2027 is `2026-27`.
- May 31, 2026 belongs to `2025-26`.

## 5. Leave Application Endpoints

### 5.1 Create application: `POST /leave-applications/`

Requires authentication. The employee is taken from the JWT; the frontend must not send `employee_id`.

#### Request

```json
{
  "leave_type_id": 1,
  "start_date": "2026-09-10",
  "end_date": "2026-09-12",
  "reason": "Personal work",
  "station_leaving": false,
  "station_name": null,
  "station_contact_number": null
}
```

Field rules:

| Field | Type | Required | Rules |
|---|---|---:|---|
| `leave_type_id` | integer | yes | Must refer to a configured leave type |
| `start_date` | `YYYY-MM-DD` | yes | Inclusive start date |
| `end_date` | `YYYY-MM-DD` | yes | Must be on or after `start_date` |
| `reason` | string/null | no | Optional |
| `station_leaving` | boolean | no | Defaults to `false` |
| `station_name` | string/null | no | Must be null when `station_leaving` is false |
| `station_contact_number` | string/null | no | Must be null when `station_leaving` is false |

The current implementation calculates requested and calculated days as inclusive calendar days. Academic-calendar exclusions are not yet applied in this endpoint.

#### Successful response: `200 OK`

```json
{
  "application_id": 10025,
  "employee_id": 101,
  "leave_type_id": 1,
  "start_date": "2026-09-10",
  "end_date": "2026-09-12",
  "requested_days": 3,
  "calculated_days": 3,
  "status": "PENDING_DEPARTMENT_HEAD",
  "submitted_at": "2026-09-07T10:30:00Z"
}
```

#### Frontend rules

- Disable duplicate submission while the request is in flight.
- On success, replace the form with the returned server object.
- Never calculate or submit `requested_days`, `calculated_days`, `status`, or `employee_id`.
- Treat the backend response as the source of truth.
- Do not deduct the application from balance until Admin approval creates a leave record.

### 5.2 My applications: `GET /leave-applications/my`

Requires authentication.

Optional filter:

```text
GET /api/v1/leave-applications/my?status=PENDING_ADMIN
```

Response:

```json
[
  {
    "application_id": 10025,
    "employee_id": 101,
    "leave_type_id": 1,
    "start_date": "2026-09-10",
    "end_date": "2026-09-12",
    "requested_days": 3,
    "calculated_days": 3,
    "status": "PENDING_ADMIN",
    "submitted_at": "2026-09-07T10:30:00Z"
  }
]
```

The current endpoint supports only the `status` query parameter. Do not send unsupported filters such as `from_date`, `to_date`, or `leave_type` until the backend adds them.

An empty list is a valid success response:

```json
[]
```

## 6. Approval Endpoints

### Status state machine

```text
PENDING_DEPARTMENT_HEAD
    -> PENDING_ADMIN          HOD approves
    -> DEPARTMENT_REJECTED    HOD rejects

PENDING_ADMIN
    -> ADMIN_APPROVED         Admin approves
    -> ADMIN_REJECTED         Admin rejects

ADMIN_APPROVED
    -> leave_record created
    -> leave counts as used
```

Only `ADMIN_APPROVED` creates official leave usage.

### HOD queue: `GET /hod/leave-applications`

Requires a user with the `DEPARTMENT_HEAD` role.

Returns only applications in the HOD's department with status `PENDING_DEPARTMENT_HEAD`.

### HOD approve: `POST /hod/leave-applications/{application_id}/approve`

Request:

```json
{
  "comments": "Approved"
}
```

### HOD reject: `POST /hod/leave-applications/{application_id}/reject`

Request:

```json
{
  "comments": "Insufficient staffing during this period"
}
```

### Admin queue: `GET /admin/leave-applications`

Requires a user with the `ADMIN` role.

Returns only applications with status `PENDING_ADMIN`.

### Admin approve: `POST /admin/leave-applications/{application_id}/approve`

Request:

```json
{
  "comments": "Approved"
}
```

Admin approval is transactional. It records the approval, changes the application status, and creates one official `leave_record`. The database also prevents more than one leave record for an application.

### Admin reject: `POST /admin/leave-applications/{application_id}/reject`

Request:

```json
{
  "comments": "Leave balance or operational requirements do not permit approval"
}
```

### Approval error handling

| Status | Meaning |
|---:|---|
| `401` | Missing or invalid bearer token |
| `403` | User lacks the required role |
| `404` | Application does not exist |
| `409` | Application is no longer in the expected pending state |
| `422` | Comments payload is invalid |

A `409` is expected when two reviewers act on the same application at nearly the same time. The frontend should refresh the queue and show the current state instead of retrying the same decision.

## 7. TypeScript Types

Use types equivalent to the backend schemas:

```ts
export type Role = "EMPLOYEE" | "DEPARTMENT_HEAD" | "ADMIN";

export type LeaveApplicationStatus =
  | "PENDING_DEPARTMENT_HEAD"
  | "PENDING_ADMIN"
  | "DEPARTMENT_REJECTED"
  | "ADMIN_APPROVED"
  | "ADMIN_REJECTED"
  | "CANCELLED";

export interface AuthResponse {
  access_token: string | null;
  refresh_token: string | null;
  token_type: "bearer";
  expires_in: number | null;
  user_id: string | null;
  requires_email_confirmation: boolean;
}

export interface EmployeeProfile {
  employee_id: number;
  employee_code: string;
  first_name: string;
  last_name: string | null;
  email: string;
  department_id: number;
  designation: string | null;
}

export interface LeaveBalance {
  leave_type_id: number;
  leave_type: string;
  entitled: number;
  carry_forward: number;
  used: number;
  remaining: number;
}

export interface LeaveApplication {
  application_id: number;
  employee_id: number;
  leave_type_id: number;
  start_date: string;
  end_date: string;
  requested_days: number;
  calculated_days: number;
  status: LeaveApplicationStatus;
  submitted_at: string;
}
```

## 8. Recommended Frontend Startup Flow

```text
1. Initialize Supabase client.
2. Read the Supabase session.
3. If no session exists, display login/signup.
4. If a session exists, call GET /auth/me.
5. If /auth/me returns 401, refresh the Supabase session once.
6. If refresh fails, sign out and display login.
7. Load /me/profile and /me/leave-balance in parallel.
8. Use returned roles to select the dashboard.
9. Never grant access based only on a frontend route or local role value.
```

Recommended request sequence after login:

```ts
const session = await supabase.auth.getSession();
const accessToken = session.data.session?.access_token;

const me = await apiRequest<{ user_id: string; employee_id: number; roles: string[] }>(
  "/auth/me",
  { headers: { Authorization: `Bearer ${accessToken}` } },
);
```

## 9. Error Normalization

FastAPI errors generally have this shape:

```json
{
  "detail": "Human-readable error message"
}
```

Validation errors have this shape:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "abc"
    }
  ]
}
```

The frontend should:

- Handle `detail` as either a string or an array.
- Display field-specific messages when `loc` contains `body` and a field name.
- Display a generic fallback when the response is not JSON.
- Never display raw stack traces to users.
- Log request IDs if request-ID middleware is added later, but never log passwords or tokens.

## 10. Important Current Limitations

The following features are described in the larger system design but are not yet implemented in the current API:

- Refresh-token endpoint in FastAPI. Use the Supabase client SDK refresh flow.
- Password reset endpoint.
- Email verification endpoint.
- Application detail endpoint: `/leave-applications/{id}`.
- Leave types endpoint.
- Alerts endpoint.
- Attachments endpoint.
- Calendar-aware leave-day calculation.
- Pagination on queues and application history.
- Admin employee-management endpoints.
- Frontend application itself.

The frontend should hide or disable UI for these features until their endpoints are added. Do not call undocumented routes and do not assume that a successful HOD approval means leave usage has changed.

## 11. Security Checklist

- Use HTTPS outside local development.
- Keep `SUPABASE_ANON_KEY` in frontend environment configuration only if using the Supabase client; it is public by design but must not be confused with the service-role key.
- Never expose `SUPABASE_JWT_SECRET` or `SUPABASE_SERVICE_ROLE_KEY` to the frontend.
- Never commit `.env` files.
- Send access tokens only in the `Authorization` header.
- Do not send access tokens in query parameters or URLs.
- Clear session state on logout and invalid refresh.
- Treat all role and balance values returned by the backend as server-owned data.
