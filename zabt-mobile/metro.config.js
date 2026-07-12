const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");
const path = require("path");

const projectRoot = __dirname;
const sharedRoot = path.resolve(projectRoot, "../packages/shared");

const config = getDefaultConfig(projectRoot);

// @zabt/shared lives outside projectRoot (file: dep symlinked into node_modules).
// Metro needs to watch the real path and follow the symlink.
config.watchFolders = [sharedRoot];
config.resolver.unstable_enableSymlinks = true;
config.resolver.nodeModulesPaths = [path.resolve(projectRoot, "node_modules")];

module.exports = withNativeWind(config, { input: "./global.css" });
