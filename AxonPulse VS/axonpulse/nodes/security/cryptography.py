from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.lib.provider_node import ProviderNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

import hashlib

import base64

import os

import threading

import time

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

Fernet = None

def ensure_crypto():
    global Fernet
    if Fernet:
        return True
    if DependencyManager.ensure('cryptography'):
        try:
            from cryptography.fernet import Fernet as _F
            Fernet = _F
            return True
        except ImportError:
            return False
    return False

def _simple_xor_crypt(data: str, key: str) -> str:
    """Robust fallback if cryptography is missing."""
    if not key:
        return data
    try:
        key_bytes = key.encode()
        data_bytes = data.encode()
        result = bytearray()
        for i in range(len(data_bytes)):
            result.append(data_bytes[i] ^ key_bytes[i % len(key_bytes)])
        return base64.b64encode(result).decode()
    except:
        return data

def _simple_xor_decrypt(encoded_data: str, key: str) -> str:
    """Robust fallback if cryptography is missing."""
    if not key:
        return encoded_data
    try:
        data_bytes = base64.b64decode(encoded_data)
        key_bytes = key.encode()
        result = bytearray()
        for i in range(len(data_bytes)):
            result.append(data_bytes[i] ^ key_bytes[i % len(key_bytes)])
        return result.decode()
    except:
        return '[Decryption Error]'

@NodeRegistry.register('Encryption Provider', 'Security/Cryptography')
class EncryptionProviderNode(ProviderNode):
    """
    Standardized data encryption and decryption service.
    
    This provider establishes a cryptographic environment using a master secret 
    key. It handles Fernet (AES-128) encryption and can intercept system-wide 
    file operations for transparent data security.
    
    Inputs:
    - Flow: Start the encryption service.
    - Provider End: Shutdown the encryption service.
    - Key: The master secret key for all cryptographic operations.
    
    Outputs:
    - Provider Flow: Active while the service is operational.
    - Provider ID: Identifier for automation node targeting.
    - Flow: Pulse triggered after the service is closed.
    """
    version = '2.1.0'
    provider_type = 'ENCRYPTION'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_service = True
        self.properties['Key'] = 'secret-key'
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema['Key'] = DataType.STRING

    def register_provider_context(self):
        key = self.bridge.get(f'{self.node_id}_Inputs', {}).get('Key')
        pass

    def start_scope(self, **kwargs):
        key = kwargs.get('Key') or self.properties.get('Key', self.properties.get('Key', 'secret-key'))
        self.properties['CurrentKey'] = key
        self.bridge.register_super_function(self.node_id, 'Write File', self.node_id)
        self.bridge.register_super_function(self.node_id, 'Read File', self.node_id)
        self.bridge.set(f'{self.node_id}_Key', key, self.name)
        self._stop_event = threading.Event()
        self._listener_thread = threading.Thread(target=self._hijack_listener, daemon=True)
        self._listener_thread.start()
        return super().start_scope(**kwargs)

    def cleanup_provider_context(self):
        if hasattr(self, '_stop_event'):
            self._stop_event.set()
        self.bridge.unregister_super_functions(self.node_id)
        super().cleanup_provider_context()

    def _hijack_listener(self):
        while not self._stop_event.is_set():
            req = self.bridge.get(f'{self.node_id}_HijackRequest')
            if req:
                func = req.get('func')
                data = req.get('data')
                req_id = req.get('id')
                self.bridge.set(f'{self.node_id}_HijackRequest', None, self.name)
                result = self.handle_hijack(func, data)
                self.bridge.set(f'{self.node_id}_HijackResponse', {'id': req_id, 'result': result}, self.name)
            time.sleep(0.01)

    def handle_hijack(self, func_name, data):
        key = self.bridge.get(f'{self.node_id}_Key')
        if func_name == 'Write File':
            return self._encrypt_data(data, key)
        elif func_name == 'Read File':
            return self._decrypt_data(data, key)
        return data

    def _encrypt_data(self, data, key):
        if not key:
            return data
        if ensure_crypto():
            try:
                k_hash = hashlib.sha256(key.encode()).digest()
                k_b64 = base64.urlsafe_b64encode(k_hash)
                f = Fernet(k_b64)
                return f.encrypt(str(data).encode()).decode()
            except:
                pass
        return _simple_xor_crypt(str(data), key)

    def _decrypt_data(self, data, key):
        if not key:
            return data
        if ensure_crypto():
            try:
                k_hash = hashlib.sha256(key.encode()).digest()
                k_b64 = base64.urlsafe_b64encode(k_hash)
                f = Fernet(k_b64)
                return f.decrypt(str(data).encode()).decode()
            except:
                pass
        return _simple_xor_decrypt(str(data), key)

