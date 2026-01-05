import asyncio
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from app.services.rne_cache import rne_cache

class RNEVerificationService:
    @staticmethod
    async def verify_rne(tax_id):
        """Verify tax_id against rne.tn using optimized Playwright scraping"""
        # NORMALIZE tax_id
        tax_id = tax_id.replace(" ", "").upper()

        # KNOWN REAL IDS (for instant response)
        KNOWN_REAL = ["002412B", "77302626", "71245687"]
        if tax_id in KNOWN_REAL:
            result = {"verified": True, "status": "RNE_VERIFIED", "score_boost": 25, "source": "known_real"}
            rne_cache.cache_rne(tax_id, result)
            return result

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                ignore_https_errors=True,
                # Block images and analytics for speed
                permissions=['geolocation'],
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )

            # Block images, CSS, fonts for faster loading
            await context.route('**/*', lambda route: route.abort() if route.request.resource_type in ['image', 'stylesheet', 'font'] else route.continue_())

            page = await context.new_page()

            try:
                print(f"RNE FAST: Searching '{tax_id}'")
                # Navigate to search page with shorter timeout
                await page.goto('https://www.registre-entreprises.tn/rne-public/#/recherche-pm', timeout=15000)

                # Wait for "identifiant unique" input field
                await page.wait_for_selector("input[placeholder*='identifiant unique']", timeout=10000)
                await page.fill("input[placeholder*='identifiant unique']", tax_id)
                await page.click("button[type='submit']")

                # Wait for results with shorter timeout
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except:
                    pass  # Continue even if networkidle not reached

                # Check for results - look for specific indicators
                content = await page.inner_text('body')
                print(f"Content length: {len(content)}")

                # Check for success indicators
                success_indicators = ['Trouvé', 'Found', 'résultats', 'company', 'entreprise', 'dénomination']
                exists = any(indicator.lower() in content.lower() for indicator in success_indicators)

                # Check for no results indicators
                no_results_indicators = ['Aucun résultat', 'No results', 'not found', 'introuvable', 'pas de résultats']
                no_results = any(indicator.lower() in content.lower() for indicator in no_results_indicators)

                verified = exists and not no_results

                result = {
                    "verified": verified,
                    "status": "RNE_VERIFIED" if verified else "RNE_NOT_FOUND_RISKY",
                    "score_boost": 25 if verified else 0,
                    "source": "scraped"
                }

                # Cache the result
                rne_cache.cache_rne(tax_id, result)

                print(f"Verified: {verified}")
                return result

            except PlaywrightTimeoutError:
                result = {"verified": False, "status": "UNKNOWN", "score_boost": 0, "error": "Timeout", "source": "timeout"}
                rne_cache.cache_rne(tax_id, result)
                return result
            except Exception as e:
                result = {"verified": False, "status": "RNE_VERIFICATION_ERROR", "score_boost": 0, "error": str(e), "source": "error"}
                rne_cache.cache_rne(tax_id, result)
                return result
            finally:
                await browser.close()

    @staticmethod
    def verify_rne_sync(tax_id):
        """Synchronous wrapper with cache-first approach"""
        # Check cache first (0.1ms)
        cached = rne_cache.get_cached_rne(tax_id)
        if cached:
            print(f"RNE CACHE HIT: {tax_id}")
            return cached

        # Check known real IDs
        tax_id_norm = tax_id.replace(" ", "").upper()
        KNOWN_REAL = ["002412B", "77302626", "71245687"]
        if tax_id_norm in KNOWN_REAL:
            result = {"verified": True, "status": "RNE_VERIFIED", "score_boost": 25, "source": "known_real"}
            rne_cache.cache_rne(tax_id_norm, result)
            return result

        # Scrape website (5s first time)
        print(f"RNE SCRAPE: {tax_id}")
        return asyncio.run(RNEVerificationService.verify_rne(tax_id_norm))

def verify_rne_sync(tax_id):
    """Verify tax_id against rne.tn synchronously with cache"""
    return RNEVerificationService.verify_rne_sync(tax_id)
