/**
 * Adaptive Button Component
 * Platform-agnostic button with adaptive styling
 */

import React, { ReactNode } from 'react';

const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

interface AdaptiveButtonProps {
  children: ReactNode;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  style?: any;
  testID?: string;
  icon?: ReactNode;
}

// Theme colors
const theme = {
  primary: '#007AFF',
  secondary: '#5856D6',
  danger: '#FF3B30',
  success: '#34C759',
  background: '#FFFFFF',
  text: '#000000',
  textInverse: '#FFFFFF',
  border: '#E5E5EA',
  disabled: '#C7C7CC',
};

// Size configurations
const sizeConfig = {
  small: { paddingVertical: 8, paddingHorizontal: 12, fontSize: 14, borderRadius: 6 },
  medium: { paddingVertical: 12, paddingHorizontal: 16, fontSize: 16, borderRadius: 8 },
  large: { paddingVertical: 16, paddingHorizontal: 24, fontSize: 18, borderRadius: 10 },
};

// Variant styles
const getVariantStyles = (variant: string, disabled: boolean) => {
  const base = {
    primary: {
      backgroundColor: disabled ? theme.disabled : theme.primary,
      color: theme.textInverse,
      borderWidth: 0,
    },
    secondary: {
      backgroundColor: disabled ? theme.disabled : theme.secondary,
      color: theme.textInverse,
      borderWidth: 0,
    },
    outline: {
      backgroundColor: 'transparent',
      color: disabled ? theme.disabled : theme.primary,
      borderWidth: 1,
      borderColor: disabled ? theme.disabled : theme.primary,
    },
    ghost: {
      backgroundColor: 'transparent',
      color: disabled ? theme.disabled : theme.primary,
      borderWidth: 0,
    },
    danger: {
      backgroundColor: disabled ? theme.disabled : theme.danger,
      color: theme.textInverse,
      borderWidth: 0,
    },
  };

  return base[variant as keyof typeof base] || base.primary;
};

// React Native implementation
const RNButton: React.FC<AdaptiveButtonProps> = ({
  children,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  style,
  testID,
  icon,
}) => {
  const { TouchableOpacity, View, Text, ActivityIndicator } = require('react-native');
  
  const sizeStyles = sizeConfig[size];
  const variantStyles = getVariantStyles(variant, disabled);

  const buttonStyle = {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: sizeStyles.paddingVertical,
    paddingHorizontal: sizeStyles.paddingHorizontal,
    backgroundColor: variantStyles.backgroundColor,
    borderRadius: sizeStyles.borderRadius,
    borderWidth: variantStyles.borderWidth,
    borderColor: variantStyles.borderColor,
    opacity: disabled || loading ? 0.6 : 1,
    ...style,
  };

  const textStyle = {
    fontSize: sizeStyles.fontSize,
    fontWeight: '600',
    color: variantStyles.color,
    marginLeft: icon ? 8 : 0,
  };

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      style={buttonStyle}
      testID={testID}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator color={variantStyles.color} />
      ) : (
        <>
          {icon}
          <Text style={textStyle}>{children}</Text>
        </>
      )}
    </TouchableOpacity>
  );
};

// Web implementation
const WebButton: React.FC<AdaptiveButtonProps> = ({
  children,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  style,
  testID,
  icon,
}) => {
  const sizeStyles = sizeConfig[size];
  const variantStyles = getVariantStyles(variant, disabled);

  const buttonStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: `${sizeStyles.paddingVertical}px ${sizeStyles.paddingHorizontal}px`,
    backgroundColor: variantStyles.backgroundColor,
    borderRadius: sizeStyles.borderRadius,
    border: variantStyles.borderWidth ? `${variantStyles.borderWidth}px solid ${variantStyles.borderColor}` : 'none',
    opacity: disabled || loading ? 0.6 : 1,
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    transition: 'all 0.2s ease',
    outline: 'none',
    ...style,
  };

  const textStyle: React.CSSProperties = {
    fontSize: sizeStyles.fontSize,
    fontWeight: 600,
    color: variantStyles.color,
    marginLeft: icon ? 8 : 0,
    fontFamily: 'system-ui, -apple-system, sans-serif',
  };

  const handleMouseEnter = (e: React.MouseEvent) => {
    if (!disabled && !loading) {
      (e.target as HTMLElement).style.opacity = '0.8';
      (e.target as HTMLElement).style.transform = 'translateY(-1px)';
    }
  };

  const handleMouseLeave = (e: React.MouseEvent) => {
    (e.target as HTMLElement).style.opacity = disabled || loading ? '0.6' : '1';
    (e.target as HTMLElement).style.transform = 'translateY(0)';
  };

  return (
    <button
      onClick={onPress}
      disabled={disabled || loading}
      style={buttonStyle}
      data-testid={testID}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {loading ? (
        <span className="loading-spinner" style={{ 
          width: sizeStyles.fontSize, 
          height: sizeStyles.fontSize,
          border: `2px solid ${variantStyles.color}`,
          borderTopColor: 'transparent',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }} />
      ) : (
        <>
          {icon}
          <span style={textStyle}>{children}</span>
        </>
      )}
    </button>
  );
};

export const AdaptiveButton: React.FC<AdaptiveButtonProps> = (props) => {
  if (isReactNative) {
    return <RNButton {...props} />;
  }
  return <WebButton {...props} />;
};

export default AdaptiveButton;
