import ipaddress
import subprocess
import random


def generate_key_pair():
    """Generates a new WireGuard key pair."""
    private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
    public_key = subprocess.check_output(['wg', 'pubkey'], input=private_key.encode()).decode().strip()

    return private_key, public_key


def get_assigned_ips():
    """Returns a set of all IP addresses that have been assigned to WireGuard clients."""
    assigned_ips = set()

    output = subprocess.check_output(['wg', 'show', 'wg0'])
    for line in output.splitlines():
        if b'peer' in line:
            parts = line.decode().split()
            assigned_ips.add(parts[3].split('/')[0])

    return assigned_ips


def get_available_ip_address(subnet, assigned_ips):
    """Returns an available IP address within the specified subnet that is not already assigned."""
    subnet = ipaddress.ip_network(subnet)

    for ip in subnet.hosts():
        if str(ip) not in assigned_ips:
            return str(ip)

    return None
