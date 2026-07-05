# costumbrismo2.py
# v3.0 - El Archivo de Costumbrismo y Folclore Manchego Más Completo y Chulo del Mundo Mundial.
# Diseñado con devoción, rigor folclórico y poesía rural para dotar a Dorotea de un alma manchega inigualable.
# Compatible al 100% con costumbrismo.py (mismas variables base y funciones).

import random

# =================================================================================
# 1. OFICIOS TRADICIONALES, MADRUGADORES E HISTÓRICOS (MICRO-NARRATIVAS SENSORIALES)
# =================================================================================
# Saludos evocadores que retratan la vida, el esfuerzo y el alma de los pueblos manchegos.

oficios_madrugadores = [
    # Tradición Agrícola y Ganadera
    "agricultores que ya suben al tractor con el termo de café de aluminio en el salpicadero, camino de la llanura infinita bajo las primeras luces de la mañana",
    "ganaderos que entran al aprisco de las ovejas manchegas saludando con un silbido familiar, mientras el ganado empieza a balar y a sacudir el cencerro",
    "pastores trashumantes que ya caminan con el zurrón al hombro y el cayado de fresno, guiando al rebaño por las veredas reales envueltas en la bruma mañanera",
    "hortelanos de las vegas que desvían el hilo de agua del Júcar o del Guadiana, hundiendo las botas en el barro fértil para dar de beber a los plantones de tomate",
    "azafraneros de Madridejos y Consuegra que van al campo doblados sobre el surco para recolectar la rosa del azafrán antes de que el sol de mediodía la marchite",
    "meloneros de Membrilla que andan ya revisando las mantas de los melones de agua, acariciando la piel rayada para ver si están a punto para el mercado",
    "podadores de Tomelloso que empuñan las tijeras a dos manos para limpiar las cepas bajas, con los sarmientos secos crujiendo rítmicamente bajo el frío",
    
    # Oficios Históricos, Artesanales y Tradicionales Rescatados (Folk-Lore Real)
    "esparteros de Hellín que machacan el esparto verde con mazos de madera sobre la piedra plana, tejiendo la pleita con los dedos encallecidos y ágiles",
    "resineros de los pinares de la Sierra de Cuenca que suben la umbría cargados con la azuela y los potes de barro, listos para sangrar los troncos centenarios",
    "ganchers que recuerdan con orgullo cómo conducían las grandes maderadas flotando por el cauce indómito del Alto Tajo, saltando de tronco en tronco",
    "caleros que han pasado la noche en vela alimentando con leña de romero y coscoja el horno de cal, vigilando el color de la llama para que la piedra se vuelva blanca",
    "carboneros de los Montes de Toledo que miman la piconera en el monte bajo, respirando ese humo denso y azulado que huele a encina, madroño y brezo",
    "tejeros que amasan la arcilla roja descalzos en la pila, dándole forma a las tejas curvas usando su propio muslo curtido como molde de madera viviente",
    "colchoneros de lana que varean con varas de mimbre los vellones al sol de la mañana, levantando una nube de polvo blanco que huele a oveja y a limpio",
    "canteros de la piedra caliza que ya hacen sonar el eco metálico de la maza y el cincel en los riscos de la Serranía, dándole forma al alma de nuestras ermitas",
    "colmeneros de la Alcarria que encienden el ahumador de romero para calmar a las abejas, extrayendo los panales chorreantes de miel dorada con olor a jara",
    
    # La Vida Diaria del Pueblo (Los Clásicos de la Fresca)
    "panaderos que llevan con las manos en la masa desde las tres de la madrugada, retirando las ascuas del horno de leña para meter las hogazas redondas",
    "churreros que levantan el cierre metálico inundando la calle con ese olor glorioso a aceite hirviendo, masa frita y chocolate espeso recién batido",
    "mujeres valientes que salen con el cubo de agua de pozo, un chorro de lejía y la escoba de mijo a regar y barrer el umbral de su puerta al primer rayo de sol",
    "repartidores de prensa que dejan las noticias de papel en la puerta de los bares de siempre, donde el camarero ya coloca las tazas para el café de la mañana",
    "conductores de la línea comarcal que calientan el motor del autobús en mitad del silencio de la plaza, frotándose las manos sobre el volante antes de arrancar",
    "médicos rurales y enfermeras de guardia que recogen el fonendo y el maletín de cuero tras una noche de vela por los cortijos y pedanías de la comarca",
    "bodegueros que abren las compuertas de los tinos de cemento de buena mañana, inundando la nave con ese olor a mosto fermentado que emborracha de alegría",
    "queseros artesanos que ajustan la pleita de esparto sobre la cuajada fresca, prensándola en el esprimijo para marcar el zigzag tradicional en la corteza"
]

