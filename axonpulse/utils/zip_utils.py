import os
import zipfile
import shutil
import logging

logger = logging.getLogger("AxonPulseZipUtils")

try:
    import pyzipper
    HAS_PYZIPPER = True
except ImportError:
    HAS_PYZIPPER = False
    logger.warning("pyzipper not found. AES-encrypted zips will not be supported. Falling back to standard zipfile.")

def is_zip_encrypted(zip_path):
    """Checks if the zip file is password protected."""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for info in zf.infolist():
                if info.flag_bits & 0x1:
                    return True
        return False
    except Exception as e:
        logger.error(f"Failed to check encryption for {zip_path}: {e}")
        return False

def extract_package(zip_path, extract_to, password=None):
    """
    Extracts .syp, .spy, and .py files from a zip archive.
    Supports pyzipper for AES encryption if available.
    """
    if not os.path.exists(extract_to):
        os.makedirs(extract_to, exist_ok=True)

    try:
        if HAS_PYZIPPER:
            # Use pyzipper for modern encryption support
            with pyzipper.AESZipFile(zip_path) as zf:
                if password:
                    zf.setpassword(password.encode())
                
                # Filter for allowed extensions
                allowed_extensions = {'.syp', '.spy', '.py'}
                members_to_extract = [
                    m for m in zf.namelist() 
                    if os.path.splitext(m)[1].lower() in allowed_extensions
                    and not m.startswith('__MACOSX') # Skip macOS metadata
                ]
                
                zf.extractall(path=extract_to, members=members_to_extract)
        else:
            # Fallback to standard zipfile
            with zipfile.ZipFile(zip_path) as zf:
                if password:
                    zf.setpassword(password.encode())
                
                allowed_extensions = {'.syp', '.spy', '.py'}
                members_to_extract = [
                    m for m in zf.namelist() 
                    if os.path.splitext(m)[1].lower() in allowed_extensions
                    and not m.startswith('__MACOSX')
                ]
                
                zf.extractall(path=extract_to, members=members_to_extract)
        
        return True
    except RuntimeError as re:
        if "password" in str(re).lower():
            logger.error(f"Invalid password for {zip_path}")
        else:
            logger.error(f"Runtime error extracting {zip_path}: {re}")
        return False
    except Exception as e:
        logger.error(f"Failed to extract {zip_path}: {e}")
        return False
