# Django: Best Practices

## Data Access: ORM (SQL) & NoSQL Flexibility

Django applications can use standard relational databases via the Django ORM, non-relational (NoSQL) databases (e.g., MongoDB, Google Cloud Firestore, AWS DynamoDB), or a hybrid of both.

### Relational Databases & Django ORM
- **Fat models/services, thin views.** Business logic belongs in model methods, managers, or a dedicated `services.py` — not in views.
- Use **custom managers** to encapsulate common querysets:

```python
class ActiveUserManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(is_active=True)

class User(AbstractUser):
    active = ActiveUserManager()
```

- Always use `select_related()` for `ForeignKey`/`OneToOneField` traversals and `prefetch_related()` for `ManyToManyField`/reverse FKs to avoid N+1 queries.
- Never call `.all()` in a view without a subsequent `.filter()` or `.select_related()`.
- Use `.only()` or `.defer()` to exclude heavy fields (e.g., large `TextField`) when full objects aren't needed.
- Wrap multi-step DB operations in `transaction.atomic()`.

```python
from django.db import transaction

@transaction.atomic
def transfer_credits(sender: User, recipient: User, amount: int) -> None:
    sender.credits = models.F("credits") - amount
    recipient.credits = models.F("credits") + amount
    sender.save(update_fields=["credits"])
    recipient.save(update_fields=["credits"])
```

- **Database Indexes:** Always evaluate query patterns and add indexes for performance.
  - Use `db_index=True` on fields that are frequently used in `.filter()`, `.exclude()`, or `order_by()`.
  - Use `class Meta: indexes = [...]` for composite indexes (filtering on multiple columns together) or when using specific index types (e.g., `GinIndex`, `BrinIndex`).
  - Avoid creating indexes on low-cardinality fields (like `BooleanField`) unless the data is highly skewed.
  - Remember that `unique=True` and `ForeignKey` automatically create an index.

### NoSQL & Non-Relational Databases (MongoDB, Firestore, DynamoDB)
Django projects are not restricted to relational databases or the Django ORM alone. When project requirements call for document, key-value, or graph storage:
- **Client & ODM Choice:** Use official Python client SDKs (e.g., `PyMongo`, `google-cloud-firestore`, `boto3`) or Object Document Mappers (ODMs like `mongoengine`, `bunnet`, `beanie`) directly.
- **Service Layer Abstraction:** Encapsulate all NoSQL queries inside dedicated `services.py` or repository classes. Views and serializers must interact with Python dataclasses, dicts, or Pydantic schemas — never leak driver-specific objects (like BSON `ObjectId` or Firestore `DocumentSnapshot`) directly into view logic.
- **Document Validation:** Validate document structures at API boundaries using Pydantic or ODM models prior to persisting to NoSQL collections.
- **Atomic Operations:** Use database-native session/transaction mechanisms (e.g., `client.start_session()` in PyMongo or `db.transaction()` in Firestore) when multi-document consistency is required.

---

## External Authentication & Identity Providers (IDP)

When integrating external identity providers (such as **Google Cloud Identity Platform**, **Auth0**, **Firebase Auth**, or **Okta**), Django applications should rely on token-based verification (JWTs) instead of session cookies or basic database password authentication.

### Token Validation & DRF Authentication Backends
For Django REST Framework APIs, create a custom authentication backend inheriting from `rest_framework.authentication.BaseAuthentication`. Validate incoming JWTs against the provider's JWKS (JSON Web Key Set) endpoint.

```python
import jwt
from jwt import PyJWKClient
from rest_framework import authentication, exceptions
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class ExternalJWTAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication backend for external Identity Providers (Auth0, Google Cloud Identity Platform, etc.).
    """
    def __init__(self):
        self.jwks_client = PyJWKClient(settings.IDP_JWKS_URL)

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.IDP_AUDIENCE,
                issuer=settings.IDP_ISSUER,
            )
        except jwt.PyJWTError as e:
            raise exceptions.AuthenticationFailed(f"Invalid external token: {str(e)}")

        user = self.get_or_map_user(payload)
        return (user, token)

    def get_or_map_user(self, payload: dict):
        external_id = payload.get("sub")
        email = payload.get("email", "")

        if not external_id:
            raise exceptions.AuthenticationFailed("Token payload missing subject ('sub') claim.")

        # Pattern A: Map claim to a persistent Django DB User
        user, _ = User.objects.get_or_create(
            username=external_id,
            defaults={"email": email, "is_active": True},
        )
        return user
```

