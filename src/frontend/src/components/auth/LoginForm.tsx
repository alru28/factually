import React, { useState } from 'react';
import { loginUser } from '../../api/auth';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await loginUser(email, password);
      alert('Logged in successfully!');
    } catch (err) {
      alert('Login failed. Check credentials.');
    }
  };

  return (
    <form onSubmit={handleLogin} className="space-y-4">
      <input type="email" placeholder="Email" className="input" value={email} onChange={e => setEmail(e.target.value)} required />
      <input type="password" placeholder="Password" className="input" value={password} onChange={e => setPassword(e.target.value)} required />
      <button type="submit" className="btn bg-fact-blue-600">Login</button>
    </form>
  );
}
