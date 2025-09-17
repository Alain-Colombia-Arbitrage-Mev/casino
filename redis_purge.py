#!/usr/bin/env python3
"""
🧹 REDIS PURGE UTILITY - Limpieza Completa de Datos
Funciones para purgar y resetear todos los datos de Redis
"""

import redis
import json
import argparse
from datetime import datetime

class RedisPurgeUtility:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        """Initialize Redis purge utility"""
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )

    def log_message(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def test_connection(self):
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            self.log_message("✅ Redis connection successful")
            return True
        except Exception as e:
            self.log_message(f"❌ Redis connection failed: {e}", "ERROR")
            return False

    def get_roulette_keys(self):
        """Get all roulette-related keys"""
        try:
            keys = self.redis_client.keys("roulette:*")
            return keys
        except Exception as e:
            self.log_message(f"❌ Error getting keys: {e}", "ERROR")
            return []

    def get_ml_keys(self):
        """Get all ML-related keys"""
        try:
            keys = self.redis_client.keys("ml:*")
            return keys
        except Exception as e:
            self.log_message(f"❌ Error getting ML keys: {e}", "ERROR")
            return []

    def backup_data(self, backup_file="redis_backup.json"):
        """Create backup of all roulette data before purging"""
        try:
            self.log_message("🔄 Creating backup of Redis data...")

            backup_data = {}

            # Backup roulette data
            roulette_keys = self.get_roulette_keys()
            backup_data['roulette'] = {}

            for key in roulette_keys:
                try:
                    key_type = self.redis_client.type(key)
                    if key_type == 'string':
                        backup_data['roulette'][key] = self.redis_client.get(key)
                    elif key_type == 'list':
                        backup_data['roulette'][key] = self.redis_client.lrange(key, 0, -1)
                    elif key_type == 'hash':
                        backup_data['roulette'][key] = self.redis_client.hgetall(key)
                    elif key_type == 'set':
                        backup_data['roulette'][key] = list(self.redis_client.smembers(key))
                except Exception as e:
                    self.log_message(f"⚠️ Error backing up key {key}: {e}", "WARNING")

            # Backup ML data
            ml_keys = self.get_ml_keys()
            backup_data['ml'] = {}

            for key in ml_keys:
                try:
                    key_type = self.redis_client.type(key)
                    if key_type == 'string':
                        backup_data['ml'][key] = self.redis_client.get(key)
                    elif key_type == 'list':
                        backup_data['ml'][key] = self.redis_client.lrange(key, 0, -1)
                    elif key_type == 'hash':
                        backup_data['ml'][key] = self.redis_client.hgetall(key)
                except Exception as e:
                    self.log_message(f"⚠️ Error backing up ML key {key}: {e}", "WARNING")

            # Save backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            self.log_message(f"✅ Backup saved to {backup_file}")
            return True

        except Exception as e:
            self.log_message(f"❌ Backup failed: {e}", "ERROR")
            return False

    def purge_roulette_data(self):
        """Purge all roulette data"""
        try:
            self.log_message("🧹 Purging roulette data...")

            roulette_keys = self.get_roulette_keys()
            if not roulette_keys:
                self.log_message("ℹ️ No roulette keys found to delete")
                return True

            # Delete in batches for performance
            batch_size = 100
            deleted_count = 0

            for i in range(0, len(roulette_keys), batch_size):
                batch = roulette_keys[i:i+batch_size]
                deleted_count += self.redis_client.delete(*batch)

            self.log_message(f"✅ Deleted {deleted_count} roulette keys")
            return True

        except Exception as e:
            self.log_message(f"❌ Purge roulette data failed: {e}", "ERROR")
            return False

    def purge_ml_data(self):
        """Purge all ML data (strategies, performance, etc.)"""
        try:
            self.log_message("🧹 Purging ML data...")

            ml_keys = self.get_ml_keys()
            if not ml_keys:
                self.log_message("ℹ️ No ML keys found to delete")
                return True

            # Delete in batches
            batch_size = 100
            deleted_count = 0

            for i in range(0, len(ml_keys), batch_size):
                batch = ml_keys[i:i+batch_size]
                deleted_count += self.redis_client.delete(*batch)

            self.log_message(f"✅ Deleted {deleted_count} ML keys")
            return True

        except Exception as e:
            self.log_message(f"❌ Purge ML data failed: {e}", "ERROR")
            return False

    def purge_all_casino_data(self):
        """Purge ALL casino-related data (roulette + ML)"""
        try:
            self.log_message("🧹 Starting COMPLETE purge of all casino data...")

            success = True
            success &= self.purge_roulette_data()
            success &= self.purge_ml_data()

            if success:
                self.log_message("✅ COMPLETE purge successful!")
            else:
                self.log_message("⚠️ Purge completed with some errors", "WARNING")

            return success

        except Exception as e:
            self.log_message(f"❌ Complete purge failed: {e}", "ERROR")
            return False

    def reset_to_clean_state(self):
        """Reset to completely clean state (keep only essential keys)"""
        try:
            self.log_message("🔄 Resetting to clean state...")

            # Get all keys
            all_keys = self.redis_client.keys("*")

            # Essential keys to preserve (if any)
            preserve_keys = [
                # Add any keys you want to preserve
            ]

            keys_to_delete = [key for key in all_keys if key not in preserve_keys]

            if keys_to_delete:
                deleted_count = self.redis_client.delete(*keys_to_delete)
                self.log_message(f"✅ Deleted {deleted_count} keys, preserved {len(preserve_keys)} keys")
            else:
                self.log_message("ℹ️ No keys to delete")

            return True

        except Exception as e:
            self.log_message(f"❌ Reset failed: {e}", "ERROR")
            return False

    def show_data_summary(self):
        """Show summary of current data in Redis"""
        try:
            self.log_message("📊 Redis Data Summary:")

            # Roulette keys
            roulette_keys = self.get_roulette_keys()
            self.log_message(f"   Roulette keys: {len(roulette_keys)}")

            # ML keys
            ml_keys = self.get_ml_keys()
            self.log_message(f"   ML keys: {len(ml_keys)}")

            # Total keys
            all_keys = self.redis_client.keys("*")
            self.log_message(f"   Total keys: {len(all_keys)}")

            # Memory usage
            info = self.redis_client.info('memory')
            used_memory = info.get('used_memory_human', 'Unknown')
            self.log_message(f"   Memory used: {used_memory}")

            # Show some example data
            if roulette_keys:
                self.log_message("📋 Sample roulette keys:")
                for key in roulette_keys[:5]:
                    self.log_message(f"   - {key}")
                if len(roulette_keys) > 5:
                    self.log_message(f"   ... and {len(roulette_keys) - 5} more")

            return True

        except Exception as e:
            self.log_message(f"❌ Show summary failed: {e}", "ERROR")
            return False

def main():
    parser = argparse.ArgumentParser(description='Redis Purge Utility for AI Casino')
    parser.add_argument('--action', choices=[
        'backup', 'purge-roulette', 'purge-ml', 'purge-all', 'reset', 'summary'
    ], required=True, help='Action to perform')
    parser.add_argument('--backup-file', default='redis_backup.json',
                       help='Backup file name (default: redis_backup.json)')
    parser.add_argument('--host', default='localhost', help='Redis host')
    parser.add_argument('--port', default=6379, type=int, help='Redis port')
    parser.add_argument('--confirm', action='store_true',
                       help='Confirm destructive operations without prompt')

    args = parser.parse_args()

    # Initialize purge utility
    purge = RedisPurgeUtility(redis_host=args.host, redis_port=args.port)

    # Test connection
    if not purge.test_connection():
        return 1

    # Execute action
    if args.action == 'summary':
        purge.show_data_summary()

    elif args.action == 'backup':
        purge.backup_data(args.backup_file)

    elif args.action == 'purge-roulette':
        if not args.confirm:
            confirm = input("⚠️ This will DELETE all roulette data. Continue? (yes/NO): ")
            if confirm.lower() != 'yes':
                print("❌ Operation cancelled")
                return 1
        purge.purge_roulette_data()

    elif args.action == 'purge-ml':
        if not args.confirm:
            confirm = input("⚠️ This will DELETE all ML data. Continue? (yes/NO): ")
            if confirm.lower() != 'yes':
                print("❌ Operation cancelled")
                return 1
        purge.purge_ml_data()

    elif args.action == 'purge-all':
        if not args.confirm:
            confirm = input("⚠️ This will DELETE ALL casino data. Continue? (yes/NO): ")
            if confirm.lower() != 'yes':
                print("❌ Operation cancelled")
                return 1
        purge.purge_all_casino_data()

    elif args.action == 'reset':
        if not args.confirm:
            confirm = input("⚠️ This will RESET Redis to clean state. Continue? (yes/NO): ")
            if confirm.lower() != 'yes':
                print("❌ Operation cancelled")
                return 1
        purge.reset_to_clean_state()

    return 0

if __name__ == "__main__":
    exit(main())