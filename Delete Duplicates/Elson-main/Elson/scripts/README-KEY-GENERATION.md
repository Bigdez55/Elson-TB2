# Production Key Generation

This directory contains the script for generating secure production keys and TLS certificates for the Elson Wealth Trading Platform.

## Overview

The `generate_production_keys.sh` script creates cryptographically secure random values for:

- Application secrets (SECRET_KEY, JWT tokens)
- Encryption keys (for PII field encryption)
- Database credentials
- Redis passwords
- Self-signed TLS certificates
- Initial admin credentials
- Webhook signing secrets

## Usage

Run the script in a secure environment:

```bash
# Make the script executable
chmod +x generate_production_keys.sh

# Run the script
./generate_production_keys.sh
```

The script will:

1. Generate all required secrets
2. Create self-signed TLS certificates for development/staging
3. Output Kubernetes YAML files with the secrets
4. Provide instructions for applying the secrets to Kubernetes
5. Explain how to initialize and unseal Vault

## Security Considerations

- **Run in a secure environment**: Ideally on an air-gapped system
- **Protect the output**: Store secrets securely in a password manager
- **Never commit secrets**: Do not commit the generated files to version control
- **Rotate regularly**: Use the script to generate new keys on a scheduled basis

## Key Rotation

For production key rotation:

1. Run the script to generate new keys
2. Apply the new secrets to Kubernetes (without deleting old ones)
3. Update Vault with the new values
4. Gradually roll out services to use the new keys
5. Remove old secrets after confirmation all services use new keys

## Production Certificates

For production deployment, replace the self-signed certificates with certificates from a trusted certificate authority.

## Troubleshooting

If you encounter issues:

- Ensure the script has execute permissions
- Check that OpenSSL is installed
- Verify your temporary directory has sufficient space
- Make sure you have permissions to create files

For more information about secure key management, see the [Security Guide](../../docs/setup/security-guide.md).