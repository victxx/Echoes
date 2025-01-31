import traceback
import requests
import openai
import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from flask_cors import CORS
from ankr import AnkrWeb3
from ankr.types import GetAccountBalanceRequest, GetNFTsByOwnerRequest, GetInteractionsRequest, GetBlockchainStatsRequest  # Updated imports
from ankr.providers import MultichainHTTPProvider  # Add this import

load_dotenv()

# Add debug prints
print("Current working directory:", os.getcwd())
print("Environment variables loaded:")
print("ANKR_API_KEY:", os.getenv("ANKR_API_KEY")[:10] + "..." if os.getenv("ANKR_API_KEY") else None)
print("OPENAI_API_KEY:", "***" if os.getenv("OPENAI_API_KEY") else None)

# Initialize Ankr SDK with API key
ANKR_API_KEY = os.getenv("ANKR_API_KEY")
if not ANKR_API_KEY:
    raise ValueError("ANKR_API_KEY not found in environment variables")

# Initialize with API key directly
ankr_w3 = AnkrWeb3(ANKR_API_KEY)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Network configurations with Ankr blockchain mappings
NETWORKS = {
    "mantle-testnet": {
        "chain": "mantle_testnet",
        "explorer": "https://explorer.testnet.mantle.xyz",
        "faucet": "https://faucet.testnet.mantle.xyz"
    },
    "base-goerli": {
        "chain": "base_goerli",
        "explorer": "https://goerli.basescan.org",
        "faucet": "https://bridge.base.org/deposit"
    },
    "goerli": {
        "chain": "eth_goerli",
        "explorer": "https://goerli.etherscan.io",
        "faucet": "https://goerlifaucet.com"
    },
    "sepolia": {
        "chain": "eth_sepolia",
        "explorer": "https://sepolia.etherscan.io",
        "faucet": "https://sepoliafaucet.com"
    }
}

def get_wallet_data(wallet, network="mantle-testnet"):
    try:
        data = {
            "balance_eth": 0,
            "tx_count": 0,
            "tokens": [],
            "nfts": [],
            "network": network
        }

        # Get token balances with USD prices across chains
        try:
            token_response = ankr_w3.token.get_account_balance(
                request=GetAccountBalanceRequest(
                    walletAddress=wallet
                )
            )
            # Convert response to a list and extract relevant data
            tokens_list = []
            for token in token_response:
                token_data = {
                    "name": getattr(token, "name", "Unknown"),
                    "symbol": getattr(token, "symbol", ""),
                    "balance": getattr(token, "balance", 0),
                    "usdValue": getattr(token, "usdValue", 0),
                    "thumbnail": getattr(token, "thumbnail", None)
                }
                tokens_list.append(token_data)
            data["tokens"] = tokens_list
            print(f"Found {len(data['tokens'])} tokens")
        except Exception as token_error:
            print(f"Error getting tokens: {str(token_error)}")
            data["tokens"] = []
        
        # Get NFTs across chains
        try:
            nft_response = ankr_w3.nft.get_nfts(
                request=GetNFTsByOwnerRequest(
                    walletAddress=wallet
                )
            )
            # Convert response to a list and extract relevant data
            nfts_list = []
            for nft in nft_response:
                nft_data = {
                    "name": getattr(nft, "name", "Unknown"),
                    "collectionName": getattr(nft, "collectionName", ""),
                    "imageUrl": getattr(nft, "imageUrl", None),
                    "description": getattr(nft, "description", "")
                }
                nfts_list.append(nft_data)
            data["nfts"] = nfts_list
            print(f"Found {len(data['nfts'])} NFTs")
        except Exception as nft_error:
            print(f"Error getting NFTs: {str(nft_error)}")
            data["nfts"] = []

        # Calculate total balance in ETH
        for token in data["tokens"]:
            if token["symbol"] == "ETH":
                try:
                    data["balance_eth"] = float(token["balance"])
                    print(f"Found ETH balance: {data['balance_eth']}")
                except (ValueError, TypeError) as e:
                    print(f"Error parsing ETH balance: {str(e)}")
                break

        # Get transaction count (simplified)
        data["tx_count"] = len(data["tokens"]) + len(data["nfts"])
        print(f"Total transaction count: {data['tx_count']}")

        # Print full response for debugging
        print("Token data sample:", data["tokens"][:1] if data["tokens"] else "No tokens")
        print("NFT data sample:", data["nfts"][:1] if data["nfts"] else "No NFTs")

        return data

    except Exception as e:
        print(f"Error getting wallet data: {str(e)}")
        print(traceback.format_exc())
        raise ValueError(f"Failed to retrieve wallet data: {str(e)}")

