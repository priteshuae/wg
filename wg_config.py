import io
import subprocess
from datetime import datetime, timedelta
import sys
import argparse
import qrcode
from wg_database import get_client_by_name, save_client_to_database
from wg_utils import *


SERVER_PORT = 51820
SERVER_PRIVATE_IP = '10.0.0.1'
SERVER_PUBLIC_IP = subprocess.check_output(['curl', 'ifconfig.me']).decode().strip()
SERVER_DNS = '1.1.1.1'
# private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
# public_key = subprocess.check_output(['wg', 'pubkey'], input=private_key.encode()).decode().strip()
assigned_ips= get_assigned_ips()
SERVER_PUBLIC_KEY = generate_key_pair()[0]

subnet_prefix_length = 24



def create_wireguard_interface():
    """Creates a new WireGuard interface with a random private key."""
    private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
    subprocess.check_output(['wg', 'set', 'wg0', 'listen-port', str(SERVER_PORT), 'private-key', io.StringIO(private_key)])
    subprocess.check_output(['ip', 'address', 'add', f'{SERVER_PRIVATE_IP}/{subnet_prefix_length}', 'dev', 'wg0'])
    subprocess.check_output(['sysctl', '-w', 'net.ipv4.ip_forward=1'])
    subprocess.check_output(['iptables', '-A', 'FORWARD', '-i', 'wg0', '-j', 'ACCEPT'])
    subprocess.check_output(['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', 'eth0', '-j', 'MASQUERADE'])
    subprocess.check_output(['wg', 'showconf', 'wg0'])


def generate_client_config(name, email):
    """Generates a new WireGuard client configuration."""
    client = get_client_by_name(name)

    if client is None:
        return None

    config = f"""
[Interface]
Address = {client['ip_address']}/{subnet_prefix_length}
PrivateKey = {client['private_key']}
DNS = {SERVER_DNS}

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
AllowedIPs = 0.0.0.0/0
Endpoint = {SERVER_PUBLIC_IP}:{SERVER_PORT}
PersistentKeepalive = 21
"""

    return config


def generate_qr_code(name, email):
    """Generates a new QR code for a WireGuard client."""
    config = generate_client_config(name, email)

    if config is None:
        return None

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(config)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf)
    qr_data = buf.getvalue()

    return qr_data


def get_expiry_date():
    """Returns the expiry date for a new WireGuard client."""
    return datetime.now() + timedelta(days=30)


def create_client(name, email):
    """Creates a new WireGuard client with a random private key and IP address."""
    private_key, public_key = generate_key_pair()
    ip_address = get_available_ip_address(f'10.0.0', assigned_ips)
    expiry = get_expiry_date().isoformat()

    save_client_to_database(name, email, ip_address, public_key, expiry)

    return {
        'name': name,
        'email': email,
        'ip_address': ip_address,
        'private_key': private_key,
        'public_key': public_key,
        'expiry': datetime.fromisoformat(expiry)
    }

def main():
    parser = argparse.ArgumentParser(description='Manage WireGuard clients.')
    subparsers = parser.add_subparsers(title='subcommands', dest='command')
    create_parser = subparsers.add_parser('create', help='Create a new WireGuard client.')
    create_parser.add_argument('name', type=str, help='The name of the client.')
    create_parser.add_argument('email', type=str, help='The email of the client.')

    get_parser = subparsers.add_parser('get', help='Get the configuration for a WireGuard client.')
    get_parser.add_argument('name', type=str, help='The name of the client.')
    get_parser.add_argument('--qr', action='store_true', help='Generate a QR code instead of a configuration file.')

    args = parser.parse_args()

    if args.command == 'create':
        client = create_client(args.name, args.email)
        print(f"Created client '{client['name']}' with IP address '{client['ip_address']}' and expiry date '{client['expiry'].strftime('%Y-%m-%d %H:%M:%S')}'.")
    elif args.command == 'get':
        if args.qr:
            qr_code = generate_qr_code(args.name, args.email)

            if qr_code is None:
                print(f"Could not find client '{args.name}'.")
            else:
                print(f"Generated QR code for client '{args.name}'.")
                # Save QR code to file or display on screen
        else:
            config = generate_client_config(args.name, args.email)

            if config is None:
                print(f"Could not find client '{args.name}'.")
            else:
                print(f"Generated configuration file for client '{args.name}'.")
                # Save configuration file to disk or display on screen
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
