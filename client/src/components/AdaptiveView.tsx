/**
 * Adaptive View Component
 * Platform-agnostic container that adapts to the current platform
 */

import React, { ReactNode } from 'react';

// Platform detection
const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

interface AdaptiveViewProps {
  children: ReactNode;
  style?: any;
  testID?: string;
  accessibilityLabel?: string;
}

// React Native implementation
const RNView: React.FC<AdaptiveViewProps> = ({ children, style, testID, accessibilityLabel }) => {
  const { View } = require('react-native');
  return (
    <View style={style} testID={testID} accessibilityLabel={accessibilityLabel}>
      {children}
    </View>
  );
};

// Web implementation
const WebView: React.FC<AdaptiveViewProps> = ({ children, style, testID, accessibilityLabel }) => {
  const webStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: style?.flexDirection || 'column',
    justifyContent: style?.justifyContent,
    alignItems: style?.alignItems,
    padding: style?.padding,
    margin: style?.margin,
    backgroundColor: style?.backgroundColor,
    borderRadius: style?.borderRadius,
    ...style,
  };

  return (
    <div style={webStyle} data-testid={testID} aria-label={accessibilityLabel}>
      {children}
    </div>
  );
};

export const AdaptiveView: React.FC<AdaptiveViewProps> = (props) => {
  if (isReactNative) {
    return <RNView {...props} />;
  }
  return <WebView {...props} />;
};

export default AdaptiveView;
