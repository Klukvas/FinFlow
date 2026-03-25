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
 disabled?: boolean;
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
 disabled?: boolean;
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
 contentRef?: React.RefObject<HTMLDivElement> | undefined;
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
 const contentRef = useRef<HTMLDivElement>(null) as React.RefObject<HTMLDivElement>;

 // Sync internal state with external value prop
 useEffect(() => {
 if (value !== undefined) {
 setSelectedValue(value);
 }
 }, [value]);

 const handleValueChange = (newValue: string) => {
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
 <div className="relative">
 {children}
 </div>
 </SelectContext.Provider>
 );
};

export const SelectTrigger: React.FC<SelectTriggerProps> = ({ 
 children, 
 className = '',
 disabled = false,
 'data-testid': testId
}) => {
 const { isOpen, setIsOpen, contentRef } = React.useContext(SelectContext);
 const triggerRef = useRef<HTMLButtonElement>(null);

 useEffect(() => {
 const handleClickOutside = (event: MouseEvent) => {
 const isClickInsideTrigger = triggerRef.current && triggerRef.current.contains(event.target as Node);
 const isClickInsideContent = contentRef?.current && contentRef.current.contains(event.target as Node);
 
 if (!isClickInsideTrigger && !isClickInsideContent) {
 setIsOpen(false);
 }
 };

 if (isOpen) {
 document.addEventListener('mousedown', handleClickOutside);
 }

 return () => {
 document.removeEventListener('mousedown', handleClickOutside);
 };
 }, [isOpen, setIsOpen]);

 return (
 <button
 ref={triggerRef}
 type="button"
 onClick={() => {
 setIsOpen(!isOpen);
 }}
 className={`flex h-12 w-full items-center justify-between rounded-lg border-[var(--border)] border bg-surface px-3 py-3 text-base text-content focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-colors hover:border-[var(--border-hover)] disabled:cursor-not-allowed disabled:opacity-50 touch-manipulation overflow-hidden ${className}`}
 disabled={disabled}
 data-testid={testId || 'select-trigger'}
 >
 <span className="flex-1 min-w-0 overflow-hidden text-left">
 {children}
 </span>
 <svg
 className={`h-5 w-5 text-content-secondary transition-transform duration-200 flex-shrink-0 ml-2 ${isOpen ? 'rotate-180' : ''}`}
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


 if (!isOpen) return null;

 return (
 <div 
 ref={contentRef}
 className={`absolute top-full left-0 z-50 mt-1 w-full max-w-full overflow-hidden rounded-lg border-[var(--border)] border bg-elevated theme-shadow animate-in fade-in-0 zoom-in-95 max-h-60 overflow-y-auto box-border ${className}`}
 data-testid={testId || 'select-content'}
 >
 <div className="p-1 w-full box-border">
 {children}
 </div>
 </div>
 );
};

export const SelectItem: React.FC<SelectItemProps> = ({ 
 children, 
 value, 
 className = '',
 disabled = false,
 'data-testid': testId
}) => {
 const { onValueChange } = React.useContext(SelectContext);

 return (
 <div
 onMouseDown={(e) => {
 if (!disabled) {
 e.preventDefault();
 }
 }}
 onClick={(e) => {
 if (!disabled) {
 e.preventDefault();
 e.stopPropagation();
 onValueChange?.(value);
 }
 }}
 className={`relative flex w-full select-none items-center rounded-md py-3 px-3 text-base outline-none text-content hover:bg-surface-alt focus:bg-surface-alt data-[disabled]:pointer-events-none data-[disabled]:opacity-50 cursor-pointer transition-colors touch-manipulation min-h-[44px] overflow-hidden ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
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
 className="text-content"
 data-testid={testId ? `${testId}-value` : 'select-value'}
 >
 {value}
 </span>
 );
 }

 return (
 <span 
 className="text-content-tertiary"
 data-testid={testId ? `${testId}-placeholder` : 'select-placeholder'}
 >
 {placeholder}
 </span>
 );
};
