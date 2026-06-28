from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext

# ------------------------------------------------------------------
# SECRET KEY
# ------------------------------------------------------------------
# Used to sign JWT tokens.
#
# IMPORTANT:
# Never expose this publicly.
#
SECRET_KEY = "super-secret-key"

# JWT algorithm
ALGORITHM = "HS256"

# ------------------------------------------------------------------
# PASSWORD HASHING CONFIGURATION
# ------------------------------------------------------------------
# bcrypt is a secure password hashing algorithm.

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str):
    """
    Convert plain text password
    into secure bcrypt hash.
    """
    return pwd_context.hash(password)


def verify_password(
        plain_password: str,
        hashed_password: str
):
    """
    Compare entered password
    with stored hash.
    """
    return pwd_context.verify(
        plain_password,
        hashed_password
    )

# Generate JWT token for authenticated user
def create_access_token(data: dict):

    # copy incoming data
    payload = data.copy()

    # Set token expiration time (e.g., 30 minutes)\
    expire = datetime.utcnow() + timedelta(
        minutes=30
    )

    # Add expiration time to payload
    payload["exp"] = expire

    # Create JWT token
    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token

# Decode and verify JWT token
def decode_access_token(token: str):

    

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

       

        return payload

    except Exception as e:
        print("JWT ERROR:", str(e))
        print("===============================\n")
        return None