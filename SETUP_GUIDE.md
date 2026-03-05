# Mrki Mobile App - Setup Guide

## 🚀 Quick Overview

**Mrki** is a powerful AI workflow automation platform with a React Native mobile app for iOS & Android.

### Features Available:
- ✅ Game Development: Generate Unity, Unreal, Godot code
- ✅ Full-Stack Apps: Scaffold MERN, PERN, FastAPI+Vue projects  
- ✅ Visual Prototyping: Screenshots to React/Tailwind code
- ✅ Code Analysis: 256K token context for refactoring
- ✅ Parallel Tasks: 50+ sub-agents simultaneously
- ✅ IDE Integration: VS Code, Cursor, Zed
- ✅ Local AI: Llama, Mistral with GPU acceleration
- ✅ Cloud Deploy: AWS/GCP/Azure Kubernetes

---

## 📱 Project Structure

```
~/workspace/mrki/
├── client/
│   ├── mobile/          # React Native iOS & Android App
│   │   ├── ios/         # iOS Xcode Project (Mrki.xcodeproj)
│   │   ├── android/     # Android Gradle Project
│   │   └── src/         # Shared React Native code
│   └── desktop/         # Electron Desktop App
├── core/                # Python backend core
├── api/                 # FastAPI REST API
└── infrastructure/      # K8s, Docker, Terraform configs
```

---

## ✅ Completed Setup

### 1. Project Copied ✅
- Location: `~/workspace/mrki`

### 2. Dependencies Installed ✅
- Mobile npm packages: `~/workspace/mrki/client/mobile/node_modules`
- Fixed react-native-reanimated to v3.5.4 (compatible with RN 0.72)

### 3. iOS Configuration ✅
- Fixed Podfile paths
- Fixed boost.podspec checksum & URL
- Removed missing MrkiTests target
- **Status:** Ready for Xcode build (requires full Xcode)

### 4. Android Configuration ✅
- Fixed all gradle paths (build.gradle, settings.gradle, app/build.gradle)
- Created gradle wrapper
- Built react-native-gradle-plugin.jar
- **Status:** Ready for Android build

---

## 🛠️ Remaining Steps

### iOS Build Requirements

**⚠️ Xcode Full Installation Required**

Current issue: Only Xcode Command Line Tools are installed. iOS build requires full Xcode.

```bash
# Install Xcode from App Store OR use xip file:
# Download from: https://developer.apple.com/download/all/
# Or install via App Store

# After installation, run:
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -license accept

# Then build iOS:
cd ~/workspace/mrki/client/mobile/ios
pod install
npx react-native run-ios
```

### Android Build Steps

```bash
cd ~/workspace/mrki/client/mobile

# Start Metro bundler
npx react-native start

# In another terminal, build Android:
npx react-native run-android

# Or build APK:
cd android
./gradlew assembleDebug
```

### Backend Setup (Optional - for full functionality)

```bash
cd ~/workspace/mrki

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (using requirements.txt)
pip install -r requirements.txt

# Or install from setup.py (note: pyproject.toml has version issues)
pip install fastapi uvicorn sqlalchemy alembic pydantic

# Start backend
python main.py server start
```

---

## 🔧 Configuration

### Mobile API Connection

Edit `~/workspace/mrki/client/mobile/src/App.tsx`:

```typescript
// Update these to your backend URL
const API_URL = 'http://YOUR_BACKEND_IP:3000';
const WS_URL = 'ws://YOUR_BACKEND_IP:3001';
```

### Environment Variables

Copy and configure:
```bash
cp ~/workspace/mrki/.env.example ~/workspace/mrki/.env
# Edit with your API keys and configuration
```

---

## 🚀 Quick Start Commands

```bash
# 1. Navigate to mobile app
cd ~/workspace/mrki/client/mobile

# 2. Start Metro bundler (keeps running)
npx react-native start

# 3. Build & run iOS (requires Xcode)
npx react-native run-ios

# 3. Build & run Android
npx react-native run-android

# 4. Build release APK
cd android && ./gradlew assembleRelease
```

---

## 📋 Troubleshooting

### iOS Issues

**"SDK iphoneos cannot be located"**
- Install full Xcode from App Store
- Run: `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer`

**Pod install fails**
```bash
cd ios
rm -rf Pods Podfile.lock
pod cache clean --all
pod install
```

### Android Issues

**Gradle sync fails**
```bash
cd android
rm -rf .gradle build
./gradlew clean
./gradlew assembleDebug
```

**Metro bundler issues**
```bash
# Clear all caches
npx react-native start --reset-cache
cd android && ./gradlew clean
```

---

## 🎯 What's Working Now

✅ Project structure setup  
✅ Mobile dependencies installed  
✅ iOS Podfile configured  
✅ Android Gradle configured  
✅ React Native code ready  

## 🚧 What's Needed

⏳ Full Xcode installation for iOS builds  
⏳ Android emulator/device for testing  
⏳ Backend server running (optional)  

---

## 📚 Next Steps

1. **Install Xcode** (for iOS) or setup Android Emulator
2. **Start Metro bundler**: `npx react-native start`
3. **Run the app**: `npx react-native run-ios` or `npx react-native run-android`
4. **Connect backend** (optional): Start Python server and update API_URL

---

## 🔗 Key Files

| File | Description |
|------|-------------|
| `client/mobile/src/App.tsx` | Main app entry point |
| `client/mobile/ios/Podfile` | iOS dependencies |
| `client/mobile/android/app/build.gradle` | Android build config |
| `core/` | Python backend logic |
| `main.py` | CLI entry point |

---

**Project Location**: `~/workspace/mrki`  
**Status**: Ready for build (pending Xcode/Android SDK)
