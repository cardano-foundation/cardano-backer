#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from pycardano import *

derivation_path = "m/1852'/1815'/0'/0/0"

generated_mnemonics = HDWallet.generate_mnemonic()
hdwallet = HDWallet.from_mnemonic(generated_mnemonics)
child_hdwallet = hdwallet.derive_from_path(derivation_path)
spend_public_key = child_hdwallet.public_key.hex()
spend_vk = PaymentVerificationKey.from_primitive(bytes.fromhex(spend_public_key))
WALLET_ADDRESS_CBORHEX = PaymentSigningKey.from_primitive(child_hdwallet.public_key).to_cbor()

payment_signing_key = PaymentSigningKey.from_cbor(WALLET_ADDRESS_CBORHEX)
payment_verification_key = PaymentVerificationKey.from_signing_key(payment_signing_key)
bech32_address = Address(payment_verification_key.hash(), None, Network.TESTNET)

print("[+] Generated mnemonics:", generated_mnemonics)
print("[+] Spending Address:", bech32_address)
print(f"[+] WALLET_ADDRESS_CBORHEX={WALLET_ADDRESS_CBORHEX}")
