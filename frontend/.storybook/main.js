module.exports = {
  stories: ["../src/**/*.stories.@(js|jsx|ts|tsx)"],
  addons: [
    "@storybook/addon-links",
    "@storybook/addon-essentials",
    "@storybook/preset-create-react-app",
  ],
  framework: {
    name: "@storybook/react-webpack5",
    options: {},
  },
  docs: {
    autodocs: true,
  },
  webpackFinal: async (config) => {
    config.module.rules.push({
      test: /\.(js|jsx)$/,
      loader: require.resolve("babel-loader"),
      options: {
        presets: [require.resolve("@babel/preset-react")],
      },
    });
    return config;
  },
};
