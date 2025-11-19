import pyone
import logging
import os

logger = logging.getLogger("opennebula_connector")

class OpenNebulaClient:
    def __init__(self, endpoint, auth_token):
        """
        endpoint: http://localhost:2633/RPC2
        auth_token: user:password
        """
        self.endpoint = endpoint
        self.auth_token = auth_token
        self.one = None

    def connect(self):
        try:
            # logger.info(f"Connecting to OpenNebula XML-RPC: {self.endpoint}")
            self.one = pyone.OneServer(self.endpoint, session=self.auth_token)
            # Test connection
            version = self.one.system.version()
            # logger.info(f"✅ Connected to OpenNebula. Version: {version}")
        except Exception as e:
            logger.error(f"❌ OpenNebula Connection Failed: {str(e)}")
            raise

    def register_image(self, vm_name: str, qcow2_path: str, ds_id: int):
        """
        Registers the QCOW2 file as a new Image in OpenNebula.
        """
        if not self.one:
            self.connect()

        # SRE Best Practice: Use a unique name to avoid collisions
        image_name = f"{vm_name}-disk0"
        
        # Define the OpenNebula Image Template
        # In a real scenario, PATH should be a URL or a path accessible by the OpenNebula FE
        image_template = f"""
            NAME = "{image_name}"
            PATH = "{qcow2_path}"
            TYPE = "OS"
            DRIVER = "qcow2"
            DESCRIPTION = "Migrated from VMware by SRE-Tool"
        """

        logger.info(f"☁️  Registering image '{image_name}' to Datastore {ds_id}...")

        try:
            # one.image.allocate(session, template, datastore_id)
            image_id = self.one.image.allocate(image_template, int(ds_id))
            logger.info(f"✅ Image Registered Successfully! ID: {image_id}")
            return image_id
        except Exception as e:
            logger.error(f"❌ Failed to register image: {e}")
            raise