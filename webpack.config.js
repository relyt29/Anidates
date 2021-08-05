const autoprefixer = require('autoprefixer');

module.exports = {
  mode: 'development',
  entry: ['./app.scss', './app.js'],
  output: {
    filename: 'bundle.js',
  },
  module: {
    rules: [
      {
        test: /\.scss$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: 'bundle.css',
            },
          },
          //{loader: 'extract-loader'},
          //{loader: 'style-loader'},
          //{loader: 'css-loader'},
          //{
          //  loader: 'postcss-loader',
          //  options: {
          //    postcssOptions: {
          //      plugins: [
          //        autoprefixer()
          //      ]
          //    }
          //  }
          //},
          {
            loader: 'sass-loader',
            options: {
              // Prefer Dart Sass
              implementation: require('sass'),

              // See https://github.com/webpack-contrib/sass-loader/issues/804
              webpackImporter: false,
              sassOptions: {
                includePaths: ['./node_modules'],
              },
            },
          }
        ],
      },
/*      {
        test: /\.m?js$/,
        exclude: /(node_modules|bower_components)/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
            targets: ['> 0.25%, not dead']
          }
        }
      },
      */
    ],
  },
};

