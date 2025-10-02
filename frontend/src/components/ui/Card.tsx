import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  'data-testid'?: string;
}

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
  'data-testid'?: string;
}

interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
  'data-testid'?: string;
}

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
  'data-testid'?: string;
}

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
  'data-testid'?: string;
}

export const Card: React.FC<CardProps> = ({ children, className = '', hover = false, 'data-testid': testId }) => {
  return (
    <div 
      className={`rounded-lg border theme-border theme-surface theme-shadow theme-transition ${
        hover ? 'hover:theme-shadow-hover hover:theme-border-hover' : ''
      } ${className}`}
      data-testid={testId || 'card'}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className = '', 'data-testid': testId }) => {
  return (
    <div 
      className={`p-4 sm:p-6 pb-0 ${className}`}
      data-testid={testId || 'card-header'}
    >
      {children}
    </div>
  );
};

export const CardTitle: React.FC<CardTitleProps> = ({ children, className = '', 'data-testid': testId }) => {
  return (
    <h3 
      className={`text-lg font-semibold leading-none tracking-tight theme-text-primary ${className}`}
      data-testid={testId || 'card-title'}
    >
      {children}
    </h3>
  );
};

export const CardContent: React.FC<CardContentProps> = ({ children, className = '', 'data-testid': testId }) => {
  return (
    <div 
      className={`p-4 sm:p-6 ${className}`}
      data-testid={testId || 'card-content'}
    >
      {children}
    </div>
  );
};

export const CardFooter: React.FC<CardFooterProps> = ({ children, className = '', 'data-testid': testId }) => {
  return (
    <div 
      className={`p-4 sm:p-6 pt-0 theme-border border-t ${className}`}
      data-testid={testId || 'card-footer'}
    >
      {children}
    </div>
  );
};
