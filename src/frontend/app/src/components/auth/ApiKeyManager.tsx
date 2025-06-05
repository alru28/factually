import { useState } from 'react'
import { ClipboardDocumentIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline'

interface ApiKey {
  id: number;
  key: string;
  expires_at: string;
  created_at: string;
}

interface ApiKeyManagerProps {
  apiKeys: ApiKey[];
  onGenerate: () => Promise<void>;
  onRenew: (apiKeyId: number) => Promise<void>;
  onRevoke: (apiKeyId: number) => Promise<void>;
}

export default function ApiKeyManager({ apiKeys, onGenerate, onRenew, onRevoke }: ApiKeyManagerProps) {
  const [visibleKeys, setVisibleKeys] = useState<Record<number, boolean>>({});
  const [copiedKeyId, setCopiedKeyId] = useState<number | null>(null);

  const toggleKeyVisibility = (keyId: number) => {
    setVisibleKeys(prev => ({ ...prev, [keyId]: !prev[keyId] }));
  };

  const copyToClipboard = async (key: string, keyId: number) => {
    await navigator.clipboard.writeText(key);
    setCopiedKeyId(keyId);
    setTimeout(() => setCopiedKeyId(null), 2000);
  };

  return (
    <div className="space-y-8">
      <div className="bg-fact-blue-800 rounded-xl p-6">
        <h2 className="text-xl font-semibold mb-6">Your API Keys</h2>
        
        {apiKeys.length === 0 ? (
          <div className="text-center py-6">
            <p className="text-fact-blue-300 mb-4">
              No API keys found. Generate your first key to get started.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {apiKeys.map(key => (
              <div key={key.id} className="p-4 bg-fact-blue-700 rounded-lg">
                <div className="flex items-center justify-between gap-4">
                  {/* KEY INFO */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <button
                        onClick={() => toggleKeyVisibility(key.id)}
                        className="text-fact-blue-300 hover:text-fact-blue-200"
                      >
                        {visibleKeys[key.id] ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </button>
                      
                      <span className="font-mono text-fact-blue-200 break-all">
                        {visibleKeys[key.id] ? key.key : `${key.key.substring(0, 8)}••••${key.key.slice(-4)}`}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-fact-blue-400">
                      <span>Created: {new Date(key.created_at).toLocaleDateString()}</span>
                      <span>|</span>
                      <span>Expires: {new Date(key.expires_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* ACTIONS */}
                  <div className="flex items-center gap-4 flex-shrink-0">
                    <button
                      onClick={() => copyToClipboard(key.key, key.id)}
                      className="relative text-fact-blue-300 hover:text-fact-blue-200"
                      title="Copy to clipboard"
                    >
                      <ClipboardDocumentIcon className="h-5 w-5" />
                      {copiedKeyId === key.id && (
                        <span className="absolute -top-8 left-1/2 -translate-x-1/2 bg-fact-blue-900 text-xs px-2 py-1 rounded">
                          Copied!
                        </span>
                      )}
                    </button>
                    <div className="flex gap-2">
                      <button
                        onClick={() => onRenew(key.id)}
                        className="px-3 py-1 text-sm bg-fact-blue-600 hover:bg-fact-blue-500 rounded"
                      >
                        Renew
                      </button>
                      <button
                        onClick={() => onRevoke(key.id)}
                        className="px-3 py-1 text-sm bg-red-700 hover:bg-red-600 rounded"
                      >
                        Revoke
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <button
          onClick={onGenerate}
          className="mt-6 w-full py-2 px-4 bg-fact-blue-600 hover:bg-fact-blue-500 rounded-lg transition-colors font-medium flex items-center justify-center gap-2"
        >
          {apiKeys.length === 0 ? 'Generate First API Key' : 'Generate New API Key'}
        </button>
      </div>
    </div>
  );
}