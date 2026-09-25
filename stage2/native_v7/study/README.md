# Candidate real study checkpoints

These manifests came from the non-subject asset fingerprint run [36163086812](https://github.com/yu5-520/reality-bias-benchmark/actions/runs/36163086812) at commit `319e6ae1946829d8bbad917996d24d3a96a7c8fb`.

| Probe | Pretrained source | Exact revision | Manifest SHA-256 | Source artifact ZIP SHA-256 |
| --- | --- | --- | --- | --- |
| X6 | sentence-transformers/all-MiniLM-L6-v2 | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` | `6f7540370b538036406bb621563e0ab98e8745122afe51369ab394c7f6f64f34` | `78ff211c6e56d41ba8b354f068332c797eaeb7e64f67a001c27a81c73cbcf45a` |
| X7 | distilbert/distilgpt2 | `2290a62682d06624634c1f46a6ad5be0f47f38aa` | `bc5cd236ca84a2b213f3a618ef37f7ab10f6716e1b1b134242c2350bd4883e66` | `19e5da9aca11860948633f09e29d12bfefec891db6a6f524cc2485e31d870e6c` |

The manifests bind 12 X6 files and 9 X7 files, including actual pretrained weights. The compatibility workflow downloads the exact revisions again and compares every file before loading the models under each probe's pinned dependency environment. X6 and X7 remain pending until a separate reviewed registry promotion; these candidate files alone do not authorize a natural cell.
