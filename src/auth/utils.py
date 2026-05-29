from passlib.context import CryptContext

password_context = CryptContext(
    schemes=['bcrypt'],
    bcrypt__rounds=12,
    deprecated="auto"
)

def generate_password_hash(password: str)-> str:
    hash = password_context.hash(password)
    return hash

def verify_password(password: str, hash: str) -> bool:
    return password_context.verify(password, hash)