import json

import web3
from cryptography.fernet import Fernet

from web3 import Web3
from django.conf import settings
from web3.types import TxReceipt

from datetime import datetime, timezone
from django.utils import timezone as django_timezone


def convert_wei_to_celo(wei_amount):
    """Convert wei amount to celo"""
    celo_amount = wei_amount / 1e18
    return celo_amount


def encrypt_private_key(private_key: str) -> str:
    """Fernet encrypt a private key."""
    fernet = Fernet(settings.WALLET_ENCRYPTION_KEY)
    encrypted_key = fernet.encrypt(private_key.encode())
    return encrypted_key.decode()


def decrypt_private_key(encrypted_key: str) -> str:
    """Fernet decrypt a private key."""
    fernet = Fernet(settings.WALLET_ENCRYPTION_KEY)
    decrypted_key = fernet.decrypt(encrypted_key.encode())
    return decrypted_key.decode()


def load_contract(abi_path: str, contract_address: str):
    """Load contract from ABI file and contract address."""
    with open(abi_path, "r", encoding="utf-8") as abi_file:
        contract_abi = json.load(abi_file)

    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    return contract


class CryptoUtils:
    """Utility class for performing blockchain interactions"""
    def __init__(
            self,
            contract_abi_path: str,
            contract_address: str,
            registry: bool = False,
            faucet: bool = False
    ):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        self.contract = load_contract(contract_abi_path, contract_address)
        if registry:
            self.registry = load_contract(
                settings.REGISTRY_ABI_FILE_PATH,
                settings.REGISTRY_ADDRESS
            )
        else:
            self.registry = None
        if faucet:
            self.faucet = load_contract(
                settings.FAUCET_ABI_FILE_PATH,
                settings.FAUCET_ADDRESS
            )

    def create_wallet(self) -> dict:
        """Create a wallet on the blockchain."""
        account = self.w3.eth.account.create()
        return {
            'private_key': account._private_key.hex(),
            'address': account.address
        }

    def complete_transaction(
            self,
            private_key: str,
            transaction: dict
    ) -> TxReceipt:
        """
        Sign, hash and get transaction receipt.
        ---
        Required fields:
        - private_key: decrypted private key to sign transaction
        - transaction: transaction to sign
        returns receipt of transaction
        """
        signed_tx = self.w3.eth.account.sign_transaction(
            transaction,
            private_key=private_key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        # Wait for the transaction to be mined
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt

    def estimate_gas_for_transfer(
            self,
            contract: web3.eth.Contract,
            from_address: str,
            to_address: str,
            token_amount: int
    ) -> int:
        """Estimate the gas required for a transfer."""
        transfer_function = contract.functions.transfer(
            to_address,
            token_amount
        )

        return transfer_function.estimate_gas(
            {'from': from_address}
        )

    def send_to_wallet_address(
            self,
            from_address: str,
            private_key: str,
            to_address: str,
            amount: float
    ) -> TxReceipt:
        """Send tokens to a wallet address."""
        # Calculate token amount adjusted for decimals
        decimals = self.contract.functions.decimals().call()
        token_amount = int(amount * (10**decimals))
        # Estimate gas and get current gas price
        gas = self.estimate_gas_for_transfer(
            self.contract,
            from_address,
            to_address,
            token_amount
        )

        gas_price = self.w3.eth.gas_price

        # Prepare and sign the transaction
        nonce = self.w3.eth.get_transaction_count(from_address)
        transfer = self.contract.functions.transfer(to_address, token_amount)
        tx = transfer.build_transaction({
            'chainId': self.w3.eth.chain_id,
            'gas': gas,
            'gasPrice': gas_price,
            'nonce': nonce,
        })

        receipt = self.complete_transaction(private_key, tx)
        return receipt

    def check_gas_status(self, from_address: str, gas_amount: int) -> bool:
        gas_balance = self.balance_of_celo(from_address)
        if gas_balance > gas_amount:
            return True
        return False

    def balance_of(self, address: str) -> float:
        """Check the balance of a wallet."""
        raw_balance = self.contract.functions.balanceOf(address).call()
        decimals = self.contract.functions.decimals().call()
        return raw_balance / (10**decimals)

    def balance_of_celo(self, address: str) -> float:
        """
        Check the CELO balance of a wallet.
        This checks the native CELO balance of the address.
        """
        try:
            # Get the raw balance in Wei
            raw_balance = self.w3.eth.get_balance(address)
            # Convert the balance from Wei to CELO
            celo_balance = raw_balance
            # celo_balance = convert_wei_to_celo(raw_balance)
            return celo_balance
        except Exception as e:
            print(f"Error fetching CELO balance for address {address}: {e}")
            return 0.0

    def faucet_give_to(
            self,
            private_key: str,
            give_to_address: str
    ) -> TxReceipt:
        """Give tokens to an address registered in the account index"""
        account = self.w3.eth.account.from_key(private_key)
        sender_address = account.address

        nonce = self.w3.eth.get_transaction_count(sender_address)
        gas_price = self.w3.eth.gas_price

        gas_estimate = self.faucet.functions.giveTo(
            give_to_address
        ).estimate_gas({
            'from': sender_address
        })

        tx = self.faucet.functions.giveTo(
            give_to_address
        ).build_transaction(
            {
                'from': sender_address,
                'nonce': nonce,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id,
            }
        )

        receipt = self.complete_transaction(private_key, tx)

        if receipt:
            return receipt
        else:
            raise Exception("Transaction failed")

    def account_index_check_active(self, address_to_check: str) -> bool:
        """Check if an address is active on the account index."""
        active = self.registry.functions.isActive(address_to_check).call()
        return active

    def pre_transaction_check(
            self,
            private_key_admin: str,
            from_address: str,
            to_address: str,
            amount: float) -> bool:
        """Check if transaction will be successful. Rectify if not"""
        decimals = self.contract.functions.decimals().call()
        token_amount = int(amount * (10 ** decimals))

        # Estimate gas and get current gas price
        gas = self.estimate_gas_for_transfer(
            self.contract,
            from_address,
            to_address,
            token_amount
        )

        # ensure wallet has enough gas
        gas_status = self.check_gas_status(from_address, gas)
        # there is not enough gas to transact
        if not gas_status:
            active = self.account_index_check_active(from_address)
            if not active:
                self.registry_add(private_key_admin, from_address)
            self.faucet_give_to(private_key_admin, from_address)
        # if no error is raised return true
        return True

    def registry_add(self, private_key: str, address_to_add: str) -> TxReceipt:
        """
        Add an address to a registry using the private key
        of the contract owner
        """
        account = self.w3.eth.account.from_key(private_key)
        sender_address = account.address

        nonce = self.w3.eth.get_transaction_count(sender_address)
        gas_price = self.w3.eth.gas_price
        gas_estimate = self.registry.functions.add(
            address_to_add
        ).estimate_gas({
            'from': sender_address
        })

        tx = self.registry.functions.add(address_to_add).build_transaction({
            'from': sender_address,
            'nonce': nonce,
            'gas': gas_estimate,
            'gasPrice': gas_price,
            'chainId': self.w3.eth.chain_id,
        })

        receipt = self.complete_transaction(private_key, tx)
        if receipt:
            return receipt
        else:
            raise Exception("Transaction failed")

    def faucet_check_time(self, address_to_check: str) -> dict:
        """Check if an address can receive funds at this time"""
        next_time = self.faucet.functions.nextTime(
            _subject=address_to_check
        ).call({'from': address_to_check})

        aware_utc_dt = datetime.fromtimestamp(next_time, tz=timezone.utc)
        now = django_timezone.localtime(django_timezone.now())
        local_dt = django_timezone.localtime(aware_utc_dt)
        is_older = local_dt <= now
        return {
            'is_older': is_older,
            'time_stamp': str(local_dt),
        }

    def faucet_balance_threshold(self, address: str) -> float:
        """Check what the threshold amount is for a faucet"""
        try:
            balance_threshold = self.faucet.functions.nextBalance(
                _subject=address
            ).call({'from': address})
            celo_amount = convert_wei_to_celo(balance_threshold)
            return celo_amount
        except Exception as e:
            print(f'Error calling nextBalance: {e}')

    def faucet_gimme(self, private_key: str, address: str) -> dict:
        """Call the gimme function for an account from the faucet"""
        raw_balance = self.w3.eth.get_balance(address)
        balance = convert_wei_to_celo(raw_balance)

        faucet_thresh = self.faucet_balance_threshold(address)

        # do not proceed if they cannot request because current balance
        if balance > faucet_thresh:
            print('Your balance is too high')
            return {
                'balance': balance,
                'threshold': faucet_thresh,
                'faucet_thresh': True,
                'amount': -1,
                'success': False,
                'time_check': False,
                'time': -1
            }

        # do not proceed if they cannot request because of time
        time_check = self.faucet_check_time(address)
        if not time_check['is_older']:
            return {
                'balance': balance,
                'threshold': faucet_thresh,
                'amount': -1,
                'success': False,
                'time_check': True,
                'time': time_check['time_stamp'],
            }

        nonce = self.w3.eth.get_transaction_count(address)
        gas_price = self.w3.eth.gas_price

        gas_estimate = self.faucet.functions.gimme().estimate_gas({
            'from': address,
        })
        tx = self.faucet.functions.gimme().build_transaction({
            'from': address,
            'nonce': nonce,
            'gas': gas_estimate,
            'gasPrice': gas_price,
            'chainId': self.w3.eth.chain_id,
        })

        # Sign the transaction
        signed_tx = self.w3.eth.account.sign_transaction(
            tx,
            private_key=private_key
        )

        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for the transaction to be mined
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        try:
            give_event = self.faucet.events.Give().process_receipt(receipt)
            for event in give_event:
                amount = event['args']['_amount']
                return {
                    'balance': balance,
                    'threshold': faucet_thresh,
                    'amount': convert_wei_to_celo(amount),
                    'success': True,
                    'time_check': True,
                    'time': time_check['time_stamp'],
                }
        except Exception as e:
            print(f'Error processing events: {e}')