@axon_node(category="Security", version="2.3.0", node_label="AES Encrypt", outputs=['Encrypted Data'])
def EncryptNode(Data: str, Key: str = 'secret-key', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Encrypts a string or data object using a secret key.

Uses Fernet (AES-128) for high-security encryption when available. 
Encrypted data is returned as a base64-encoded string.

Inputs:
- Flow: Trigger the encryption process.
- Data: The plaintext content to encrypt.
- Key: The secret key for encryption.

Outputs:
- Flow: Pulse triggered after encryption.
- Encrypted Data: The resulting base64 encoded ciphertext."""
    val = Data if Data is not None else ''
    key = Key if Key is not None else _node.properties.get('Key', _node.properties.get('Key', ''))
    result = ''
    if ensure_crypto():
        try:
            k_hash = hashlib.sha256(key.encode()).digest()
            k_b64 = base64.urlsafe_b64encode(k_hash)
            f = Fernet(k_b64)
            result = f.encrypt(str(val).encode()).decode()
        except Exception as e:
            _node.logger.error(f'Fernet Error: {e}')
            result = _simple_xor_crypt(str(val), key)
        finally:
            pass
    else:
        result = _simple_xor_crypt(str(val), key)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Security", version="2.3.0", node_label="AES Decrypt", outputs=['Decrypted Data'])
def DecryptNode(Encrypted_Data: str, Key: str = 'secret-key', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Decrypts an encrypted string back to its original state.

Attempts to reverse encryption using the provided key. Matches the 
security logic used by the 'AES Encrypt' node.

Inputs:
- Flow: Trigger the decryption process.
- Encrypted Data: The base64 encoded ciphertext.
- Key: The secret key used during encryption.

Outputs:
- Flow: Pulse triggered after decryption.
- Decrypted Data: The recovered plaintext content."""
    val = Encrypted_Data if Encrypted_Data is not None else kwargs.get('Encrypted Data', '')
    key = Key if Key is not None else _node.properties.get('Key', _node.properties.get('Key', ''))
    result = ''
    if ensure_crypto():
        try:
            k_hash = hashlib.sha256(key.encode()).digest()
            k_b64 = base64.urlsafe_b64encode(k_hash)
            f = Fernet(k_b64)
            result = f.decrypt(str(val).encode()).decode()
        except Exception as e:
            result = _simple_xor_decrypt(str(val), key)
        finally:
            pass
    else:
        result = _simple_xor_decrypt(str(val), key)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Security", version="2.3.0", node_label="Hash String", outputs=['SHA Key'])
def SHANode(Data: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Generates a secure SHA-256 hash (fingerprint) of a string.

Hashing is a one-way transformation used for data integrity verification 
or password masking. It cannot be reversed.

Inputs:
- Flow: Trigger the hashing process.
- Data: The string to hash.

Outputs:
- Flow: Pulse triggered after hashing.
- SHA Key: The resulting 64-character hexadecimal hash."""
    val = Data if Data is not None else ''
    h = hashlib.sha256(str(val).encode()).hexdigest()
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return h


@axon_node(category="Security/Cryptography", version="2.3.0", node_label="Checksum/Hash", outputs=['Hash'])
def ChecksumNode(Data: str, Hash_Type: str = 'SHA-256', Secret: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Generates a cryptographic checksum for strings or files.

Supports multiple algorithms (SHA-256, MD5) and secure HMAC 
(Keyed-Hash Message Authentication Code) for verified message integrity.

Inputs:
- Flow: Trigger the calculation.
- Data: The string or absolute file path to verify.
- Hash Type: Algorithm to use (SHA-256, MD5, HMAC).
- Secret: The authentication key (required for HMAC).

Outputs:
- Flow: Pulse triggered after calculation.
- Hash: The resulting hexadecimal checksum string."""
    data = Data if Data is not None else ''
    hash_type = Hash_Type if Hash_Type is not None else _node.properties.get('HashType', _node.properties.get('Hash Type', 'SHA-256'))
    secret = Secret if Secret is not None else _node.properties.get('Secret', '')
    hash_type = hash_type.upper().replace('-', '')
    data_bytes = b''
    if isinstance(data, str) and os.path.exists(data) and os.path.isfile(data):
        try:
            with open(data, 'rb') as f:
                data_bytes = f.read()
        except:
            data_bytes = str(data).encode('utf-8')
        finally:
            pass
    elif isinstance(data, str):
        data_bytes = data.encode('utf-8')
    elif isinstance(data, (bytes, bytearray)):
        data_bytes = bytes(data)
    else:
        data_bytes = str(data).encode('utf-8')
    result_hash = ''
    try:
        if hash_type == 'HMAC':
            if not secret:
                _node.logger.error('HMAC requires a Secret (Key).')
                return
            else:
                pass
            import hmac
            h = hmac.new(secret.encode('utf-8'), data_bytes, hashlib.sha256)
            result_hash = h.hexdigest()
        elif hash_type == 'MD5':
            result_hash = hashlib.md5(data_bytes).hexdigest()
        else:
            result_hash = hashlib.sha256(data_bytes).hexdigest()
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'Hashing Error: {e}')
    finally:
        pass
    return result_hash
