#!/usr/bin/env python
"""
Database restore script for Elson Trading Bot Platform.

This script restores a PostgreSQL database from a backup created by the backup_database.py script.
It supports decryption, decompression, and restoration from various storage backends.

Usage:
    python restore_database.py --backup-file FILENAME [--storage-backend {local,s3,azure}] [--target-db DATABASE] [--target-host HOST] [--target-port PORT] [--target-user USER]
    
Options:
    --backup-file       The filename of the backup to restore
    --storage-backend   Storage backend where the backup is stored (default: as configured)
    --target-db         The target database to restore to (default: from config)
    --target-host       The target database host (default: from config)
    --target-port       The target database port (default: from config)
    --target-user       The target database user (default: from config)
    --list-backups      List available backups instead of restoring
    --latest            Restore the latest backup
"""

import os
import sys
import argparse
import logging
import subprocess
import datetime
import time
import gzip
import shutil
import json
import tempfile
from typing import Optional, Dict, List, Any, Tuple

import boto3
import azure.storage.blob
from azure.identity import DefaultAzureCredential
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/elson/database-restore.log")
    ]
)
logger = logging.getLogger("database-restore")

# Import config from backup script to maintain consistency
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from backup_database import load_config, DEFAULT_CONFIG, get_encryption_key
except ImportError:
    logger.warning("Could not import from backup_database.py, using internal defaults")
    
    DEFAULT_CONFIG = {
        "backup_dir": "/backup",
        "storage": {
            "backend": "local",
            "s3": {
                "bucket": "elson-backups",
                "prefix": "db-backups/",
                "region": "us-east-1"
            },
            "azure": {
                "container": "elson-backups",
                "account_name": "elsonsa"
            },
            "local": {
                "path": "/backup"
            }
        },
        "encryption": {
            "enabled": True
        },
        "compression": {
            "enabled": True
        },
        "database": {
            "host": "db",
            "port": 5432,
            "name": "elson_production",
            "user": "elson"
        }
    }
    
    def load_config() -> Dict[str, Any]:
        """Load configuration from environment variables or config file."""
        config = DEFAULT_CONFIG.copy()
        
        # Try to load from config file
        config_path = os.environ.get("BACKUP_CONFIG_PATH", "/etc/elson/backup-config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    # Update recursively
                    def update_recursive(d, u):
                        for k, v in u.items():
                            if isinstance(v, dict) and k in d:
                                d[k] = update_recursive(d.get(k, {}), v)
                            else:
                                d[k] = v
                        return d
                    config = update_recursive(config, file_config)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")
        
        # Override with environment variables
        if os.environ.get("DB_HOST"):
            config["database"]["host"] = os.environ.get("DB_HOST")
        if os.environ.get("DB_PORT"):
            config["database"]["port"] = int(os.environ.get("DB_PORT"))
        if os.environ.get("DB_NAME"):
            config["database"]["name"] = os.environ.get("DB_NAME")
        if os.environ.get("DB_USER"):
            config["database"]["user"] = os.environ.get("DB_USER")
        if os.environ.get("BACKUP_STORAGE"):
            config["storage"]["backend"] = os.environ.get("BACKUP_STORAGE")
        if os.environ.get("ENCRYPTION_KEY"):
            config["encryption"]["key"] = os.environ.get("ENCRYPTION_KEY")
        
        return config
    
    def get_encryption_key(config: Dict[str, Any]) -> Optional[bytes]:
        """Get or generate an encryption key."""
        if not config["encryption"]["enabled"]:
            return None
        
        key_path = os.environ.get("ENCRYPTION_KEY_PATH", "/etc/elson/backup-encryption.key")
        
        # Try to get from environment
        if "key" in config["encryption"]:
            return config["encryption"]["key"].encode()
        
        # Try to load from file
        try:
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"Failed to load encryption key: {e}")
        
        return None

