# Tests for AnkiScape

- All tests live under `tests/`.
- They use Python's built-in `unittest` framework (no pytest dependency).

## How to run

Use the helper at repo root:

```
python3 run_tests.py
```

It discovers and runs all `tests/test_*.py` files. The script adds the repo root to `PYTHONPATH` so tests can import modules like `logic_pure` directly.
