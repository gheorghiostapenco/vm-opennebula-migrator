# VMware to OpenNebula Migration Tool

An automated infrastructure-as-code tool designed to facilitate the migration of Virtual Machines from VMware vSphere/ESXi to OpenNebula. This tool handles the export, disk conversion, and registration processes, acting as a bridge between proprietary and open-source virtualization stacks.

## Project Overview

With the shifting landscape of virtualization licensing, many enterprises are seeking open-source alternatives. This project solves the technical challenge of migrating workloads by automating the "heavy lifting" of disk format conversion and API interaction.

### Key Features

* **Multi-Cloud Support:** Connects natively to both VMware vSphere (via pyvmomi) and OpenNebula (via XML-RPC).
* **Automated Conversion:** Orchestrates `ovftool` and `qemu-img` to convert VMDK disks to QCOW2 format.
* **Safety First:** Includes "Dry Run" and "Pre-flight Check" modes to validate environments before executing changes.
* **SRE-Centric Design:** Implements robust logging, modular architecture, and environment variable separation for secrets.

## Architecture

The pipeline follows a linear extract-transform-load (ETL) pattern:

1.  **Extract:** Stream VM data from ESXi to a local staging server using `ovftool`.
2.  **Transform:** Convert monolithic VMDK files to sparse QCOW2 images using `qemu-img`.
3.  **Load:** Upload and register the new image artifacts into the OpenNebula datastore via the OCA API.

## Prerequisites

* **Python 3.10+**
* **System Tools:**
    * `qemu-img` (Required for disk conversion)
    * `ovftool` (Required for VMware export)
* **Network:** Access to both vCenter (Port 443) and OpenNebula Frontend (Port 2633).

## Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/yourusername/vm-migrator.git](https://github.com/yourusername/vm-migrator.git)
    cd vm-migrator
    ```

2.  Create a virtual environment and install dependencies:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  Configure the application:
    ```bash
    cp config/settings.yaml.example config/settings.yaml
    cp .env.example .env
    ```

4.  Edit `.env` with your credentials:
    ```bash
    VMWARE_PASSWORD="YourPassword"
    OPENNEBULA_AUTH="user:token"
    ```

## Usage

The tool uses a CLI interface managed by `argparse`.

### 1. Pre-flight Check
Validate that all system tools and API connections are operational.

```bash
python src/main.py check-env
```

2. List Available VMs
Retrieve a list of VMs from the source vCenter to identify migration targets.

```bash
python src/main.py list-vms --pattern "web-server"
```

3. Migrate a VM
Execute the migration pipeline.

Standard Migration (Full):
```bash
python src/main.py migrate Web-App-01
```
Simulation (Dry Run): Verify logic without moving data.
```bash
python src/main.py migrate Web-App-01 --mode dry-run
```

Development Mode (Skip Export): Use this if you already have the .vmdk file in the staging directory and only want to test conversion and upload.
```bash
python src/main.py migrate Web-App-01 --mode local
```

Technical Implementation
Language: Python 3

VMware API: pyvmomi

OpenNebula API: pyone

Configuration: YAML + DotEnv (12-Factor App compliance)

### Disclaimer
This tool is a portfolio project and proof of concept. While it handles standard migration tasks, please perform adequate testing in a non-production environment before using it on critical infrastructure.
