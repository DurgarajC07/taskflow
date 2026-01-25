import { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface DropdownItem {
  label: string;
  value: string;
  icon?: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  divider?: boolean;
}

interface DropdownProps {
  trigger: React.ReactNode;
  items: DropdownItem[];
  align?: 'left' | 'right';
  className?: string;
}

const Dropdown: React.FC<DropdownProps> = ({
  trigger,
  items,
  align = 'left',
  className,
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

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleItemClick = (item: DropdownItem) => {
    if (!item.disabled && item.onClick) {
      item.onClick();
      setIsOpen(false);
    }
  };

  return (
    <div ref={dropdownRef} className={cn('relative', className)}>
      <div onClick={() => setIsOpen(!isOpen)} className="cursor-pointer">
        {trigger}
      </div>

      {isOpen && (
        <div
          className={cn(
            'absolute mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          {items.map((item, index) => (
            <div key={item.value}>
              {item.divider && index > 0 && (
                <div className="my-1 border-t border-gray-200" />
              )}
              <button
                onClick={() => handleItemClick(item)}
                disabled={item.disabled}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-2 text-sm transition-colors',
                  item.disabled
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-700 hover:bg-gray-100'
                )}
              >
                {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
                <span className="flex-1 text-left">{item.label}</span>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export { Dropdown };
