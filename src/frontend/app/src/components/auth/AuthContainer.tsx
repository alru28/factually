import { useState, useEffect } from 'react'
import { loginUser, registerUser, requestPasswordReset, getApiKeys, generateApiKey, renewApiKey, revokeApiKey } from '../../api/auth'
import LoginForm from './LoginForm.tsx'
import PasswordResetForm from './PasswordResetForm.tsx'
import RegisterForm from './RegisterForm.tsx'
import ApiKeyManager from './ApiKeyManager.tsx'
import { AxiosError } from 'axios';

interface ApiKey {
  created_at: string;
  id: number;
  key: string;
  expires_at: string;
}

interface Message {
  type: 'success' | 'error' | '';
  content: any;
}

export default function AuthContainer() {
  const [activeTab, setActiveTab] = useState<'login' | 'register' | 'reset'>('login');
const [isLoggedIn, setIsLoggedIn] = useState(false);
const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
const [message, setMessage] = useState<Message>({ type: '', content: '' });

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      checkAuthStatus()
    }
  }, [])

  const checkAuthStatus = async () => {
    try {
      const response = await getApiKeys()
      setIsLoggedIn(true)
      setApiKeys(response.data.api_keys || [])
    } catch (err) {
      const error = err as AxiosError;
      if (error.response?.status === 404) {
        // No API keys found - valid empty state
        setIsLoggedIn(true);
        setApiKeys([]);
      } else {
        // Other errors - log out
        localStorage.removeItem('token');
        setIsLoggedIn(false);
      }
    }
  }

  const handleAuthAction = async (action: string, data: any) => {
    try {
      switch(action) {
        case 'login':
          await loginUser(data.email, data.password)
          await checkAuthStatus()
          break
        case 'register':
          await registerUser(data.email, data.password)
          setMessage({ type: 'success', content: 'Registration successful! Check your email to verify.' })
          setActiveTab('login')
          break
        case 'reset':
          await requestPasswordReset(data.email)
          setMessage({ type: 'success', content: 'Password reset instructions sent to your email' })
          break
        case 'generate':
          const newKey = await generateApiKey()
          setApiKeys([...apiKeys, newKey.data])
          break
        case 'renew':
          await renewApiKey(data.api_key_id);
          const renewedKeys = await getApiKeys();
          setApiKeys(renewedKeys.data.api_keys || []);
          break;
        case 'revoke':
          await revokeApiKey(data.api_key_id);
          setApiKeys(prev => prev.filter(key => key.id !== data.api_key_id));
          break;
      }
    } catch (err) {
        const error = err as AxiosError;
        console.error('API Error:', error);

        setMessage({
          type: 'error',
          content: 'An unexpected error occurred'
        });
    }
  }

  if (isLoggedIn) {
  return (
    <ApiKeyManager 
      apiKeys={apiKeys} 
      onGenerate={() => handleAuthAction('generate', {})}
      onRenew={(apiKeyId) => handleAuthAction('renew', { api_key_id: apiKeyId })}
      onRevoke={(apiKeyId) => handleAuthAction('revoke', { api_key_id: apiKeyId })}
    />
  );
}

  return (
    <div className="bg-fact-blue-800 rounded-xl shadow-lg p-8">
      {message.content && (
        <div className={`mb-6 p-4 rounded-lg ${message.type === 'error' ? 'bg-red-900' : 'bg-green-900'}`}>
          {message.content}
        </div>
      )}
      
      <div className="flex gap-4 mb-8 border-b border-fact-blue-600">
        <button
          onClick={() => setActiveTab('login')}
          className={`pb-2 px-4 ${activeTab === 'login' ? 'border-b-2 border-fact-blue-500' : ''}`}>
          Sign In
        </button>
        <button
          onClick={() => setActiveTab('register')}
          className={`pb-2 px-4 ${activeTab === 'register' ? 'border-b-2 border-fact-blue-500' : ''}`}>
          Register
        </button>
      </div>

      {activeTab === 'login' ? (
        <LoginForm 
          onSubmit={(data) => handleAuthAction('login', data)}
          onForgotPassword={() => setActiveTab('reset')}
        />
      ) : activeTab === 'register' ? (
        <RegisterForm onSubmit={(data) => handleAuthAction('register', data)} />
      ) : (
        <PasswordResetForm onSubmit={(data) => handleAuthAction('reset', data)} />
      )}
    </div>
  )
}