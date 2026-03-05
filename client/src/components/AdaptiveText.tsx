/**
 * Adaptive Text Component
 * Platform-agnostic text component with adaptive styling
 */

import React, { ReactNode } from 'react';

const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

interface AdaptiveTextProps {
  children: ReactNode;
  style?: any;
  variant?: 'h1' | 'h2' | 'h3' | 'body' | 'caption' | 'label';
  numberOfLines?: number;
  testID?: string;
  onPress?: () => void;
}

// Default styles for variants
const variantStyles: Record<string, any> = {
  h1: {
    fontSize: 32,
    fontWeight: 'bold',
    lineHeight: 40,
  },
  h2: {
    fontSize: 24,
    fontWeight: 'bold',
    lineHeight: 32,
  },
  h3: {
    fontSize: 20,
    fontWeight: '600',
    lineHeight: 28,
  },
  body: {
    fontSize: 16,
    fontWeight: 'normal',
    lineHeight: 24,
  },
  caption: {
    fontSize: 14,
    fontWeight: 'normal',
    lineHeight: 20,
    color: '#666',
  },
  label: {
    fontSize: 12,
    fontWeight: '500',
    lineHeight: 16,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
};

// React Native implementation
const RNText: React.FC<AdaptiveTextProps> = ({ 
  children, 
  style, 
  variant = 'body',
  numberOfLines,
  testID,
  onPress 
}) => {
  const { Text } = require('react-native');
  
  const combinedStyle = {
    ...variantStyles[variant],
    ...style,
  };

  return (
    <Text 
      style={combinedStyle} 
      numberOfLines={numberOfLines}
      testID={testID}
      onPress={onPress}
    >
      {children}
    </Text>
  );
};

// Web implementation
const WebText: React.FC<AdaptiveTextProps> = ({ 
  children, 
  style, 
  variant = 'body',
  numberOfLines,
  testID,
  onPress 
}) => {
  const variantStyle = variantStyles[variant];
  
  const webStyle: React.CSSProperties = {
    fontSize: variantStyle.fontSize,
    fontWeight: variantStyle.fontWeight,
    lineHeight: `${variantStyle.lineHeight}px`,
    color: style?.color || variantStyle.color || '#000',
    margin: 0,
    padding: 0,
    cursor: onPress ? 'pointer' : 'inherit',
    display: '-webkit-box',
    WebkitLineClamp: numberOfLines,
    WebkitBoxOrient: 'vertical',
    overflow: numberOfLines ? 'hidden' : 'visible',
    textOverflow: numberOfLines ? 'ellipsis' : 'clip',
    ...style,
  };

  const Tag = variant === 'h1' ? 'h1' : 
              variant === 'h2' ? 'h2' : 
              variant === 'h3' ? 'h3' : 'span';

  return (
    <Tag 
      style={webStyle} 
      data-testid={testID}
      onClick={onPress}
    >
      {children}
    </Tag>
  );
};

export const AdaptiveText: React.FC<AdaptiveTextProps> = (props) => {
  if (isReactNative) {
    return <RNText {...props} />;
  }
  return <WebText {...props} />;
};

export default AdaptiveText;
