import sqlite3

from config import SUPREME_USER
from config import DATABASE_PATH
from config import CRYPTO_ADDRESSES

def db_connection():
    conn = sqlite3.connect(database=DATABASE_PATH)
    return conn

def setup_crypto_payment_methods():
    with db_connection() as conn:
        cursor = conn.cursor()
        
        # First clear existing crypto payment methods
        cursor.execute("DELETE FROM payment_methods WHERE type = 'crypto'")
        
        # Insert new crypto payment methods
        for crypto_name, crypto_info in CRYPTO_ADDRESSES.items():
            cursor.execute("""
                INSERT INTO payment_methods (name, trigger_name, trigger_value, type)
                VALUES (?, ?, ?, 'crypto')
            """, (crypto_name, crypto_info['network'], crypto_info['address']))

def setup_tables():
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY NOT NULL,
                points INT NOT NULL DEFAULT 0,
                admin BOOLEAN DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS slots (
                id INT PRIMARY KEY NOT NULL,
                points INT NOT NULL,
                default_name TEXT NOT NULL,
                occupied BOOLEAN DEFAULT 0,
                occupied_by INT DEFAULT 0,
                occupied_till INT DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_methods (
                name TEXT NOT NULL,
                trigger_name TEXT NOT NULL,
                trigger_value TEXT NOT NULL,
                type TEXT NOT NULL)
        """)

        cursor.close()
        
    # Setup crypto payment methods
    setup_crypto_payment_methods()

def get_points(id: int):
    add_user(id=id)
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT points FROM users WHERE id = {id}
        """)
        return cursor.fetchone()[0]


def add_points(id: int, points: int) -> bool:
    add_user(id=id)
    with db_connection() as conn:
        try:
            cursor = conn.cursor()

            cursor.execute(f"""
                UPDATE users SET points = points + {points} WHERE id = {id}
            """)
            return True
        except:
            return False
        
def add_user(id: int) -> bool:
    with db_connection() as conn:
        try:
            cursor = conn.cursor()

            cursor.execute(f"""
                INSERT OR IGNORE INTO users (id) VALUES ({id})
            """)
            return True
        except:
            return False
        
def user_admin(id: int) -> bool:
    if id == SUPREME_USER:
        return True
    
    add_user(id=id)
    with db_connection() as conn:
        try:
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT admin FROM users WHERE id = {id}
            """)

            value = cursor.fetchone()
            if value[0] == 0:
                return False
            elif value[0] == 1:
                return True
        except:
            return False

def set_admin(id: int, is_admin: bool) -> bool:
    add_user(id=id)
    with db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE users SET admin = {1 if is_admin else 0} WHERE id = {id}
            """)
            return True
        except:
            return False

def get_admins() -> list:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM users WHERE admin = 1
        """)
        return [row[0] for row in cursor.fetchall()]

def add_slot(channel_id: int, price_points: int, default_name: str) -> bool:
    with db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO slots (id, points, default_name) 
                VALUES ({channel_id}, {price_points}, '{default_name}')
            """)
            return True
        except:
            return False

def get_slots() -> list:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM slots
        """)
        return [row[0] for row in cursor.fetchall()]

def remove_slot(channel_id: int) -> bool:
    with db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                DELETE FROM slots WHERE id = {channel_id}
            """)
            return True
        except:
            return False

def get_user_slot(user_id: int) -> tuple:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, occupied_till FROM slots 
            WHERE occupied_by = {user_id}
        """)
        return cursor.fetchone()

def get_slot_info(slot_id: int) -> tuple:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT points, default_name, occupied, occupied_by, occupied_till 
            FROM slots WHERE id = {slot_id}
        """)
        return cursor.fetchone()

def purchase_slot(slot_id: int, user_id: int, duration_seconds: int, points_cost: int) -> bool:
    with db_connection() as conn:
        try:
            cursor = conn.cursor()
            # Check if user has enough points
            cursor.execute(f"SELECT points FROM users WHERE id = {user_id}")
            user_points = cursor.fetchone()
            if not user_points or user_points[0] < points_cost:
                return False
                
            # Check if slot is available
            cursor.execute(f"SELECT occupied FROM slots WHERE id = {slot_id}")
            slot_status = cursor.fetchone()
            if not slot_status or slot_status[0]:
                return False
                
            # Calculate end time
            import time
            end_time = int(time.time()) + duration_seconds
            
            # Update slot status
            cursor.execute(f"""
                UPDATE slots 
                SET occupied = 1, 
                    occupied_by = {user_id}, 
                    occupied_till = {end_time} 
                WHERE id = {slot_id}
            """)
            
            # Deduct points from user
            cursor.execute(f"""
                UPDATE users 
                SET points = points - {points_cost} 
                WHERE id = {user_id}
            """)
            
            return True
        except:
            return False