### Claim Mapping Patterns
- **DB-Backed User Mapping (Pattern A):** Use `User.objects.get_or_create(username=payload['sub'])` to sync external IDP claims (`sub`, `email`, `name`, `roles`) into Django's user table. This enables standard Django permissions (`user.has_perm()`) and foreign key relationships.
- **Lightweight / Stateless User Mapping (Pattern B):** For microservices or stateless APIs where local DB persistence is unnecessary or user data resides in a NoSQL store, construct a lightweight, non-persisted user object:

```python
class StatelessUser:
    """Lightweight user representation for stateless APIs authenticated by external IDPs."""
    def __init__(self, payload: dict):
        self.id = payload.get("sub")
        self.email = payload.get("email", "")
        self.roles = payload.get("roles", [])
        self.is_authenticated = True
        self.is_anonymous = False
        self.is_active = True

    def __str__(self) -> str:
        return f"StatelessUser({self.email or self.id})"
```

### Standard Django Auth Backend (Sessions / Admin)
To support standard Django views or admin access with external IDP tokens, implement a custom authentication backend inheriting from `django.contrib.auth.backends.BaseBackend`:

```python
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class ExternalIDPBackend(BaseBackend):
    def authenticate(self, request, token=None, **kwargs):
        if not token:
            return None
        # Validate JWT and map payload to User instance...
        payload = verify_external_token(token)
        if not payload:
            return None
        user, _ = User.objects.get_or_create(username=payload["sub"], defaults={"email": payload.get("email", "")})
        return user if user.is_active else None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
```

Register custom backends in `settings.py`:
```python
AUTHENTICATION_BACKENDS = [
    "apps.users.auth.ExternalIDPBackend",
    "django.contrib.auth.backends.ModelBackend",  # Fallback for local/admin accounts
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.users.auth.ExternalJWTAuthentication",
    ],
}
```

---

## Views
- Use **Class-Based Views** for standard CRUD operations — they reduce boilerplate and are easily extended.
- Use **Function-Based Views** for simple, one-off endpoints or when CBV mixins make the code harder to follow.
- Use `get_object_or_404(Model, pk=pk)` instead of try/except `ObjectDoesNotExist` in views.
- Never put queryset logic directly in the view — delegate to the model manager or a service function.

---

## Django REST Framework (APIs)
- Use `ModelSerializer` for standard CRUD serializers; override only what differs.
- Use `Serializer` (or Pydantic models) when working with non-ORM data sources or NoSQL documents.
- Use `ViewSet` + `Router` for full CRUD resources; `APIView` for custom endpoints.
- Always declare `permission_classes` and `authentication_classes` explicitly on every view — don't rely on global defaults alone.
- Validate all input with serializers at the API boundary. Never trust `request.data` directly.

```python
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("profile").filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExternalJWTAuthentication]

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.user.organization)
```

---

## Security
- Never store secrets in source code or `settings.py` — use environment variables via `django-environ` or `python-decouple`.
- Always set `ALLOWED_HOSTS`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, and `CSRF_COOKIE_SECURE` in production settings.
- Use Django's built-in CSRF protection for cookie/session auth; for JWT auth APIs, ensure tokens are transmitted over TLS via Bearer authorization headers.
- Avoid `raw()` and `extra()` queryset methods; if raw SQL is necessary, use parameterized queries only.

---

## Testing
- Use `pytest-django` with `@pytest.mark.django_db` rather than `unittest.TestCase`.
- Use **factories** (`factory_boy`) instead of fixtures for test data — they're more maintainable and composable.
- Test at three levels: unit (model methods, service functions), integration (view + DB/NoSQL), and API (serializer + endpoint with `APIClient`).
- Use `--reuse-db` in local development to speed up test runs; always create fresh DB in CI.

### Testing External Auth & NoSQL
- **Mock IDP Token Validation:** Use `unittest.mock.patch` to mock `PyJWKClient` and `jwt.decode` in API tests so unit/integration tests do not perform external network calls.
- **Testing NoSQL Services:** Mock the NoSQL client driver (e.g. `unittest.mock.MagicMock(spec=pymongo.MongoClient)`) or test against local containers/emulators (e.g. MongoDB Docker container, Firestore Emulator).

```python
from unittest.mock import patch
import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
@patch("apps.users.auth.jwt.decode")
@patch("apps.users.auth.PyJWKClient.get_signing_key_from_jwt")
def test_external_auth_success(mock_key, mock_decode):
    mock_decode.return_value = {"sub": "ext_123", "email": "user@example.com"}
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer valid-idp-jwt-token")
    
    response = client.get("/api/users/me/")
    assert response.status_code == 200
    assert response.data["email"] == "user@example.com"
```

---

## Signals
- Keep signal handlers thin — they should call a service function, not contain logic themselves.
- Register signals in an `AppConfig.ready()` method, not at module level.
- Avoid signals for anything you can accomplish with model `save()` overrides or `post_save` in a service — signals are harder to trace.

