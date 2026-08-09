# FastAPI: Best Practices

## Routers & Route Design
- Split routes into **APIRouter** instances, one per resource. Mount all routers in a central `main.py` — never define routes directly on the `FastAPI()` app instance.
- Use meaningful HTTP methods: `GET` for reads, `POST` for creates, `PUT`/`PATCH` for updates, `DELETE` for deletes. Don't use `POST` for everything.
- Version your API from day one: prefix routers with `/api/v1/`.
- Return the correct HTTP status code: `201` for creates, `204` for deletes with no body, `422` is automatic for validation errors.

```python
# Good
router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    payload: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserResponse:
    return await user_repo.create(payload)
```

## Dependency Injection
- Use `Depends()` for everything that crosses request boundaries: database connections/repositories, authenticated user contexts, pagination params, feature flags.
- Abstract storage and authentication dependencies behind clean dependency functions. Avoid tightly coupling route handlers to specific storage engines or identity providers.
- Chain dependencies: a `get_current_user` dependency can validate tokens and return a standardized user context without hardcoding database models into authentication.

```python
# core/dependencies.py
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserContext:
    try:
        payload = verify_external_token(credentials.credentials)
        return UserContext(
            id=payload["sub"],
            email=payload.get("email"),
            roles=payload.get("roles", []),
        )
    except TokenValidationError as e:
        raise HTTPException(status_code=401, detail=str(e))
```

## Database Access & Flexibility (SQL vs. NoSQL)
FastAPI is database-agnostic. Projects can use relational databases (PostgreSQL, MySQL via SQLAlchemy 2.x or SQLModel) or NoSQL databases (MongoDB via Motor/Beanie, Google Cloud Firestore, AWS DynamoDB).

### Architecture & Repository Pattern
- Decouple route handlers from database access using a Service or Repository layer.
- Router handlers accept schemas and dependency-injected repository or service objects, making storage backends swappable and easily mockable in tests.

### SQL Guidelines (SQLAlchemy 2.x Async)
- Always use `async with async_session_factory() as session:` — never the sync `Session`.
- Use the 2.x `select()` construct, not the legacy `.query()` ORM API.
- Use `session.execute(select(Model)...)` and call `.scalars().all()` or `.scalar_one_or_none()`.
- Use `session.scalar(select(Model)...)` for single-row fetches.
- **Database Indexes:** Add indexes proactively (`mapped_column(..., index=True)` or `Index(...)` in `__table_args__`).

```python
# SQL Repository pattern with SQLAlchemy 2.x async
class SQLUserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
```

### NoSQL Guidelines (MongoDB / Document DBs / Key-Value)
- Use asynchronous drivers or ODMs, such as **Motor** / **Beanie** for MongoDB or official async client libraries for Firestore / DynamoDB.
- Manage client connections and connection pools inside FastAPI's `lifespan` context manager (`asynccontextmanager`).
- Define document schemas using Pydantic-backed classes (e.g. `beanie.Document`).

```python
# NoSQL Repository pattern with Motor/Beanie (MongoDB)
class MongoUserRepository:
    async def get_by_email(self, email: str) -> UserDocument | None:
        return await UserDocument.find_one(UserDocument.email == email)
```

## Pydantic v2 Schemas
- Use Pydantic models as request/response schemas — never pass raw dicts across the API boundary.
- Separate schemas by intent: `UserCreate` (input), `UserResponse` (output), `UserUpdate` (partial input). Don't reuse one schema for all three.
- Use `model_config = ConfigDict(from_attributes=True)` on response schemas so they can be constructed directly from ORM/Document objects.
- Use `model_validator` and `field_validator` for cross-field validation instead of custom logic in route handlers.

```python
from pydantic import BaseModel, ConfigDict, EmailStr

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    is_active: bool
```

