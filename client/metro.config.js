/**
 * Metro configuration for React Native
 */
const path = require('path');

module.exports = {
  resolver: {
    sourceExts: ['js', 'jsx', 'json', 'ts', 'tsx', 'cjs', 'mjs'],
    assetExts: ['glb', 'gltf', 'png', 'jpg', 'ttf', 'obj', 'mtl'],
    nodeModulesPaths: [
      path.resolve(__dirname, 'mobile/node_modules'),
      path.resolve(__dirname, 'node_modules'),
    ],
  },
  watchFolders: [
    __dirname,
    __dirname + '/src',
    __dirname + '/shared',
  ],
};
