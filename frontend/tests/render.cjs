const fs = require('node:fs');
const ts = require('typescript');
for (const extension of ['.ts', '.tsx']) require.extensions[extension] = (module, filename) => {
  const source = fs.readFileSync(filename, 'utf8');
  module._compile(ts.transpileModule(source, {compilerOptions: {
    module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop:true,
  }}).outputText, filename);
};
require.extensions['.css'] = () => {};
module.exports = {React:require('react'),render:require('react-dom/server').renderToStaticMarkup};
