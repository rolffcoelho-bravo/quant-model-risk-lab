# Excel/VBA Revalidation Bridge

This folder proves the bridge between the Python IR derivatives validation engine and Excel/VBA review workflows.

Python remains the pricing and validation engine. Excel/VBA is the reviewer interface and legacy-bank workflow bridge.

Workflow:
Python IR derivatives validation -> pricing summary CSV -> shock table CSV -> lifecycle register CSV -> Excel-ready control export -> optional workbook template -> VBA macro revalidation checks.

Files:
- excel_vba/vba/Revalidate_IR_Swap.bas
- excel_vba/exports/ir_swap_revalidation_control_panel.csv
- excel_vba/exports/ir_swap_revalidation_shock_table.csv
- excel_vba/exports/ir_swap_revalidation_lifecycle_record.csv
- excel_vba/templates/ir_swap_revalidation_template.xlsx
- reports/excel_vba_revalidation_bridge.md

The VBA macro checks PV symmetry, DV01 sign, shock direction and the XVA model boundary.
