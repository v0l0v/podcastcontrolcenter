import feedparser
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
from src.news_engine import parsear_fecha_segura

def analizar_frecuencia_fuentes(feeds_file: str):
    """
    Analiza los feeds y devuelve un DataFrame con estadísticas de publicación.
    Nota: Limitado por el historial que mantenga cada RSS (raramente más de un mes).
    """
    with open(feeds_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
        
    stats = []
    now = datetime.now()
    
    for url in urls:
        try:
            feed = feedparser.parse(url)
            nombre = feed.feed.get('title', url)[:40]
            
            # Contadores
            hoy = 0
            semana = 0
            mes = 0
            total = len(feed.entries)
            
            ultima_fecha = None
            
            for entry in feed.entries:
                fecha = parsear_fecha_segura(entry)
                if not ultima_fecha or fecha > ultima_fecha:
                    ultima_fecha = fecha
                    
                delta = now - fecha
                if delta.days < 1:
                    hoy += 1
                if delta.days < 7:
                    semana += 1
                if delta.days < 30:
                    mes += 1
            
            estado = "🟢 Activa"
            if total == 0:
                estado = "⚪ Vacía"
            elif semana == 0 and mes > 0:
                estado = "🟡 Lenta"
            elif mes == 0:
                estado = "🔴 Inactiva"
                
            stats.append({
                "Fuente": nombre,
                "Estado": estado,
                "24h": hoy,
                "7 días": semana,
                "30 días": mes,
                "Total (Feed)": total,
                "Última": ultima_fecha.strftime("%Y-%m-%d") if ultima_fecha else "N/A"
            })
            
        except Exception:
            stats.append({
                "Fuente": url[:30] + "...",
                "Estado": "❌ Error",
                "24h": 0, "7 días": 0, "30 días": 0, "Total (Feed)": 0, "Última": "Error"
            })
            
    return pd.DataFrame(stats)

def analizar_contenido_noticias(cache_file: str, min_date: datetime = None):
    """
    Analiza el contenido de las noticias cacheadas para generar nubes de palabras.
    Devuelve 3 diccionarios de frecuencias:
    1. Poblaciones (usando datos_geograficos.py)
    2. GAL (Grupos de Acción Local)
    3. Temas/Eventos (palabras clave generales)

    Args:
        cache_file (str): Ruta al archivo JSON con las noticias cacheadas.
        min_date (datetime, optional): Fecha mínima de las noticias a considerar.
                                       Las noticias anteriores a esta fecha serán ignoradas.
                                       Defaults to None.
    """
    import json
    import re
    from collections import Counter
    from datos_geograficos import MUNICIPIO_A_PROVINCIA
    
    # Palabras vacías (stopwords) básicas en español para filtrar "Temas"
    STOPWORDS = {
        'de','la','que','el','en','y','a','los','del','se','las','por','un','para','con',
        'no','una','su','al','lo','como','más','pero','sus','le','ya','o','este','sí',
        'porque','esta','entre','cuando','muy','sin','sobre','también','me','hasta',
        'hay','donde','quien','desde','todo','nos','durante','todos','uno','les',
        'ni','contra','otros','ese','eso','ante','ellos','e','esto','mí','antes',
        'algunos','qué','unos','yo','otro','otras','otra','él','tanto','esa','estos',
        'mucho','quienes','nada','muchos','cual','poco','ella','estar','estas','algunas',
        'algo','nosotros','mi','mis','tú','te','ti','tu','tus','ellas','nosotras',
        'vosotros','vosotras','os','mío','mía','míos','mías','tuyo','tuya','tuyos',
        'tuyas','suyo','suya','suyos','suyas','nuestro','nuestra','nuestros','nuestras',
        'vuestro','vuestra','vuestros','vuestras','esos','esas','estoy','estás',
        'está','estamos','estáis','están','esté','estés','estemos','estéis','estén',
        'estaré','estarás','estará','estaremos','estaréis','estarán',
        'ser','soy','eres','es','somos','sois','son','fui','fuiste','fue','fuimos','fuisteis','fueron',
        'era','eras','éramos','erais','eran','sido','siendo',
        'haber','he','has','ha','hemos','habéis','han','hube','hubiste','hubo','hubimos','hubisteis','hubieron',
        'había','habías','habíamos','habíais','habían','habido','habiendo',
        'tener','tengo','tienes','tiene','tenemos','tenéis','tienen','tuve','tuviste','tuvo','tuvimos','tuvisteis','tuvieron',
        'tenía','tenías','teníamos','teníais','tenían','tenido','teniendo',
        'hacer','hago','haces','hace','hacemos','hacéis','hacen','hice','hiciste','hizo','hicimos','hicisteis','hicieron',
        'hacía','hacías','hacíamos','hacíais','hacían','hecho','haciendo',
        'decir','digo','dices','dice','decimos','decís','dicen','dije','dijiste','dijo','dijimos','dijisteis','dijeron',
        'decía','decías','decíamos','decíais','decían','dicho','diciendo',
        'ir','voy','vas','va','vamos','vais','van','fui','fuiste','fue','fuimos','fuisteis','fueron',
        'iba','ibas','íbamos','ibais','iban','ido','yendo',
        'ver','veo','ves','ve','vemos','veis','ven','vi','viste','vio','vimos','visteis','vieron',
        'veía','veías','veíamos','veíais','veían','visto','viendo',
        'dar','doy','das','da','damos','dais','dan','di','diste','dio','dimos','disteis','dieron',
        'daba','dabas','dábamos','dabais','daban','dado','dando',
        'saber','sé','sabes','sabe','sabemos','sabéis','saben','supe','supiste','supo','supimos','supisteis','supieron',
        'sabía','sabías','sabíamos','sabíais','sabían','sabido','sabiendo',
        'querer','quiero','quieres','quiere','queremos','queréis','quieren','quise','quisiste','quiso','quisimos','quisisteis','quisieron',
        'quería','querías','queríamos','queríais','querían','querido','queriendo',
        'llegar','llego','llegas','llega','llegamos','llegáis','llegan','llegué','llegaste','llegó','llegamos','llegasteis','llegaron',
        'llegaba','llegabas','llegábamos','llegabais','llegaban','llegado','llegando',
        'pasar','paso','pasas','pasa','pasamos','pasáis','pasan','pasé','pasaste','pasó','pasamos','pasasteis','pasaron',
        'pasaba','pasabas','pasábamos','pasabais','pasaban','pasado','pasando',
        'deber','debo','debes','debe','debemos','debéis','deben','debí','debiste','debió','debimos','debisteis','debieron',
        'debía','debías','debíamos','debíais','debían','debido','debiendo',
        'poner','pongo','pones','pone','ponemos','ponéis','ponen','puse','pusiste','puso','pusimos','pusisteis','pusieron',
        'ponía','ponías','poníamos','poníais','ponían','puesto','poniendo',
        'parecer','parezco','pareces','parece','parecemos','parecéis','parecen','parecí','pareciste','pareció','parecimos','parecisteis','parecieron',
        'parecía','parecías','parecíamos','parecíais','parecían','parecido','pareciendo',
        'quedar','quedo','quedas','queda','quedamos','quedáis','quedan','quedé','quedaste','quedó','quedamos','quedasteis','quedaron',
        'quedaba','quedabas','quedábamos','quedabais','quedaban','quedado','quedando',
        'creer','creo','crees','cree','creemos','creéis','creen','creí','creíste','creyó','creímos','creísteis','creyeron',
        'creía','creías','creíamos','creíais','creían','creído','creyendo',
        'hablar','hablo','hablas','habla','hablamos','habláis','hablan','hablé','hablaste','habló','hablamos','hablasteis','hablaron',
        'hablaba','hablabas','hablábamos','hablabais','hablaban','hablado','hablando',
        'llevar','llevo','llevas','lleva','llevamos','lleváis','llevan','llevé','llevaste','llevó','llevamos','llevasteis','llevaron',
        'llevaba','llevabas','llevábamos','llevabais','llevaban','llevado','llevando',
        'dejar','dejo','dejas','deja','dejamos','dejáis','dejan','dejé','dejaste','dejó','dejamos','dejasteis','dejaron',
        'dejaba','dejabas','dejábamos','dejabais','dejaban','dejado','dejando',
        'seguir','sigo','sigues','sigue','seguimos','seguís','siguen','seguí','seguiste','siguió','seguimos','seguisteis','siguieron',
        'seguía','seguías','seguíamos','seguíais','seguían','seguido','siguiendo',
        'encontrar','encuentro','encuentras','encuentra','encontramos','encontráis','encuentran','encontré','encontraste','encontró','encontramos','encontrasteis','encontraron',
        'encontraba','encontrabas','encontrábamos','encontrabais','encontraban','encontrado','encontrando',
        'llamar','llamo','llamas','llama','llamamos','llamáis','llaman','llamé','llamaste','llamó','llamamos','llamasteis','llamaron',
        'llamaba','llamabas','llamábamos','llamabais','llamaban','llamado','llamando',
        'año','años','día','días','mes','meses','semana','semanas','hora','horas','minuto','minutos','segundo','segundos',
        'hoy','ayer','mañana','ahora','después','luego','siempre','nunca','jamás','tarde','temprano','pronto',
        'aquí','ahí','allí','acá','allá','cerca','lejos','arriba','abajo','dentro','fuera','encima','debajo','delante','detrás',
        'castilla-la','mancha','castilla','mancha','región','regional','comunidad','autónoma','provincia','provincias',
        'municipio','municipios','localidad','localidades','pueblo','pueblos','ciudad','ciudades','zona','zonas',
        'parte','partes','lugar','lugares','sitio','sitios','punto','puntos','lado','lados','centro','centros',
        'gobierno','junta','consejería','diputación','ayuntamiento','alcalde','alcaldesa','concejal','concejala',
        'presidente','presidenta','director','directora','secretario','secretaria','consejero','consejera',
        'millón','millones','mil','ciento','cientos','miles','euro','euros','peseta','pesetas',
        'noticia','noticias','información','informaciones','actualidad','reportaje','reportajes','entrevista','entrevistas',
        'foto','fotos','imagen','imágenes','video','videos','audio','audios','enlace','enlaces','web','webs'
    }

    # Palabras clave para detectar GAL
    KEYWORDS_GAL = [
        "GAL", "G.A.L.", "Grupo de Acción Local", "Desarrollo Rural", 
        "LEADER", "PRODER", "RECAMDER", "FADETA", "ADAC", "ADESIMAN", 
        "ADIMAN", "PRODESE", "SACAM", "Monte Ibérico", "Sierra del Segura",
        "Mancha Júcar", "Campos de Hellín", "La Manchuela", "Entreparques",
        "Tierras de Libertad", "MonteSur", "Mancha Norte", "Alto Guadiana",
        "Campo de Calatrava", "Valle de Alcudia", "El Záncara", "Alcarria Conquense",
        "Molina de Aragón", "Alto Tajo", "Sierra Norte", "Montes Toledanos",
        "Tierras de Talavera", "Campana de Oropesa", "Castillos del Medio Tajo",
        "Dulcinea", "Don Quijote"
    ]

    poblaciones_counter = Counter()
    gal_counter = Counter()
    temas_counter = Counter()
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            noticias = json.load(f)
            
        for n in noticias.values():
            # Filtrado por fecha
            if min_date:
                try:
                    fecha_str = n.get('fecha', '')
                    # Intentar parsear fecha YYYY-MM-DD
                    fecha_noticia = datetime.strptime(fecha_str, "%Y-%m-%d")
                    if fecha_noticia < min_date:
                        continue
                except ValueError:
                    # Si no tiene fecha válida, la ignoramos si hay filtro activo
                    continue

            # Usar entidades pre-calculadas
            entidades = n.get('entidades', [])
            
            for entidad in entidades:
                entidad_clean = entidad.strip()
                entidad_lower = entidad_clean.lower()
                
                # 1. Clasificar como Población
                # Buscamos si la entidad coincide con algún municipio (case insensitive)
                es_poblacion = False
                for municipio in MUNICIPIO_A_PROVINCIA.keys():
                    if municipio.lower() == entidad_lower:
                        poblaciones_counter[municipio] += 1
                        es_poblacion = True
                        break
                
                if es_poblacion:
                    continue
                    
                # 2. Clasificar como GAL
                es_gal = False
                for kw in KEYWORDS_GAL:
                    if kw.lower() in entidad_lower:
                        gal_counter[kw] += 1 # Usamos el nombre canónico del GAL
                        es_gal = True
                        break
                
                if es_gal:
                    continue
                    
                # 3. Si no es ni Población ni GAL, es un Tema
                # Filtramos entidades muy cortas o irrelevantes si es necesario
                if len(entidad_clean) > 2:
                    temas_counter[entidad_clean] += 1
                    
    except Exception as e:
        print(f"Error analizando contenido: {e}")
        return {}, {}, {}
        
    return poblaciones_counter, gal_counter, temas_counter
