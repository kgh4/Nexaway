import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

class RNEVerificationService:
    @staticmethod
    async def verify_rne(tax_id):
        """Verify tax_id against rne.tn using Playwright scraping"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                ignore_https_errors=True
            )
            page = await context.new_page()

            try:
                print(f"Navigating to registre-entreprises.tn for tax_id: {tax_id}")
                # Navigate to search page
                await page.goto('https://www.registre-entreprises.tn/rne-public/#/recherche-pm', timeout=30000)
                print("Page loaded")

                # Wait for page to load
                await page.wait_for_load_state('networkidle', timeout=10000)
                print("Page ready")

                # Find search input - may need to adjust selector
                search_input = await page.query_selector('input[type="text"], input[name="rne"], #search-input')
                if not search_input:
                    # Try alternative selectors
                    search_input = await page.query_selector('input[placeholder*="RNE"], input[placeholder*="tax"]')

                if not search_input:
                    print("Search input not found")
                    return {"verified": False, "exists": False, "score_boost": 0, "error": "Search input not found"}

                print(f"Filling tax_id: {tax_id}")
                # Input tax_id
                await search_input.fill(tax_id)

                # Find and click search button
                search_button = await page.query_selector('button[type="submit"], input[type="submit"], .search-btn')
                if not search_button:
                    print("Search button not found, pressing Enter")
                    # Try clicking enter on input
                    await search_input.press('Enter')
                else:
                    print("Clicking search button")
                    await search_button.click()

                # Wait for results
                await page.wait_for_load_state('networkidle', timeout=15000)
                print("Results loaded")

                # Check for results - look for "Trouvé", "Found", or company details
                content = await page.inner_text('body')
                print(f"Page content length: {len(content)}")
                print(f"First 500 chars: {content[:500]}")

                # Check for success indicators
                success_indicators = ['Trouvé', 'Found', 'résultats', 'company', 'entreprise']
                exists = any(indicator.lower() in content.lower() for indicator in success_indicators)

                # Check for no results indicators
                no_results_indicators = ['Aucun résultat', 'No results', 'not found', 'introuvable']
                no_results = any(indicator.lower() in content.lower() for indicator in no_results_indicators)

                verified = exists and not no_results

                print(f"Exists: {exists}, No results: {no_results}, Verified: {verified}")

                return {
                    "verified": verified,
                    "exists": verified,
                    "score_boost": 25 if verified else 0
                }

            except PlaywrightTimeoutError:
                return {"verified": False, "exists": False, "score_boost": 0, "error": "Timeout"}
            except Exception as e:
                return {"verified": False, "exists": False, "score_boost": 0, "error": str(e)}
            finally:
                await browser.close()

    @staticmethod
    def verify_rne_sync(tax_id):
        """Synchronous wrapper for verify_rne"""
        return asyncio.run(RNEVerificationService.verify_rne(tax_id))

def verify_rne_sync(tax_id):
    """Verify tax_id against rne.tn synchronously"""
    return RNEVerificationService.verify_rne_sync(tax_id)