def create_payment_ticket(user_id: int, points_amount: int, price_eur: float) -> int:
    with db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INT NOT NULL,
                    points_amount INT NOT NULL,
                    price_eur FLOAT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at INT NOT NULL,
                    completed_at INT
                )
            """)
            
            import time
            current_time = int(time.time())
            
            cursor.execute(f"""
                INSERT INTO payment_tickets (user_id, points_amount, price_eur, created_at)
                VALUES ({user_id}, {points_amount}, {price_eur}, {current_time})
            """)
            
            return cursor.lastrowid
        except:
            return None

def get_payment_ticket(ticket_id: int) -> tuple:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM payment_tickets WHERE id = {ticket_id}
        """)
        return cursor.fetchone()

def complete_payment_ticket(ticket_id: int) -> bool:
    with db_connection() as conn:
        try:
            cursor = conn.cursor()
            import time
            current_time = int(time.time())
            
            # Get ticket info
            cursor.execute(f"SELECT user_id, points_amount, status FROM payment_tickets WHERE id = {ticket_id}")
            ticket = cursor.fetchone()
            if not ticket or ticket[2] != 'pending':
                return False
                
            # Update ticket status
            cursor.execute(f"""
                UPDATE payment_tickets 
                SET status = 'completed', 
                    completed_at = {current_time} 
                WHERE id = {ticket_id}
            """)
            
            # Add points to user
            cursor.execute(f"""
                INSERT INTO users (id, points) 
                VALUES ({ticket[0]}, {ticket[1]})
                ON CONFLICT(id) DO UPDATE SET points = points + {ticket[1]}
            """)
            
            return True
        except:
            return False

def get_crypto_addresses() -> dict:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, trigger_value FROM payment_methods 
            WHERE type = 'crypto'
        """)
        return {row[0]: row[1] for row in cursor.fetchall()}

def create_ticket_tables():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                points_amount INT,
                price_eur FLOAT,
                status TEXT DEFAULT 'pending',
                created_at INT NOT NULL,
                crypto_type TEXT,
                transaction_id TEXT
            )
        """)

def create_ticket(channel_id: int, user_id: int) -> int:
    with db_connection() as conn:
        try:
            cursor = conn.cursor()
            import time
            current_time = int(time.time())
            
            cursor.execute("""
                INSERT INTO tickets (channel_id, user_id, created_at)
                VALUES (?, ?, ?)
            """, (channel_id, user_id, current_time))
            
            return cursor.lastrowid
        except:
            return None

def update_ticket_payment(ticket_id: int, points_amount: int, price_eur: float, crypto_type: str) -> bool:
    with db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tickets 
                SET points_amount = ?, 
                    price_eur = ?,
                    crypto_type = ?
                WHERE id = ?
            """, (points_amount, price_eur, crypto_type, ticket_id))
            return True
        except:
            return False

def verify_transaction(ticket_id: int, transaction_id: str) -> bool:
    with db_connection() as conn:
        try:
            cursor = conn.cursor()
            
            # Get ticket info
            cursor.execute("SELECT user_id, points_amount, crypto_type, status FROM tickets WHERE id = ?", (ticket_id,))
            ticket = cursor.fetchone()
            if not ticket or ticket[3] != 'pending':
                return False
            
            # TODO: Implement actual blockchain verification here
            # For now, we'll just accept any transaction ID
            
            # Update ticket status
            cursor.execute("""
                UPDATE tickets 
                SET status = 'completed',
                    transaction_id = ?
                WHERE id = ?
            """, (transaction_id, ticket_id))
            
            # Add points to user
            cursor.execute("""
                INSERT INTO users (id, points) 
                VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET points = points + ?
            """, (ticket[0], ticket[1], ticket[1]))
            
            return True
        except:
            return False

def get_ticket_info(ticket_id: int) -> tuple:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        return cursor.fetchone()

def get_user_tickets(user_id: int) -> list:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, status, created_at FROM tickets WHERE user_id = ?", (user_id,))
        return cursor.fetchall()

def is_transaction_id_used(transaction_id: str) -> bool:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM tickets WHERE transaction_id = ?", (transaction_id,))
        return cursor.fetchone() is not None
