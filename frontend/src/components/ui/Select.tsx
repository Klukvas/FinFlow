import React, { useState, useRef, useEffect } from 'react';

interface SelectProps {
  children: React.ReactNode;
  value?: string;
  onValueChange?: (value: string) => void;
  defaultValue?: string;
  'data-testid'?: string;
}

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
  'data-testid'?: string;
}

interface SelectContentProps {
  children: React.ReactNode;
  className?: string;
  'data-testid'?: string;
}

interface SelectItemProps {
  children: React.ReactNode;
  value: string;
  className?: string;
  'data-testid'?: string;
}

interface SelectValueProps {
  children?: React.ReactNode;
  placeholder?: string;
  'data-testid'?: string;
}

const SelectContext = React.createContext<{
  value?: string;
  onValueChange?: (value: string) => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  contentRef?: React.RefObject<HTMLDivElement>;
}>({
  isOpen: false,
  setIsOpen: () => {},
  contentRef: undefined
});

export const Select: React.FC<SelectProps> = ({ 
  children, 
  value, 
  onValueChange, 
  defaultValue 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedValue, setSelectedValue] = useState(value || defaultValue || '');
  const contentRef = useRef<HTMLDivElement>(null);

  // Sync internal state with external value prop
  useEffect(() => {
    if (value !== undefined) {
      setSelectedValue(value);
    }
  }, [value]);

  const handleValueChange = (newValue: string) => {
    console.log('🔧 Select - handleValueChange called with:', newValue);
    console.log('🔧 Select - current selectedValue:', selectedValue);
    console.log('🔧 Select - onValueChange function:', onValueChange);
    setSelectedValue(newValue);
    onValueChange?.(newValue);
    setIsOpen(false);
  };

  return (
    <SelectContext.Provider value={{
      value: selectedValue,
      onValueChange: handleValueChange,
      isOpen,
      setIsOpen,
      contentRef
    }}>
      {children}
    </SelectContext.Provider>
  );
};

export const SelectTrigger: React.FC<SelectTriggerProps> = ({ 
  children, 
  className = '',
  'data-testid': testId
}) => {
  const { isOpen, setIsOpen, contentRef } = React.useContext(SelectContext);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      console.log('🔧 SelectTrigger - handleClickOutside called');
      console.log('🔧 SelectTrigger - event.target:', event.target);
      console.log('🔧 SelectTrigger - triggerRef.current:', triggerRef.current);
      
      const isClickInsideTrigger = triggerRef.current && triggerRef.current.contains(event.target as Node);
      const isClickInsideContent = contentRef?.current && contentRef.current.contains(event.target as Node);
      
      if (!isClickInsideTrigger && !isClickInsideContent) {
        console.log('🔧 SelectTrigger - Click outside detected, closing dropdown');
        setIsOpen(false);
      } else {
        console.log('🔧 SelectTrigger - Click inside, keeping dropdown open');
      }
    };

    if (isOpen) {
      console.log('🔧 SelectTrigger - Adding click outside listener');
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      console.log('🔧 SelectTrigger - Removing click outside listener');
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, setIsOpen]);

  return (
    <button
      ref={triggerRef}
      type="button"
      onClick={() => {
        console.log('🔧 SelectTrigger - onClick, current isOpen:', isOpen);
        setIsOpen(!isOpen);
        console.log('🔧 SelectTrigger - isOpen set to:', !isOpen);
      }}
      className={`flex h-12 w-full items-center justify-between rounded-lg theme-border border theme-bg px-3 py-3 text-base theme-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition hover:theme-border-hover disabled:cursor-not-allowed disabled:opacity-50 touch-manipulation ${className}`}
      data-testid={testId || 'select-trigger'}
    >
      {children}
      <svg
        className={`h-5 w-5 theme-text-secondary transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        data-testid={testId ? `${testId}-icon` : 'select-trigger-icon'}
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
};

export const SelectContent: React.FC<SelectContentProps> = ({ 
  children, 
  className = '',
  'data-testid': testId
}) => {
  const { isOpen, contentRef } = React.useContext(SelectContext);

  console.log('🔧 SelectContent - isOpen:', isOpen);

  if (!isOpen) return null;

  return (
    <div 
      ref={contentRef}
      className={`absolute z-50 min-w-full overflow-hidden rounded-lg theme-border border theme-surface theme-shadow animate-in fade-in-0 zoom-in-95 max-h-60 overflow-y-auto ${className}`}
      data-testid={testId || 'select-content'}
    >
      <div className="p-1">
        {children}
      </div>
    </div>
  );
};

export const SelectItem: React.FC<SelectItemProps> = ({ 
  children, 
  value, 
  className = '',
  'data-testid': testId
}) => {
  const { onValueChange } = React.useContext(SelectContext);

  console.log('🔧 SelectItem - Component rendered with value:', value);
  console.log('🔧 SelectItem - onValueChange function:', onValueChange);

  return (
    <div
      onMouseDown={(e) => {
        console.log('🔧 SelectItem - onMouseDown called with value:', value);
        e.preventDefault();
      }}
      onClick={(e) => {
        console.log('🔧 SelectItem - onClick called with value:', value);
        console.log('🔧 SelectItem - event:', e);
        console.log('🔧 SelectItem - onValueChange function:', onValueChange);
        e.preventDefault();
        e.stopPropagation();
        onValueChange?.(value);
      }}
      className={`relative flex w-full select-none items-center rounded-md py-3 px-3 text-base outline-none theme-text-primary hover:theme-surface-hover focus:theme-surface-hover data-[disabled]:pointer-events-none data-[disabled]:opacity-50 cursor-pointer theme-transition touch-manipulation min-h-[44px] ${className}`}
      data-testid={testId || `select-item-${value}`}
    >
      {children}
    </div>
  );
};

export const SelectValue: React.FC<SelectValueProps> = ({ 
  children, 
  placeholder = 'Select...',
  'data-testid': testId
}) => {
  const { value } = React.useContext(SelectContext);

  if (value && children) {
    return <>{children}</>;
  }

  if (value && !children) {
    return (
      <span 
        className="theme-text-primary"
        data-testid={testId ? `${testId}-value` : 'select-value'}
      >
        {value}
      </span>
    );
  }

  return (
    <span 
      className="theme-text-tertiary"
      data-testid={testId ? `${testId}-placeholder` : 'select-placeholder'}
    >
      {placeholder}
    </span>
  );
};
