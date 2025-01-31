'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';

interface TokenData {
  name: string;
  symbol: string;
  thumbnail?: string;
  balance: string;
  usdValue?: string;
}

interface NFTData {
  name: string;
  collectionName?: string;
  imageUrl?: string;
  description?: string;
}

interface WalletStats {
  total_value_usd: number;
  nft_count: number;
  token_count: number;
  interaction_count: number;
}

interface Profile {
  type: string;
  activity_level: string;
  interests: string[];
  stats: WalletStats;
}

interface WalletData {
  balance_eth: number;
  tx_count: number;
  tokens: TokenData[];
  nfts: NFTData[];
  network: string;
  stats: WalletStats;
}

interface AIResponse {
  wallet: string;
  network: string;
  profile: Profile;
  narrative: string;
  data: WalletData;
}

export default function Home() {
  const [wallet, setWallet] = useState('');
  const [network, setNetwork] = useState('mantle-testnet');
  const [response, setResponse] = useState<AIResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const networks = {
    "mantle-testnet": "Mantle Testnet",
    "base-goerli": "Base Goerli",
    "goerli": "Ethereum Goerli",
    "sepolia": "Ethereum Sepolia"
  };

  // Add a test function to check backend connectivity
  useEffect(() => {
    async function testBackend() {
      try {
        const res = await fetch('/api/test', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
        });

        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }

        const data = await res.json();
        console.log('Backend test response:', data);
      } catch (err) {
        console.error('Backend test failed:', err);
        setError(`Backend connection failed: ${err instanceof Error ? err.message : String(err)}`);
      }
    }
    testBackend();
  }, []);

  async function fetchAIResponse() {
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`/api/echo_ai?wallet=${encodeURIComponent(wallet)}&network=${network}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`HTTP error! status: ${res.status}, body: ${errorText}`);
      }
      
      const data = await res.json();
      console.log('Response data:', data);
      setResponse(data);
    } catch (err) {
      console.error('Error details:', err);
      setError(`Failed to fetch AI response: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Echoes of the Blockchain
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Discover your on-chain persona across different networks
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            <input 
              type="text" 
              placeholder="Enter Wallet Address" 
              value={wallet} 
              onChange={(e) => setWallet(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <select
              value={network}
              onChange={(e) => setNetwork(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {Object.entries(networks).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
            <button 
              onClick={fetchAIResponse}
              disabled={loading || !wallet}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Analyzing...' : 'Analyze Wallet'}
            </button>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
              <span className="block sm:inline">{error}</span>
            </div>
          )}
        </div>

        {response && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Profile Card */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Profile</h2>
              <div className="space-y-4">
                <div>
                  <span className="text-lg font-semibold text-blue-600 dark:text-blue-400">Type:</span>
                  <span className="ml-2 text-gray-700 dark:text-gray-300">{response.profile.type}</span>
                </div>
                <div>
                  <span className="text-lg font-semibold text-blue-600 dark:text-blue-400">Activity Level:</span>
                  <span className="ml-2 text-gray-700 dark:text-gray-300">{response.profile.activity_level}</span>
                </div>
                <div>
                  <span className="text-lg font-semibold text-blue-600 dark:text-blue-400">Interests:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {response.profile.interests.map((interest, index) => (
                      <span key={index} className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm">
                        {interest}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Stats Card */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Statistics</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <div className="text-sm text-gray-500 dark:text-gray-400">Total Value</div>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">
                    ${response.profile.stats.total_value_usd.toFixed(2)}
                  </div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <div className="text-sm text-gray-500 dark:text-gray-400">NFTs Owned</div>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">
                    {response.profile.stats.nft_count}
                  </div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <div className="text-sm text-gray-500 dark:text-gray-400">Token Types</div>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">
                    {response.profile.stats.token_count}
                  </div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <div className="text-sm text-gray-500 dark:text-gray-400">Interactions</div>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">
                    {response.profile.stats.interaction_count}
                  </div>
                </div>
              </div>
            </div>

            {/* Narrative Card */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 md:col-span-2">
              <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Your Blockchain Story</h2>
              <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed">
                {response.narrative}
              </p>
            </div>

            {/* Tokens Card */}
            {response.data.tokens.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Tokens</h2>
                <div className="space-y-4">
                  {response.data.tokens.map((token, index) => (
                    <div key={index} className="flex items-center space-x-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      {token.thumbnail && (
                        <Image
                          src={token.thumbnail}
                          alt={token.name}
                          width={32}
                          height={32}
                          className="rounded-full"
                        />
                      )}
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">{token.name}</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {token.balance} {token.symbol}
                          {token.usdValue && ` ($${parseFloat(token.usdValue).toFixed(2)})`}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* NFTs Card */}
            {response.data.nfts.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">NFTs</h2>
                <div className="grid grid-cols-2 gap-4">
                  {response.data.nfts.map((nft, index) => (
                    <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      {nft.imageUrl && (
                        <Image
                          src={nft.imageUrl}
                          alt={nft.name}
                          width={200}
                          height={200}
                          className="rounded-lg mb-2"
                        />
                      )}
                      <div className="font-medium text-gray-900 dark:text-white">{nft.name}</div>
                      {nft.collectionName && (
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {nft.collectionName}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
