import React, { useState, useRef, useEffect } from "react";

interface DropdownMenuProps {
  trigger: React.ReactNode;
  children: React.ReactNode;
  align?: "left" | "right";
}

export const DropdownMenu: React.FC<DropdownMenuProps> = ({
  trigger,
  children,
  align = "right",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <div onClick={() => setIsOpen(!isOpen)}>{trigger}</div>

      {isOpen && (
        <div
          className={`absolute z-50 mt-2 w-48 rounded-[var(--radius-lg)] bg-[var(--bg-surface)] border border-[var(--border)] ${
            align === "right" ? "right-0" : "left-0"
          }`}
          style={{ boxShadow: "var(--shadow-md)" }}
        >
          <div className="py-1">{children}</div>
        </div>
      )}
    </div>
  );
};

interface DropdownMenuItemProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
  title?: string;
}

export const DropdownMenuItem: React.FC<DropdownMenuItemProps> = ({
  children,
  onClick,
  className = "",
  disabled = false,
  title,
}) => (
  <button
    className={`w-full text-left px-4 py-2 text-[13px] transition-colors ${
      disabled
        ? "text-[var(--text-tertiary)] cursor-not-allowed"
        : "text-[var(--text-secondary)] hover:bg-[var(--bg-raised)] hover:text-[var(--text-primary)]"
    } ${className}`}
    onClick={onClick}
    disabled={disabled}
    title={title}
  >
    {children}
  </button>
);

export const DropdownMenuSeparator: React.FC = () => (
  <div className="my-1 border-t border-[var(--border)]" />
);
