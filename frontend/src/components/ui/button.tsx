// src/components/ui/button.tsx
import React from 'react';
import classNames from 'classnames';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'solid' | 'outline' | 'ghost';
  size?: 'small' | 'medium' | 'large' | 'icon';
}

const Button: React.FC<ButtonProps> = ({
  variant = 'solid',
  size = 'medium',
  className,
  ...props
}) => {
  const classes = classNames(
    'px-4 py-2 rounded-md font-medium',
    {
      'bg-blue-500 text-white hover:bg-blue-600': variant === 'solid',
      'border border-blue-500 text-blue-500 hover:bg-blue-50': variant === 'outline',
      'text-blue-500 hover:bg-blue-50': variant === 'ghost',
      'p-1': size === 'icon',
      'px-4 py-2': size === 'medium',
      // Add other size variants as needed
    },
    className
  );

  return <button className={classes} {...props} />;
};

export { Button };
