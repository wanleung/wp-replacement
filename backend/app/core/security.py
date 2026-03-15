"""
WordPress phpass-compatible password verification + JWT helpers.
WordPress uses phpass (MD5-based iterated hashing) with the prefix $P$ or $H$.
"""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from app.config import settings

# ---------------------------------------------------------------------------
# phpass (WordPress) password verification
# ---------------------------------------------------------------------------

_ITOA64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _encode64(data: bytes, count: int) -> str:
    output = []
    i = 0
    while i < count:
        value = data[i]
        i += 1
        output.append(_ITOA64[value & 0x3F])
        if i < count:
            value |= data[i] << 8
        output.append(_ITOA64[(value >> 6) & 0x3F])
        if i >= count:
            break
        i += 1
        if i < count:
            value |= data[i] << 16
        output.append(_ITOA64[(value >> 12) & 0x3F])
        if i >= count:
            break
        i += 1
        output.append(_ITOA64[(value >> 18) & 0x3F])
    return "".join(output)


def wp_check_password(password: str, stored_hash: str) -> bool:
    """Verify a plain-text password against a WordPress hash."""
    if stored_hash.startswith("$P$") or stored_hash.startswith("$H$"):
        iter_char = stored_hash[3]
        if iter_char not in _ITOA64:
            return False
        iterations = 1 << _ITOA64.index(iter_char)
        salt = stored_hash[4:12]

        pw_bytes = password.encode("utf-8")
        hash_val = hashlib.md5((salt + password).encode("utf-8")).digest()
        for _ in range(iterations):
            hash_val = hashlib.md5(hash_val + pw_bytes).digest()

        computed = stored_hash[:12] + _encode64(hash_val, 16)
        return computed == stored_hash

    # Legacy WordPress plain MD5
    if len(stored_hash) == 32:
        return hashlib.md5(password.encode("utf-8")).hexdigest() == stored_hash

    return False


# ---------------------------------------------------------------------------
# Password hashing for new users (bcrypt via passlib)
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a new password using bcrypt (stored as $2b$...)."""
    return pwd_context.hash(password)


def verify_password(plain: str, stored: str) -> bool:
    """Try WordPress phpass first, then fallback to bcrypt."""
    if stored.startswith("$P$") or stored.startswith("$H$") or len(stored) == 32:
        return wp_check_password(plain, stored)
    # WordPress 6.8+ wraps bcrypt with a $wp$ prefix — replace $wp$ with $ before verifying
    if stored.startswith("$wp$"):
        stored = "$" + stored[4:]
    # Normalize PHP/WordPress $2y$ bcrypt variant to $2b$ for passlib compatibility
    if stored.startswith("$2y$"):
        stored = "$2b$" + stored[4:]
    try:
        return pwd_context.verify(plain, stored)
    except UnknownHashError:
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def create_access_token(subject: str | int, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(subject), "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None
