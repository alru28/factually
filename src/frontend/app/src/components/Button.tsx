import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  href?: string;
}

export default function Button({ href, children, ...props }: ButtonProps) {
  const className = "inline-block px-4 py-2 bg-fact-blue-700 text-white font-bold rounded-lg hover:bg-fact-blue-500 transition-colors";
  
  return href ? (
    <a href={href} className={className}>
      {children}
    </a>
  ) : (
    <button {...props} className={`${className} ${props.className || ''}`}>
      {children}
    </button>
  );
}