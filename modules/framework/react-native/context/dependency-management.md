# React Native (Expo): Dependency Management

## Overview

Expo projects use a JavaScript/Node.js package manager — **npm**, **pnpm**, or **Yarn** — combined with the **Expo SDK** to manage native dependencies. The key distinction from plain React web: many packages have native code (iOS/Android modules) that must be linked into the app binary, and Expo manages this through its plugin system.

**Recommendation: use npm or pnpm.** Expo's own tooling (`npx expo install`) wraps whichever manager you use. pnpm is faster and more disk-efficient; npm is universally compatible and has zero setup friction.

## Two Layers of Dependencies

React Native (Expo) has two dependency concerns that don't exist in web:

1. **JS dependencies** — installed via your package manager into `node_modules`, same as web.
2. **Native dependencies** — packages with Expo Config Plugins that modify the native iOS/Android project. These are installed the same way but require an **EAS Build** (or `expo prebuild`) to take effect. You cannot just `npm install` a native module and expect it to work in Expo Go.

## `npx expo install` — Always Use This for Expo Packages

When adding Expo SDK packages, **always use `npx expo install`** instead of `npm install` / `pnpm add` directly. It automatically resolves the correct version that is compatible with your current Expo SDK version.

```bash
# Good — installs the SDK-compatible version
npx expo install expo-camera expo-location

# Risky — may install a version incompatible with your SDK
npm install expo-camera
pnpm add expo-camera
```

For non-Expo packages (e.g., `date-fns`, `zod`, `@reduxjs/toolkit`), use your package manager directly — `npx expo install` works for these too, but there's no SDK constraint to worry about.

## Common Commands

```bash
# Installing
npx expo install expo-image expo-router   # Expo/React Native packages (SDK-aware)
npm install zod @reduxjs/toolkit react-redux   # Pure JS packages
pnpm add zod @reduxjs/toolkit react-redux      # Same, with pnpm

# Dev dependencies
npm install -D @testing-library/react-native jest-expo
pnpm add -D @testing-library/react-native jest-expo

# Removing
npm uninstall expo-camera
pnpm remove expo-camera

# Checking for incompatible versions
npx expo-doctor                           # Detects SDK version mismatches
npx expo install --check                  # Lists packages with incompatible versions
npx expo install --fix                    # Auto-corrects version mismatches

# Upgrading the Expo SDK
npx expo upgrade                          # Bumps SDK version and adjusts all expo deps
```

## package.json Structure

```json
{
  "name": "my-expo-app",
  "version": "1.0.0",
  "main": "expo-router/entry",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "build:preview": "eas build --profile preview",
    "test": "jest"
  },
  "dependencies": {
    "expo": "~51.0.0",
    "expo-router": "~3.5.0",
    "expo-status-bar": "~1.12.1",
    "react": "18.2.0",
    "react-native": "0.74.1",
    "@sentry/react-native": "~5.22.0",
    "@reduxjs/toolkit": "^2.2.7",
    "react-redux": "^9.1.2",
    "redux-persist": "^6.0.0",
    "@react-native-async-storage/async-storage": "1.23.1"
  },
  "devDependencies": {
    "@babel/core": "^7.24.0",
    "@testing-library/react-native": "^12.5.1",
    "jest": "^29.7.0",
    "jest-expo": "~51.0.0",
    "typescript": "^5.3.3"
  }
}
```

Note that `react` and `react-native` are **exact pins** (no `^`) — Expo specifies exact versions that are tested against the SDK. Do not change these manually; let `npx expo upgrade` manage them.

## Lockfiles

Always commit the lockfile (`package-lock.json` or `pnpm-lock.yaml`). EAS Build uses the lockfile to reproduce your exact dependency tree in the cloud builder. Without a committed lockfile, two builds of the same commit may produce different binaries.

## Native Modules and EAS Build

Packages with native code (camera, sensors, notifications, etc.) require a native build to take effect. The workflow is:

1. Install the package: `npx expo install expo-camera`
2. Add required permissions/config to `app.json` (the package's README specifies what's needed)
3. Build with EAS: `eas build --profile development` — this triggers a new native build with the module linked in

Changes to native modules **do not** take effect in Expo Go or a previous development build — you need a new build.

```bash
# Create a development build (one-time per native dependency change)
eas build --profile development --platform ios
eas build --profile development --platform android
```

## Keeping Dependencies Updated

```bash
npx expo-doctor          # Shows SDK mismatches and known issues
npx expo install --fix   # Corrects Expo package versions to match current SDK
npx expo upgrade         # Upgrades to latest Expo SDK (follow migration guide after)
```

For automated updates, use **Renovate** with the `expo` preset — it understands Expo SDK constraints and opens PRs for safe updates. Manual big-bang upgrades of Expo SDK versions are painful; keeping up with each minor release is far easier.

```bash
# Security audit
npm audit
pnpm audit
```

## pnpm-Specific: Expo Compatibility

Expo works with pnpm but requires one workaround for Metro bundler, which doesn't follow pnpm's symlinked `node_modules` by default. Add to your project:

```js
// metro.config.js
const { getDefaultConfig } = require('expo/metro-config');
const config = getDefaultConfig(__dirname);

// Required for pnpm: resolve symlinks
config.resolver.unstable_enableSymlinks = true;

module.exports = config;
```

And in `.npmrc`:
```ini
# .npmrc — required for pnpm + Expo
node-linker=hoisted
```

This tells pnpm to use a flat `node_modules` layout (like npm), which Metro can resolve without issues.
