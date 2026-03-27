import secrets
import hashlib
import hmac

# PBKDF2 hashing (secure, standard)
_ITERATIONS = 150_000

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt}${dk.hex()}"

def verify_password(password: str, stored: str) -> bool:
    algo, iters, salt, digest = stored.split("$")
    iters = int(iters)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iters).hex()
    return hmac.compare_digest(dk, digest)

def generate_temp_password(length: int = 10) -> str:
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789@#%!"
    return "".join(secrets.choice(chars) for _ in range(length))