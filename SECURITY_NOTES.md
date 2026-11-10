# Security baseline – anonymous access

- 2026-11-09 – Anonymous GET /recipes → 200, returns full list of recipes with no identity or permissions required.
- 2026-11-09 – Anonymous PATCH /recipes/1 → 200, recipe title changed to "Shakshuka (hacked)" with no identity or permissions required.
- 2026-11-09 – Anonymous DELETE /recipes/1 → 204, recipe is removed; follow-up GET /recipes/1 → 404, no identity or permissions required.