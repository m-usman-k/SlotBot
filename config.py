DATABASE_PATH = "./databases/database.db"
SUPREME_USER = 1155936906274672730  # Replace with your ID

# Slot duration configurations
DURATION_CONFIG = {
    "10min": (600, "10 Minutes"),
    "30min": (1800, "30 Minutes"),
    "1h": (3600, "1 Hour"),
    "3h": (10800, "3 Hours"),
    "6h": (21600, "6 Hours"),
    "12h": (43200, "12 Hours"),
    "1d": (86400, "1 Day")
}

# Points prices in EUR
POINTS_PRICES = {
    50: 2,
    100: 3,
    250: 6,
    500: 10,
    750: 13,
    1000: 20
}

# Category ID for tickets
TICKET_CATEGORY_ID = 1367470589362704445  # Replace with your category ID

# Ticket naming format
TICKET_NAME_FORMAT = "ticket-{user_name}-{ticket_id}"

# Roles that can see tickets (admin roles)
TICKET_ADMIN_ROLES = []  # Add role IDs here

# Crypto payment configuration
CRYPTO_ADDRESSES = {
    "Bitcoin": {
        "address": "17pK5x3GWHy1miX7W6u3mi5JE6Cp2U9Z1S",  # Add your BTC address
        "network": "BTC",
        "min_confirmations": 0
    },
    "Ethereum": {
        "address": "0x9ea79aba6994f68f58ccd82cc542531cbd20e451",
        "network": "ETH",
        "min_confirmations": 0
    },
    "Litecoin": {
        "address": "LQwbKixbqbTuzk4cZtdw8R3rBPzSsMBto4",  # Add your LTC address
        "network": "LTC",
        "min_confirmations": 0
    },
    "Solana": {
        "address": "fdafdsa",  # Add your SOL address
        "network": "SOL",
        "min_confirmations": 0
    }
}

# API Keys for blockchain verification
API_KEYS = {
    "BLOCKCHAIR_API_KEY": "YOUR_BLOCKCHAIR_API_KEY",  # Add your Blockchair API key
    "SOLSCAN_API_KEY": "YOUR_SOLSCAN_API_KEY"  # Add your Solscan API key
}

# Default verification settings
VERIFICATION_SETTINGS = {
    "check_amount": True,           # Whether to verify the exact amount
    "check_confirmations": True,    # Whether to verify minimum confirmations
    "auto_approve": False,          # Whether to automatically approve verified transactions
    "max_wait_time": 3600,          # Maximum time to wait for confirmation (in seconds)
    "retry_interval": 60,           # How often to retry verification (in seconds)
    "max_retries": 60               # Maximum number of retries before giving up
}