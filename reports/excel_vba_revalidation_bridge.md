# Excel/VBA Revalidation Bridge

## Purpose

This layer connects the Python IR derivatives validation engine to an Excel/VBA review workflow.

Python remains the controlled pricing and validation engine. Excel/VBA provides a reviewer-facing revalidation bridge for teams that still use spreadsheet-based controls.

## Generated outputs

| Artifact | Path |
|---|---|
| Control panel CSV | `excel_vba\exports\ir_swap_revalidation_control_panel.csv` |
| Shock table CSV | `excel_vba\exports\ir_swap_revalidation_shock_table.csv` |
| Lifecycle record CSV | `excel_vba\exports\ir_swap_revalidation_lifecycle_record.csv` |
| VBA module | `excel_vba/vba/Revalidate_IR_Swap.bas` |
| Workbook template | `excel_vba\templates\ir_swap_revalidation_template.xlsx` |

## VBA validation controls

| Control | Rule | Decision use |
|---|---|---|
| PV symmetry | payer NPV plus receiver NPV close to zero | Detect side mismatch |
| DV01 sign | payer DV01 positive, receiver DV01 negative | Detect rate-risk sign error |
| Shock direction | -100bp payer P&L negative and +100bp payer P&L positive | Detect curve-shock inconsistency |
| XVA coverage | marked as NOT COVERED | Prevent overclaiming model coverage |

## Archer/MRM use

The bridge supports a model lifecycle record by exporting model ID, product scope, validation status, monitoring trigger and next lifecycle action.

Generated at: 2026-07-09T16:42:33
