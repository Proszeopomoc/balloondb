# Frozen: V03H4A BQL compat release fix

V03H4A is intentionally frozen.

Reason: the active module contained a top-level bug:

```python
HELPER = r
```

This produced:

```text
NameError: name 'r' is not defined
```

Replacement: `V03H4B_TARGET_STATE_BQL_COMPAT`.
