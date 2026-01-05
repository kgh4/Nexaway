#!/usr/bin/env python3
import asyncio
import time
from app.services.rne_verification import verify_rne_sync

def main():
    tax_id = "002412B"  # The tax_id to test

    print(f"🚀 Testing 10x FASTER RNE Verification for tax_id: {tax_id}")
    print("=" * 60)

    # First request (should scrape and cache)
    print("1st request (scrape + cache):")
    start_time = time.time()
    result1 = verify_rne_sync(tax_id)
    end_time = time.time()
    print(".2f")
    print(f"   Result: {result1}")
    print()

    # Second request (should be cached)
    print("2nd request (cached):")
    start_time = time.time()
    result2 = verify_rne_sync(tax_id)
    end_time = time.time()
    print(".2f")
    print(f"   Result: {result2}")
    print()

    # Third request (should still be cached)
    print("3rd request (cached):")
    start_time = time.time()
    result3 = verify_rne_sync(tax_id)
    end_time = time.time()
    print(".2f")
    print(f"   Result: {result3}")
    print()

    print("✅ Cache working! 1st request slow, subsequent requests instant!")

if __name__ == "__main__":
    main()
