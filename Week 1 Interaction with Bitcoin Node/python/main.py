# Import Bitcoin RPC library for node communication
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json

# Define Bitcoin node connection URL with credentials (regtest mode on port 18443)
RPC_URL = "http://alice:password@127.0.0.1:18443"

def create_or_load_wallet(rpc, wallet_name="testwallet"): # check if wallet exists, if not create it
    try:
        # Get list of currently loaded wallets
        existing_wallets = rpc.listwallets()
        # If wallet already exists, just print and return
        if wallet_name in existing_wallets:
            print(f"Wallet {wallet_name} is already loaded")
            return
        
        # Create new wallet with specified parameters    
        rpc.createwallet(
            wallet_name,      # Name of the wallet
            False,           # Don't disable private keys
            False,           # Don't create blank wallet
            "",             # No passphrase
            False,          # Don't avoid address reuse
            False,          # Don't use descriptors
            True            # Load wallet on startup
        )
        print(f"Created and loaded new wallet: {wallet_name}") # Print wallet creation message
    except JSONRPCException as e:
        # Handle any RPC errors
        print(f"Error with wallet: {str(e)}")
        raise

def mine_to_address(rpc, address, blocks=101):
    # Generate specified number of blocks and reward goes to address
    rpc.generatetoaddress(blocks, address)
    print(f"Mined {blocks} blocks to {address}")

def create_and_send_transaction(rpc, recipient_address):
    # Define OP_RETURN message and convert to hex
    message = "We are all Satoshi!!"
    message_hex = message.encode('utf-8').hex()
    
    # Define transaction outputs: payment and OP_RETURN data
    outputs = [
        {recipient_address: 100},  # 100 BTC payment
        {"data": message_hex}      # OP_RETURN message
    ]
    
    # Create initial raw transaction structure
    tx = rpc.createrawtransaction([], outputs)
    
    # Add inputs and calculate fees (21 sat/vB)
    funded_tx = rpc.fundrawtransaction(
        tx,
        {
            "fee_rate": 21,            # Set exact fee rate
            "subtractFeeFromOutputs": [], # Don't subtract fee from outputs
            "replaceable": False,       # No RBF
        }
    )
    
    # Sign transaction with wallet's private keys
    signed_tx = rpc.signrawtransactionwithwallet(funded_tx["hex"])
    
    # Verify transaction details and fees
    decoded_tx = rpc.decoderawtransaction(signed_tx["hex"])
    vsize = decoded_tx["vsize"]
    fee_sats = int(funded_tx["fee"] * 100000000)  # BTC to satoshis
    expected_fee = vsize * 21 # 21 sat/vB fee rate
    
    # Print fee details for verification
    print(f"Virtual size: {vsize} vBytes")
    print(f"Fee rate: {fee_sats/vsize} sats/vB")
    print(f"Actual fee: {fee_sats} sats")
    print(f"Expected fee: {expected_fee} sats")
    
    # Warning if fee isn't exact
    if fee_sats != expected_fee:
        print("Warning: Fee rate is not exactly 21 sats/vB")
    
    # Broadcast transaction to network
    txid = rpc.sendrawtransaction(signed_tx["hex"])
    print(f"Transaction sent! TXID: {txid}")
    return txid

def main():
    # Initialize RPC connection to Bitcoin node
    rpc = AuthServiceProxy(RPC_URL)

    # Verify node connection and network type
    info = rpc.getblockchaininfo()
    print("Connected to node:", info['chain'])

    # Setup or load existing wallet
    create_or_load_wallet(rpc)

    # Generate new receiving address from wallet
    address = rpc.getnewaddress()
    print(f"Generated address: {address}")

    # Mine blocks to get enough funds (each block = 50 BTC)
    mine_to_address(rpc, address, 250)

    # Check wallet's current balance
    balance = rpc.getbalance()
    print(f"Wallet balance: {balance} BTC")

    # Define recipient and send transaction
    recipient = "bcrt1qq2yshcmzdlznnpxx258xswqlmqcxjs4dssfxt2"
    txid = create_and_send_transaction(rpc, recipient)

    # Save transaction ID to file
    with open("out.txt", "w") as f:
        f.write(txid)

# Standard Python entry point
if __name__ == "__main__":
    main()