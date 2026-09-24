# E0-DIR change plan and gates

1. **G0 audit**: freeze branch, record assets and run existing focused tests.
2. **G1 contract**: add finite vector, identity, residual and observation checks.
3. **G2 controller**: add three legal branches, shared selector and query budget.
4. **G3 synthetic**: add tests for cancellation, wrong dimensions, hidden
   observation binding, keep/no-query and equal-information views.
5. **G4 model preflight**: real State actual-path call is allowed; latent path is
   blocked until a chemCPA checkpoint and adapter are registered.
6. **G5 API smoke**: default off; an explicitly enabled call is separately
   accounted and cannot alter hidden scoring.
7. **G6 formal evaluation**: not run until model service, frozen menus, private
   observations and a declared spend ceiling are available.

No automatic push is part of this branch.

