"""
WordPress phpass-compatible password verification + JWT helpers.
WordPress uses phpass (MD5-based iterated hashing) with the prefix $P$ or $H$.
"""
import base64
import hashlib
import hmac
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

# WordPress 6.8+ stores bcrypt hashes as '$wp' + the bcrypt string, and bcrypts a
# pre-hashed password rather than the password itself — see wp_hash_password().
_WP_BCRYPT_PREFIX = "$wp"
_WP_HMAC_KEY = b"wp-sha384"


def _wp_bcrypt_pre_hash(password: str) -> str:
    """Pre-hash a password the way WordPress 6.8+ does before handing it to bcrypt.

    base64(hmac_sha384(password, 'wp-sha384')) — a fixed 64-char digest, so
    bcrypt's 72-byte input limit can never truncate a long password.
    """
    digest = hmac.new(
        _WP_HMAC_KEY, password.encode("utf-8"), hashlib.sha384
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def hash_password(password: str) -> str:
    """Hash a new password in the WordPress 6.8+ format ($wp$2y$...).

    Written in WordPress's own format so the same hash keeps working if the site is
    ever administered through WordPress again.
    """
    # Match PHP trim() when creating hashes; verification must not trim.
    password = password.strip(" \t\n\r\x00\x0b")
    bcrypt_hash = pwd_context.hash(_wp_bcrypt_pre_hash(password))
    # WordPress writes the PHP-native $2y$ variant; passlib emits the equivalent $2b$.
    if bcrypt_hash.startswith("$2b$"):
        bcrypt_hash = "$2y$" + bcrypt_hash[4:]
    return _WP_BCRYPT_PREFIX + bcrypt_hash


def verify_password(plain: str, stored: str) -> bool:
    """Try WordPress phpass first, then fallback to bcrypt."""
    if stored.startswith("$P$") or stored.startswith("$H$") or len(stored) == 32:
        return wp_check_password(plain, stored)

    # WordPress 6.8+ bcrypt: strip the '$wp' marker and verify against the pre-hash,
    # not the raw password. Bare $2y$/$2b$ hashes predate this and verify directly.
    if stored.startswith(_WP_BCRYPT_PREFIX):
        stored = stored[len(_WP_BCRYPT_PREFIX):]
        plain = _wp_bcrypt_pre_hash(plain)

    # Normalize PHP/WordPress $2y$ bcrypt variant to $2b$ for passlib compatibility
    if stored.startswith("$2y$"):
        stored = "$2b$" + stored[4:]
    try:
        return pwd_context.verify(plain, stored)
    except (UnknownHashError, ValueError):
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
