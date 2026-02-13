
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.humanization import obtener_toque_humano, load_pueblos_data, seleccionar_pueblo_diario

class TestCSVTowns(unittest.TestCase):
    
    def test_csv_loading(self):
        """Verify CSV loads correctly and has expected columns."""
        pueblos = load_pueblos_data()
        self.assertTrue(len(pueblos) > 0, "No towns loaded from CSV")
        print(f"✅ Loaded {len(pueblos)} towns from CSV.")
        
        # Check first row keys
        first = pueblos[0]
        expected_keys = ['Municipio', 'Provincia', 'Población', 'Superficie (km²)', 'Altitud (m s.n.m.)']
        for k in expected_keys:
            self.assertIn(k, first, f"Missing key {k} in CSV")
            
        # Check numeric conversions
        try:
            p = float(first['Población'])
            a = float(first['Altitud (m s.n.m.)'])
            s = float(first['Superficie (km²)'])
            print(f"✅ Numeric conversion safe: Pop={p}, Alt={a}, Surf={s}")
        except ValueError as e:
            self.fail(f"Numeric conversion failed: {e}")

    def test_humanization_generation(self):
        """Verify humanization generates valid instruction with real data."""
        # Force a specific week/day to test rotation mechanism logic is callable
        # We won't test randomness strictly, just that it returns an instruction
        
        context = obtener_toque_humano(num_noticias=5)
        instruction = context.get('humanizacion_instruccion', '')
        
        self.assertIn("DINÁMICA 'BINGO DE PUEBLOS'", instruction)
        self.assertIn("Contexto Humanizado", instruction)
        
        # Check for Wikipedia content (it might be empty if connection fails or no page, but let's see)
        # We print it to verify visually
        if "Wikipedia" in instruction:
            print("✅ Wikipedia context found!")
            # Extract and print the wikipedia part for verification
            try:
                start = instruction.index("CURIOSIDAD / HISTORIA")
                end = instruction.index("(Usa esto", start)
                print(f"📄 WIKI CONTENT: {instruction[start:end]}")
            except:
                pass
        else:
            print("⚠️ Wikipedia context NOT found (could be network issue or no page).")
        
        print("\n📝 Sample Instruction Generated:")
        print(instruction[:300] + "...")

if __name__ == '__main__':
    unittest.main()
