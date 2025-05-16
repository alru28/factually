import { useState } from 'react'

interface ApiKey {
  id: number;
  prefix: string;
  expires_at: string;
}

interface ApiKeyManagerProps {
  apiKeys: ApiKey[];
  onGenerate: () => Promise<void>;
}

export default function ApiKeyManager({ apiKeys, onGenerate }: ApiKeyManagerProps) {
  const [newKey, setNewKey] = useState('')

  const handleGenerate = async () => {
    try {
      await onGenerate()
    } catch (err) {
      // Error handling
    }
  }

  return (
    <div className="space-y-8">
      <div className="bg-fact-blue-800 rounded-xl p-6">
        <h2 className="text-xl font-semibold mb-4">Your API Keys</h2>
        
        {apiKeys.map(key => (
          <div key={key.id} className="p-4 bg-fact-blue-700 rounded-lg mb-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-mono text-fact-blue-200">{key.prefix}******</span>
                <span className="text-sm text-fact-blue-400 ml-4">Expires: {new Date(key.expires_at).toLocaleDateString()}</span>
              </div>
              <div className="space-x-3">
                <button className="text-fact-blue-300 hover:text-fact-blue-200 text-sm">
                  Renew
                </button>
                <button className="text-red-400 hover:text-red-300 text-sm">
                  Revoke
                </button>
              </div>
            </div>
          </div>
        ))}

        <button
          onClick={handleGenerate}
          className="mt-4 px-4 py-2 bg-fact-blue-600 hover:bg-fact-blue-500 rounded-lg transition-colors">
          Generate New API Key
        </button>
      </div>
    </div>
  )
}