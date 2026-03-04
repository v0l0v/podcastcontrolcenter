# costumbrismo.py
# Archivo de recursos locales, oficios, comidas y refranes para Dorotea.
# Puedes añadir todos los elementos que quieras a estas listas y diccionarios.

# ==========================================
# 1. OFICIOS Y SITUACIONES COTIDIANAS
# ==========================================
# Listas simples de oficios que tienen sentido saludar por la mañana o durante el día.

oficios_madrugadores = [
    "panaderos que llevan horas con las manos en la masa",
    "churreros que están levantando el cierre con ese olor a aceite caliente",
    "ganaderos que ya han echado de comer a los animales",
    "agricultores que van en el tractor camino de la finca",
    "repartidores de prensa que dejan las noticias de verdad en la puerta",
    "conductores del autobús de línea escolar",
    "mujeres que salen a barrer y regar la puerta al amanecer",
    "camioneros que llevan horas de ruta atravesando la región",
    "profesionales del centro de salud o el hospital saliendo del turno de noche",
    "esparteros tejiendo la pleita al sol de la mañana",
    "pastores trashumantes guiando sus rebaños",
    "queseros elaborando queso con cinchos de esparto y esprimijos",
    "alfareros dando forma a la cerámica",
    "tratantes cerrando tratos de ganado de buena mañana",
    "panaderos sacando por fin esos panes de leña del horno",
    "cocineras preparando unos buenos barbos"
]

oficios_tarde_noche = [
    "comerciantes que echan el cierre a sus tiendas",
    "hosteleros que empiezan a preparar las cenas",
    "pastores que recogen el rebaño",
    "estudiantes que siguen peleándose con los apuntes en la biblioteca"
]

# ==========================================
# 2. CLIMA Y ATMÓSFERA POR PROVINCIAS/ÁREAS
# ==========================================
# Diccionario para adaptar el "mood" meteorológico según dónde se sitúe el pueblo.

clima_local = {
    "La Mancha": [
        "una niebla densa que no deja ver a tres metros",
        "una escarcha que cruje al pisar",
        "un frío seco que curte la piel",
        "un sol de justicia cayendo a plomo",
        "ese viento solano que vuelve loco a cualquiera"
    ],
    "La Alcarria / Sierra Norte (Guadalajara)": [
        "viento helado que corta la cara",
        "rocío húmedo inundando los campos",
        "olor a pino y jara mojada"
    ],
    "Serranía de Cuenca": [
        "una pelona importante cayendo sobre los tejados",
        "nieve asomando en las cunetas",
        "un frío de bufanda hasta las orejas"
    ],
    "Montes de Toledo / Cabañeros": [
        "bruma de madrugada levantándose de los valles",
        "el olor a campo fresco tras la tormenta",
        "humedad calando los huesos"
    ],
    "Sierra de Segura / Alcaraz (Albacete)": [
        "ese frescor de la sierra que espabila de golpe",
        "el contraste del sol picando sobre la escarcha"
    ]
}

# ==========================================
# 3. GASTRONOMÍA Y COSTUMBRES
# ==========================================

comidas_provincias = {
    "Toledo": [
        "unas buenas carcamusas",
        "una perdiz estofada a fuego lento",
        "venado en salsa",
        "mazapán de desayuno para los más golosos",
        "un buen Arroz con liebre como el que preparan en El Bercial",
        "una Cachuela contundente típica de Navalmoralejo",
        "esas famosas Puches de la Campana de Oropesa",
        "unas Carillas con oreja al estilo de Velada",
        "las tradicionales Floretas y Suspiros de Herreruela",
        "los sabrosos buñuelos de bacalao típicos de Lagartera",
        "el clásico picadillo con vino de pitarra de la matanza"
    ],
    "Ciudad Real": [
        "un buen pisto manchego",
        "unas migas ruleras con uvas",
        "gachas con sus tropezones",
        "asadillo manchego"
    ],
    "Albacete": [
        "unos gazpachos manchegos con su torta y su caza",
        "atascaburras para los días de frío",
        "queso frito"
    ],
    "Cuenca": [
        "un buen morteruelo",
        "ajoarriero bien untado en pan",
        "zarajos crujientes"
    ],
    "Guadalajara": [
        "cabrito asado al horno",
        "bizcochos borrachos",
        "sopa de ajo espesita"
    ],
    "General_Manchega": [
        "queso curado del bueno y un chato de vino",
        "flores manchegas o pestiños si estamos en época",
        "un buen plato de cuchara de los que resucitan muelas"
    ]
}

# ==========================================
# 4. REFRANES Y SABIDURÍA POPULAR
# ==========================================

refranes_clima_tiempo = [
    "Mañanitas de niebla, tardes de paseo.",
    "El que madruga, Dios le ayuda, o eso dicen los que ya no pueden pegar ojo.",
    "Año de nieves, año de bienes.",
    "Cuando el grajo vuela bajo, hace un frío del carajo.",
    "Hasta el cuarenta de mayo no te quites el sayo."
]

refranes_gastronomia = [
    "A buen hambre, no hay pan duro.",
    "Uvas con queso, saben a beso.",
    "Al pan, pan, y al vino, vino.",
    "Con pan y vino se anda el camino."
]

dichos_y_cancioncillas = [
    "Como se canta por ahí: «Asómate a la ventana si te quieres asomar, que el puchero de las puches a tu ventanita está».",
    "Como dice la sabiduría popular sobre Oropesa: «Pesa oro, Oro pesa».",
    "Como cantan en carnavales: «Jopé, jopé, la rana se peé y el burro también batiendo café...»"
]

# ==========================================
# FUNCIONES DE AYUDA (Opcional)
# ==========================================
# Puedes importar módulos de forma muy fácil:
# import costumbrismo
# import random
# clima = random.choice(costumbrismo.clima_local['La Mancha'])

import random

def obtener_saludo_aleatorio(provincia="General_Manchega", momento_dia="manana"):
    """
    Función de ejemplo para generar un pequeño texto costumbrista aleatorio
    que podrías inyectar en tu prompt.
    """
    if momento_dia == "manana":
        oficio = random.choice(oficios_madrugadores)
    else:
        oficio = random.choice(oficios_tarde_noche)
        
    # Asignar comida según provincia, o comida general si no se encuentra
    comida_lista = comidas_provincias.get(provincia, comidas_provincias["General_Manchega"])
    comida = random.choice(comida_lista)
    
    # Añadimos las cancioncillas al pool de refranes
    pool_frases = refranes_clima_tiempo + refranes_gastronomia + dichos_y_cancioncillas
    refran = random.choice(pool_frases)
    
    return f"Un abrazo enorme para esos {oficio}. Ojalá tengáis hoy al fuego {comida}. Y recordad: {refran}"
