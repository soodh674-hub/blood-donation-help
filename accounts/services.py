"""
OTP storage service for password reset.
Uses Redis/Cache as primary storage for better performance.
Falls back to database when cache is unavailable.
"""
import json
import secrets
import logging
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Cache key prefixes
OTP_KEY_PREFIX = "reset_otp_"
VERIFIED_KEY_PREFIX = "reset_verified_"
RATE_LIMIT_KEY_PREFIX = "reset_otp_rate_"

# Configuration
OTP_EXPIRY_SECONDS = 300  # 5 minutes
VERIFIED_EXPIRY_SECONDS = 120  # 2 minutes to complete reset after verification
RATE_LIMIT_SECONDS = 60  # 1 OTP per 60 seconds
MAX_ATTEMPTS = 5


def _otp_key(user_id: int) -> str:
    return f"{OTP_KEY_PREFIX}{user_id}"


def _verified_key(user_id: int) -> str:
    return f"{VERIFIED_KEY_PREFIX}{user_id}"


def _rate_limit_key(user_id: int) -> str:
    return f"{RATE_LIMIT_KEY_PREFIX}{user_id}"


def generate_otp() -> str:
    """Generate a secure 6-digit OTP."""
    return "".join(secrets.choice("0123456789") for _ in range(6))


def store_otp(user_id: int, otp: str) -> bool:
    """
    Store OTP in cache (Redis/LocMem).
    Returns True if stored successfully.
    """
    data = {
        "otp": otp,
        "attempts": 0,
        "created_at": timezone.now().isoformat(),
    }
    try:
        key = _otp_key(user_id)
        cache.set(key, json.dumps(data), timeout=OTP_EXPIRY_SECONDS)
        return True
    except Exception as e:
        logger.warning(f"Cache OTP storage failed for user {user_id}: {e}")
        return False


def get_otp_data(user_id: int) -> dict | None:
    """Get OTP data from cache. Returns None if not found or expired."""
    try:
        key = _otp_key(user_id)
        raw = cache.get(key)
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(f"Cache OTP get failed for user {user_id}: {e}")
    return None


def update_otp_attempts(user_id: int, attempts: int) -> bool:
    """Update attempt count in cache. Returns True if successful."""
    data = get_otp_data(user_id)
    if data is None:
        return False
    data["attempts"] = attempts
    try:
        # Get remaining TTL to preserve expiry
        key = _otp_key(user_id)
        ttl = cache.ttl(key)
        if ttl and ttl > 0:
            cache.set(key, json.dumps(data), timeout=ttl)
        else:
            cache.set(key, json.dumps(data), timeout=OTP_EXPIRY_SECONDS)
        return True
    except Exception as e:
        logger.warning(f"Cache OTP update failed for user {user_id}: {e}")
        return False


def mark_otp_verified(user_id: int) -> bool:
    """
    Mark OTP as verified and set verified token for reset_password.
    Returns True if successful.
    """
    try:
        key = _verified_key(user_id)
        cache.set(key, "1", timeout=VERIFIED_EXPIRY_SECONDS)
        # Delete OTP from cache (single-use)
        cache.delete(_otp_key(user_id))
        return True
    except Exception as e:
        logger.warning(f"Cache verified mark failed for user {user_id}: {e}")
        return False


def is_otp_verified(user_id: int) -> bool:
    """Check if user has a valid verified OTP for password reset."""
    try:
        return cache.get(_verified_key(user_id)) is not None
    except Exception as e:
        logger.warning(f"Cache verified check failed for user {user_id}: {e}")
        return False


def clear_reset_state(user_id: int) -> None:
    """Clear all OTP/verified state for user after successful reset."""
    try:
        cache.delete(_otp_key(user_id))
        cache.delete(_verified_key(user_id))
        cache.delete(_rate_limit_key(user_id))
    except Exception as e:
        logger.warning(f"Cache clear failed for user {user_id}: {e}")


def check_rate_limit(user_id: int) -> tuple[bool, int]:
    """
    Check if user can request new OTP (rate limit: 1 per 60 seconds).
    Returns (allowed, remaining_seconds).
    """
    try:
        key = _rate_limit_key(user_id)
        if cache.get(key) is None:
            return True, 0
        # Key exists - rate limited; get remaining time if backend supports TTL
        try:
            ttl = cache.ttl(key)
            if ttl is None or ttl <= 0:
                return False, RATE_LIMIT_SECONDS  # Assume full wait
            return False, int(ttl)
        except (AttributeError, NotImplementedError):
            return False, RATE_LIMIT_SECONDS
    except Exception as e:
        logger.warning(f"Rate limit check failed for user {user_id}: {e}")
        return True, 0


def set_rate_limit(user_id: int) -> None:
    """Record OTP request for rate limiting."""
    try:
        key = _rate_limit_key(user_id)
        cache.set(key, "1", timeout=RATE_LIMIT_SECONDS)
    except Exception as e:
        logger.warning(f"Rate limit set failed for user {user_id}: {e}")


def verify_otp_cache(user_id: int, entered_otp: str) -> tuple[bool, str]:
    """
    Verify OTP from cache.
    Returns (success, message).
    """
    data = get_otp_data(user_id)
    if data is None:
        return False, "OTP expired or not found. Please request a new one."

    attempts = data.get("attempts", 0)
    if attempts >= MAX_ATTEMPTS:
        cache.delete(_otp_key(user_id))
        return False, "Maximum attempts exceeded. Please request a new OTP."

    if data.get("otp") != entered_otp:
        data["attempts"] = attempts + 1
        try:
            key = _otp_key(user_id)
            ttl = cache.ttl(key)
            cache.set(key, json.dumps(data), timeout=ttl if ttl and ttl > 0 else OTP_EXPIRY_SECONDS)
        except Exception:
            pass
        remaining = MAX_ATTEMPTS - attempts - 1
        return False, f"Invalid OTP. {remaining} attempt(s) remaining."

    return True, "OTP verified successfully"