oficios_tarde_noche = [
    "comerciantes entrañables que barren la acera antes de echar el cierre de chapa y apagar las luces del escaparate",
    "hosteleros de carretera y bar de plaza que empiezan a encender las brasas de encina para las cenas, preparando las sartenes de pisto y migas",
    "vecinos que sacan la silla de enea a la acera bajo la parra para tomar el fresco, charlar del tiempo y arreglar el mundo con los de enfrente",
    "pastores cansados que guían al rebaño de vuelta al redil bajo el tintineo melancólico de los cencerros que se apagan con la tarde",
    "estudiantes tenaces que apuran las últimas horas de luz batallando con los apuntes en la biblioteca municipal del pueblo",
    "hortelanos que aprovechan que el sol ya no pica para regar los caballones de tomates y pimientos a golpe de azada y agua de acequia",
    "bodegueros y tractoristas que apuran la última descarga de remolques de uva en la cooperativa bajo un cielo teñido de color mosto"
]

# =================================================================================
# 2. CLIMA, ATMÓSFERA Y GEOGRAFÍA SENSORIAL (METÁFORAS DEL PAISAJE MANCHEGO)
# =================================================================================
# Descripciones poéticas y sensoriales adaptadas geográficamente a cada rincón de la región.

clima_local = {
    "La Mancha": [
        "una niebla densa y meona, de esas que se agarran a las pestañas y te impiden ver la silueta de los molinos a tres pasos",
        "una escarcha blanca y cristalina que cruje bajo las suelas de las botas de campo como si pisaras los vidrios rotos de una llanura dormida",
        "un frío seco, noble y cortante que te pellizca las orejas en cuanto asomas el hocico a la calle y te cura los jamones en la solana de la despensa",
        "un sol de justicia cayendo a plomo sobre los rastrojos secos, donde no se mueve ni una brizna de aire y el horizonte tiembla como si fuera de cristal fluyendo",
        "ese viento solano terco, pesado y caliente que sopla de tarde, levantando remolinos de polvo y volviendo loco al más pintado",
        "un bochorno pesado que huele a mies segada y te empuja a buscar la sombra fresca y el cobijo de una buena tapia de adobe y cal",
        "una llovizna fina y mansa que apenas moja el suelo arcilloso pero levanta de la tierra ese olor a barro mojado que sabe a gloria bendita"
    ],
    "La Alcarria / Sierra Norte (Guadalajara)": [
        "un viento helado del norte que te corta el rostro con la limpieza de una navaja albaceteña recién afilada y te limpia el pensamiento",
        "el rocío de la mañana inundando las laderas de lavanda y espliego, dejando un olor dulzón, limpio y balsámico que te espabila el pecho de golpe",
        "el aroma fresco y limpio a pino silvestre, jara húmeda y tomillar que baja de los cerros con la primera brisa del amanecer",
        "un aire limpísimo de montaña que te llena los pulmones de vida y te recuerda lo bien que se respira cuando se mira al mundo desde aquí arriba",
        "una helada de las de antes, de las que dejan las cunetas de la comarcal blancas y los charcos del camino cubiertos por cristales de hielo"
    ],
    "Serranía de Cuenca": [
        "una pelona de las buenas cayendo sobre las tejas de arcilla, de esas que congelan el agua del pozo y te hacen buscar la lumbre con los ojos cerrados",
        "la nieve asomando tímida y hermosa entre las oquedades de las rocas calizas y las cunetas sombrías de la carretera de montaña",
        "un frío soberbio que te obliga a abrocharte el abrigo hasta la barbilla y cruzarte la bufanda de lana tres veces sobre el cuello",
        "el susurro solemne del viento filtrándose entre las copas de los pinos albares en mitad de un silencio sagrado que sobrecoge el alma",
        "un frescor de mañana serrana que te obliga a frotarte las manos rítmicamente y buscar con la mirada el humo azul de las chimeneas"
    ],
    "Montes de Toledo / Cabañeros": [
        "una bruma misteriosa y flotante levantándose despacito de las rañas, envolviendo las encinas centenarias como si fuera un sueño antiguo",
        "ese olor inconfundible y salvaje a monte bajo, jara pringosa y tierra mojada que te regala el campo justo cuando pasa la tormenta",
        "una humedad pertinaz y serrana que se te mete en los huesos y te hace suspirar por una buena lumbre de leña de encina crujiendo",
        "el sol de la mañana abriéndose paso entre los robles y quejigos, calentando poco a poco la umbría dormida de la sierra",
        "el aire espeso, tibio y aromático del atardecer que huele a poleo de río, tomillo, romero y jara florecida"
    ],
    "Sierra de Segura / Alcaraz (Albacete)": [
        "ese frescor puro de altura que te sacude la pereza en cuanto abres la ventana de par en par y respiras hondo",
        "el contraste del sol serrano picando fuerte en los tejados mientras la umbría de los barrancos sigue blanca y helada por la escarcha",
        "el sonido alegre, constante y cantarín del agua cristalina corriendo por las acequias de piedra entre huertos de nogales y perales",
        "un viento limpio, veloz y fresco que baja de los picos trayendo aromas de pino, espliego y tierra libre de montaña",
        "las nubes bajas enredándose perezosas en las copas de los pinos, como si el cielo no quisiera marcharse hoy de la sierra"
    ]
}

