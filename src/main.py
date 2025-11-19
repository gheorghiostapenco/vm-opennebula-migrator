import argparse
import logging.config
import yaml
import os
import glob
import sys
from dotenv import load_dotenv
from pathlib import Path

# Import custom modules
from connectors.vmware_api import VMwareClient
from connectors.opennebula_api import OpenNebulaClient
from core.converter import Converter

# Load Environment Variables
load_dotenv()
SETTINGS = {}
logger = logging.getLogger("main")

def setup():
    """Load config and logging settings."""
    global SETTINGS
    
    # Load Logging
    config_path = os.path.join("config", "logging.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Load Settings
    settings_path = os.path.join("config", "settings.yaml")
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            SETTINGS = yaml.safe_load(f)
    else:
        print("❌ Config file not found!")
        sys.exit(1)

def cmd_check_env(args):
    """Pre-flight check."""
    print("🔍 Starting Pre-flight checks...")
    if os.system("which qemu-img > /dev/null 2>&1") == 0:
        print("✅ qemu-img found")
    else:
        print("❌ qemu-img missing")

def cmd_list_vms(args):
    """List VMs on VMware."""
    print(f"Listing VMs (Pattern: {args.pattern})...")
    # Logic skipped for brevity

def cmd_migrate(args):
    """
    🚀 Run the migration pipeline.
    """
    vm_name = args.vm_name
    mode = args.mode.lower()

    # 1. Setup
    staging_path = SETTINGS['app']['staging_path']
    converter = Converter(staging_path)
    
    print(f"\n🚀 Starting Migration Job for: {vm_name} [Mode: {mode}]")
    print("="*60)

    # 2. Dry Run Check
    if mode == "dry-run":
        print("⚠️  DRY RUN: Skipping actual data movement.")
        return

    # 3. Export Logic
    vmdk_path = None
    try:
        if mode == "full":
            print("⬇️  Exporting from VMware...")
            # Real export logic would go here:
            # vmdk_path = converter.export_vm_from_vmware(...)
            
            # For Demo: Fail if 'full' because we don't have a server
            print("⚠️  (Simulated Export)...")
            # Check if file exists anyway to proceed
            search_pattern = os.path.join(staging_path, vm_name, "*.vmdk")
            potential_files = glob.glob(search_pattern)
            if potential_files:
                vmdk_path = Path(potential_files[0])
            else:
                print("❌ Simulation failed: No local file to use as fallback.")
                sys.exit(1)

        elif mode == "local":
            # Dev Mode: Look for existing file
            search_pattern = os.path.join(staging_path, vm_name, "*.vmdk")
            potential_files = glob.glob(search_pattern)
            if potential_files:
                vmdk_path = Path(potential_files[0])
                print(f"⏩ Skipped Export. Using: {vmdk_path}")
            else:
                print(f"❌ No .vmdk found in {search_pattern}")
                sys.exit(1)
        
    except Exception as e:
        print(f"❌ Export Error: {e}")
        sys.exit(1)

    # 4. Convert Logic
    qcow2_path = None
    try:
        print("🔄 Phase 2: Converting to QCOW2...")
        if vmdk_path:
            qcow2_path = converter.convert_vmdk_to_qcow2(vmdk_path)
            print(f"✅ Conversion Complete: {qcow2_path}")
    except Exception as e:
        print(f"❌ Conversion Failed: {e}")
        sys.exit(1)

    # 5. Upload Logic
    print("☁️  Phase 3: Uploading to OpenNebula...")
    one_auth = os.getenv("OPENNEBULA_AUTH")
    one_cfg = SETTINGS['opennebula']

    try:
        if not one_auth:
            print("❌ OPENNEBULA_AUTH missing in .env")
            
        elif qcow2_path:
            one_client = OpenNebulaClient(one_cfg['endpoint'], one_auth)
            image_id = one_client.register_image(
                vm_name, 
                str(qcow2_path.absolute()), 
                one_cfg['default_datastore_id']
            )
            print(f"✅ Upload Complete! New Image ID: {image_id}")

    except Exception as e:
        print(f"❌ Upload Failed (Expected if no server): {e}")

    print(f"🎉 Pipeline Finished for {vm_name}!")

def main():
    setup()
    
    # Create Top-level Parser
    parser = argparse.ArgumentParser(description="VMware to OpenNebula Migration Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: check-env
    subparsers.add_parser('check-env', help="Pre-flight check")

    # Command: list-vms
    parser_list = subparsers.add_parser('list-vms', help="List available VMs")
    parser_list.add_argument('--pattern', type=str, default="", help="Filter VMs by name")

    # Command: migrate
    parser_migrate = subparsers.add_parser('migrate', help="Migrate a VM")
    parser_migrate.add_argument('vm_name', type=str, help="Name of the VM")
    parser_migrate.add_argument('--mode', type=str, default='full', choices=['full', 'local', 'dry-run'], 
                                help="Mode: full, local (skip export), dry-run")

    # Parse
    args = parser.parse_args()

    # Route to function
    if args.command == 'check-env':
        cmd_check_env(args)
    elif args.command == 'list-vms':
        cmd_list_vms(args)
    elif args.command == 'migrate':
        cmd_migrate(args)

if __name__ == "__main__":
    main()