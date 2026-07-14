"""
Generate a self-signed SSL certificate for local HTTPS development.
Run once: python scripts/generate_cert.py
Creates: instance/cert.pem and instance/key.pem
"""

import os
import sys
from pathlib import Path

# Ensure cryptography is available
try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    import datetime, ipaddress
except ImportError:
    print("Installing cryptography...")
    os.system(f"{sys.executable} -m pip install cryptography")
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    import datetime, ipaddress

BASE = Path(__file__).parent.parent / "instance"
BASE.mkdir(exist_ok=True)

CERT_FILE = BASE / "cert.pem"
KEY_FILE  = BASE / "key.pem"

# Generate private key
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Build certificate
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, u"127.0.0.1"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Smart HRMS Dev"),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(u"localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

# Write files
KEY_FILE.write_bytes(key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
))

CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

print(f"✓ Certificate generated:")
print(f"  Cert: {CERT_FILE}")
print(f"  Key:  {KEY_FILE}")
print()
print("Now run: python run.py")
print("Then open: https://127.0.0.1:5000")
print("Chrome will show a warning — click Advanced → Proceed (one time only).")
