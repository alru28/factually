import { useState } from 'react'
import Button from '../Button.tsx'

interface LoginFormProps {
  onSubmit: (data: { email: string; password: string }) => void;
  onForgotPassword: () => void;
}

export default function LoginForm({ onSubmit, onForgotPassword }: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    onSubmit({ email, password })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium mb-2">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-4 py-2 bg-fact-blue-700 rounded-lg focus:ring-2 focus:ring-fact-blue-500"
          required
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium mb-2">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-4 py-2 bg-fact-blue-700 rounded-lg focus:ring-2 focus:ring-fact-blue-500"
          required
        />
      </div>

      <Button type="submit" className="w-full">
        Sign In
      </Button>

      <Button type="submit" className="w-full" onClick={onForgotPassword}>
        Reset Password
      </Button>
    </form>
  )
}