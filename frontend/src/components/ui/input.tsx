// src/components/ui/input.tsx
import React from 'react';
import classNames from 'classnames';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input: React.FC<InputProps> = ({ className, ...props }) => {
  const classes = classNames(
    'border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
    className
  );

  return <input className={classes} {...props} />;
};

export { Input };
