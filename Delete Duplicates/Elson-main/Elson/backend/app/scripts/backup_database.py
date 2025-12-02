#!/usr/bin/env python
"""
Database backup script for Elson Trading Bot Platform.

This script creates automated backups of the PostgreSQL database, encrypts them,
and uploads them to a configured storage backend (local, S3, or Azure Blob Storage).
It also handles backup rotation and retention based on policy.

Usage:
    python backup_database.py [--full] [--storage-backend {local,s3,azure}]
    
Options:
    --full              Perform a full backup instead of an incremental backup
    --storage-backend   Specify where to store the backup (default: as configured)
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
import hashlib
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Any

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
        logging.FileHandler("/var/log/elson/database-backup.log")
    ]
)
logger = logging.getLogger("database-backup")

# Default configuration
DEFAULT_CONFIG = {
    "backup_dir": "/backup",
    "retention": {
        "daily": 7,      # Keep daily backups for 7 days
        "weekly": 4,     # Keep weekly backups for 4 weeks
        "monthly": 12,   # Keep monthly backups for 12 months
        "yearly": 7      # Keep yearly backups for 7 years
    },
    "storage": {
        "backend": "local",  # local, s3, or azure
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
    
    # Generate new key
    key = Fernet.generate_key()
    try:
        # Save key to file
        key_dir = os.path.dirname(key_path)
        if not os.path.exists(key_dir):
            os.makedirs(key_dir)
        with open(key_path, 'wb') as f:
            f.write(key)
        logger.info(f"Generated new encryption key and saved to {key_path}")
    except Exception as e:
        logger.warning(f"Failed to save encryption key: {e}")
    
    return key

def create_backup(config: Dict[str, Any], full_backup: bool = False) -> str:
    """Create a database backup using pg_dump."""
    db_host = config["database"]["host"]
    db_port = config["database"]["port"]
    db_name = config["database"]["name"]
    db_user = config["database"]["user"]
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_id = str(uuid.uuid4())[:8]
    backup_type = "full" if full_backup else "incremental"
    filename = f"{db_name}_{timestamp}_{backup_type}_{backup_id}.sql"
    backup_path = os.path.join(config["backup_dir"], filename)
    
    # Ensure backup directory exists
    os.makedirs(config["backup_dir"], exist_ok=True)
    
    # Set environment variables for pg_dump
    env = os.environ.copy()
    # Password should be in PGPASSWORD env var or .pgpass file
    
    # Build pg_dump command
    cmd = [
        "pg_dump",
        "-h", db_host,
        "-p", str(db_port),
        "-U", db_user,
        "-F", "c",  # Custom format for restorability
        "-v",       # Verbose output
        "-f", backup_path
    ]
    
    if not full_backup:
        # For incremental, we could use --schema-only or other specific options
        # This is a simplified example
        pass
    
    cmd.append(db_name)
    
    logger.info(f"Starting {backup_type} backup of {db_name} database")
    
    try:
        process = subprocess.run(
            cmd, 
            env=env, 
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Backup completed successfully: {backup_path}")
        logger.debug(process.stdout)
        return backup_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise RuntimeError(f"Database backup failed: {e}")

def compress_backup(backup_path: str) -> str:
    """Compress the backup file using gzip."""
    compressed_path = f"{backup_path}.gz"
    logger.info(f"Compressing backup: {backup_path} -> {compressed_path}")
    
    try:
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove the original file
        os.remove(backup_path)
        logger.info(f"Compression completed: {compressed_path}")
        return compressed_path
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        raise

def encrypt_backup(backup_path: str, key: bytes) -> str:
    """Encrypt the backup file."""
    encrypted_path = f"{backup_path}.enc"
    logger.info(f"Encrypting backup: {backup_path} -> {encrypted_path}")
    
    try:
        fernet = Fernet(key)
        with open(backup_path, 'rb') as f_in:
            data = f_in.read()
        
        encrypted_data = fernet.encrypt(data)
        
        with open(encrypted_path, 'wb') as f_out:
            f_out.write(encrypted_data)
        
        # Remove the unencrypted file
        os.remove(backup_path)
        logger.info(f"Encryption completed: {encrypted_path}")
        return encrypted_path
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_metadata(backup_path: str, config: Dict[str, Any], full_backup: bool) -> Dict[str, Any]:
    """Create metadata for the backup."""
    filename = os.path.basename(backup_path)
    checksum = calculate_checksum(backup_path)
    size = os.path.getsize(backup_path)
    
    metadata = {
        "filename": filename,
        "timestamp": datetime.datetime.now().isoformat(),
        "database": config["database"]["name"],
        "type": "full" if full_backup else "incremental",
        "size": size,
        "checksum": checksum,
        "checksum_algorithm": "sha256",
        "compressed": filename.endswith(".gz"),
        "encrypted": filename.endswith(".enc"),
        "version": "1.0"
    }
    
    return metadata

def save_metadata(metadata: Dict[str, Any], backup_path: str) -> str:
    """Save metadata to a file."""
    metadata_path = f"{backup_path}.meta.json"
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Metadata saved to {metadata_path}")
    return metadata_path

def upload_to_storage(backup_path: str, metadata_path: str, config: Dict[str, Any]) -> None:
    """Upload backup and metadata to the configured storage backend."""
    backend = config["storage"]["backend"]
    
    if backend == "local":
        # For local storage, we just move the files to the specified directory
        storage_path = config["storage"]["local"]["path"]
        os.makedirs(storage_path, exist_ok=True)
        
        backup_filename = os.path.basename(backup_path)
        metadata_filename = os.path.basename(metadata_path)
        
        target_backup_path = os.path.join(storage_path, backup_filename)
        target_metadata_path = os.path.join(storage_path, metadata_filename)
        
        shutil.move(backup_path, target_backup_path)
        shutil.move(metadata_path, target_metadata_path)
        
        logger.info(f"Backup saved locally to {target_backup_path}")
    
    elif backend == "s3":
        # Upload to S3
        bucket = config["storage"]["s3"]["bucket"]
        prefix = config["storage"]["s3"]["prefix"]
        region = config["storage"]["s3"]["region"]
        
        s3 = boto3.client('s3', region_name=region)
        
        backup_filename = os.path.basename(backup_path)
        metadata_filename = os.path.basename(metadata_path)
        
        s3_backup_key = f"{prefix}{backup_filename}"
        s3_metadata_key = f"{prefix}{metadata_filename}"
        
        # Upload backup
        s3.upload_file(
            backup_path, 
            bucket, 
            s3_backup_key,
            ExtraArgs={'StorageClass': 'STANDARD_IA'}
        )
        
        # Upload metadata
        s3.upload_file(
            metadata_path, 
            bucket, 
            s3_metadata_key
        )
        
        logger.info(f"Backup uploaded to S3: s3://{bucket}/{s3_backup_key}")
        
        # Remove local files
        os.remove(backup_path)
        os.remove(metadata_path)
    
    elif backend == "azure":
        # Upload to Azure Blob Storage
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
        
        backup_filename = os.path.basename(backup_path)
        metadata_filename = os.path.basename(metadata_path)
        
        # Upload backup
        with open(backup_path, "rb") as data:
            container_client.upload_blob(
                name=backup_filename,
                data=data,
                overwrite=True
            )
        
        # Upload metadata
        with open(metadata_path, "rb") as data:
            container_client.upload_blob(
                name=metadata_filename,
                data=data,
                overwrite=True
            )
        
        logger.info(f"Backup uploaded to Azure: {account_name}/{container}/{backup_filename}")
        
        # Remove local files
        os.remove(backup_path)
        os.remove(metadata_path)
    
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")

def classify_backup(timestamp: datetime.datetime) -> str:
    """Classify a backup as daily, weekly, monthly, or yearly."""
    # If it's the first day of the year, it's a yearly backup
    if timestamp.month == 1 and timestamp.day == 1:
        return "yearly"
    
    # If it's the first day of the month, it's a monthly backup
    if timestamp.day == 1:
        return "monthly"
    
    # If it's Monday, it's a weekly backup
    if timestamp.weekday() == 0:  # Monday
        return "weekly"
    
    # Otherwise, it's a daily backup
    return "daily"

def apply_retention_policy(config: Dict[str, Any]) -> None:
    """Apply retention policy to existing backups."""
    backend = config["storage"]["backend"]
    retention = config["retention"]
    
    now = datetime.datetime.now()
    
    if backend == "local":
        storage_path = config["storage"]["local"]["path"]
        
        # Find all backup files
        backup_files = [f for f in os.listdir(storage_path) if f.endswith('.sql.gz.enc') or f.endswith('.sql.gz')]
        
        for backup_file in backup_files:
            # Parse the timestamp from the filename
            parts = backup_file.split('_')
            if len(parts) >= 2:
                try:
                    timestamp_str = parts[1]
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d")
                    
                    # Classify the backup
                    classification = classify_backup(timestamp)
                    
                    # Check if it should be retained
                    age_days = (now - timestamp).days
                    
                    if classification == "daily" and age_days > retention["daily"]:
                        file_path = os.path.join(storage_path, backup_file)
                        metadata_path = f"{file_path}.meta.json"
                        
                        os.remove(file_path)
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                            
                        logger.info(f"Deleted expired daily backup: {backup_file}")
                    
                    elif classification == "weekly" and age_days > retention["weekly"] * 7:
                        file_path = os.path.join(storage_path, backup_file)
                        metadata_path = f"{file_path}.meta.json"
                        
                        os.remove(file_path)
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                            
                        logger.info(f"Deleted expired weekly backup: {backup_file}")
                    
                    elif classification == "monthly" and age_days > retention["monthly"] * 30:
                        file_path = os.path.join(storage_path, backup_file)
                        metadata_path = f"{file_path}.meta.json"
                        
                        os.remove(file_path)
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                            
                        logger.info(f"Deleted expired monthly backup: {backup_file}")
                    
                    elif classification == "yearly" and age_days > retention["yearly"] * 365:
                        file_path = os.path.join(storage_path, backup_file)
                        metadata_path = f"{file_path}.meta.json"
                        
                        os.remove(file_path)
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                            
                        logger.info(f"Deleted expired yearly backup: {backup_file}")
                
                except Exception as e:
                    logger.warning(f"Failed to parse timestamp from {backup_file}: {e}")
    
    elif backend == "s3":
        # Logic for applying retention policy to S3 backups would go here
        # This would involve listing objects in the bucket, parsing their timestamps,
        # and deleting expired backups based on the retention policy
        pass
    
    elif backend == "azure":
        # Logic for applying retention policy to Azure backups would go here
        # Similar to S3, but using Azure Blob Storage APIs
        pass

def main():
    """Main function to execute the backup process."""
    parser = argparse.ArgumentParser(description="Database backup script for Elson Trading Bot Platform")
    parser.add_argument("--full", action="store_true", help="Perform a full backup instead of an incremental backup")
    parser.add_argument("--storage-backend", choices=["local", "s3", "azure"], help="Storage backend to use")
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config()
        
        # Override storage backend if specified
        if args.storage_backend:
            config["storage"]["backend"] = args.storage_backend
        
        # Get encryption key
        encryption_key = get_encryption_key(config)
        
        # Create backup
        backup_path = create_backup(config, args.full)
        
        # Compress backup if enabled
        if config["compression"]["enabled"]:
            backup_path = compress_backup(backup_path)
        
        # Encrypt backup if enabled
        if config["encryption"]["enabled"] and encryption_key:
            backup_path = encrypt_backup(backup_path, encryption_key)
        
        # Create and save metadata
        metadata = create_metadata(backup_path, config, args.full)
        metadata_path = save_metadata(metadata, backup_path)
        
        # Upload to storage
        upload_to_storage(backup_path, metadata_path, config)
        
        # Apply retention policy
        apply_retention_policy(config)
        
        logger.info("Backup process completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Backup process failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())