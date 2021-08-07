const autoprefixer = require("autoprefixer");
const path = require("path");

module.exports = {
  mode: "production",
  entry: ["./app.scss", "./app.js"],
  output: {
    filename: "bundle.js",
    path: path.resolve(__dirname, "dist"),
  },
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
      //{
      //  test: /\.tsx?$/,
      //  use: "ts-loader",
      //  exclude: /node_modules/,
      //},
    ],
  },
  //resolve: {
  //  extensions: [".tsx", ".ts", ".js"],
  //},
};
