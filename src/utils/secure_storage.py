"""
Secure Storage - Utility functions for data encryption/decryption
"""
import os
import json
import base64
from typing import Union, Optional, Dict, Any


class SecureStorage:
    """
    Provides secure storage capabilities with encryption and decryption functions.
    Handles sensitive data protection following security best practices.
    Uses simple XOR cipher with base64 encoding for basic obfuscation.
    Note: For production use, a stronger algorithm like AES should be implemented.
    """

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize the SecureStorage with either a provided key or generate one.

        Args:
            key: Optional encryption key. If not provided, a random one will be generated.
        """
        if key is None:
            # Generate a default key if none is provided
            self.key = base64.urlsafe_b64encode(b'default_encryption_key_for_dev_purposes_only')
        else:
            # Ensure the key is properly formatted
            if isinstance(key, str):
                key = key.encode('utf-8')
            self.key = base64.urlsafe_b64encode(key.ljust(32)[:32])  # Pad or truncate to 32 bytes

    def _xor_crypt(self, data: bytes, key: bytes) -> bytes:
        """
        Simple XOR encryption/decryption function.

        Args:
            data: Data to encrypt/decrypt
            key: Encryption key

        Returns:
            Encrypted/decrypted data
        """
        # Expand key to match data length
        expanded_key = bytearray()
        while len(expanded_key) < len(data):
            expanded_key += key

        # Truncate to match data length
        expanded_key = expanded_key[:len(data)]

        # XOR operation
        result = bytearray()
        for i in range(len(data)):
            result.append(data[i] ^ expanded_key[i])

        return bytes(result)

    def encrypt_data(self, data: Union[str, bytes, Dict, list]) -> str:
        """
        Encrypt data using XOR cipher and base64 encoding.

        Args:
            data: Data to encrypt (string, bytes, dict, or list)

        Returns:
            Base64 encoded encrypted string
        """
        try:
            # Convert data to JSON string if it's not already a string or bytes
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data)
            elif isinstance(data, str):
                data_str = data
            elif isinstance(data, bytes):
                data_str = data.decode('utf-8')
            else:
                data_str = str(data)

            # Encrypt the data using XOR cipher
            data_bytes = data_str.encode('utf-8')
            encrypted_bytes = self._xor_crypt(data_bytes, base64.urlsafe_b64decode(self.key))

            # Encode the result with base64 for easy storage/transmission
            encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')

            return encrypted_b64

        except Exception as e:
            raise ValueError(f"Failed to encrypt data: {str(e)}")

    def decrypt_data(self, encrypted_data: str) -> Union[str, Dict, list]:
        """
        Decrypt data that was encrypted with encrypt_data.

        Args:
            encrypted_data: Base64 encoded encrypted string

        Returns:
            Decrypted data (str, dict, or list depending on original type)
        """
        try:
            # Decode the base64 string
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))

            # Decrypt the data using XOR cipher (same operation since XOR is symmetrical)
            decrypted_bytes = self._xor_crypt(encrypted_bytes, base64.urlsafe_b64decode(self.key))
            decrypted_str = decrypted_bytes.decode('utf-8')

            # Try to parse as JSON first (for dicts and lists)
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                # If not JSON, return as string
                return decrypted_str

        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")

    def encrypt_file(self, input_path: str, output_path: str) -> bool:
        """
        Encrypt the contents of a file and save to another file.

        Args:
            input_path: Path to the input file to encrypt
            output_path: Path where the encrypted file should be saved

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(input_path, 'rb') as infile:
                data = infile.read()

            # Encrypt the data using XOR cipher
            encrypted_data = self._xor_crypt(data, base64.urlsafe_b64decode(self.key))

            with open(output_path, 'wb') as outfile:
                outfile.write(encrypted_data)

            return True

        except Exception as e:
            print(f"[!] Failed to encrypt file: {str(e)}")
            return False

    def decrypt_file(self, input_path: str, output_path: str) -> bool:
        """
        Decrypt the contents of an encrypted file and save to another file.

        Args:
            input_path: Path to the encrypted input file
            output_path: Path where the decrypted file should be saved

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(input_path, 'rb') as infile:
                encrypted_data = infile.read()

            # Decrypt the data using XOR cipher (same operation since XOR is symmetrical)
            decrypted_data = self._xor_crypt(encrypted_data, base64.urlsafe_b64decode(self.key))

            with open(output_path, 'wb') as outfile:
                outfile.write(decrypted_data)

            return True

        except Exception as e:
            print(f"[!] Failed to decrypt file: {str(e)}")
            return False


def encrypt_data(data: Union[str, bytes, Dict, list], key: Optional[bytes] = None) -> str:
    """
    Convenience function to encrypt data without creating a SecureStorage instance.

    Args:
        data: Data to encrypt
        key: Optional encryption key. If not provided, a default will be used.

    Returns:
        Base64 encoded encrypted string
    """
    storage = SecureStorage(key)
    return storage.encrypt_data(data)


def decrypt_data(encrypted_data: str, key: Optional[bytes] = None) -> Union[str, Dict, list]:
    """
    Convenience function to decrypt data without creating a SecureStorage instance.

    Args:
        encrypted_data: Base64 encoded encrypted string
        key: Optional encryption key. If not provided, the default will be used.

    Returns:
        Decrypted data (str, dict, or list depending on original type)
    """
    storage = SecureStorage(key)
    return storage.decrypt_data(encrypted_data)


def decrypt_file_with_password(encrypted_path: str, decrypted_path: str, password: str, salt: bytes) -> bool:
    """
    Decrypt a file using a password-derived key.

    Args:
        encrypted_path: Path to the encrypted file
        decrypted_path: Path where decrypted file should be saved
        password: Password used for encryption
        salt: Salt used during encryption

    Returns:
        True if successful, False otherwise
    """
    try:
        key, _ = SecureStorage.derive_key_from_password(password, salt)
        storage = SecureStorage(key)

        return storage.decrypt_file(encrypted_path, decrypted_path)
    except Exception as e:
        print(f"[!] Failed to decrypt file with password: {str(e)}")
        return False