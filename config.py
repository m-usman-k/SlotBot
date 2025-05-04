DATABASE_PATH = "./databases/database.db"
SUPREME_USER = 1155936906274672730  # Replace with your ID

# Slot duration configurations
DURATION_CONFIG = {
    "10min": {
        "seconds": 600,
        "name": "10 Minutes",
        "points": 1  # 100 points per hour / 6 (since 10min is 1/6 of an hour)
    },
    "30min": {
        "seconds": 1800,
        "name": "30 Minutes",
        "points": 50  # 100 points per hour / 2
    },
    "1h": {
        "seconds": 3600,
        "name": "1 Hour",
        "points": 100  # Base rate
    },
    "3h": {
        "seconds": 10800,
        "name": "3 Hours",
        "points": 250  # Slight discount for longer durations
    },
    "6h": {
        "seconds": 21600,
        "name": "6 Hours",
        "points": 450  # More discount
    },
    "12h": {
        "seconds": 43200,
        "name": "12 Hours",
        "points": 800  # Even more discount
    },
    "1d": {
        "seconds": 86400,
        "name": "1 Day",
        "points": 1500  # Best discount
    }
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
        "address": "bc1qrk6npzzz74uwjntz4wpw3kmc2ncwt65ejd9spn",
        "network": "BTC",
        "min_confirmations": 0
    },
    "Ethereum": {
        "address": "0xd3878E1ee4b6373bA2053B5f8ADF965650E8e21A",
        "network": "ETH",
        "min_confirmations": 0
    },
    "Litecoin": {
        "address": "LKLCiG6iM48fZgzrdTqG5Q9hhjYQ3GbK36",  # Add your LTC address
        "network": "LTC",
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

# Slot configurations
SLOT_CONFIG = {
    "default_pings": 3,             # Default number of pings when slot is purchased
    "points_per_hour": 100,         # Points cost per hour of slot rental
    "default_name": "Available Slot" # Default name for available slots
}