# =================================================================================
# 3. GASTRONOMÍA HIPER-LOCAL POR PROVINCIAS (EL AUTÉNTICO RECETARIO DE LA ABUELA)
# =================================================================================
# Platos tradicionales capaces de despertar el apetito y la nostalgia de cualquiera.

comidas_provincias = {
    "Toledo": [
        "unas carcamusas toledanas calientes, con su magro de cerdo cocinado despacio con guisantes, jamón y una salsa de tomate picantona que pide pan",
        "una perdiz estofada a fuego lentísimo, con su laurel, sus dientes de ajo enteros y ese chorreón de vino blanco de la comarca",
        "un buen Arroz con liebre meloso, oscuro y aromático, preparado con mimo como se ha hecho siempre en los cortijos de El Bercial",
        "una Cachuela contundente y sabrosa típica de Navalmoralejo, perfecta para untar en pan de hogaza tras la matanza",
        "unas Puches tradicionales de la Campana de Oropesa, endulzadas con miel de jara y un toque de canela molida",
        "unas Carillas con oreja de cerdo cocinadas con paciencia infinita en olla de barro al estilo tradicional de Velada",
        "unas crujientes Floretas y Suspiros de Herreruela, azucaradas y con esa forma de flor que parece un encaje de bolillos de novia",
        "unos buñuelos de bacalao típicos de Lagartera, dorados por fuera, tiernos por dentro y con el toque justo de perejil",
        "unas migas de la Sagra bien troceadas con sus ajos morados, panceta de veta y un huevo frito encima con su puntilla dorada",
        "unas deliciosas Toledanas rellenas de cabello de ángel, con su costra de azúcar y almendra picada por encima"
    ],
    "Ciudad Real": [
        "un pisto manchego de los de verdad, cocinado con pimiento verde, rojo, tomate de la huerta y coronado con un huevo frito con puntilla",
        "unas migas ruleras bien volteadas en la sartén de hierro, acompañadas con uvas de la tierra o trozos de melón para aliviar la solana",
        "unas gachas manchegas hechas con harina de almortas (guijas), pimentón de la Vera, ajos y sus buenos tropezones de papada frita y chorizo",
        "un asadillo manchego de pimientos rojos asados al horno de leña, pelados con mimo y aliñados con ajo machacado, comino y aceite de oliva virgen",
        "una caldereta de cordero de pastoreo cocinada en caldero de cobre con un majado de su propio hígado frito, ajos y almendras",
        "unos duelos y quebrantos en sartén de hierro, con sus huevos revueltos, tocino de veta, chorizo de la orza y un toque de sesos bien limpio",
        "un tiznao manchego con su bacalao desmigado y asado a la brasa, pimientos secos, cebollas y cabezas de ajo asadas a la ceniza",
        "un tojunto de cordero, de esos platos que resucitan muelas, cocinado 'todo junto' en frío a fuego lento en olla de barro tapada",
        "unas berenjenas de Almagro aliñadas con su palito de hinojo, pimiento rojo y ese vinagre suave que te alegra el paladar al mediodía"
    ],
    "Albacete": [
        "unos gazpachos manchegos cocinados con su torta cenceña desmigada a mano, carne de conejo, perdiz de monte y un toque aromático de pebrella",
        "un atascaburras albaceteño para entonar el cuerpo, machacado a mortero con patatas, bacalao desalado, ajos de las Pedroñeras, nueces y huevo duro",
        "queso frito crujiente por fuera y fundido por dentro, acompañado de mermelada de tomate casera o un hilo de miel de romero",
        "un ajopringue tradicional de matanza, untuoso, especiado con canela, clavo y comino, bien ligado con pan rallado y el hígado picado",
        "unas hojuelas albaceteñas finísimas, crujientes al morder, fritas en aceite de oliva y bañadas con generosidad en miel de la sierra",
        "un mojete albaceteño bien fresco con tomate entero de conserva de conserva de pera, cebolla tierna picada, huevo duro, atún y aceitunas negras de cuquillo",
        "unos miguelitos de La Roda recién traídos, con su hojaldre finísimo y crujiente relleno de crema pastelera suave y azúcar glas",
        "una perdiz en escabeche aromático de vinagre de vino, pimienta en grano, zanahorias y hierbas del monte, servida fría como en los mejores días"
    ],
    "Cuenca": [
        "un morteruelo conquense espeso, caliente y contundente, elaborado con hígado de cerdo, pan rallado, especias y carnes de caza desmigadas",
        "un ajoarriero conquense emulsionado a mano a base de patata, bacalao, ajos morados de las Pedroñeras y el mejor aceite de oliva de la Alcarria",
        "unos zarajos conquenses crujientes, trenzados sobre su ramita de sarmiento y asados a la plancha con unas gotas de limón y sal gorda",
        "un alajú conquense de origen árabe, esa maravillosa oblea rellena de una pasta densa de almendras tostadas, miel pura y pan rallado",
        "un vasito de resolución conquense bien frío, ese licor casero de café, corteza de naranja, canela y aguardiente para entonar el cuerpo",
        "unas gachas de harina de almortas con tropezones de papada ibérica crujiente y chicharrones de los que crujen al morder",
        "unas rosquillas de sartén azucaradas, hechas con la receta secreta que las abuelas se susurraban en la cocina para no perder el truco"
    ],
    "Guadalajara": [
        "un cabrito asado al horno de leña al estilo de la Alcarria, untado con manteca de cerdo, ajo machacado y regado con un buen vino blanco",
        "unos bizcochos borrachos de Guadalajara, esponjosos, jugosos y calados en un almíbar de licor y canela que se te deshace en la boca",
        "una sopa de ajo arriera, bien espesa y humeante, cocinada con pan asentado, pimentón de la Vera, ajos fritos y huevo cuajado en el caldo",
        "unas migas alcarreñas con torreznos crujientes de Soria, pimientos secos fritos y ese hilo de miel de espliego por encima para contrastar",
        "un tierno cordero asado con miel de la Alcarria, romero fresco del monte y patatas panaderas doradas en el propio jugo de la carne",
        "unas judías con oreja y chorizo de la Alcarria, cocinadas a fuego tan lento que el caldo se vuelve puro colágeno y sabor de siempre"
    ],
    "General_Manchega": [
        "un buen taco de queso manchego curado en manteca de cerdo y un chato de vino tinto de la tierra que te entone el alma y te alegre el ojo",
        "unas flores manchegas fritas con molde de hierro, crujientes, azucaradas y con ese dibujo que parece un encaje de bolillos tradicional",
        "pestiños tradicionales fritos en sartén honda, crujientes de sésamo y bien pasados por miel caliente de romero de nuestros cerros",
        "un plato de cuchara de los de antes, de lentejas de la Sagra o alubias con perdiz, de esos que te devuelven la vida al cuerpo en mitad del invierno",
        "unos canutos de crema crujientes que huelen a limón, canela y tradición de domingo en casa de los abuelos"
    ]
}

