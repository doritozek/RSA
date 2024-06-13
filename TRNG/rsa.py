from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA512
from trng_generator import generate_random_data
import rsa

class RandomGenerator:
    def __init__(self):
        self.index = 0
        self.data = generate_random_data()

    def get_random_bytes(self, n):
        if self.index + n > len(self.data):
            self.data = generate_random_data()
            self.index = 0
        result = self.data[self.index : self.index + n]
        self.index += n
        return bytes(result)

def generate_key_pair():
    random_gen = RandomGenerator()
    key = RSA.generate(2048, randfunc=random_gen.get_random_bytes)
    with open("private_key.pem", "wb") as f:
        f.write(key.export_key())
    with open("public_key.pem", "wb") as f:
        f.write(key.publickey().export_key())

def hash_function(data):
    h = SHA512.new()
    h.update(data)
    return h

def sign_data(data):
    with open("private_key.pem", "rb") as f:
        key = RSA.import_key(f.read())
    h = hash_function(data)
    signature = pkcs1_15.new(key).sign(h)
    return signature

def load_key_from_file(file_name):
    with open(file_name, "rb") as f:
        key = RSA.import_key(f.read())
    return key

if __name__ == "__main__":

    generate_key_pair()

    with open("deszcz.wav", "rb") as f:
        data = f.read()
    message = sign_data(data)
    
    public_key = load_key_from_file("public_key.pem")

    # Sprawdzenie integralności danych
    h = hash_function(data)
    try:
        pkcs1_15.new(public_key).verify(h, message)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    print(is_valid)

    with open("cazzette.wav", "rb") as f:
        data = f.read()
    
    h = hash_function(data)
    try:
        pkcs1_15.new(public_key).verify(h, message)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    print(is_valid)

    # Sprawdzenie niezbywalności danych
    generate_key_pair()

    public_key2 = load_key_from_file("public_key.pem")

    with open("deszcz.wav", "rb") as f:
        data = f.read()
    h = hash_function(data)
    try:
        pkcs1_15.new(public_key2).verify(h, message)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    print(is_valid)

    message2 = sign_data(data)

    print(public_key)
    print(public_key2)


    
