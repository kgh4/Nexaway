# TODO: Integrate RNE Verification into TAX ID Validation

## Tasks
- [x] Modify `calculate_trust_score` method in `agency_service.py` to include RNE verification as part of TAX ID validation
- [x] Update `add_agency` method to use the integrated RNE verification and remove separate RNE check
- [x] Test the POST endpoint to ensure RNE verification is integrated into trust score calculation

## Details
- Add `verify_rne` parameter to `calculate_trust_score` (default False)
- In TAX ID validation section, perform RNE verification if `verify_rne=True` and adjust score
- Return rne_status and rne_adjust from `calculate_trust_score`
- Update `add_agency` to pass `verify_rne=True` and use returned RNE values
- Remove duplicate RNE verification code in `add_agency`
