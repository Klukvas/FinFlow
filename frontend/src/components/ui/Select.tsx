import React, { useState, useRef, useEffect } from 'react';

interface SelectProps {
  children: React.ReactNode;
  value?: string;
  onValueChange?: (value: string) => void;
  defaultValue?: string;
}

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectContentProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectItemProps {
  children: React.ReactNode;
  value: string;
  className?: string;
}

interface SelectValueProps {
  children?: React.ReactNode;
  placeholder?: string;
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
  className = '' 
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
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm ring-offset-white dark:ring-offset-gray-900 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
    >
      {children}
      <svg
        className={`h-4 w-4 opacity-50 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
};

export const SelectContent: React.FC<SelectContentProps> = ({ 
  children, 
  className = '' 
}) => {
  const { isOpen, contentRef } = React.useContext(SelectContext);

  console.log('🔧 SelectContent - isOpen:', isOpen);

  if (!isOpen) return null;

  return (
    <div 
      ref={contentRef}
      className={`absolute z-50 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-md animate-in fade-in-0 zoom-in-95 ${className}`}
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
  className = '' 
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
      className={`relative flex w-full select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-gray-100 dark:focus:bg-gray-700 focus:text-gray-900 dark:focus:text-gray-100 data-[disabled]:pointer-events-none data-[disabled]:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer ${className}`}
    >
      {children}
    </div>
  );
};

export const SelectValue: React.FC<SelectValueProps> = ({ 
  children, 
  placeholder = 'Select...' 
}) => {
  const { value } = React.useContext(SelectContext);

  if (value && children) {
    return <>{children}</>;
  }

  if (value && !children) {
    return (
      <span className="text-gray-900 dark:text-gray-100">
        {value}
      </span>
    );
  }

  return (
    <span className="text-gray-500 dark:text-gray-400">
      {placeholder}
    </span>
  );
};
