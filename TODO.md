# RNE NORMALIZER Implementation

## Tasks
- [x] Update app/models.py: Change CheckConstraint to '^[0-9]{8}[A-Z]$'
- [x] Create alembic migration to normalize existing tax_ids (remove dashes, uppercase)
- [x] Update seed_agencies.py: Remove dashes from tax_id in test_agencies
- [x] Update app/routes/reviews.py: Normalize input by removing dashes and uppercasing, validate as 8 digits + 1 letter
- [x] Update app/routes/agencies.py: Update validate_rne_format to match new format (8 digits + 1 letter, no dash)

## Followup Steps
- [ ] Run python migrate_rne_tax_id.py
- [ ] Test with Insomnia using both formats
- [ ] Run bulk update CLI if needed
