#!/usr/bin/env python3
"""Generate a free self-signed SSL certificate valid for 10 years"""

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import datetime
import os

def generate_certificate():
    """Generate self-signed certificate"""
    
    # Certificate directory
    cert_dir = r"C:\Smart_HRMS\certs"
    os.makedirs(cert_dir, exist_ok=True)
    
    # Generate private key
    print("✓ Generating private key...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Certificate details
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"State"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"City"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Smart HRMS"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"smarthrms.local"),
    ])
    
    # Build certificate
    print("✓ Building certificate (10 year validity)...")
    cert = x509.CertificateBuilder().add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(u"smarthrms.local"),
            x509.DNSName(u"*.smarthrms.local"),
            x509.DNSName(u"localhost"),
            x509.IPAddress(__import__("ipaddress").IPv4Address("192.168.0.205")),
            x509.IPAddress(__import__("ipaddress").IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    ).subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)  # 10 years
    ).sign(private_key, hashes.SHA256(), default_backend())
    
    # Save certificate
    cert_path = os.path.join(cert_dir, "smart-hrms.crt")
    print(f"✓ Saving certificate to {cert_path}...")
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Save private key
    key_path = os.path.join(cert_dir, "smart-hrms.key")
    print(f"✓ Saving private key to {key_path}...")
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    print("\n" + "="*60)
    print("✅ SSL CERTIFICATE GENERATED SUCCESSFULLY!")
    print("="*60)
    print(f"\nCertificate: {cert_path}")
    print(f"Private Key: {key_path}")
    print(f"\nValid for: 10 years (until {(datetime.datetime.utcnow() + datetime.timedelta(days=3650)).strftime('%Y-%m-%d')})")
    print(f"Supports: smarthrms.local, localhost, 192.168.0.205, 127.0.0.1")
    print(f"\nAccess at: https://192.168.0.205:8000")
    print("="*60 + "\n")

if __name__ == "__main__":
    generate_certificate()
