import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({ 
  className, 
  children, 
  hover = false,
  ...props 
}) => {
  return (
    <div
      className={cn(
        'bg-white rounded-xl border border-neutral-200 shadow-soft p-6',
        hover && 'transition-all duration-200 hover:shadow-medium hover:border-neutral-300 cursor-pointer',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ 
  className, 
  children,
  ...props 
}) => {
  return (
    <div className={cn('mb-4', className)} {...props}>
      {children}
    </div>
  );
};

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ 
  className, 
  children,
  ...props 
}) => {
  return (
    <h3 className={cn('text-lg font-semibold text-neutral-900', className)} {...props}>
      {children}
    </h3>
  );
};

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({ 
  className, 
  children,
  ...props 
}) => {
  return (
    <p className={cn('text-sm text-neutral-600 mt-1', className)} {...props}>
      {children}
    </p>
  );
};

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ 
  className, 
  children,
  ...props 
}) => {
  return (
    <div className={cn('', className)} {...props}>
      {children}
    </div>
  );
};
