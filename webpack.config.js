const autoprefixer = require("autoprefixer");
const path = require("path");
const NodePolyfillPlugin = require("node-polyfill-webpack-plugin")

module.exports = {
  //mode: "production",
  mode: "development",
  entry: { "cssBundle":"./app.scss", "bundle":"./app.js", "indexBundle":"./index.ts"},
  output: {
    path: path.resolve(__dirname, "static"),
  },
  plugins: [new NodePolyfillPlugin()],
  module: {
    rules: [
      {
        test: /\.scss$/,
        use: [
          {
            loader: "file-loader",
            options: {
              name: "bundle.css",
            },
          },
          {
            loader: "sass-loader",
            options: {
              // Prefer Dart Sass
              implementation: require("sass"),

              // See https://github.com/webpack-contrib/sass-loader/issues/804
              webpackImporter: false,
              sassOptions: {
                includePaths: ["./node_modules"],
              },
            },
          },
        ],
      },
      {
        test: /\.tsx?$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
    ],
  },
  //resolve: {
  //  extensions: [".tsx", ".ts", ".js"],
  //},
};
