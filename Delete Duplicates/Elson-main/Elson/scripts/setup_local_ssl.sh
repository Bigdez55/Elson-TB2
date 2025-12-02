#!/bin/bash
#
# Local SSL Certificate Generator for Elson Wealth Beta Testing
#
# This script sets up local DNS and SSL certificates for beta.elsonwealth.com
#

set -e

# Print welcome banner
echo "================================================================================"
echo "              ELSON WEALTH BETA - LOCAL SSL CERTIFICATE SETUP                   "
echo "================================================================================"
echo ""

# Check for required tools
if ! command -v mkcert &> /dev/null; then
    echo "mkcert is not installed. Installing now..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            echo "Homebrew is required but not installed."
            echo "Please install Homebrew first: https://brew.sh"
            exit 1
        fi
        brew install mkcert
        brew install nss # For Firefox support
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "Please install mkcert manually for your Linux distribution."
        echo "See: https://github.com/FiloSottile/mkcert#linux"
        exit 1
    else
        echo "Unsupported operating system: $OSTYPE"
        echo "Please install mkcert manually: https://github.com/FiloSottile/mkcert"
        exit 1
    fi
fi

# Create SSL directory if it doesn't exist
SSL_DIR=~/.ssl
mkdir -p $SSL_DIR

# Install mkcert root CA
echo "Installing mkcert root CA..."
mkcert -install

# Generate certificate for beta.elsonwealth.com
echo "Generating certificate for beta.elsonwealth.com..."
cd $SSL_DIR
mkcert beta.elsonwealth.com localhost 127.0.0.1 ::1

# Rename files to match what the docker-compose file expects
cp beta.elsonwealth.com+3.pem beta.elsonwealth.com.pem
cp beta.elsonwealth.com+3-key.pem beta.elsonwealth.com-key.pem

echo "Certificates generated successfully at $SSL_DIR"
echo ""
echo "Certificate: $SSL_DIR/beta.elsonwealth.com.pem"
echo "Key: $SSL_DIR/beta.elsonwealth.com-key.pem"
echo ""

# Update hosts file
echo "Updating hosts file to point beta.elsonwealth.com to 127.0.0.1..."
echo ""

if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # macOS or Linux
    HOSTS_FILE="/etc/hosts"
    
    # Check if entry already exists
    if grep -q "beta.elsonwealth.com" $HOSTS_FILE; then
        echo "Host entry already exists in $HOSTS_FILE"
    else
        echo "Adding host entry to $HOSTS_FILE"
        echo "This requires sudo access:"
        echo "127.0.0.1    beta.elsonwealth.com" | sudo tee -a $HOSTS_FILE
    fi
else
    # Windows or other OS
    echo "Please manually add the following entry to your hosts file:"
    echo "127.0.0.1    beta.elsonwealth.com"
    
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "On Windows, edit: C:\\Windows\\System32\\drivers\\etc\\hosts as administrator"
    fi
fi

echo ""
echo "================================================================================"
echo "                            SETUP COMPLETE!                                      "
echo "================================================================================"
echo ""
echo "You can now access the Elson Wealth beta at: https://beta.elsonwealth.com"
echo ""
echo "To start the beta environment, run:"
echo "  ./launch-beta.sh"
echo ""
echo "Note: Your browser may still show a certificate warning the first time you visit."
echo "This is normal - the certificate is valid but self-signed."
echo ""