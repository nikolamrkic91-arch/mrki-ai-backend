# Mrki Client

Cross-platform client for Mrki - built with React Native (iOS/Android) and Electron (Windows).

## Project Structure

```
mrki/client/
├── src/
│   ├── App.tsx              # Main shared React component
│   └── hooks/
│       └── useWebSocket.ts  # WebSocket hook for real-time communication
├── mobile/
│   ├── index.js             # React Native entry point
│   ├── ios/                 # iOS project files
│   └── android/             # Android project files
├── desktop/
│   ├── main.js              # Electron main process
│   ├── preload.js           # Electron preload script
│   └── index.html           # Desktop app HTML shell
├── package.json             # Dependencies and scripts
└── tsconfig.json            # TypeScript configuration
```

## Prerequisites

- **Node.js** >= 18.0.0
- **npm** or **yarn**
- **iOS**: macOS with Xcode 14+
- **Android**: Android Studio with SDK 34
- **Windows**: Windows 10/11 with Visual Studio Build Tools

## Installation

```bash
# Install dependencies
npm install

# iOS - Install CocoaPods
cd mobile/ios && pod install && cd ../..
```

## Development

### Mobile (iOS/Android)

```bash
# Start Metro bundler
npm run mobile:start

# Run on iOS simulator
npm run mobile:ios

# Run on Android emulator
npm run mobile:android
```

### Desktop (Windows)

```bash
# Start Electron in development mode
npm run desktop:start
```

## Building for Production

### iOS

```bash
cd mobile/ios
# Build for device
xcodebuild -workspace Mrki.xcworkspace -scheme Mrki -configuration Release
# Or archive for App Store
xcodebuild -workspace Mrki.xcworkspace -scheme Mrki archive
```

### Android

```bash
cd mobile/android
# Build APK
./gradlew assembleRelease
# Build AAB for Play Store
./gradlew bundleRelease
```

### Windows (Electron)

```bash
# Build installer
npm run desktop:build

# Build unpacked (for testing)
npm run desktop:pack
```

Output will be in `dist/` directory.

## WebSocket Configuration

The WebSocket client connects to `ws://localhost:3000` by default. Update the URL in `src/App.tsx`:

```typescript
const { connect, send, isConnected } = useWebSocket({
  url: 'ws://your-server:port',
  autoConnect: true,
  // ...
});
```

## Environment Variables

Create `.env` files for different environments:

```bash
# .env.development
REACT_APP_WS_URL=ws://localhost:3000
REACT_APP_API_URL=http://localhost:3000/api

# .env.production
REACT_APP_WS_URL=wss://api.mrki.com
REACT_APP_API_URL=https://api.mrki.com/api
```

## Troubleshooting

### iOS Build Issues

```bash
# Clean build
cd mobile/ios && rm -rf build Pods Podfile.lock && pod install

# Reset Metro cache
npm start -- --reset-cache
```

### Android Build Issues

```bash
# Clean build
cd mobile/android && ./gradlew clean

# Sync project with Gradle files in Android Studio
```

### Electron Build Issues

```bash
# Rebuild native modules
npm rebuild

# Clear Electron cache
rm -rf node_modules/electron/dist
```

## Architecture

### Shared Components

- `App.tsx` - Main UI component (works on all platforms)
- `useWebSocket.ts` - Universal WebSocket hook using socket.io-client

### Platform-Specific

- **Mobile**: Uses React Native's native components
- **Desktop**: Uses Electron with React Native Web (optional) or standard React

### Communication Flow

```
┌─────────────┐     WebSocket      ┌─────────────┐
│   Mobile    │ ◄────────────────► │   Server    │
│  (iOS/And)  │                    │  (Node.js)  │
└─────────────┘                    └─────────────┘
                                        ▲
┌─────────────┐     WebSocket           │
│   Desktop   │ ◄───────────────────────┘
│  (Electron) │
└─────────────┘
```

## License

MIT
