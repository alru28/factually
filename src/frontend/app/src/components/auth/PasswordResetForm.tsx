import { useState } from 'react';
import Button from '../Button.tsx';

interface PasswordResetFormProps {
  onSubmit: (data: { email: string }) => void;
}

export default function PasswordResetForm({ onSubmit }: PasswordResetFormProps) {
  const [email, setEmail] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ email });
  };

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

      <Button type="submit" className="w-full">
        Send Reset Instructions
      </Button>
    </form>
  );
}