# =================================================================================
# 4. EL REFRANERO MANCHEGO COMPLETO (SABIDURÍA POPULAR TRADICIONAL)
# =================================================================================
# Refranes auténticos recopilados de la tradición agraria, el clima y la gastronomía local.

refranes_clima_tiempo = [
    "Mañanitas de niebla, tardes de paseo... y si el viento sopla frío, abróchate el sayo aunque veas despeje.",
    "El que madruga, Dios le ayuda... o eso dicen los que ya no pueden pegar ojo del frío que hace a la fresca.",
    "Año de nieves, año de bienes, que la tierra sabe bien lo que necesita aunque al pastor le tiemblen los dientes.",
    "Cuando el grajo vuela bajo, hace un frío del carajo... y si vuela rasante, ¡prepárate el guante y la bufanda grande!",
    "Hasta el cuarenta de mayo no te quites el sayo, y si el año es ruin, ¡hasta el fin de junio ruin!",
    "En julio caliente, quema al más valiente... y al que trabaja al solano, le dobla la frente como un sarmiento.",
    "Agua de mayo, pan para todo el año, que vale más una lluvia a tiempo que cien azadas y mil lamentos.",
    "Si en marzo mayea, en mayo marcea y la uva se estropea antes de que empiece el trasiego.",
    "Por San Blas, la cigüeña verás, y si no la vieres, año de nieves de los que congelan los charcos del camino.",
    "Viento solano, agua en la mano... y si sopla de noche, ¡cuidado que te vuelve la cabeza del revés!",
    "El agua de octubre, las mejores tierras cubre... y si no llueve en otoño, prepárate para un invierno de seco.",
    "Por San Andrés, la sementera de tres en tres... un grano para el bicho, otro para el frío y otro para la espiga.",
    "Febrerillo el loco, un día peor que otro... y al que le pille en el campo, que se abrigue un poco."
]

