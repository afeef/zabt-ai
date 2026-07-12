module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ["babel-preset-expo", { jsxImportSource: "nativewind" }],
      "nativewind/babel",
    ],
    // NOTE: babel-preset-expo v55+ auto-applies react-native-worklets/plugin
    // when react-native-worklets is in deps. Don't add it manually — double
    // application breaks runtime init with "Cannot read property 'default' of undefined"
    // at setUpDefaltReactNativeEnvironment.
  };
};
