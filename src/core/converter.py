import os
import subprocess
import logging
import shlex
from pathlib import Path

logger = logging.getLogger("core.converter")

class Converter:
    def __init__(self, staging_dir: str):
        self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def export_vm_from_vmware(self, vm_name: str, vcenter_user: str, vcenter_pass: str, vcenter_host: str):
        """
        Uses 'ovftool' to export the VM to the local staging directory.
        Returns the path to the exported .vmdk file.
        """
        # Define the output path (e.g. /tmp/staging/vm_name/vm_name.ovf)
        target_dir = self.staging_dir / vm_name
        target_dir.mkdir(exist_ok=True)
        
        target_ovf = target_dir / f"{vm_name}.ovf"

        # Construct the source URL (vi://user:pass@host/vm_name)
        # SRE NOTE: In production, handle special chars in passwords via URL encoding!
        source_url = f"vi://{vcenter_user}:{vcenter_pass}@{vcenter_host}/{vm_name}"

        logger.info(f"⬇️ Starting Export: {vm_name} -> {target_dir}")
        
        # We use --noSSLVerify for labs. Remove for production.
        cmd = [
            "ovftool",
            "--noSSLVerify",
            "--overwrite",        # Force overwrite if exists
            "--machineOutput",    # Machine readable progress
            source_url,
            str(target_ovf)
        ]

        try:
            # Execute the command and stream output
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Simple blocking wait (In a GUI we would thread this)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise Exception(f"OVF Tool failed: {stderr}")
            
            logger.info("✅ Export complete.")
            
            # Find the VMDK file (ovftool might rename it slightly)
            # Usually it is vm_name-disk1.vmdk
            vmdk_files = list(target_dir.glob("*.vmdk"))
            if not vmdk_files:
                raise Exception("Export finished but no .vmdk file found!")
            
            return vmdk_files[0] # Return the first disk found

        except Exception as e:
            logger.error(f"❌ Export Error: {e}")
            raise

    def convert_vmdk_to_qcow2(self, vmdk_path: Path):
        """
        Uses 'qemu-img' to convert VMDK to QCOW2.
        Returns the path to the new .qcow2 file.
        """
        qcow2_path = vmdk_path.with_suffix(".qcow2")
        
        logger.info(f"🔄 Converting disk: {vmdk_path.name} -> qcow2...")
        
        cmd = [
            "qemu-img", "convert",
            "-f", "vmdk",      # Input format
            "-O", "qcow2",     # Output format
            "-p",              # Show progress
            str(vmdk_path),
            str(qcow2_path)
        ]
        
        try:
            # We use os.system here to allow the user to see the native progress bar of qemu-img
            # In a strict automation tool, we would capture stdout instead.
            exit_code = os.system(" ".join(cmd))
            
            if exit_code != 0:
                raise Exception("qemu-img conversion failed.")
            
            logger.info(f"✅ Conversion successful: {qcow2_path}")
            return qcow2_path

        except Exception as e:
            logger.error(f"❌ Conversion Error: {e}")
            raise