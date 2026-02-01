import { Spinner } from './Spinner';
import { spacing, colors } from '../../lib/design-tokens';

interface LoadingStateProps {
  message?: string;
  fullScreen?: boolean;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const LoadingState = ({ 
  message = 'Loading...', 
  fullScreen = false,
  size = 'lg',
}: LoadingStateProps) => {
  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing[4],
    padding: spacing[8],
  };

  if (fullScreen) {
    containerStyle.position = 'fixed';
    containerStyle.top = 0;
    containerStyle.left = 0;
    containerStyle.right = 0;
    containerStyle.bottom = 0;
    containerStyle.backgroundColor = 'rgba(255, 255, 255, 0.95)';
    containerStyle.zIndex = 9999;
  } else {
    containerStyle.minHeight = '400px';
  }

  return (
    <div style={containerStyle}>
      <Spinner size={size} />
      {message && (
        <p
          style={{
            fontSize: '0.875rem',
            color: colors.neutral[600],
            fontWeight: 500,
          }}
        >
          {message}
        </p>
      )}
    </div>
  );
};
