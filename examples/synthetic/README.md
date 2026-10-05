# Synthetic fixture

These three short sentences are an original test fixture, provided under CC0-1.0.
They do not reproduce a book or a vendor output. A has a deliberately reversed
meaning. The deterministic test provider knows only this fixture. Its output
checks plumbing, evidence links and presentation, not real model accuracy.

Run `python tools/prepare_demo.py --data-dir .judge-data/jury-preview` from the
repository root with the project virtual environment. It runs the real comparison
protocol with the test-only provider, makes no network calls and writes a labelled
catalog example. Test dependencies must be installed. It refuses to replace an
existing catalog entry. Other uploads never receive fabricated fixture scores.
