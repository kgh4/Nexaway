# TODO: Replace RNE Verification with AI Trust Engine

## Tasks
- [x] Update CSV schema: Add `fake_flag` and `analysis_reason` columns to `data/tunisia_agencies_real_dataset.csv`
- [x] Implement AI trust scoring logic in `AgencyCreate` class (rule-based on email, phone, company_name, governorate, tax_id)
- [x] Modify `create_agency` method: Remove Playwright RNE verification, add trust scoring, fake_flag, analysis_reason
- [x] Add rejection logic: Reject POST if trust_score < 30
- [x] Add Premium Verified badge: Set flag if trust_score > 80
- [x] Update response format: Include trust_score, fake_flag, analysis_reason, agency_id
- [x] Remove unused imports: playwright, bs4, requests from `app/routes/agencies.py`
- [x] Test POST endpoint with various inputs
- [x] Verify CSV updates correctly
