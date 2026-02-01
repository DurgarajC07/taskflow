import { Component, type ReactNode, type ErrorInfo } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { colors, spacing } from '../../lib/design-tokens';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '400px',
            padding: spacing[8],
          }}
        >
          <div
            style={{
              textAlign: 'center',
              maxWidth: '32rem',
            }}
          >
            <div
              style={{
                width: '4rem',
                height: '4rem',
                margin: '0 auto',
                marginBottom: spacing[4],
                borderRadius: '50%',
                backgroundColor: colors.error[100],
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <AlertCircle size={32} color={colors.error[600]} />
            </div>

            <h2
              style={{
                fontSize: '1.5rem',
                fontWeight: 600,
                color: colors.neutral[900],
                marginBottom: spacing[2],
              }}
            >
              Something went wrong
            </h2>

            <p
              style={{
                fontSize: '0.875rem',
                color: colors.neutral[600],
                marginBottom: spacing[6],
                lineHeight: 1.6,
              }}
            >
              We're sorry for the inconvenience. An unexpected error occurred.
            </p>

            <button
              onClick={this.handleReset}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: spacing[2],
                padding: `${spacing[3]} ${spacing[6]}`,
                backgroundColor: colors.brand[600],
                color: 'white',
                border: 'none',
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'background-color 150ms',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = colors.brand[700])}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = colors.brand[600])}
            >
              <RefreshCw size={16} />
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
