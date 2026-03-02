"""Authentication Service"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from skillpilot.core.config import settings
from skillpilot.core.models.auth import Token, TokenPayload
from skillpilot.core.models.common import UserRole
from skillpilot.core.models.user import User
from skillpilot.core.utils.logger import get_logger
from skillpilot.core.utils.validators import validate_password_strength
from skillpilot.db.seekdb import seekdb_client

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: str, email: str, role: UserRole, permissions: list) -> str:
        """Create JWT access token"""
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "permissions": permissions,
            "exp": expire,
            "type": "access",
            "iat": datetime.now(UTC),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh",
            "iat": datetime.now(UTC),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> TokenPayload | None:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            return TokenPayload(
                sub=payload.get("sub"),
                email=payload.get("email"),
                role=UserRole(payload.get("role", "free")),
                permissions=payload.get("permissions", []),
            )
        except JWTError as e:
            logger.warning("Token decode failed", error=str(e))
            return None

    async def register(self, email: str, password: str, name: str | None = None) -> User:
        """Register a new user"""
        # Validate password strength
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_msg)

        # Check if email already exists
        existing = await seekdb_client.query("users", filters={"email": email}, limit=1)
        if existing:
            logger.warning("Registration attempt with existing email", email=email)
            raise ValueError("Email already registered")

        user_id = f"usr_{uuid4().hex[:12]}"
        now = datetime.now(UTC)

        user_data = {
            "user_id": user_id,
            "email": email,
            "password_hash": self.hash_password(password),
            "name": name or email.split("@")[0],
            "avatar_url": None,
            "role": UserRole.FREE.value,
            "created_at": now,
        }

        await seekdb_client.insert("users", user_data)
        logger.info("User registered", user_id=user_id, email=email)

        return User(
            user_id=user_id,
            email=email,
            name=name,
            role=UserRole.FREE,
            created_at=now,
            updated_at=now,
        )

    async def login(self, email: str, password: str) -> Token:
        """Login user with email and password"""
        users = await seekdb_client.query("users", filters={"email": email}, limit=1)

        if not users:
            logger.warning("Login attempt with non-existent email", email=email)
            raise ValueError("Invalid email or password")

        user = users[0]

        if not self.verify_password(password, user["password_hash"]):
            logger.warning("Login attempt with invalid password", email=email)
            raise ValueError("Invalid email or password")

        # Update last login time
        await seekdb_client.update("users", user["user_id"], {"last_login_at": datetime.now(UTC)})

        # Generate tokens
        role = UserRole(user.get("role", "free"))
        permissions = self._get_permissions(role)

        access_token = self.create_access_token(user["user_id"], email, role, permissions)
        refresh_token = self.create_refresh_token(user["user_id"])

        logger.info("User logged in", user_id=user["user_id"], email=email)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def get_user(self, user_id: str) -> User | None:
        """Get user info by ID"""
        user_data = await seekdb_client.get("users", user_id)
        if not user_data:
            return None

        return User(
            user_id=user_data["user_id"],
            email=user_data["email"],
            name=user_data.get("name"),
            avatar_url=user_data.get("avatar_url"),
            role=UserRole(user_data.get("role", "free")),
            created_at=user_data.get("created_at", datetime.now(UTC)),
            updated_at=user_data.get("updated_at", datetime.now(UTC)),
            last_login_at=user_data.get("last_login_at"),
        )

    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        payload = self.decode_token(refresh_token)
        if not payload or payload.sub is None:
            raise ValueError("Invalid refresh token")

        # Check token type
        try:
            decoded = jwt.decode(
                refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            if decoded.get("type") != "refresh":
                raise ValueError("Invalid token type")
        except JWTError as e:
            raise ValueError("Invalid refresh token") from e

        user = await self.get_user(payload.sub)
        if not user:
            raise ValueError("User not found")

        permissions = self._get_permissions(user.role)
        access_token = self.create_access_token(user.user_id, user.email, user.role, permissions)
        new_refresh_token = self.create_refresh_token(user.user_id)

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    @staticmethod
    def _get_permissions(role: UserRole) -> list:
        """Get permissions for a given role"""
        permissions_map = {
            UserRole.FREE: ["skill:read"],
            UserRole.PERSONAL: ["skill:read", "skill:write", "orchestration:execute"],
            UserRole.ENTERPRISE: [
                "skill:read",
                "skill:write",
                "orchestration:execute",
                "analytics:read",
            ],
            UserRole.ADMIN: ["*"],
        }
        return permissions_map.get(role, [])


auth_service = AuthService()
