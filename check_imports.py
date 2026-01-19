
try:
    import holidays
    import bs4
    from src.calendar_utils import obtener_festividades_contexto
    print("SUCCESS: All imports working correctly.")
except ImportError as e:
    print(f"ERROR: {e}")
except Exception as e:
    print(f"ERROR: {e}")
