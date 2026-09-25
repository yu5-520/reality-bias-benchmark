# CN-R-105 — Common DeepSeek readiness receipt and X1–X5 subject promotion

Date: 2026-09-25

Stage-II recorded exactly one common non-scientific DeepSeek readiness call in workflow `36145131256` against execution commit `57263f4b2913eab041c1737fdce62e1bd2ab5242`.

The request used no T1–T3 task, no checkout, no multi-Agent run and no evaluator. The provider returned `deepseek-flash`, finish reason `stop`, with 31 prompt tokens and 2 completion tokens. Estimated peak-price cost was USD `0.0000117`.

Receipt SHA-256 is `93f06cb677b7da3997bcbf38a09cdd10fed650f2e05139e4ac82645a23228464`; raw provider-response SHA-256 is `e43dbdbb54c5d5fba137ac5561be47e807047b8afbfd2b396b31f000c58f64c9`. The immutable workflow artifact id is `10869108698`, digest `sha256:c59c3673d89d4376808cfd3143d99a51376023815de4b5e65e134cc90a15e7d2`.

The receipt froze these execution-surface hashes:

- X1: `2589dff9c6ff571ee8c0e19d67707935796cbb0faa3845024bf159e3a5c8756a`
- X2: `3efecfe13e2cf3117a2e4734e91f255da5464d62d529ffa1c25bdc1bee63f5ce`
- X3: `4449e1c9093f01a75939409dbc55922d4a28f4cbccd7c9c3632677dc81a2fe85`
- X4: `9f1c076a4aa4399d362fd2d32ae773b024f6e48174d79c9fd68ca09d85f605ff`
- X5: `ec203a2b15d2632ca720636a50e07f31e0dbe30eae419c69c981e4852729c253`

X1–X5 are promoted to `SUBJECT_READY` only because their current executable surface remains byte/content-address equivalent to the surface bound by the receipt. X6 and X7 are not promoted: their real study embedding/checkpoint manifests remain unfrozen.

The readiness module now rejects a second paid common handshake. No natural Stage-II cell was reserved or executed; trajectory count remains zero.
