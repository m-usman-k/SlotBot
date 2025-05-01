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
        """Verify Bitcoin transaction using Blockstream API"""
        url = f"https://blockstream.info/api/tx/{tx_id}"
        response = requests.get(url)
        if response.status_code != 200:
            return False
        
        data = response.json()
        
        # Check confirmations
        if data['status']['block_height'] is None:
            return False  # Transaction not confirmed
        
        # Get block height
        block_height = data['status']['block_height']
        current_height = requests.get("https://blockstream.info/api/blocks/tip/height").json()
        confirmations = current_height - block_height + 1
        
        if confirmations < min_confirmations:
            return False
        
        # Check if any output matches our address and amount
        for output in data['vout']:
            if output['scriptpubkey_address'] == address:
                # Convert satoshis to BTC
                amount = output['value'] / 100000000
                if abs(amount - expected_amount) < 0.00000001:  # Allow for small floating point differences
                    return True
        
        return False

    @staticmethod
    async def _verify_eth_transaction(tx_id: str, address: str, expected_amount: float, min_confirmations: int) -> bool:
        """Verify Ethereum transaction using Etherscan API"""
        api_key = API_KEYS['ETHERSCAN_API_KEY']
        if not api_key:
            print("Etherscan API key not configured")
            return False
            
        url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionByHash&txhash={tx_id}&apikey={api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            return False
        
        data = response.json()
        if data['result'] is None:
            return False
        
        # Get transaction receipt to check confirmations
        receipt_url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionReceipt&txhash={tx_id}&apikey={api_key}"
        receipt_response = requests.get(receipt_url)
        if receipt_response.status_code != 200:
            return False
        
        receipt_data = receipt_response.json()
        if receipt_data['result'] is None:
            return False
        
        # Check confirmations
        current_block = int(requests.get(f"https://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey={api_key}").json()['result'], 16)
        tx_block = int(receipt_data['result']['blockNumber'], 16)
        confirmations = current_block - tx_block
        
        if confirmations < min_confirmations:
            return False
        
        # Check address and amount
        tx_data = data['result']
        if tx_data['to'].lower() == address.lower():
            # Convert wei to ETH
            amount = int(tx_data['value'], 16) / 1e18
            if abs(amount - expected_amount) < 0.00000001:
                return True
        
        return False

    @staticmethod
    async def _verify_ltc_transaction(tx_id: str, address: str, expected_amount: float, min_confirmations: int) -> bool:
        """Verify Litecoin transaction using Blockchair API"""
        api_key = API_KEYS['BLOCKCHAIR_API_KEY']
        if not api_key:
            print("Blockchair API key not configured")
            return False
            
        url = f"https://api.blockchair.com/litecoin/dashboards/transaction/{tx_id}?key={api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            return False
        
        data = response.json()
        if not data['data']:
            return False
        
        tx_data = data['data'][tx_id]
        
        # Check confirmations
        current_height = requests.get(f"https://api.blockchair.com/litecoin/stats?key={api_key}").json()['data']['blocks']
        confirmations = current_height - tx_data['transaction']['block_id'] + 1
        
        if confirmations < min_confirmations:
            return False
        
        # Check outputs
        for output in tx_data['outputs']:
            if output['recipient'] == address:
                amount = output['value'] / 1e8  # Convert to LTC
                if abs(amount - expected_amount) < 0.00000001:
                    return True
        
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