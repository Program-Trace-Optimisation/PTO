# PTO Playground (JavaScript)

An experimental JavaScript implementation of PTO that runs in the browser: write a generator
and a fitness function, pick a solver, and watch the search. It is deployed to GitHub Pages
from `ui/` by [.github/workflows/deploy-pages.yml](../.github/workflows/deploy-pages.yml).

- `src/` - the library: tracer, `rnd`, distributions, operators, the naming compiler
  (`compiler.js`, which rewrites the generator's source to give each `rnd` call a structured
  name) and the solvers.
- `ui/` - the page (`index.html`, `app.js`, `style.css`) and `pto-bundle.js`, the library
  bundled by esbuild.
- `tests/` - unit tests, run with Node's built-in test runner.

To try it, open `ui/index.html` in a browser (no build needed).

To work on it (Node.js 22 or later):

```
cd pto-webapp
npm ci            # install dependencies from package-lock.json
npm test          # run the tests
npm run build     # rebuild ui/pto-bundle.js from src/
```

After changing `src/`, run `npm run build` and commit `ui/pto-bundle.js` too: the workflow
checks that the committed bundle matches `src/`.
