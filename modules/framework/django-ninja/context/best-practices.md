# Django Ninja: Best Practices

## API Design
- **Routers over Global API:** Use `NinjaRouter` for feature-specific endpoints and mount them to a main `NinjaAPI` instance in `config/urls.py` or a central `api.py`.
- **Pydantic Schemas:** Always use Pydantic schemas for request and response validation. Avoid using raw dictionaries.
- **Type Safety:** Leverage Python type hints for all endpoint parameters to ensure automatic validation and OpenAPI documentation generation.
- **Error Handling:** Use Django Ninja's built-in exception handlers for common errors (e.g., 404, validation errors).

## Database Flexibility & Data Layer (SQL & NoSQL)
Django Ninja is database-agnostic. Projects can use Django ORM (relational/SQL), alternative async ORMs, or NoSQL databases (e.g., MongoDB, Firestore, DynamoDB). Do not assume a relational database or Django ORM is always present.

- **Relational Databases (Django ORM / SQL):**
  - **Async Integration:** When using `async def` endpoints with Django ORM, wrap sync ORM calls using `asgiref.sync.sync_to_async` or use Django's native async ORM methods (`aget()`, `afirst()`, `acreate()`, `aexists()`, etc.).
  - **Query Optimization:** Use `select_related()` and `prefetch_related()` on ORM querysets to avoid N+1 issues. Ensure index definitions (`db_index=True` or `Meta.indexes`) match frequent query filters.
- **NoSQL Databases (MongoDB, Firestore, DynamoDB):**
  - **Direct Async Drivers:** Use native async drivers (e.g., `motor` for MongoDB, `google-cloud-firestore` async client, or `aioboto3` for DynamoDB) directly inside `async def` endpoints. These bypass the need for `sync_to_async`.
  - **Document Modeling:** Map NoSQL documents to Pydantic schemas for serialization and validation.
  - **Indexing & Projections:** Create proper index specs on database collections/containers and use field projections to minimize payload size and query latency.

## Authentication & External IDP Integration
Django Ninja supports custom security handlers via `HttpBearer`, `APIKeyHeader`, or `HttpBasicAuth`.

- **External Identity Providers (Google Cloud Identity Platform, Auth0, etc.):**
  - Custom authentication handlers should intercept incoming Bearer tokens, verify the JWT (checking signature via JWKS, issuer, audience, and expiration), and extract user metadata.
  - Return the parsed payload or domain user object from `authenticate(request, token)`. Django Ninja automatically attaches this return value to `request.auth`.
- **Scoped Router Authentication:**
  - Apply authentication to specific `NinjaRouter` instances (`router = NinjaRouter(auth=FirebaseAuth())`) or individual endpoints rather than enforcing a single global auth strategy across the entire API.

### Custom HttpBearer Implementation Pattern
```python
import jwt
from jwt import PyJWKClient
from django_ninja import NinjaRouter
from django_ninja.security import HttpBearer
from django_ninja.errors import HttpError

class ExternalIdpBearerAuth(HttpBearer):
    def __init__(self, jwks_url: str, issuer: str, audience: str):
        super().__init__()
        self.jwks_client = PyJWKClient(jwks_url)
        self.issuer = issuer
        self.audience = audience

    def authenticate(self, request, token: str):
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience,
            )
            # request.auth will be set to this returned object
            return {
                "uid": payload.get("sub"),
                "email": payload.get("email"),
                "roles": payload.get("roles", []),
            }
        except jwt.PyJWTError as e:
            # Returning None or raising HttpError triggers a 401 Unauthorized response
            raise HttpError(401, f"Invalid or expired token: {str(e)}")

# Router-scoped authentication setup
auth_handler = ExternalIdpBearerAuth(
    jwks_url="https://YOUR_DOMAIN/.well-known/jwks.json",
    issuer="https://YOUR_DOMAIN/",
    audience="https://api.yourdomain.com",
)

protected_router = NinjaRouter(auth=auth_handler)

@protected_router.get("/profile")
def get_profile(request):
    # Access authenticated user payload extracted by HttpBearer
    user_info = request.auth
    return {"uid": user_info["uid"], "email": user_info["email"]}
```

## Performance & Concurrency
- **Async Endpoints:** Use `async def` for endpoints performing external network I/O (e.g., API calls, external IDP token fetching) or using async DB drivers. Use standard `def` for CPU-bound tasks or synchronous ORM queries to let Django handle thread pooling automatically.
- **Pagination:** Use Django Ninja's built-in pagination wrappers (`@router.get("/", response=List[ItemOut], pagination=...)`) for lists of items, adapting limit/offset or cursor parameters to the underlying SQL or NoSQL database.
