# v4 Source Adapter Contract

Date: 2026-09-16

A source adapter may derive behavior records only from fields actually present in the named source version.

Every adapter must:

- name source version(s);
- preserve source refs;
- map proposal/realization separately where source permits;
- preserve missingness;
- avoid semantic C/P/R classification;
- be deterministic for the same frozen source evidence;
- be independently testable without provider calls.