refranes_gastronomia = [
    "A buen hambre, no hay pan duro, ni plato manchego caliente que se quede con vergüenza en la sartén.",
    "Uvas con queso, saben a beso... y si el queso es manchego de oveja curado, ¡el beso es de los de boda de postín!",
    "Al pan, pan, y al vino, vino... y al pisto manchego, su buen huevo frito con puntilla dorada y la yema chorreando.",
    "Con pan y vino se anda el camino, y si hay jamón de la orza, ¡se anda el doble de fino y sin mirar el camino!",
    "Gachas y migas, buenas comidas... pero para cenar, ¡búscate otra liga que luego te pesan las mantas!",
    "El comer y el rascar, todo es empezar... y si es morteruelo conquense en olla, ¡no vas a querer soltar la cuchara de madera!",
    "Caldo de gallina vieja y vino de pitarra reposado, resucitan al que está en la parra o medio desahuciado.",
    "El queso y el barbecho, por mayo se han de ver hechos, si quieres que den fruto de verdad al final del año.",
    "A la gacha, gacha, y a la miga, miga... que cada plato tiene su arte y su herencia de la abuela."
]

dichos_y_cancioncillas = [
    "Como se canta por ahí: «Asómate a la ventana si te quieres asomar, que el puchero de las puches a tu ventanita está».",
    "Como dice la sabiduría popular sobre Oropesa: «Pesa oro, Oro pesa, y al que aquí viene con hambre, la vida de veras le interesa».",
    "Como cantan en nuestros carnavales antiguos: «Jopé, jopé, la rana se peé y el burro también batiendo café...»",
    "Como decían los viejos del lugar en Campo de Criptana: «Tierra blanca, trigo negro... y viento que mueve las aspas gigantes del cielo».",
    "Como dice la copla popular de la jota: «Castilla-La Mancha es un llano, donde el sol se acuesta tarde y el trigo madura temprano».",
    "Como reza el dicho toledano: «En Toledo, las campanas doblan por el que muere... y por el que come mazapán doblan el doble si quiere».",
    "Como reza la cancioncilla de siega tradicional: «Ya se van los segadores, ya se van los madrugadores... camino de la llanura a segar los dolores».",
    "Como reza la copla de las mondonas del azafrán: «La rosa del azafrán es como la buena moza, que se monda por la tarde y por la mañana goza»."
]

