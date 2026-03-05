/**
 * Electron Forge Configuration
 * Build configuration for Windows desktop app
 */

module.exports = {
  packagerConfig: {
    name: 'Mrki',
    executableName: 'mrki',
    asar: true,
    icon: './assets/icon',
    appBundleId: 'com.mrki.app',
    appCategoryType: 'public.app-category.productivity',
    win32metadata: {
      CompanyName: 'Mrki Team',
      FileDescription: 'Mrki - AI Agent Platform',
      OriginalFilename: 'mrki.exe',
      ProductName: 'Mrki',
      InternalName: 'mrki',
    },
  },
  rebuildConfig: {},
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'Mrki',
        exe: 'mrki.exe',
        setupExe: 'Mrki-Setup.exe',
        setupIcon: './assets/icon.ico',
        iconUrl: 'https://mrki.app/assets/icon.ico',
        loadingGif: './assets/installing.gif',
        noMsi: false,
        msi: 'Mrki.msi',
        msiUpgradeCode: '12345678-1234-1234-1234-123456789012',
      },
    },
    {
      name: '@electron-forge/maker-zip',
      platforms: ['darwin', 'win32', 'linux'],
    },
    {
      name: '@electron-forge/maker-deb',
      config: {
        options: {
          maintainer: 'Mrki Team',
          homepage: 'https://mrki.app',
          icon: './assets/icon.png',
        },
      },
    },
    {
      name: '@electron-forge/maker-rpm',
      config: {
        options: {
          homepage: 'https://mrki.app',
          icon: './assets/icon.png',
        },
      },
    },
  ],
  plugins: [
    {
      name: '@electron-forge/plugin-webpack',
      config: {
        mainConfig: './webpack.main.config.js',
        renderer: {
          config: './webpack.renderer.config.js',
          entryPoints: [
            {
              html: './src/index.html',
              js: './src/renderer.tsx',
              name: 'main_window',
              preload: {
                js: './src/preload.ts',
              },
            },
          ],
        },
      },
    },
    {
      name: '@electron-forge/plugin-auto-unpack-natives',
      config: {},
    },
  ],
  publishers: [
    {
      name: '@electron-forge/publisher-github',
      config: {
        repository: {
          owner: 'mrki',
          name: 'mrki-desktop',
        },
        prerelease: false,
        draft: true,
      },
    },
  ],
};
