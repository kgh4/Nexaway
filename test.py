print("1. PYTHON WORKS")
print("2. CURRENT FOLDER:", __file__)
print("3. FILES HERE:")
import os
for f in os.listdir('.'):
    print(f"   {f}")