def list_backups(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """List available backups from the configured storage backend."""
    backend = config["storage"]["backend"]
    backups = []
    
    if backend == "local":
        storage_path = config["storage"]["local"]["path"]
        
        # Find all metadata files
        metadata_files = [f for f in os.listdir(storage_path) if f.endswith('.meta.json')]
        
        for metadata_file in metadata_files:
            try:
                with open(os.path.join(storage_path, metadata_file), 'r') as f:
                    metadata = json.load(f)
                    
                    # Check if the backup file actually exists
                    backup_filename = metadata.get("filename")
                    if backup_filename and os.path.exists(os.path.join(storage_path, backup_filename)):
                        backups.append(metadata)
                    else:
                        logger.warning(f"Metadata references missing backup file: {backup_filename}")
            except Exception as e:
                logger.warning(f"Failed to read metadata file {metadata_file}: {e}")
    
    elif backend == "s3":
        bucket = config["storage"]["s3"]["bucket"]
        prefix = config["storage"]["s3"]["prefix"]
        region = config["storage"]["s3"]["region"]
        
        s3 = boto3.client('s3', region_name=region)
        
        # List objects in the bucket
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        # Find all metadata files
        metadata_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.meta.json')]
        
        for metadata_key in metadata_files:
            try:
                obj = s3.get_object(Bucket=bucket, Key=metadata_key)
                metadata = json.loads(obj['Body'].read().decode('utf-8'))
                
                # Check if the backup file is in the listing
                backup_filename = metadata.get("filename")
                backup_key = f"{prefix}{backup_filename}"
                
                # This is a simple check - for a more thorough check, you might want to use head_object
                if any(obj['Key'] == backup_key for obj in response.get('Contents', [])):
                    backups.append(metadata)
                else:
                    logger.warning(f"Metadata references missing backup file: {backup_key}")
            except Exception as e:
                logger.warning(f"Failed to read metadata file {metadata_key}: {e}")
    
    elif backend == "azure":
        container = config["storage"]["azure"]["container"]
        account_name = config["storage"]["azure"]["account_name"]
        
        # Use DefaultAzureCredential for auth
        credential = DefaultAzureCredential()
        
        # Create blob service client
        blob_service_client = azure.storage.blob.BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=credential
        )
        
        container_client = blob_service_client.get_container_client(container)
        
        # List blobs in the container
        blob_list = container_client.list_blobs()
        
        # Find all metadata files
        metadata_files = [blob.name for blob in blob_list if blob.name.endswith('.meta.json')]
        
        for metadata_name in metadata_files:
            try:
                blob_client = container_client.get_blob_client(metadata_name)
                metadata_content = blob_client.download_blob().readall()
                metadata = json.loads(metadata_content)
                
                # Check if the backup file exists
                backup_filename = metadata.get("filename")
                if backup_filename:
                    backup_blob_client = container_client.get_blob_client(backup_filename)
                    if backup_blob_client.exists():
                        backups.append(metadata)
                    else:
                        logger.warning(f"Metadata references missing backup file: {backup_filename}")
                else:
                    logger.warning(f"Metadata file {metadata_name} missing filename attribute")
            except Exception as e:
                logger.warning(f"Failed to read metadata file {metadata_name}: {e}")
    
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")
    
    # Sort backups by timestamp, newest first
    backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return backups

def print_backup_list(backups: List[Dict[str, Any]]) -> None:
    """Print a formatted list of available backups."""
    if not backups:
        print("No backups found.")
        return
    
    print(f"Found {len(backups)} backup(s):")
    print(f"{'Timestamp':<20} {'Type':<12} {'Size':<10} {'Database':<20} {'Filename':<40}")
    print("-" * 100)
    
    for backup in backups:
        timestamp = backup.get("timestamp", "Unknown")
        if "T" in timestamp:  # ISO format with T separator
            timestamp = timestamp.split("T")[0]  # Just the date part
            
        backup_type = backup.get("type", "Unknown")
        size = backup.get("size", 0)
        # Format size
        if size > 1024 * 1024 * 1024:
            size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
        elif size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.2f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.2f} KB"
        else:
            size_str = f"{size} B"
            
        database = backup.get("database", "Unknown")
        filename = backup.get("filename", "Unknown")
        
        print(f"{timestamp:<20} {backup_type:<12} {size_str:<10} {database:<20} {filename:<40}")