## Error Handling
- Raise `HTTPException` for expected, client-facing errors (404, 403, 409). Include a descriptive `detail` string.
- Register a global exception handler for unexpected errors — log the full traceback and return a generic `500` response. Never leak stack traces to clients.
- Use custom exception classes for domain errors; catch them in a middleware or exception handler and convert to `HTTPException`.

```python
@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

## Security & Authentication (Local & External IDPs)
FastAPI applications support both self-hosted local authentication (password hashing + OAuth2 local tokens) and external Identity Providers (e.g., **Google Cloud Identity Platform / Firebase Auth**, **Auth0**, Okta, Keycloak).

### Guidelines for External IDPs (Google Cloud Identity Platform, Auth0, etc.)
- Use `HTTPBearer` (via `fastapi.security.HTTPBearer`) to extract Bearer tokens from incoming `Authorization` headers.
- Validate tokens against the external provider's public key / JSON Web Key Set (JWKS).
- Cache JWKS public keys locally (e.g. using `PyJWT`'s `PyJWKClient`) to avoid network requests on every API call.
- Verify token parameters: issuer (`iss`), audience (`aud`), expiration (`exp`), and signature algorithms (typically `RS256`).
- Map validated claims (such as `sub`/`uid`, `email`, `roles`, or tenant info) to a clean, decoupled `UserContext` schema.

```python
# core/security.py — External IDP token validation (Auth0 / GCIP)
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security_scheme = HTTPBearer()

class UserContext(BaseModel):
    user_id: str
    email: str | None = None
    roles: list[str] = []

# JWKS client automatically caches keys
jwks_client = PyJWKClient("https://YOUR_DOMAIN.auth0.com/.well-known/jwks.json")

def verify_external_jwt(token: str) -> dict:
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="https://api.yourdomain.com",
            issuer="https://YOUR_DOMAIN.auth0.com/",
        )
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
        )

async def get_current_user_context(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> UserContext:
    payload = verify_external_jwt(credentials.credentials)
    return UserContext(
        user_id=payload["sub"],
        email=payload.get("email"),
        roles=payload.get("https://yourdomain.com/roles", []),
    )
```

### Self-Hosted / Local Password Auth
- For local user management, extract credentials using `OAuth2PasswordBearer(tokenUrl="token")`.
- Hash passwords with **bcrypt** via `passlib` or `pwdlib`. Never store plaintext passwords.
- Sign local JWTs with a strong asymmetric or symmetric secret (`HS256` / `RS256`) and validate expiration.

### General Security
- Never store secrets in source code — use environment variables loaded via `pydantic-settings`.
- Set `CORS` origins explicitly — never use `allow_origins=["*"]` in production.

## Background Tasks & Async
- Use FastAPI's `BackgroundTasks` for fire-and-forget work that doesn't need a result (sending emails, webhooks).
- For heavy or long-running work, use a task queue (Celery, ARQ, or Dramatiq) — don't block the event loop.
- Never mix sync and async code without care: calling a blocking I/O function inside an `async def` route will block the entire event loop. Use `run_in_executor` or make the dependency sync.

## Testing
- Use `pytest` with `pytest-asyncio` for async test functions.
- Use `httpx.AsyncClient` with `ASGITransport` for integration tests — it runs the full ASGI stack without a real server.
- Mock external auth services / JWKS endpoints or override the `get_current_user_context` dependency in tests using `app.dependency_overrides`.
- For database tests, use dedicated test fixtures (in-memory SQLite, test container PostgreSQL, or test MongoDB database) and clean state between tests.

```python
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.dependencies import get_current_user_context
from app.core.security import UserContext

@pytest.fixture
def mock_user_override():
    async def _override():
        return UserContext(user_id="test_user_123", email="test@example.com", roles=["admin"])

    app.dependency_overrides[get_current_user_context] = _override
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_protected_route(mock_user_override):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/profile")
    assert response.status_code == 200
    assert response.json()["user_id"] == "test_user_123"
```