def analyze_wallet_activity(wallet_data):
    try:
        profile = {
            "type": "",
            "activity_level": "",
            "interests": [],
            "stats": {
                "total_value_usd": 0,
                "nft_count": len(wallet_data.get("nfts", [])),
                "token_count": len(wallet_data.get("tokens", [])),
                "interaction_count": 0  # Removed interactions count
            }
        }

        # Calculate total value in USD
        for token in wallet_data.get("tokens", []):
            if "usdValue" in token:
                try:
                    profile["stats"]["total_value_usd"] += float(token["usdValue"])
                except (ValueError, TypeError):
                    continue

        # Analyze activity level
        if wallet_data["tx_count"] > 100:
            profile["activity_level"] = "whale"
        elif wallet_data["tx_count"] > 50:
            profile["activity_level"] = "high"
        elif wallet_data["tx_count"] > 10:
            profile["activity_level"] = "medium"
        else:
            profile["activity_level"] = "explorer"

        # Determine user type based on activity
        if profile["stats"]["nft_count"] > 10:
            profile["type"] = "NFT Collector"
            profile["interests"].append("NFTs")
        elif profile["stats"]["token_count"] > 5:
            profile["type"] = "DeFi Explorer"
            profile["interests"].append("DeFi")
        elif profile["stats"]["total_value_usd"] > 1000:
            profile["type"] = "Hodler"
            profile["interests"].append("Investment")
        else:
            profile["type"] = "Network Explorer"

        # Add network-specific traits
        if wallet_data["network"] == "mantle-testnet":
            profile["interests"].append("L2 Scaling")
        elif wallet_data["network"] == "base-goerli":
            profile["interests"].append("Coinbase Ecosystem")

        return profile

    except Exception as e:
        print(f"Error in profile analysis: {str(e)}")
        print(traceback.format_exc())
        raise ValueError(f"Failed to analyze wallet: {str(e)}")
    
def generate_ai_narrative(profile, wallet_data):
    try:
        # Create a detailed prompt for GPT-4o
        prompt = f"""
        As a blockchain identity analyzer, create a narrative for this wallet:

        Profile Overview:
        - Type: {profile['type']}
        - Activity Level: {profile['activity_level']}
        - Interests: {', '.join(profile['interests'])}
        
        Portfolio:
        - Total Value: ${profile['stats']['total_value_usd']:.2f}
        - NFTs: {profile['stats']['nft_count']}
        - Token Types: {profile['stats']['token_count']}
        - Network: {wallet_data['network']}
        
        Holdings:
        - NFTs: {', '.join([nft.get('name', 'Unknown') for nft in wallet_data.get('nfts', [])[:3]])}
        - Tokens: {', '.join([token.get('name', 'Unknown') for token in wallet_data.get('tokens', [])[:3]])}

        Create a first-person narrative that:
        1. Describes their DeFi/NFT persona
        2. Highlights their trading style and preferences
        3. Mentions specific tokens/NFTs they hold
        4. Suggests what kind of Web3 user they might be (degen, collector, investor, etc.)
        5. Keep it engaging and fun, like a character backstory
        
        Keep it under 200 words and make it sound like a Web3 native telling their story.
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a Web3 identity analyzer that creates engaging narratives about crypto wallets. You speak in crypto-native terms and understand DeFi/NFT culture."
                },
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content

    except Exception as e:
        print(f"Error generating narrative: {str(e)}")
        print(traceback.format_exc())
        raise ValueError(f"Failed to generate narrative: {str(e)}")

# Flask Configuration
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["https://echoes-victxx.vercel.app", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"]
    }
})

@app.errorhandler(Exception)
def handle_error(error):
    # Print the full traceback for debugging
    print("Error occurred:")
    print(traceback.format_exc())
    return jsonify({
        "error": str(error),
        "traceback": traceback.format_exc(),
        "status": getattr(error, 'code', 500)
    }), getattr(error, 'code', 500)

@app.before_request
def before_request():
    # Log all incoming requests
    print(f"Received {request.method} request to {request.path}")
    print(f"Headers: {dict(request.headers)}")
    if request.args:
        print(f"Query params: {dict(request.args)}")
    
    if not request.is_json and request.method != "GET":
        return jsonify({"error": "Content-Type must be application/json"}), 400

@app.after_request
def after_request(response):
    # Log all responses
    print(f"Responding with status {response.status}")
    print(f"Response headers: {dict(response.headers)}")
    
    if not response.headers.get('Content-Type'):
        response.headers['Content-Type'] = 'application/json'
    return response

# Add a test endpoint
@app.route("/test", methods=["GET"])
def test():
    try:
        response = jsonify({"message": "Backend is working!"})
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        print("Error in test endpoint:")
        print(traceback.format_exc())
        raise e

@app.route("/echo_ai", methods=["GET"])
def echo_ai():
    try:
        wallet = request.args.get("wallet")
        if not wallet:
            return jsonify({"error": "Wallet address is required"}), 400
            
        network = request.args.get("network", "mantle-testnet").lower()
        
        print(f"Processing request for wallet: {wallet} on network: {network}")
        
        # Get wallet data using Ankr SDK
        wallet_data = get_wallet_data(wallet, network)
        
        # Analyze wallet activity
        profile = analyze_wallet_activity(wallet_data)
        
        # Generate narrative using GPT-4o
        narrative = generate_ai_narrative(profile, wallet_data)
        
        response = jsonify({
            "wallet": wallet,
            "network": network,
            "profile": profile,
            "narrative": narrative,
            "data": wallet_data
        })
        
        return response

    except Exception as e:
        print(f"Error in echo_ai endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "wallet": wallet if 'wallet' in locals() else None,
            "network": network if 'network' in locals() else None
        }), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