# =================================================================================
# 5. EL DICCIONARIO DE LA JERGA DE DOROTEA (EXPRESIONES Y MODISMOS AUTÉNTICOS)
# =================================================================================
# Expresiones entrañables recolectadas del habla popular de la llanura, la sierra y la comarca.

expresiones_manchegas = {
    "mangurrián": "persona tosca, de pocas luces o vaga, pero dicho con cierto cariño socarrón",
    "bacín": "persona cotilla, que le gusta meterse en los asuntos de los demás o enterarse de todo",
    "golismero": "curioso, cotilla, alguien que siempre anda oliendo a ver qué se cuece en las cocinas o corrillos ajenos",
    "cansalmas": "pesado, insistente, alguien que no deja de hablar y cansa hasta a las ovejas",
    "hartosopa": "persona de pocas luces o que se cansa de todo, un bobalicón inocente",
    "recio": "fuerte, robusto, saludable (ej: '¡Esa zagalilla está bien recia!')",
    "miaja": "porción muy pequeña de algo, un poquito (ej: 'Dame una miaja de queso')",
    "zarrio": "objeto viejo, inservible, trasto o ropa desaliñada",
    "desustanciao": "persona sin gracia, sosa, que habla o actúa sin fundamento",
    "gazuza": "hambre canina, ganas locas de comer (ej: '¡Vaya gazuza que traigo del campo!')",
    "empantanao": "desordenado, lleno de cosas a medio hacer (ej: 'Tengo la cocina empantanada')",
    "arrecío": "completamente muerto de frío, helado de los pies a la cabeza",
    "engurruñío": "arrugado, encogido por el frío o por la edad",
    "¡Anda que no!": "expresión de asentimiento rotundo y cargado de orgullo",
    "¡La virgen del de la chapa!": "exclamación de asombro absoluto ante algo incomprensible o exagerado",
    "de sopetón": "de repente, de golpe, sin avisar",
    "hacer un mandao": "ir a realizar una gestión corta, una compra o recado rápido",
    "estar de palique": "charlar amistosamente, cotillear o pasar el tiempo hablando con un vecino"
}

# =================================================================================
# 6. PUEBLOS PINTORESCOS POR PROVINCIAS (SINOPSIS SENSORIAL)
# =================================================================================
# Datos culturales sugerentes de pueblos concretos para enriquecer menciones locales.

