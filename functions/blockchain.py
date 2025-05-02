import requests
import json
from config import CRYPTO_ADDRESSES, VERIFICATION_SETTINGS, API_KEYS

class BlockchainVerifier:
    @staticmethod
    async def verify_transaction(crypto_type: str, transaction_id: str, expected_amount: float) -> bool:
        """
        Verify a cryptocurrency transaction.
        Returns True if the transaction is valid and matches the expected amount.
        """
        if crypto_type not in CRYPTO_ADDRESSES:
            return False

        crypto_info = CRYPTO_ADDRESSES[crypto_type]
        address = crypto_info['address']
        network = crypto_info['network']
        min_confirmations = crypto_info['min_confirmations']

        try:
            if network == 'BTC':
                return await BlockchainVerifier._verify_btc_transaction(transaction_id, address, expected_amount, min_confirmations)
            elif network == 'ETH':
                return await BlockchainVerifier._verify_eth_transaction(transaction_id, address, expected_amount, min_confirmations)
            elif network == 'LTC':
                return await BlockchainVerifier._verify_ltc_transaction(transaction_id, address, expected_amount, min_confirmations)
            elif network == 'SOL':
                return await BlockchainVerifier._verify_sol_transaction(transaction_id, address, expected_amount, min_confirmations)
            else:
                return False
        except Exception as e:
            print(f"Error verifying {network} transaction: {e}")
            return False

    @staticmethod
    async def _verify_btc_transaction(tx_id: str, address: str, expected_amount: float, min_confirmations: int) -> bool:
        """Verify Bitcoin transaction using blockchain.info API"""
        try:
            # Get transaction details from blockchain.info
            tx_url = f"https://api.blockchain.info/haskoin-store/btc/transaction/{tx_id}"
            tx_response = requests.get(tx_url)
            if tx_response.status_code != 200:
                return False
            
            tx_data = tx_response.json()
            
            # Get current BTC price from bitaps
            price_url = "https://bitaps.com/js/get/update"
            price_response = requests.post(price_url)
            if price_response.status_code != 200:
                return False
            
            price_data = price_response.json()
            btc_price = float(price_data['average']['dollars'].replace(" ", "") + "." + price_data['average']['cents'])
            
            # Verify recipient and amount
            for output in tx_data['outputs']:
                if output['address'] == address:
                    print("here 1")
                    amount_btc = output['value'] / 100000000  # Convert satoshis to BTC
                    amount_usd = amount_btc * btc_price
                    
                    # Allow 1% tolerance for price fluctuations
                    if expected_amount <= amount_usd:
                        print("here 2")
                        # Verify confirmation status
                        if 'block' in tx_data and not tx_data['deleted']:
                            print("here 3")
                            return True
                        
            return False
            
        except Exception as e:
            print(f"Error verifying BTC transaction: {e}")
            return False

    @staticmethod
    async def _verify_eth_transaction(tx_id: str, address: str, expected_amount: float, min_confirmations: int) -> bool:
        """Verify Ethereum transaction using Ethplorer API"""
        try:
            # Use Ethplorer API
            url = f"https://api.ethplorer.io/getTxInfo/{tx_id}?apiKey=freekey"
            response = requests.get(url)
            if response.status_code != 200:
                return False
            
            data = response.json()
            
            # Check if transaction was successful
            if data["success"] == False:
                return False
            
                
            # Check confirmations
            if data['confirmations'] < min_confirmations:
                return False
            
            # Check for token transfers in operations
            if data['operations']:
                for op in data['operations']:
                    if op['to'] == address:
                        # Get value and adjust for decimals
                        if op['tokenInfo']:
                            decimals = int(op['tokenInfo']['decimals'])
                            value = float(op['value']) / (10 ** decimals)
                            # Convert to USD if price info is available
                            if 'usdPrice' in op:
                                value = value * op['usdPrice']
                                # Allow 1% tolerance for price fluctuations
                                if round(expected_amount) <= round(value):
                                    return True
            
            # Check for direct ETH transfer
            elif data.get('value') and data.get('to', '').lower() == address.lower():
                value = float(data['value']) / 1e18  # Convert from wei to ETH
                # You would need to get current ETH price here for USD conversion
                # For simplicity, we're just comparing ETH value
                if abs(value - expected_amount) <= (expected_amount * 0.01):
                    print("Returning True")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error verifying ETH transaction: {e}")
            return False

    @staticmethod
    async def _verify_ltc_transaction(tx_id: str, address: str, expected_amount: float, min_confirmations: int) -> bool:
        """Verify Litecoin transaction using litecoinspace.org API"""
        try:
            # Get transaction details from litecoinspace.org
            tx_url = f"https://litecoinspace.org/api/tx/{tx_id}"
            tx_response = requests.get(tx_url)
            if tx_response.status_code != 200:
                return False
            
            tx_data = tx_response.json()
            
            # Get current LTC price from bitaps
            price_url = "https://ltc.bitaps.com/js/get/update"
            price_response = requests.post(price_url)
            if price_response.status_code != 200:
                return False
            
            price_data = price_response.json()
            ltc_price = float(price_data['average']['dollars'].replace(" ", "") + "." + price_data['average']['cents'])
            
            # Verify recipient and amount
            for output in tx_data['vout']:
                if output['scriptpubkey_address'] == address:
                    amount_ltc = output['value'] / 100000000  # Convert litoshis to LTC
                    amount_usd = amount_ltc * ltc_price
                    
                    # Allow 1% tolerance for price fluctuations
                    if expected_amount <= amount_usd:
                        # Verify confirmation status
                        if tx_data['status']['confirmed']:
                            return True
            
            return False
            
        except Exception as e:
            print(f"Error verifying LTC transaction: {e}")
            return False

    @staticmethod
    async def _verify_sol_transaction(tx_id: str, address: str, expected_amount: float, min_confirmations: int) -> bool:
        """Verify Solana transaction using Solana Explorer API"""
        api_key = API_KEYS['SOLSCAN_API_KEY']
        if not api_key:
            print("Solscan API key not configured")
            return False
            
        headers = {
            'token': api_key,
            'Accept': 'application/json'
        }
        
        url = f"https://api.solscan.io/transaction?tx={tx_id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return False
        
        data = response.json()
        if not data['success']:
            return False
        
        tx_data = data['data']
        
        # Check confirmations
        if tx_data['status'] != "Success":
            return False
        
        # Check if transaction is finalized
        if not tx_data['finalized']:
            return False
        
        # Check outputs
        for post_token_balance in tx_data['postTokenBalances']:
            if post_token_balance['owner'] == address:
                amount = float(post_token_balance['uiTokenAmount']['uiAmount'])
                if abs(amount - expected_amount) < 0.00000001:
                    return True
        
        return False