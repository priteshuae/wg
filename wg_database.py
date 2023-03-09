import sqlite3


DB_NAME = 'wg_config.db'


def create_database():
    """Creates a new SQLite database to store WireGuard client information."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            name TEXT PRIMARY KEY,
            email TEXT,
            ip_address TEXT,
            public_key TEXT,
            expiry TEXT
        )
    ''')

    conn.commit()
    conn.close()


def save_client_to_database(name, email, ip_address, public_key, expiry):
    """Saves a new WireGuard client to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        INSERT INTO clients (
            name, email, ip_address, public_key, expiry
        ) VALUES (
            ?, ?, ?, ?, ?
        )
    ''', (name, email, ip_address, public_key, expiry))

    conn.commit()
    conn.close()


def get_client_by_name(name):
    """Returns a WireGuard client with the specified name."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('SELECT * FROM clients WHERE name=?', (name,))
    client = c.fetchone()

    conn.close()

    if client is None:
        return None

    return {
        'name': client[0],
        'email': client[1],
        'ip_address': client[2],
        'public_key': client[3],
        'expiry': client[4]
    }
