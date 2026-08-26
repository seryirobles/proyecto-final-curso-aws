# rules_model — traceability (docs/verification.md Level 3)

- R1 (FR-RULE-01, FR-RULE-02, FR-RULE-04) -> `test_rule_set_declares_exactly_the_three_fields`, `test_rule_set_is_frozen`
- R2 (FR-RULE-01) -> `test_no_rules_function_takes_a_week_identity_parameter`
- R3 (FR-RULE-04) -> `test_category_count_rule_fields_are_exactly_the_fixed_shape`, `test_category_count_rule_is_frozen`
- R4 (FR-RULE-04) -> `test_pin_rule_fields_are_exactly_the_fixed_shape`, `test_pin_rule_is_frozen`
- R5 (FR-RULE-04) -> `test_rule_set_rejects_an_out_of_range_disabled_day`, `test_rule_set_rejects_an_out_of_range_pin_day`
- R6 (FR-RULE-07) -> `test_rule_set_rejects_category_totals_exceeding_available_slots`, `test_disabling_a_day_can_make_a_previously_valid_total_invalid`
- R7 (FR-RULE-07) -> `test_rule_set_rejects_a_pin_on_a_disabled_day`
- R8 (FR-RULE-04) -> `test_set_category_count_replaces_the_existing_rule_for_that_category`, `test_set_category_count_adds_a_new_rule_when_none_existed`
- R9 (FR-RULE-04) -> `test_remove_category_count_removes_the_matching_rule`, `test_remove_category_count_is_a_no_op_when_absent`
- R10 (FR-RULE-04) -> `test_set_pin_replaces_the_existing_pin_for_that_slot`
- R11 (FR-RULE-04) -> `test_remove_pin_removes_the_matching_pin`, `test_remove_pin_is_a_no_op_when_absent`
- R12 (FR-RULE-04) -> `test_disable_day_adds_the_day`, `test_disable_day_is_idempotent`
- R13 (FR-RULE-04) -> `test_enable_day_removes_the_day`, `test_enable_day_is_a_no_op_when_absent`
- R14 (FR-RULE-07, FR-RULE-03) -> `test_max_selectable_count_subtracts_other_categories_and_disabled_days`, `test_max_selectable_count_floors_at_zero`
- R15 (FR-RULE-07, FR-RULE-03) -> `test_available_days_for_pin_excludes_disabled_days`
- R16 (FR-RULE-07, FR-RULE-03) -> `test_available_days_to_disable_excludes_disabled_and_pinned_days`
- R17 (FR-RULE-07) -> `test_remove_pins_referencing_removes_every_matching_pin`, `test_remove_pins_referencing_is_a_no_op_when_nothing_matches`
- R18 (FR-RULE-07) -> `test_remove_pins_referencing_reports_exactly_what_it_removed`
- R19 (FR-RULE-05) -> `test_apply_override_uses_the_override_value_when_given`, `test_apply_override_uses_the_pins_override_when_given`, `test_apply_override_uses_the_disabled_days_override_when_given`, `test_apply_override_inherits_the_shared_value_when_none_given`
- R20 (FR-RULE-05) -> `test_apply_override_never_mutates_shared`
- R21 (FR-RULE-06) -> `test_no_rule_type_declares_an_author_field`
- R22 (FR-RULE-06) -> `test_no_mutating_function_takes_an_actor_parameter`

Every `FR-RULE-01`..`FR-RULE-07` in `covers` is reached through the map above.
