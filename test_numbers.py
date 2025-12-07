import re
from num2words import num2words

def corregir_numeros_con_puntos_tts(texto: str) -> str:
    """
    Corrige la lectura de números con puntos como separadores de miles para TTS.
    También maneja números grandes sin separadores (>= 10000).
    """
    import re
    from num2words import num2words

    is_ssml = texto.strip().startswith('<speak>')
    
    # 1. Patrón ESTRICTO para puntos de miles (Español). Ej: 1.234, 300.000
    # Ya NO acepta comas ni espacios para evitar conflictos con decimales o listas.
    pattern_dots = r'(?<![a-zA-Z])\b\d{1,3}(?:\.\d{3})+\b'
    
    # 2. Patrón para números grandes SIN separadores (>= 10000)
    # Evitamos 4 dígitos para no romper años (2025).
    pattern_plain = r'(?<![\.,])\b\d{5,}\b'

    def replacer(match):
        numero_str = match.group(0)
        numero_sin_puntos = re.sub(r'\.', '', numero_str)
        try:
            numero_int = int(numero_sin_puntos)
            palabra = num2words(numero_int, lang='es')
            
            if is_ssml:
                return f'<sub alias="{palabra}">{numero_str}</sub>'
            else:
                return palabra
        except (ValueError, OverflowError):
            return numero_str

    # Procesar contenido
    if is_ssml:
        content_match = re.search(r"<speak>(.*)</speak>", texto, re.DOTALL)
        if content_match:
            content = content_match.group(1)
            # Primero puntos
            content = re.sub(pattern_dots, replacer, content)
            # Luego planos
            content = re.sub(pattern_plain, replacer, content)
            return f"<speak>{content}</speak>"
        else:
            return texto
    else:
        texto = re.sub(pattern_dots, replacer, texto)
        texto = re.sub(pattern_plain, replacer, texto)
        return texto

test_cases = [
    "300.000",
    "1.000",
    "10.000",
    "100.000",
    "1.000.000",
    "300,000", # English style / ambiguous
    "300 000", # Space separator
    "precio: 1.234 euros",
    "año 2025", # Should not match (no separator)
    "3.14159", # Decimal?
    "1.2.3", # Version?
    "123.456.789",
    "123456", # No separator
    "300.000€", # With symbol
    "10,500", # Decimal in Spanish?
    "300000" # Plain large number
]

print("--- Testing Original Logic ---")
for case in test_cases:
    result = corregir_numeros_con_puntos_tts(case)
    print(f"Input: '{case}' -> Output: '{result}'")