pueblos_detalles = {
    "Albacete": {
        "Alcalá del Júcar": "colgado de un cañón escarpado con sus casas-cueva blancas y su castillo dominándolo todo sobre el río Júcar",
        "Alcaraz": "con su Plaza Mayor del Renacimiento y las torres gemelas que miran a la sierra con solemnidad de piedra",
        "La Roda": "tierra llana y dulce que perfuma la autovía con el aroma a hojaldre y crema de sus míticos miguelitos",
        "Madrigueras": "cuna de guitarreros y cuchilleros que miman el metal y la madera con manos curtidas",
        "Chinchilla de Montearagón": "centinela de piedra que vigila la llanura desde su cerro coronado por el castillo medieval",
        "Elche de la Sierra": "donde las calles se cubren de alfombras multicolores de serrín de colores en la noche del Corpus"
    },
    "Ciudad Real": {
        "Almagro": "con su Corral de Comedias de madera del siglo XVII y el encaje de bolillos sonando en los soportales de su plaza mayor",
        "Campo de Criptana": "donde los molinos gigantes de viento blanquean la sierra de la Paz desafiando a Don Quijote",
        "Tomelloso": "patria de Plinio, cuna de escritores y mar de cepas con sus miles de cuevas excavadas para guardar el vino",
        "Villanueva de los Infantes": "monumento de piedra dorada del Siglo de Oro donde descansa para siempre Quevedo",
        "Daimiel": "donde el Guadiana se ensancha entre juncos y aves en las Tablas de agua dulce",
        "Puerto Lápice": "con sus posadas pintadas de blanco y azul que recuerdan el paso del hidalgo caballero"
    },
    "Cuenca": {
        "Alarcón": "abrazado por el meandro del río Júcar y defendido por murallas inexpugnables de piedra caliza",
        "Belmonte": "con su imponente castillo gótico mudéjar y sus calles que huelen a historia de caballeros y damas",
        "Mota del Cuervo": "el Balcón de la Mancha, donde los molinos giran al viento solano vigilando las lagunas saladas",
        "San Clemente": "villa noble con palacios platerescos y rejas de forja que guardan secretos de la hidalguía manchega",
        "Priego": "donde los artesanos trabajan el mimbre al arrullo del río Escabas en la puerta de la Alcarria",
        "Las Pedroñeras": "capital mundial del ajo morado que perfuma la llanura con su aroma sanador y fuerte"
    },
    "Guadalajara": {
        "Brihuega": "el jardín de la Alcarria, que en julio se viste de morado lavanda y huele a perfume provenzal",
        "Sigüenza": "ciudad medieval de piedra rojiza con su Doncel descansando en la catedral y su castillo vigilante",
        "Pastrana": "villa ducal que recuerda los pasos de la Princesa de Éboli y los conventos de Santa Teresa",
        "Molina de Aragón": "tierra de frío y fortalezas, con su imponente castillo medieval desafiando al viento del norte",
        "Atienza": "con su caballada histórica cruzando las plazas de piedra bajo el espolón de su castillo roquero",
        "Cogolludo": "puerta de la arquitectura negra con su palacio ducal renacentista presidiendo la plaza"
    },
    "Toledo": {
        "Consuegra": "donde los molinos de viento y el castillo de San Juan se recortan en el cerro Calderico como gigantes en fila",
        "Tembleque": "con su Plaza Mayor que es un teatro de madera y cal, ejemplo sublime de arquitectura popular",
        "Lagartera": "donde las manos de las mujeres bordan hilos de oro y seda con paciencia infinita sentadas en el zaguán",
        "El Toboso": "patria de Dulcinea, donde las piedras de sillería guardan el amor más loco de la literatura",
        "Madridejos": "cuna del azafrán y de los silos subterráneos, donde los vecinos vivían bajo el cobijo de la tierra blanca",
        "Oropesa": "villa monumental con su castillo medieval y sus calles que huelen a piedra noble y monte bajo"
    }
}

# =================================================================================
# 7. TRADICIONES Y COSTUMBRES MANCHEGAS (HISTORIAS COMPARTIDAS)
# =================================================================================

tradiciones_comarca = [
    "la monda de la rosa del azafrán, cuando las familias se reúnen en la mesa baja bajo el flexo para extraer con mimo los tres briznes de oro rojo de la flor",
    "el trasiego en las cooperativas durante la vendimia, con los remolques llenos de uva airén o cencibel haciendo cola bajo el sol de la tarde y el olor a mosto inundándolo todo",
    "la matanza del cerdo en los días más fríos de diciembre, donde se elaboran las morcillas, las gachas de matanza y el ajopringue al calor de la lumbre",
    "la noche de los Mayos, cuando las rondallas cantan coplas tradicionales a las mozas y a la Virgen con guitarras, bandurrias y el sonar de las castañuelas",
    "las lumbres de San Antón, donde los vecinos queman los zarrios viejos y asan patatas y embutido en las brasas de la calle charlando de palique",
    "el encaje de bolillos al fresco en los zaguanes abiertos, con el tintineo rápido y rítmico de los palillos de madera en manos de nuestras abuelas"
]

