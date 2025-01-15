from passlib.context import CryptContext

context=CryptContext(schemes=["pbkdf2_sha256","des_crypt"],deprecated="auto")

def password_hash(password):

    return context.hash(password)


def password_verify(password,hash_password):
    
    return context.verify(password,hash_password)
