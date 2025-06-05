import React, { useEffect, useState } from 'react';
import { verifyEmail } from '../../api/auth.ts';
import Button from '../Button.tsx';

export default function EmailVerifyPage() {
  const [status, setStatus] = useState<'loading'|'success'|'error'>('loading');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (!token) {
      setStatus('error');
      return;
    }

    verifyEmail(token)
      .then(() => {
        setStatus('success');
        // REDIRECT
        setTimeout(() => window.location.href = '/auth', 3000);
      })
      .catch(() => {
        setStatus('error');
      });
  }, []);

  if (status === 'loading') {
    return <p className="text-fact-blue-200">Verifying your email…</p>;
  }

  if (status === 'success') {
    return (
      <div className="space-y-4">
        <p className="text-green-400">✅ Your email has been verified!</p>
        <p className="text-fact-blue-200">Redirecting you back to login…</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-red-400">❌ Invalid or expired token.</p>
        <Button href="/auth">Back to Auth</Button>
    </div>
  );
}