def get_latest_backup(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get the latest backup metadata."""
    backups = list_backups(config)
    if not backups:
        return None
    
    return backups[0]  # Already sorted by timestamp, newest first

def download_backup(backup_metadata: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Download a backup file from the storage backend to a temporary file."""
    backend = config["storage"]["backend"]
    filename = backup_metadata.get("filename")
    
    if not filename:
        raise ValueError("Backup metadata is missing filename")
    
    # Create a temporary file
    temp_dir = tempfile.mkdtemp()
    local_path = os.path.join(temp_dir, filename)
    
    logger.info(f"Downloading backup to {local_path}")
    
    if backend == "local":
        storage_path = config["storage"]["local"]["path"]
        source_path = os.path.join(storage_path, filename)
        
        # Copy the file
        shutil.copy2(source_path, local_path)
    
    elif backend == "s3":
        bucket = config["storage"]["s3"]["bucket"]
        prefix = config["storage"]["s3"]["prefix"]
        region = config["storage"]["s3"]["region"]
        
        s3 = boto3.client('s3', region_name=region)
        
        # Download the file
        s3_key = f"{prefix}{filename}"
        s3.download_file(bucket, s3_key, local_path)
    
    elif backend == "azure":
        container = config["storage"]["azure"]["container"]
        account_name = config["storage"]["azure"]["account_name"]
        
        # Use DefaultAzureCredential for auth
        credential = DefaultAzureCredential()
        
        # Create blob service client
        blob_service_client = azure.storage.blob.BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=credential
        )
        
        container_client = blob_service_client.get_container_client(container)
        
        # Download the file
        blob_client = container_client.get_blob_client(filename)
        with open(local_path, "wb") as f:
            data = blob_client.download_blob()
            f.write(data.readall())
    
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")
    
    logger.info(f"Downloaded backup to {local_path}")
    return local_path

def decrypt_backup(backup_path: str, key: bytes) -> str:
    """Decrypt a backup file."""
    if not backup_path.endswith('.enc'):
        logger.info(f"Backup file is not encrypted: {backup_path}")
        return backup_path
    
    logger.info(f"Decrypting backup: {backup_path}")
    
    decrypted_path = backup_path[:-4]  # Remove .enc extension
    
    try:
        fernet = Fernet(key)
        with open(backup_path, 'rb') as f_in:
            data = f_in.read()
        
        decrypted_data = fernet.decrypt(data)
        
        with open(decrypted_path, 'wb') as f_out:
            f_out.write(decrypted_data)
        
        # Remove the encrypted file
        os.remove(backup_path)
        logger.info(f"Decryption completed: {decrypted_path}")
        return decrypted_path
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise

def decompress_backup(backup_path: str) -> str:
    """Decompress a backup file."""
    if not backup_path.endswith('.gz'):
        logger.info(f"Backup file is not compressed: {backup_path}")
        return backup_path
    
    logger.info(f"Decompressing backup: {backup_path}")
    
    decompressed_path = backup_path[:-3]  # Remove .gz extension
    
    try:
        with gzip.open(backup_path, 'rb') as f_in:
            with open(decompressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove the compressed file
        os.remove(backup_path)
        logger.info(f"Decompression completed: {decompressed_path}")
        return decompressed_path
    except Exception as e:
        logger.error(f"Decompression failed: {e}")
        raise

def restore_database(backup_path: str, config: Dict[str, Any], target_db: Optional[str] = None, 
                    target_host: Optional[str] = None, target_port: Optional[int] = None,
                    target_user: Optional[str] = None) -> bool:
    """Restore a database from a backup file using pg_restore."""
    # Use provided values or defaults from config
    db_host = target_host or config["database"]["host"]
    db_port = target_port or config["database"]["port"]
    db_name = target_db or config["database"]["name"]
    db_user = target_user or config["database"]["user"]
    
    logger.info(f"Restoring database {db_name} from {backup_path}")
    
    # Set environment variables for pg_restore
    env = os.environ.copy()
    # Password should be in PGPASSWORD env var or .pgpass file
    
    # Build pg_restore command
    cmd = [
        "pg_restore",
        "-h", db_host,
        "-p", str(db_port),
        "-U", db_user,
        "-d", db_name,  # Target database
        "-v",           # Verbose output
        "--clean",      # Clean (drop) database objects before recreating
        "--if-exists",  # Don't error if objects don't exist
        "--no-owner",   # Don't set ownership of objects
        "--no-privileges",  # Don't include privileges (GRANT/REVOKE)
        backup_path
    ]
    
    logger.info(f"Running restore command: {' '.join(cmd)}")
    
    try:
        process = subprocess.run(
            cmd, 
            env=env, 
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Restore completed successfully")
        logger.debug(process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Restore failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise RuntimeError(f"Database restore failed: {e}")

def cleanup_temp_files(temp_dir: str) -> None:
    """Clean up temporary files created during the restore process."""
    try:
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary directory {temp_dir}: {e}")

def main():
    """Main function to execute the restore process."""
    parser = argparse.ArgumentParser(description="Database restore script for Elson Trading Bot Platform")
    parser.add_argument("--backup-file", help="The filename of the backup to restore")
    parser.add_argument("--storage-backend", choices=["local", "s3", "azure"], help="Storage backend to use")
    parser.add_argument("--target-db", help="Target database to restore to")
    parser.add_argument("--target-host", help="Target database host")
    parser.add_argument("--target-port", type=int, help="Target database port")
    parser.add_argument("--target-user", help="Target database user")
    parser.add_argument("--list-backups", action="store_true", help="List available backups instead of restoring")
    parser.add_argument("--latest", action="store_true", help="Restore the latest backup")
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config()
        
        # Override storage backend if specified
        if args.storage_backend:
            config["storage"]["backend"] = args.storage_backend
        
        # List backups if requested
        if args.list_backups:
            backups = list_backups(config)
            print_backup_list(backups)
            return 0
        
        # Determine which backup to restore
        backup_metadata = None
        
        if args.latest:
            logger.info("Finding latest backup...")
            backup_metadata = get_latest_backup(config)
            if not backup_metadata:
                logger.error("No backups found")
                return 1
            logger.info(f"Found latest backup: {backup_metadata.get('filename')}")
        
        elif args.backup_file:
            logger.info(f"Looking for specified backup: {args.backup_file}")
            backups = list_backups(config)
            for backup in backups:
                if backup.get("filename") == args.backup_file:
                    backup_metadata = backup
                    break
            
            if not backup_metadata:
                logger.error(f"Backup file not found: {args.backup_file}")
                return 1
        
        else:
            logger.error("Either --backup-file, --latest, or --list-backups must be specified")
            parser.print_help()
            return 1
        
        # Get encryption key
        encryption_key = get_encryption_key(config)
        
        # Download the backup
        temp_file = download_backup(backup_metadata, config)
        temp_dir = os.path.dirname(temp_file)
        
        try:
            # Decrypt if necessary
            if backup_metadata.get("encrypted", False) and encryption_key:
                temp_file = decrypt_backup(temp_file, encryption_key)
            
            # Decompress if necessary
            if backup_metadata.get("compressed", False):
                temp_file = decompress_backup(temp_file)
            
            # Restore the database
            restore_database(
                temp_file, 
                config, 
                target_db=args.target_db,
                target_host=args.target_host,
                target_port=args.target_port,
                target_user=args.target_user
            )
            
            logger.info("Restore process completed successfully")
        finally:
            # Clean up temporary files
            cleanup_temp_files(temp_dir)
        
        return 0
    
    except Exception as e:
        logger.error(f"Restore process failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())