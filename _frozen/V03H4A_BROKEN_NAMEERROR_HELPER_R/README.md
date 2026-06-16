# V03H4A frozen

Reason:
- active file contained broken Python statement:
  HELPER = r
- this caused:
  NameError: name 'r' is not defined

Decision:
- V03H4A is frozen as broken evidence.
- Active compatibility target is V03H4B.
- Do not restore V03H4A into active selftest path.
