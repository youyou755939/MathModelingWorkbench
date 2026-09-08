# Transferable modeling validation patterns

Read this reference when the new problem contains geometric contact, recursive rework/reuse, sequential sampling, or multi-period resource planning. It contains reusable guards only; historical benchmark answers belong outside the deployed plugin.

## Evidence and comparison

- Grade A: official statement/data or a directly derived invariant with a reproducible residual.
- Grade B: independently reproduced or cross-implementation agreement that also passes the same hard constraints.
- Grade C: a single paper, repository, blog, or unverified award claim. Use it to generate hypotheses, not as an answer key.
- Compare values only when metric definition, units, data version, accounting horizon, and hard constraints match. Otherwise mark them not commensurable.
- Recompute the headline metric from the exported decision/prediction file. A solver log is not evidence if the export cannot reproduce it.

## Geometry, kinematics, and contact

- Distinguish path distance, Euclidean chord length, radial distance, and pitch. Use the quantity stated by the physical constraint.
- Derive linked-body velocities from the differentiated rigid constraint or an equivalent Jacobian. Audit every link-length residual and compare against decreasing-step central differences.
- Represent finite-width bodies as oriented shapes. Use SAT, signed distance, or another containment-aware test; edge intersection alone misses containment and tangency.
- Treat first contact as a continuous event: coarse bracket, root-find a signed margin, then verify immediately before and after the event.
- When optimizing a design parameter subject to no collision, minimize the safety margin over the entire path, not only at the terminal boundary. Report spatial/time discretization convergence and the active contact pair.
- For piecewise paths, check position and tangent continuity at every junction before propagating speed. Locate the all-body, all-path maximum instead of sampling only requested output times.

## Sampling and sequential decisions

- “Fewest samples” is not operationally identifiable from confidence alone. State the null boundary, a practically relevant alternative or indifference region, producer risk, consumer risk, and any maximum sample size.
- Use exact discrete tails at decision boundaries when feasible. Report operating-characteristic power and expected/maximum sample number; a small type-I error alone can hide nearly zero power.
- If using a confidence-bound stopping rule, state whether coverage is fixed-sample, repeated-look, or anytime-valid. Do not reuse a fixed-sample interval after optional stopping without justification.
- For uncertain rates feeding a later optimizer, integrate over a joint posterior/confidence set or propagate scenarios. Report policy-selection frequency and regret, not only a plug-in optimum.

## Recursive production, rework, and inventory

- Define the accounting unit first: one attempted product, one sold product, one fulfilled customer order, or a fixed batch. Include replacement production if the stated exchange loss excludes it.
- Disassembled or returned components retain their latent/observed state unless the problem explicitly resets it. Do not silently treat recovered parts as new independent draws.
- Express rework as a Markov reward process, dynamic program, or balance equations. Check absorption probability or transition spectral radius before computing expected profit.
- A fixed number of rework cycles is an approximation. Report a truncation-error bound; otherwise policies with infinite recycling can look artificially profitable.
- Count purchase, inspection, assembly, disassembly, exchange, disposal, and replacement exactly once. Verify a small instance by exhaustive enumeration before trusting a heuristic on a larger assembly tree.

## Multi-period allocation and crop/rotation planning

- Generate variables from the feasible `(period, location, subperiod, item)` index set derived from the data, rather than creating all combinations and hoping penalties remove invalid ones.
- Encode capacities, compatibility, subperiod linkage, adjacency/no-repeat logic, and rolling-window requirements as separate constraints with named residuals.
- An aggregate area/frequency constraint may be a relaxation of parcel-level coverage. State the relaxation and, when it matters, track parcel identity or prove equivalence.
- Model demand/sales caps with explicit sold and surplus variables. Apply each price regime only to its corresponding quantity.
- Recompute the objective from the exported plan and the original data. Validate feasibility before comparing objective values or percentage improvements.
- Under uncertainty, justify marginal ranges and correlations, ensure covariance matrices are positive semidefinite, and use fixed seeds. Report expected value together with lower quantiles/CVaR, feasibility rate, and out-of-sample regret.

## Required evidence record

For each headline result store: run command and exit code, data hashes or versions, metric name/unit/horizon, hard-constraint residuals and tolerances, convergence or uncertainty diagnostics, and any external comparison with its evidence grade and commensurability decision.
