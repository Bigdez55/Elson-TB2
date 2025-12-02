# HashiCorp Vault Configuration

This directory contains the Kubernetes configuration for deploying HashiCorp Vault with TLS encryption for secure credentials management in the Elson Wealth Trading Platform.

## Features

- **TLS Encryption**: All communications with Vault are encrypted using TLS
- **AWS KMS Integration**: Uses AWS KMS for auto-unsealing and encrypting the master key
- **Kubernetes Authentication**: Integration with Kubernetes service accounts for authentication
- **Pod Identity**: Restricts access based on pod identity and namespace
- **Secret Templates**: Standardized templates for consistent secret access

## Deployment

The Vault deployment includes:

1. **Vault StatefulSet**: Ensures data persistence and orderly updates
2. **TLS Certificates**: Stored in Kubernetes secrets
3. **Service**: Internal access point for other services
4. **RBAC Configuration**: Role-based access control
5. **Agent Configuration**: For backend pod integration

## Initialization

After deployment, initialize Vault with:

```bash
# Initialize vault with 5 key shares, 3 needed for unseal
kubectl exec -it vault-0 -- vault operator init -key-shares=5 -key-threshold=3
```

Store the unseal keys and root token securely in a password manager or secure storage system.

## Automatic Unsealing

The configuration uses AWS KMS for auto-unsealing, eliminating the need for manual unseal operations after restarts.

## Secret Management

Secrets are organized into key-value stores:

- `kv/database`: Database credentials
- `kv/apis`: External API keys
- `kv/app`: Application configuration

## Security Considerations

- Vault runs with a non-root user (UID 100, GID 1000)
- Security contexts restrict capabilities
- Network policies limit connections
- The root token should be revoked after initial setup
- Regular token rotation is enforced

## Monitoring

Vault exposes metrics for Prometheus. A separate ServiceMonitor is included for monitoring.

## Upgrading

Upgrading Vault requires careful planning:

1. Update the image version in `vault.yaml`
2. Apply the changes with `kubectl apply -f vault.yaml`
3. Wait for the rolling upgrade to complete
4. Verify the new version with `kubectl exec -it vault-0 -- vault version`

## Troubleshooting

If you encounter issues:

1. Check pod status: `kubectl get pods | grep vault`
2. View logs: `kubectl logs vault-0`
3. Check seal status: `kubectl exec -it vault-0 -- vault status`

For more information, see the [HashiCorp Vault Documentation](https://www.vaultproject.io/docs).