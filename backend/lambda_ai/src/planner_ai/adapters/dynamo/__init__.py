"""DynamoDB-backed implementations of the api-side persistence ports, against
the single `data` table (docs/data_model.md section 1). The Spanish persisted
attribute names never cross back into planner_core — this package is the
Spanish/English boundary (docs/data_model.md section 1)."""
