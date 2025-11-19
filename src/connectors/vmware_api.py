import ssl
import atexit
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import logging

logger = logging.getLogger("vmware_connector")

class VMwareClient:
    def __init__(self, host, user, password, port=443, verify_ssl=False):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.verify_ssl = verify_ssl
        self.service_instance = None
        self.content = None

    def connect(self):
        """Establish connection to vCenter/ESXi"""
        context = None
        if not self.verify_ssl:
            context = ssl._create_unverified_context()
        
        try:
            logger.info(f"Connecting to VMware host: {self.host}")
            self.service_instance = SmartConnect(
                host=self.host,
                user=self.user,
                pwd=self.password,
                port=self.port,
                sslContext=context
            )
            self.content = self.service_instance.RetrieveContent()
            atexit.register(Disconnect, self.service_instance)
            logger.info("✅ Connected to VMware successfully.")
        except Exception as e:
            logger.error(f"❌ VMware Connection Failed: {str(e)}")
            raise

    def list_vms(self):
        """Return a list of all VMs with their power state"""
        if not self.content:
            self.connect()
        
        container = self.content.rootFolder
        view_type = [vim.VirtualMachine]
        recursive = True
        
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, recursive
        )
        
        vms = []
        for vm in container_view.view:
            # SRE Note: We only care about specific fields to save memory
            summary = vm.summary
            vms.append({
                "name": summary.config.name,
                "uuid": summary.config.uuid,
                "power_state": summary.runtime.powerState, # poweredOn / poweredOff
                "cpus": summary.config.numCpu,
                "memory_mb": summary.config.memorySizeMB
            })
        
        return vms

    def get_vm_by_name(self, name):
        """Find a specific VM object"""
        # In a real production app, we would use a search index for speed
        # For this project, iterating is acceptable.
        if not self.content:
            self.connect()
            
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, [vim.VirtualMachine], True
        )
        
        for vm in container.view:
            if vm.name == name:
                return vm
        return None