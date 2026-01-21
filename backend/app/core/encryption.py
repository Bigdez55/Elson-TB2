import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


# AES-256 Encryption
class AES256Encryptor:
    """
    Provides AES-256 encryption and decryption with the following features:
    - AES-256-CBC mode encryption
    - PKCS7 padding
    - PBKDF2HMAC key derivation with salt
    - Secure random IV generation
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize the encryptor with a master key.

        Args:
            master_key: The master encryption key. If not provided, will use the SECRET_KEY from settings.
        """
        self.master_key = master_key or settings.SECRET_KEY
        # Ensure the key is long enough for AES-256
        self.kdf_salt = os.urandom(16)  # Generate a random salt for key derivation

    def _derive_key(self, salt: bytes) -> bytes:
        """
        Derive a 32-byte key using PBKDF2HMAC.

        Args:
            salt: Salt for key derivation

        Returns:
            A 32-byte derived key for AES-256
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes for AES-256
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        return kdf.derive(self.master_key.encode())

    def encrypt(self, data: Union[str, Dict[str, Any], bytes]) -> str:
        """
        Encrypt data using AES-256-CBC.

        Args:
            data: Data to encrypt. Can be a string, dictionary, or bytes.

        Returns:
            Base64-encoded encrypted data with salt and IV prepended
        """
        # Convert data to bytes if it's not already
        if isinstance(data, dict):
            data_bytes = json.dumps(data).encode()
        elif isinstance(data, str):
            data_bytes = data.encode()
        else:
            data_bytes = data

        # Generate a random IV (16 bytes for AES-256-CBC)
        iv = os.urandom(16)

        # Derive the key
        key = self._derive_key(self.kdf_salt)

        # Pad the data to block size
        padder = self._pkcs7_pad(data_bytes)

        # Encrypt the data
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(padder) + encryptor.finalize()

        # Format the output: salt + iv + ciphertext
        encrypted_data = self.kdf_salt + iv + ct

        # Return as base64
        return base64.b64encode(encrypted_data).decode()

    def decrypt(self, encrypted_data: str) -> Union[str, Dict[str, Any]]:
        """
        Decrypt AES-256-CBC encrypted data.

        Args:
            encrypted_data: Base64-encoded encrypted data with salt and IV prepended

        Returns:
            The decrypted data
        """
        # Decode from base64
        data = base64.b64decode(encrypted_data.encode())

        # Extract the salt, IV, and ciphertext
        salt = data[:16]
        iv = data[16:32]
        ciphertext = data[32:]

        # Derive the key
        key = self._derive_key(salt)

        # Decrypt the data
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        pt = decryptor.update(ciphertext) + decryptor.finalize()

        # Unpad the data
        unpadded = self._pkcs7_unpad(pt)

        # Try to decode as JSON or return as string
        try:
            return json.loads(unpadded.decode())
        except json.JSONDecodeError:
            return unpadded.decode()
        except UnicodeDecodeError:
            return unpadded

    def _pkcs7_pad(self, data: bytes) -> bytes:
        """
        Pad data to AES block size (16 bytes) using PKCS7 padding.

        Args:
            data: Data to pad

        Returns:
            Padded data
        """
        block_size = 16
        padding_size = block_size - (len(data) % block_size)
        padding = bytes([padding_size]) * padding_size
        return data + padding

    def _pkcs7_unpad(self, data: bytes) -> bytes:
        """
        Remove PKCS7 padding from data.

        Args:
            data: Padded data

        Returns:
            Unpadded data
        """
        padding_size = data[-1]
        if padding_size > 16:
            # Invalid padding - return as is
            return data

        if all(x == padding_size for x in data[-padding_size:]):
            return data[:-padding_size]

        # Invalid padding - return as is
        return data


# Fernet encryption (simpler but still secure)
class FernetEncryptor:
    """
    Provides Fernet encryption and decryption for sensitive data.
    Fernet ensures that a message encrypted cannot be manipulated
    or read without the key. It uses AES-128-CBC with HMAC.
    """

    def __init__(self, key: Optional[str] = None):
        """
        Initialize the encryptor with a key or generate one from settings.

        Args:
            key: The encryption key. If not provided, it will be derived from settings.
        """
        if key:
            self.fernet = Fernet(key.encode())
        else:
            # Derive a key from the secret key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"ElsonWealthSecureSalt",  # Fixed salt
                iterations=100000,
                backend=default_backend(),
            )
            derived_key = base64.urlsafe_b64encode(
                kdf.derive(settings.SECRET_KEY.encode())
            )
            self.fernet = Fernet(derived_key)

    def encrypt(self, data: Union[str, Dict[str, Any]]) -> str:
        """
        Encrypt data using Fernet.

        Args:
            data: Data to encrypt (string or dictionary)

        Returns:
            Base64-encoded encrypted data
        """
        if isinstance(data, dict):
            data_str = json.dumps(data)
        else:
            data_str = str(data)

        token = self.fernet.encrypt(data_str.encode())
        return token.decode()

    def decrypt(self, token: str) -> Union[str, Dict[str, Any]]:
        """
        Decrypt Fernet-encrypted data.

        Args:
            token: Encrypted token to decrypt

        Returns:
            Decrypted data (string or dictionary)
        """
        decrypted = self.fernet.decrypt(token.encode()).decode()

        # Try to load as JSON, otherwise return as string
        try:
            return json.loads(decrypted)
        except json.JSONDecodeError:
            return decrypted


# File encryption functions
def encrypt_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    encryptor: Optional[Union[AES256Encryptor, FernetEncryptor]] = None,
) -> None:
    """
    Encrypt a file using AES-256 or Fernet.

    Args:
        input_path: Path to the file to encrypt
        output_path: Path to save the encrypted file
        encryptor: Encryptor to use. If not provided, uses AES256Encryptor.
    """
    # Create default encryptor if none provided
    if encryptor is None:
        encryptor = AES256Encryptor()

    # Read the file
    with open(input_path, "rb") as f:
        data = f.read()

    # Encrypt the data
    encrypted = encryptor.encrypt(data)

    # Write the encrypted data
    with open(output_path, "w") as f:
        f.write(encrypted)


def decrypt_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    encryptor: Optional[Union[AES256Encryptor, FernetEncryptor]] = None,
) -> None:
    """
    Decrypt a file encrypted with AES-256 or Fernet.

    Args:
        input_path: Path to the encrypted file
        output_path: Path to save the decrypted file
        encryptor: Encryptor to use. If not provided, uses AES256Encryptor.
    """
    # Create default encryptor if none provided
    if encryptor is None:
        encryptor = AES256Encryptor()

    # Read the encrypted file
    with open(input_path, "r") as f:
        encrypted = f.read()

    # Decrypt the data
    decrypted = encryptor.decrypt(encrypted)

    # If the result is bytes, write in binary mode, otherwise in text mode
    if isinstance(decrypted, bytes):
        with open(output_path, "wb") as f:
            f.write(decrypted)
    else:
        with open(output_path, "w") as f:
            f.write(decrypted)


# Create default encryptors
default_aes_encryptor = AES256Encryptor()
default_fernet_encryptor = FernetEncryptor()


# Utility functions for sensitive data encryption
def encrypt_sensitive_data(data: Union[str, Dict[str, Any], bytes]) -> str:
    """Encrypt sensitive data using the default encryptor."""
    return default_fernet_encryptor.encrypt(data)


def decrypt_sensitive_data(encrypted_data: str) -> Union[str, Dict[str, Any]]:
    """Decrypt sensitive data using the default encryptor."""
    return default_fernet_encryptor.decrypt(encrypted_data)
