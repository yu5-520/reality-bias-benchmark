# Stage II bounded closure F — resumable interruption rule

The first F workflow (`37421493309`) reached exactly one real subject-provider
response (QA, native turn 25) and then failed in the experiment harness before
any action from that response could take native effect.

This is **not** treated as a zero-call preflight and F is not rerun.

The response is frozen by request hash
`6b44bb7a4801397b4e4c3bb3ab2f52abf0367fada4c01fa2ee2a800233175c66`
and response hash
`d1ff83d8ea53189b6d9fda37fd2a340e96a75fb174670958189df1f245f5e862`.

The continuation restores the original history-24 parent, reapplies the already
frozen D/E treatment, verifies that the reconstructed turn-25 prompt is bytewise
equivalent at the message level to the frozen request, injects the exact frozen
turn-25 response without a provider recall, executes its actions once, and only
then resumes new provider calls.

Thus the scientific trajectory contains one original first response plus only
the remaining calls. No resampling of turn 25 is permitted.
