import { useState, createContext, useContext, type ReactNode } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { colors, shadows, transitions, zIndex } from '../../lib/design-tokens';

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextType {
  showToast: (toast: Omit<Toast, 'id'>) => void;
  hideToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast = { ...toast, id };
    setToasts((prev) => [...prev, newToast]);

    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => hideToast(id), duration);
    }
  };

  const hideToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast, hideToast }}>
      {children}
      <ToastContainer toasts={toasts} onClose={hideToast} />
    </ToastContext.Provider>
  );
};

const ToastContainer = ({ toasts, onClose }: { toasts: Toast[]; onClose: (id: string) => void }) => {
  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: '1rem',
        right: '1rem',
        zIndex: zIndex.toast,
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        maxWidth: '24rem',
      }}
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={onClose} />
      ))}
    </div>
  );
};

const ToastItem = ({ toast, onClose }: { toast: Toast; onClose: (id: string) => void }) => {
  const [isExiting, setIsExiting] = useState(false);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => onClose(toast.id), 200);
  };

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle size={20} />;
      case 'error':
        return <AlertCircle size={20} />;
      case 'warning':
        return <AlertTriangle size={20} />;
      case 'info':
        return <Info size={20} />;
    }
  };

  const getColors = () => {
    switch (toast.type) {
      case 'success':
        return {
          bg: colors.success[50],
          border: colors.success[500],
          icon: colors.success[600],
          text: colors.success[700],
        };
      case 'error':
        return {
          bg: colors.error[50],
          border: colors.error[500],
          icon: colors.error[600],
          text: colors.error[700],
        };
      case 'warning':
        return {
          bg: colors.warning[50],
          border: colors.warning[500],
          icon: colors.warning[600],
          text: colors.warning[700],
        };
      case 'info':
        return {
          bg: colors.info[50],
          border: colors.info[500],
          icon: colors.info[600],
          text: colors.info[700],
        };
    }
  };

  const themeColors = getColors();

  return (
    <div
      style={{
        backgroundColor: themeColors.bg,
        borderLeft: `4px solid ${themeColors.border}`,
        borderRadius: '0.5rem',
        padding: '1rem',
        boxShadow: shadows.lg,
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
        minWidth: '20rem',
        maxWidth: '24rem',
        animation: isExiting ? 'slideOut 200ms ease-out' : 'slideIn 200ms ease-out',
        transform: isExiting ? 'translateX(150%)' : 'translateX(0)',
        transition: `transform ${transitions.base}`,
      }}
    >
      <div style={{ color: themeColors.icon, flexShrink: 0 }}>{getIcon()}</div>
      
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontWeight: 600,
            fontSize: '0.875rem',
            color: themeColors.text,
            marginBottom: toast.message ? '0.25rem' : 0,
          }}
        >
          {toast.title}
        </div>
        {toast.message && (
          <div
            style={{
              fontSize: '0.8125rem',
              color: colors.neutral[600],
              lineHeight: 1.5,
            }}
          >
            {toast.message}
          </div>
        )}
      </div>

      <button
        onClick={handleClose}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: 0,
          color: colors.neutral[400],
          flexShrink: 0,
          transition: `color ${transitions.fast}`,
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = colors.neutral[600])}
        onMouseLeave={(e) => (e.currentTarget.style.color = colors.neutral[400])}
      >
        <X size={16} />
      </button>
    </div>
  );
};
