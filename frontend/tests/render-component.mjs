import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import ts from 'typescript';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
const require = createRequire(import.meta.url);
for (const extension of ['.ts','.tsx']) {
  require.extensions[extension] = (module, filename) => {
    module._compile(ts.transpileModule(readFileSync(filename,'utf8'), {compilerOptions:{
      module:ts.ModuleKind.CommonJS, jsx:ts.JsxEmit.ReactJSX, esModuleInterop:true,
      target:ts.ScriptTarget.ES2022}}).outputText, filename);
  };
}
export function render(file, name, props) {
  return renderToStaticMarkup(React.createElement(require(file)[name],props));
}
