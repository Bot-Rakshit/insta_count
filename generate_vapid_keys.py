from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

def generate_vapid_keys():
    # Generate a private key
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key to compressed point format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # Encode public key in URL-safe base64
    public_b64 = base64.urlsafe_b64encode(public_pem).decode('utf-8')
    
    return private_pem.decode('utf-8'), public_b64

if __name__ == "__main__":
    try:
        private_key, public_key = generate_vapid_keys()
        
        print("\nVAPID Public Key:")
        print(public_key)
        print("\nVAPID Private Key:")
        print(private_key)
        
        # Save to a file
        with open('vapid_keys.txt', 'w') as f:
            f.write(f"Public Key:\n{public_key}\n\nPrivate Key:\n{private_key}")
        
        print("\nKeys have been saved to vapid_keys.txt")
        
    except Exception as e:
        print(f"Error generating keys: {e}")