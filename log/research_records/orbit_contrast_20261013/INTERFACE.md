# Domain-general scientific query and evidence interface

The interface is implemented in [evidence.py](evidence.py), and every route in this study reads
evidence only through it. It is a study-local prototype. It is not promoted to `src/`, because no
method built on it has shown independent value yet.

## Records

An **Entity** is `(kind, namespace, id)`, for example `("gene", "symbol", "EGFR")`,
`("compound", "lincs_key", "BRD-K12345678")` or `("cell_line", "lincs", "A375")`.

* Identity is only the triple. Names, synonyms and salts are resolved before a record is made.
* Two records refer to the same thing only if their triples are equal.

An **EvidenceRecord** has these fields:

| Field | Meaning | Rule |
|---|---|---|
| `subject`, `predicate`, `obj` | A typed relation, e.g. compound `inhibits` gene, or gene `knockdown_response` (vector) | `predicate` comes from a closed vocabulary with declared subject and object kinds |
| `sign` | +1 increases, −1 decreases, 0 unsigned (binding, association) | An unsigned record cannot feed a signed route without an explicit sign rule |
| `observation` | `curated_annotation`, `assay_measurement`, `interventional_response`, `observational_association`, `computed_similarity` or `transported` | Observational and interventional records are never pooled in one estimate (`MERGE_REFUSED`) |
| `intervention` | For interventional records: `genetic_knockdown`, `genetic_knockout`, `genetic_overexpression`, `chemical_perturbation`; for curated relations: `inhibition`, `activation`, `binding`, `engagement`, `efficacy` | The intervention types never alias each other (see below) |
| `context` | Cell line, or `None` for context-free claims | A context-specific record used in another context must be transported explicitly |
| `source`, `available_from` | Provenance id and the date the evidence became public | A query's `as_of` date excludes later records (snapshot rule) |
| `reliability` | Tier: `curated`, `assay`, `text_mined`, `inferred` | A tier is only used as a stratum or weight declared before results |
| `depends_on` | Upstream sources this record derives from (e.g. MAP-KG edges from ChEMBL) | Records that share an upstream source are not counted as independent support |
| `value_ref` | A pointer to a measured vector (e.g. `kd_cgs:A375:EGFR`) | The record carries no outcome value, so evidence objects cannot leak outcomes |

How the intervention types relate:

* Knockdown, inhibition, engagement and efficacy are distinct.
* A knockdown response may stand in for a chemical inhibition only through a declared
  **transport**. Here that is `knockdown_as_inhibition_proxy`: its sign comes from the curated
  relation, and its provenance chain records both inputs.
* The transported record has observation `transported`. It never counts as a measurement of the
  compound.

## Queries

A **Query** is `(entity, context, outcome_type, as_of, excluded_sources)`.

* `outcome_type` names the estimand, e.g. `l1000_landmark_10uM_24h` or
  `l1000_landmark_shRNA_cgs`.
* `excluded_sources` lists sources that would leak the outcome, e.g. the compound's own signature
  in the queried line.

`select(records, query, predicate, observation, intervention)` returns either the matching
records or an `Absent(reason)` sentinel:

* **Missing is not negative.** An absent target or knockdown yields `Absent`, never a zero vector
  or a negative label.
* Routes return `None` for unavailable predictions.
* Stacking treats `None` as "route not available": no contribution, and the route's
  availability-indicator feature is set to 0.

## Orbit declarations

Each route that consumes identity-bearing evidence declares an **OrbitSpec**:

* `acts_on`: the entity kind whose labels are permuted (gene or compound);
* `strata`: the nuisance features held fixed, such as degree, coverage, signature strength or
  landmark status;
* `destroys`: the semantics the relabelling removes, such as "which gene the compound targets" or
  "which compounds share this compound's mechanism".

The orbit is the claim's null. A route without an OrbitSpec cannot have identity credit attributed
to it.

## Refusals

| Code | When |
|---|---|
| `MERGE_REFUSED` | Observational and interventional records are pooled, or two intervention types are pooled without a declared transport |
| `TRANSPORT_UNDECLARED` | An interventional record is used as another intervention type |
| `AVAILABLE_AFTER_QUERY` | A record is newer than the query's `as_of` (with `strict=True`; otherwise it is filtered out) |
| `EXCLUDED_SOURCE` | A record comes from a leaking source |
| `ORBIT_UNDECLARED` | Identity attribution is requested for a route with no OrbitSpec |
| `UNSIGNED_IN_SIGNED_ROUTE` | An unsigned record is used without a declared sign rule |
