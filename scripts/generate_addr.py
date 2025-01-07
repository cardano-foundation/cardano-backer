import os
from pycardano import PaymentSigningKey, PaymentVerificationKey, Address, Network

# Step 1: Generate a 32-byte random seed
seed = os.urandom(32)  # Generates exactly 32 bytes
seed = b'12345678901234567890123456789012' # Generates exactly 32 bytes
# Step 2: Create the signing key from the seed
signing_key = PaymentSigningKey(seed)

# Step 3: Generate the corresponding verification key
verification_key = PaymentVerificationKey.from_signing_key(signing_key)
print(f"verification_key: {verification_key}")

# Step 4: Create a new address (Testnet example, use Network.MAINNET for Mainnet)
address = Address(payment_part=verification_key.hash(), network=Network.TESTNET)

# Step 5: Convert the address to CBORHEX
cbor_hex = address.to_cbor().hex()

# Print results
print("Address:", address)
print("CBORHEX:", cbor_hex)
print(f"signing_key: {signing_key}")
