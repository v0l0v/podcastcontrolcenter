# datos_geograficos.py
# Estructura jerárquica: Provincia -> Comarca/GAL -> Lista de Municipios
# Se genera automáticamente MUNICIPIO_A_PROVINCIA para compatibilidad.

DATOS_REGIONALES = {
    # --- ALBACETE ---
    "Albacete": {
        "Mancha Júcar-Centro": [
            "Barrax", "Fuensanta", "La Gineta", "Minaya", "Montalvos", "La Roda", 
            "Tarazona de la Mancha", "Villalgordo del Júcar", "Villarrobledo"
        ],
        "Monte Ibérico-Corredor de Almansa": [
            "Almansa", "Alpera", "Bonete", "Caudete", "Chinchilla de Montearagón", 
            "Corral-Rubio", "Higueruela", "Hoya Gonzalo", "Montealegre del Castillo", 
            "Pétrola", "Pozo Cañada"
        ],
        "Sierra del Segura": [
            "Ayna", "Bogarra", "Elche de la Sierra", "Férez", "Letur", "Liétor", 
            "Nerpio", "Molinicos", "Paterna del Madera", "Riópar", "Socovos", "Yeste"
        ],
        "Campos de Hellín": [
            "Albatana", "Fuente-Álamo", "Hellín", "Ontur", "Tobarra"
        ],
        "La Manchuela": [
            "Abengibre", "Alatoz", "Alborea", "Alcalá del Júcar", "Balsa de Ves", 
            "Carcelén", "Casas de Ves", "Casas de Juan Núñez", "Casas Ibáñez", 
            "Cenizate", "El Herrumblar", "Fuentealbilla", "Golosalvo", "Jorquera", 
            "La Recueja", "Madrigueras", "Mahora", "Motilleja", "Navas de Jorquera", 
            "Pozo Lorente", "Valdeganga", "Villa de Ves", "Villamalea", "Villatoya", 
            "Villavaliente"
        ],
        "SACAM (Sierra de Alcaraz y Campo de Montiel)": [
            "Alcaraz", "Balazote", "El Ballestero", "El Bonillo", "Cotillas", "Lezuza", 
            "Munera", "Peñascosa", "Ossa de Montiel", "Robledo", "Salobre", "San Pedro", 
            "Viveros", "Pozuelo", "Alcadozo", "Bienservida", "La Herrera", "Povedilla", 
            "Casas de Lázaro", "Villapalacios", "Villaverde de Guadalimar", "Masegoso", 
            "Peñas de San Pedro", "Povedilla", "Vianos"
        ]
    },

    # --- CIUDAD REAL ---
    "Ciudad Real": {
        "Entreparques (Cabañeros-Montes Norte)": [
            "Alcoba", "Alcolea de Calatrava", "Anchuras", "Los Cortijos", "Fernán Caballero", 
            "Fontanarejo", "Fuente el Fresno", "Horcajo de los Montes", "Luciana", "Malagón", 
            "Navas de Estena", "Picón", "Piedrabuena", "Poblete", "Porzuna", 
            "Puebla de Don Rodrigo", "Retuerta del Bullaque", "El Robledo", "La EATIM El Torno"
        ],
        "Tierras de Libertad (Campo de Montiel y Calatrava)": [
            "Albaladejo", "Alcubillas", "Almedina", "Almuradiel", "Castellar de Santiago", 
            "Cózar", "Fuenllana", "Montiel", "Puebla del Príncipe", "Santa Cruz de los Cáñamos", 
            "Santa Cruz de Mudela", "Terrinches", "Torre de Juan Abad", "Torrenueva", 
            "Valdepeñas", "Villahermosa", "Villamanrique", "Villanueva de la Fuente", 
            "Villanueva de los Infantes", "Viso del Marqués"
        ],
        "MonteSur (Comarca de Almadén)": [
            "Agudo", "Alamillo", "Almadén", "Almadenejos", "Chillón", "Guadalmez", 
            "Saceruela", "Valdemanco del Esteras"
        ],
        "Mancha Norte": [
            "Alcázar de San Juan", "Alameda de Cervera", "EATIM Cinco Casas", 
            "Arenales de San Gregorio", "Campo de Criptana", "Herencia", "Pedro Muñoz", 
            "Socuéllamos", "Tomelloso"
        ],
        "Alto Guadiana Mancha": [
            "Alhambra", "Arenas de San Juan", "Argamasilla de Alba", "Carrizosa", "Daimiel", 
            "La Solana", "Las Labores", "Llanos", "Manzanares", "Membrilla", "Puerto Lápice", 
            "Ruidera", "San Carlos del Valle", "Villarrubia de los Ojos", "Villarta de San Juan"
        ],
        "Campo de Calatrava": [
            "Aldea del Rey", "Almagro", "Ballesteros de Calatrava", "Bolaños de Calatrava", 
            "Calzada de Calatrava", "Cañada de Calatrava", "Caracuel de Calatrava", 
            "Carrión de Calatrava", "Corral de Calatrava", "Granátula de Calatrava", 
            "Miguelturra", "Moral de Calatrava", "Los Pozuelos de Calatrava", 
            "Pozuelo de Calatrava", "Torralba de Calatrava", "Valenzuela de Calatrava", 
            "Villanueva de San Carlos", "Villar del Pozo"
        ],
        "Valle de Alcudia": [
            "Puertollano", "Abenójar", "Almodóvar del Campo", "Argamasilla de Calatrava", "Brazatortas", 
            "Cabezarados", "Cabezarrubias del Puerto", "Fuencaliente", "Hinojosas de Calatrava", 
            "Mestanza", "San Lorenzo de Calatrava", "Solana del Pino", "Villamayor de Calatrava"
        ]
    },

    # --- CUENCA ---
    "Cuenca": {
        "ADIMAN (Manchuela Conquense)": [
            "Alarcón", "Almodóvar del Pinar", "Buenache de Alarcón", "Campillo de Altobuey", 
            "Casas de Benítez", "Casas de Guijarro", "Casasimarro", "Castillejo de Iniesta", 
            "Enguídanos", "Gabaldón", "Graja de Iniesta", "Hontecillas", "Iniesta", "Ledaña", 
            "Minglanilla", "Motilla del Palancar", "Olmedilla de Alarcón", "Paracuellos de la Vega", 
            "El Peral", "La Pesquera", "El Picazo", "Pozoamargo", "Pozorrubielos de la Mancha", 
            "Puebla del Salvador", "Quintanar del Rey", "Sisante", "Tebar", 
            "Valhermoso de la Fuente", "Valverdejo", "Villagarcía del Llano", "Villalpardo", 
            "Villanueva de la Jara", "Villarta"
        ],
        "ADI El Záncara": [
            "Alconchel de la Estrella", "Atalaya del Cañavate", "Belmonte", "Cañada Juncosa", 
            "Carrascosa de Haro", "Casas de Fernando Alonso", "Casas de Haro", 
            "Casas de los Pinos", "Castillo de Garcimuñoz", "El Cañavate", "El Pedernoso", 
            "El Provencio", "Honrubia", "Hontanaya", "La Alberca de Záncara", "Las Mesas", 
            "Las Pedroñeras", "Los Hinojosos", "Monreal del Llano", "Mota del Cuervo", 
            "Osa de la Vega", "Pinarejo", "Rada de Haro", "San Clemente", 
            "Santa María de los Llanos", "Santa María del Campo Rus", "Torrubia del Castillo", 
            "Tresjuncos", "Vara de Rey", "Villaescusa de Haro", "Villalgordo del Marquesado", 
            "Villamayor de Santiago", "Villar de la Encina"
        ],
        "PRODESE (Serranía de Cuenca)": [
            "Alcalá de la Vega", "Algarra", "Aliaguilla", "Arcos de la Sierra", "Arguisuelas", 
            "Beamud", "Beteta", "Boniches", "Buenache de la Sierra", "Campillos Paravientos", 
            "Campillos Sierra", "Cañada del Hoyo", "Cañamares", "Cañete", "Cañizares", 
            "Carboneras de Guadazaón", "Cardenete", "Carrascosa", "Casas de Garcimolina", 
            "Castillejo-Sierra", "La Cierva", "Cólliga", "Colliguilla", "La Melgosa", "Mohorte", 
            "Nohales", "Tondos", "Valdecabras", "Villanueva de los Escuderos", "Cueva del Hierro", 
            "Fresneda de la Sierra", "La Frontera", "Fuentelespino de Moya", "Fuentes", 
            "Fuertescusa", "Garaballa", "Graja de Campalbo", "Henarejos", "Huélamo", 
            "La Huérguina", "Huerta del Marquesado", "Laguna del Marquesado", "Lagunaseca", 
            "Landete", "Las Majadas", "Mariana", "Masegosa", "Mira", "Monteagudo de las Salinas", 
            "Santo Domingo de Moya", "Narboneta", "Pajarón", "Pajaroncillo", "Palomera", 
            "Portilla", "Poyatos", "El Pozuelo", "Reillo", "Salinas del Manzano", "Salvacañete", 
            "San Martín de Boniches", "Santa Cruz de Moya", "Talayuelas", "Tejadillos", 
            "Tragacete", "Uña", "Valdemeca", "Valdemorillo de la Sierra", "Valdemoro de la Sierra", 
            "Valsalobre", "Vega del Codorno", "Villalba de la Sierra", "Villar del Humo", 
            "Víllora", "Yémeda", "Zafrilla", "Zarzuela", "Sotos", "EATIM Ribatajada"
        ],
        "ADESIMAN (Sierra y Mancha Conquense)": [
            "Abia de la Obispalía", "Albaladejo del Cuende", "Alcázar del Rey", 
            "Almonacid del Marquesado", "Almendros", "Altarejos", "El Acebrón", "La Almarcha", 
            "Arcas", "Arcos de la Cantera", "Barbalimpia", "Barchín del Hoyo", "Belinchón", 
            "Belmontejo", "Carrascosa del Campo", "Cervera del Llano", "Chillarón", "Chumillas", 
            "El Hito", "Fresneda de Altarejos", "Fuente de Pedro Naharro", 
            "Fuentesclaras de Chillarón", "Fuentelespino de Haro", "Horcajo de Santiago", 
            "Huelves", "Huerta de la Obispalía", "Jábaga", "Loranca del Campo", "Montalbanejo", 
            "Montalbo", "Mota de Altarejos", "Navalón", "Olmeda del Rey", "Olmedilla del Campo", 
            "Palomares del Campo", "Paredes", "Parra de las Vegas", "Piqueras del Castillo", 
            "Poveda de la Obispalía", "Pozorrubio de Santiago", "Puebla de Almenara", 
            "Rozalén del Monte", "Saelices", "San Lorenzo de la Parrilla", "Solera de Gabaldón", 
            "Sotoca", "Tarancón", "Torrubia del Campo", "Tribaldos", "Uclés", "Valdetórtola", 
            "Valera de Abajo", "Valeria", "Valparaíso de Abajo", "Valparaíso de Arriba", 
            "Valverde de Júcar", "Villar de Cañas", "Villar de Olalla", "Villar del Saz de Arcas", 
            "Villar del Saz de Navalón", "Villarejo-Periesteban", "Villarejo Seco", 
            "Villarejo de Fuentes", "Villares del Saz", "Villarrubio", "Villaverde y Pasaconsol", 
            "Zafra de Záncara", "Zarza de Tajo"
        ],
        "CEDER Alcarria Conquense": [
            "Albalate de la Nogueras", "Albendea", "Alcantud", "Alcohujate", 
            "Arandilla del Arroyo", "Arrancacepas", "Barajas de Melo", "Bascuñana de San Pedro", 
            "Bolliga", "Bonilla", "Buciegas", "Buendía", "Canalejas del Arroyo", "Cañaveras", 
            "Cañaveruelas", "Caracenilla", "Castejón", "Castillejo del Romeral", 
            "Castillo Albaráñez", "Cuevas de Velasco", "Culebras", "Fuentesbuenas", 
            "Garcinarro", "Gascueña", "Horcajada de la Torre", "Huete", "Jabalera", 
            "La Langa", "La Peraleja", "La Ventosa", "Leganiel", "Mazarulleque", 
            "Moncalvillo de Huete", "Naharros", "Noheda", "Olmeda de la Cuesta", 
            "Olmedilla de Eliz", "Pineda de Gigüela", "Portalrubio de Guadamejud", "Priego", 
            "Saceda del Río", "Saceda Trasierra", "Sacedoncillo", "Salmeroncillos de Abajo", 
            "Salmeroncillos de Arriba", "San Pedro Palmiches", "Tinajas", "Torralba", 
            "Torrejoncillo del Rey", "Valdecañas", "Valdecolmenas de Abajo", 
            "Valdecolmenas de Arriba", "Valdemoro del Rey", "Valdeolivas", "Vellisca", 
            "Verdelpino de Huete", "Villaconejos de Trabaque", "Villalba del Rey", 
            "Villanueva de Guadamejud", "Villar de Domingo García", "Villar del Aguila", 
            "Villar del Horno", "Villar del Infantado", "Villar del Maestre", 
            "Villarejo de la Peñuela", "Villarejo de Sobrehuerta", "Villarejo del Espartal", 
            "Vindel"
        ]
    },

    # --- GUADALAJARA ---
    "Guadalajara": {
        "Molina de Aragón-Alto Tajo": [
            "Ablanque", "Adobes", "Alcolea del Pinar", "Alcoroches", "Algar de Mesa", 
            "Alustante", "Anguita", "Anquela del Ducado", "Anquela del Pedregal", "Arbeteta", 
            "Armallones", "Baños de Tajo", "Campillo de Dueñas", "Canredondo", 
            "Castellar de la Muela", "Castilnuevo", "Checa", "Chequilla", "Ciruelos del Pinar", 
            "Cobeta", "Corduente", "Embid", "Esplegares", "Establés", "Fuembellida", 
            "Fuentelsaz", "Herreria", "Hombrados", "Huertahernando", "Iniéstola", "Luzaga", 
            "Luzón", "Maranchón", "Mazarete", "Megina", "Milmarcos", "Mochales", 
            "Molina de Aragón", "Morenilla", "Ocentejo", "Olmeda de Cobeta", "Orea", "Pardos", 
            "El Pedregal", "Peñalén", "Peralejos de las Truchas", "Pinilla de Molina", 
            "Piqueras", "El Pobo de Dueñas", "Poveda de la Sierra", "Prados", "Redondos", 
            "El Recuenco", "Riba de Saelices", "Rillo de Gallo", "Rueda de la Sierra", 
            "Sacecorbo", "Saelices de la Sal", "Selas", "Setiles", "Taravilla", "Tartanedo", 
            "Terzaga", "Tierzo", "Tordellego", "Tordesilos", "Torrecuadrada de Molina", 
            "Torrecuadradilla", "Torremocha del Pinar", "Torremochuela", "Torrubia", 
            "Tortuera", "Traíd", "Valhermoso", "Valtablado del Rio", "Villanueva de Alcorón", 
            "Villel de Mesa", "La Yunta", "Zaorejas"
        ],
        "ADASUR (Alcarria Sur)": [
            "Albalate de Zorita", "Albares", "Alhóndiga", "Almoguera", "Almonacid de Zorita", 
            "Alovera", "Aranzueque", "Armuña de Tajuña", "Cabanillas del Campo", "Chiloeches", 
            "Driebes", "Escariche", "Escopete", "Fuentelencina", "Fuentelviejo", 
            "Fuentenovilla", "Hontoba", "Horche", "Hueva", "Illana", "Loranca de Tajuña", 
            "Mazuecos", "Mondejar", "Moratilla de los Meleros", "Pastrana", "Pioz", 
            "Pozo de Guadalajara", "Pozo de Almoguera", "Renera", "Sayatón", "Valderachas", 
            "Valdeconcha", "Yebes", "Yebra", "Zorita de los Canes"
        ],
        "ADAC (Alcarria y Campiña)": [
            "Azuqueca de Henares", "Alarilla", "Aldeanueva de Guadalajara", "Atanzón", "Campillo de Ranas", "Cañizar", 
            "Casa de Uceda", "El Casar", "Casas de San Galindo", "Caspueñas", "Ciruelas", 
            "Copernal", "El Cardoso de la Sierra", "El Cubillo de Uceda", "Espinosa de Henares", 
            "Fontanar", "Fuencemillan", "Fuentelahiguera de Albatages", "Galápagos", 
            "Heras de Ayuso", "Hita", "Humanes", "Majaelrayo", "Málaga del Fresno", 
            "Malaguilla", "Marchamalo", "Matarrubia", "Miralrío", "Mohernando", "Montarrón", 
            "Muduex", "Puebla de Beleña", "Quer", "Robledillo de Mohernando", "Taragudo", 
            "Torija", "Torre del Burgo", "Torrejón del Rey", "Tórtola de Henares", "Tortuero", 
            "Trijueque", "Uceda", "Valdearenas", "Valdeavellano", "Valdeaveruelo", 
            "Valdegrudas", "Valdenuño-Fernández", "Valdepeñas de la Sierra", 
            "Villanueva de Argecilla", "Villanueva de la Torre", "Villaseca de Uceda", 
            "Viñuelas", "Yunquera de Henares"
        ],
        "ADEL Sierra Norte": [
            "Bañuelos", "Congostrina", "Condemios de Arriba", "Campisábalos", 
            "Cendejas de la Torre", "Gascueña de Bornova", "Huérmeces del Cerro", "El Sotillo", 
            "Romanillos de Atienza", "San Andrés del Congosto", "Torremocha de Jadraque", 
            "Torremocha del Campo", "Valverde de los Arroyos", "Villares de Jadraque", 
            "Pálmaces de Jadraque", "Rebollosa de Jadraque", "Zarzuela de Jadraque", 
            "Castejón de Henares", "Abánades", "Alaminos", "Albendiego", "Alcolea de las Peñas", 
            "Miedes de Atienza", "Algora", "Angón", "Arbancón", "Arroyo de Fraguas", "Atienza", 
            "Baides", "Bujalaro", "Bustares", "Cantalojas", "Cendejas de Enmedio", 
            "Cincovillas", "Cogolludo", "Condemios de Abajo", "El Ordial", "Estriégana", 
            "Galve de Sorbe", "Hiendalaencina", "Hijes", "Jirueque", "La Bodera", 
            "La Hortezuela de Océn", "La Huerce", "La Mierla", "La Miñosa", 
            "La Olmeda de Jadraque", "Las Inviernas", "Las Navas de Jadraque", "Mandayona", 
            "Matillas", "Medranda", "Membrillera", "Mirabueno", "Monasterio", "Negredo", 
            "Puebla de Valles", "Retiendas", "Riofrío del Llano", "Robledo de Corpes", 
            "Santiuste", "Saúca", "Semillas", "Sienes", "Sigüenza", "Sotodosos", "Somolinos", 
            "Tamajón", "Tordelrábano", "Ujados", "Valdelcubo", "Valdesotos", 
            "Viana de Jadraque", "Villaseca de Henares", "Paredes de Sigüenza", 
            "Pinilla de Jadraque", "Prádena de Atienza", "Jadraque", "La Toba"
        ],
        "FADETA (Tajo-Tajuña)": [
            "Alcocer", "Alique", "Almadrones", "Alocen", "Argecilla", "Auñón", "Barriopedro", 
            "Berninches", "Brihuega", "Budia", "Castilforte", "Centenera", "Chillarón del Rey", 
            "Cifuentes", "Cogollor", "Durón", "El Olivar", "Escamilla", "Gajanejos", "Henche", 
            "Irueste", "Ledanca", "Lupiana", "Mantiel", "Masegoso de Tajuña", "Millana", 
            "Pareja", "Peñalver", "Peralveche", "Romanones", "Sacedón", "Salmerón", 
            "San Andrés del Rey", "Solanillos del Extremo", "Tendilla", "Trillo", "Utande", 
            "Valderrebollo", "Valfermoso de Tajuña", "Yélamos de Abajo", "Yélamos de Arriba"
        ]
    },

    # --- TOLEDO ---
    "Toledo": {
        "Montes Toledanos": [
            "Ajofrín", "Almonacid de Toledo", "Burguillos", "Casasbuenas", "Chueca", "Cobisa", 
            "Consuegra", "Cuerva", "Gálvez", "Guadamur", "Hontanar", "Layos", "Manzaneque", 
            "Marjaliza", "Mascaraque", "Mazarambroz", "Menasalbas", "Mora", "Nambroca", 
            "Navahermosa", "Los Navalmorales", "Noez", "Polán", "Pulgar", 
            "San Bartolomé de las Abiertas", "San Martín de Montalbán", "San Martín de Pusa", 
            "San Pablo de los Montes", "Santa Ana de Pusa", "Totanés", "Urda", 
            "Las Ventas con Peña Aguilera", "Villaminaya", "Villarejo de Montalbán", 
            "Los Yébenes"
        ],
        "Tierras de Talavera (Talavera, Sierra de San Vicente y La Jara)": [
            "Talavera de la Reina", "Alcaudete de la Jara", "Aldeanueva de Barbarroya", "Aldeanueva de San Bartolomé", 
            "Almendral de la Cañada", "Belvís de la Jara", "Buenaventura", "Campillo de la Jara", 
            "Cardiel de los Montes", "Castillo de Bayuela", "Cazalegas", "Cebolla", 
            "Cervera de los Montes", "Espinoso del Rey", "Garciotún", "Hinojosa de San Vicente", 
            "La Estrella", "La Iglesuela", "La Pueblanueva", "Las Herencias", "Los Cerralbos", 
            "Lucillos", "Marrupe", "Mohedas de la Jara", "Montearagón", "Nava de Ricomalillo", 
            "Navamorcuende", "Nuño Gómez", "Pelahustán", "Pepino", "Puerto de San Vicente", 
            "Real de San Vicente", "Retamoso", "Robledo del Mazo", "San Román de los Montes", 
            "Sartajada", "Sevilleja de la Jara", "Sotillo de las Palomas", "Torrecilla de la Jara"
        ],
        "ADECOR (Campana de Oropesa)": [
            "Alberche del Caudillo", "Alcañizo", "Alcolea de Tajo", "Azután", "El Bercial", 
            "Calera y Chozas", "Caleruela", "La Calzada de Oropesa", "Herreruela de Oropesa", 
            "Lagartera", "Mejorada", "Montesclaros", "Navalcán", "Navalmoralejo", "Oropesa", 
            "Parrillas", "El Puente del Arzobispo", "Segurilla", "Torralba de Oropesa", 
            "El Torrico", "Valdeverdeja", "Velada", "Ventas de San Julián"
        ],
        "Castillos del Medio Tajo": [
            "Albarreal de Tajo", "Alcabón", "Aldea en Cabo", "Almorox", "Arcicollar", 
            "Barcience", "Burujón", "Camarena", "Camarenilla", "Carmena", "Carranque", 
            "Carriches", "Cedillo del Condado", "Chozas de Canales", "Domingo Pérez", 
            "El Carpio de Tajo", "El Casar de Escalona", "El Viso de San Juan", "Erustes", 
            "Escalona", "Escalonilla", "Fuensalida", "Gerindote", "Hormigos", "Huecas", 
            "La Mata", "La Puebla de Montalbán", "La Torre de Esteban Hambrán", 
            "Las Ventas de Retamosa", "Malpica del Tajo", "Maqueda", "Mesegar de Tajo", 
            "Méntrida", "Nombela", "Novés", "Otero", "Palomeque", "Paredes de Escalona", 
            "Portillo de Toledo", "Quismondo", "Rielves", "Santa Cruz del Retamar", 
            "Santa Olalla", "Santo Domingo-Caudilla", "Torrijos", "Ugena", "Villamiel de Toledo"
        ],
        "Dulcinea": [
            "Cabezamesada", "Camuñas", "Corral de Almaguer", "Madridejos", "Miguel Esteban", 
            "Puebla de Almoradiel", "Quero", "Quintanar de la Orden", "El Romeral", "Tembleque", 
            "El Toboso", "Turleque", "Villacañas", "Villa de Don Fradrique", 
            "Villafranca de los Caballeros", "Villanueva de Alcardete"
        ],
        "Don Quijote de La Mancha": [
            "Cabañas de Yepes", "Ciruelos", "Dosbarrios", "Huerta de Valdecarábanos", 
            "La Guardia", "Lillo", "Noblejas", "Ocaña", "Ontígola", "Santa Cruz de la Zarza", 
            "Villamuelas", "Villanueva de Bogas", "Villarrubia de Santiago", "Villasequilla", 
            "Villatobas", "Yepes"
        ]
    }
}

# --- Generación automática de MUNICIPIO_A_PROVINCIA ---
MUNICIPIO_A_PROVINCIA = {}

for provincia, comarcas in DATOS_REGIONALES.items():
    # Añadir la propia capital de provincia
    MUNICIPIO_A_PROVINCIA[provincia] = provincia
    
    for comarca, municipios in comarcas.items():
        for municipio in municipios:
            MUNICIPIO_A_PROVINCIA[municipio] = provincia

# Añadir zonas genéricas manualmente si no están cubiertas
ZONAS_GENERICAS = {
    "Castilla-La Mancha": "Castilla-La Mancha",
    "Castilla la Mancha": "Castilla-La Mancha",
    "La Mancha": "Castilla-La Mancha",
    "Sierra de Alcaraz": "Albacete",
    "Campos de Montiel": "Ciudad Real",
    "La Alcarria": "Guadalajara",
    "Serranía de Cuenca": "Cuenca",
    "La Sagra": "Toledo"
}

MUNICIPIO_A_PROVINCIA.update(ZONAS_GENERICAS)