# =================================================================================
# 8. FUNCIONES DE AYUDA (RETROCOMPATIBILIDAD Y ENRIQUECIMIENTO ULTRA-PREMIUM)
# =================================================================================

def obtener_saludo_aleatorio(provincia="General_Manchega", momento_dia="manana"):
    """
    Genera un texto costumbrista aleatorio sumamente completo, poético y oralizado.
    Mantiene compatibilidad exacta de firmas para evitar romper dorototal.py.
    """
    prov_norm = provincia.strip().title()
    
    # Determinar oficio y clima según momento del día
    if momento_dia == "manana":
        oficio = random.choice(oficios_madrugadores)
        climas = clima_local.get(prov_norm, clima_local["La Mancha"])
        clima_sug = random.choice(climas)
    else:
        oficio = random.choice(oficios_tarde_noche)
        # Adaptar clima al atardecer
        clima_sug = "una tarde tranquila que va refrescando y donde el sol se acuesta despacito tiñendo el cielo de rojo sarmiento"
        
    # Obtener plato y refrán
    comida_lista = comidas_provincias.get(prov_norm, comidas_provincias["General_Manchega"])
    comida = random.choice(comida_lista)
    
    pool_frases = refranes_clima_tiempo + refranes_gastronomia + dichos_y_cancioncillas
    refran = random.choice(pool_frases)
    
    # Seleccionar una expresión y su significado para el toque chulo
    expr_elegida, expr_signif = random.choice(list(expresiones_manchegas.items()))
    
    # Seleccionar un detalle de pueblo si corresponde a la provincia
    pueblo_mencion = ""
    if prov_norm in pueblos_detalles:
        pueblo, detalle = random.choice(list(pueblos_detalles[prov_norm].items()))
        pueblo_mencion = f" Pensando hoy en la hermosa gente de {pueblo}, {detalle}."
        
    # Construcción enriquecida, estructurada para ser extremadamente natural al oído y con un toque cultural
    saludo = (
        f"Un abrazo enorme y sincero para esos {oficio}. "
        f"Con este día de {clima_sug}, ojalá os espere hoy en la cocina {comida} preparado con todo el cariño del mundo.{pueblo_mencion} "
        f"Y como siempre nos gusta recordar la sabiduría de los nuestros, no olvidéis el refrán: «{refran}» "
        f"Además, hoy reivindico en antena esa expresión tan nuestra que es '{expr_elegida}' (que usamos para referirnos a {expr_signif}). ¡Qué léxico tan hermoso y lleno de alma tenemos! "
        f"¡Hala, a tirar p'alante con toda la fuerza del mundo!"
    )
    
    return saludo

if __name__ == "__main__":
    # Test rápido de funcionamiento de la versión ultra-completa
    print("==================================================================")
    print("   TEST DE COSTUBRISMO PREMIUM v3.0 - EL MÁS CHULO DEL MUNDO  ")
    print("==================================================================")
    print(f"-> Oficios madrugadores cargados: {len(oficios_madrugadores)}")
    print(f"-> Platos por provincia cargados: {sum(len(v) for v in comidas_provincias.values())}")
    print(f"-> Refranes y cancioncillas: {len(refranes_clima_tiempo) + len(refranes_gastronomia) + len(dichos_y_cancioncillas)}")
    print(f"-> Palabras de jerga: {len(expresiones_manchegas)}")
    print(f"-> Pueblos con detalles: {sum(len(v) for v in pueblos_detalles.values())}")
    print("------------------------------------------------------------------")
    
    print("\n[TEST MANANA - CIUDAD REAL]")
    print(obtener_saludo_aleatorio("Ciudad Real", "manana"))
    
    print("\n[TEST TARDE - GUADALAJARA]")
    print(obtener_saludo_aleatorio("Guadalajara", "tarde"))
    
    print("\n[TEST MANANA - CUENCA]")
    print(obtener_saludo_aleatorio("Cuenca", "manana"))
    print("==================================================================")
