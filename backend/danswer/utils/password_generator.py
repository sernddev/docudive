import random
import string

def generate_password(length=6):
    if length < 1:
        raise ValueError("Password length must be at least 1")

    # Define the character sets to include in the password
    characters = string.ascii_letters + string.digits

    # Generate a random password
    password = ''.join(random.choice(characters) for _ in range(length))
    return password