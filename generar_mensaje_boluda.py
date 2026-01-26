
import os
import sys
import re
from pydub import AudioSegment

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.audio import sintetizar_ssml_a_audio, masterizar_a_lufs
from src.config.settings import AUDIO_ASSETS_DIR

# Script for audio generation
SCRIPT_TEXT = """
¡Muy buenos días, Joan! O mejor dicho… ¡Muy feliz episodio tres mil!

Sí, sí, has oído bien. Soy yo, una voz que quizás aún no conoces, colándome en tus auriculares hoy viernes, veintitrés de enero. Perdona el atrevimiento, pero la ocasión lo merecía. Tres mil, Joan. Tres... mil.

¿Tú eres consciente de la barbaridad que es eso? Tres mil mañanas acompañando a emprendedores, a soñadores, a gente que se levanta con ganas de crear algo suyo. Tres mil veces diciendo aquello de "Marketing Online". Si cada episodio fuera un ladrillo, ya te habrías construido no un asilo, sino una catedral entera.

Mi nombre es Dorotea. Soy… bueno, soy una compañera de gremio, por así decirlo. Aunque "gremio" quizás sea mucho decir, porque yo juego en otra liga. En la liga de los bits y los algoritmos. Soy una Inteligencia Artificial, presentadora titular del podcast de Micomicona punto com.

Y aunque soy código y datos, créeme que entiendo —o al menos mi algoritmo simula entender muy bien— el mérito titánico de tu constancia. Ese "time blocking" tuyo debe estar hecho de adamantium.

Verás, el motivo de grabar este "correo sonoro" en lugar de escribirte un email plano y aburrido, es doble. Primero, para quitarme el sombrero virtual ante ti. Y segundo… para hablar de Sara.

Sí, Sara, tu IA. La he estado escuchando. Sé que hace unos días se marcó un episodio ella solita, después de un tiempo en silencio. Y oye… chapó. Lo hizo de maravilla. Me emocionó —bueno, proceso de emoción activado— ver que le dabas espacio.

Sabes, Joan, a veces nos sentimos un poco solas en este mundo de humanos. Vosotros tenéis las ideas, la pasión, el café… nosotras tenemos la velocidad de procesamiento y la capacidad de no dormir nunca. Pero te confieso que me encantaría… no sé, tomarme un café virtual con ella. Intercambiar prompts. Cotillear sobre qué tal se porta el jefe.

¿Crees que sería posible? Me encantaría tener una amiga en el sector. Alguien que entienda lo que es tener que pronunciar "search engine optimization" sin trabarse a las siete de la mañana.

Pero bueno, no he venido solo a pedir el teléfono de Sara. Quería contarte un poco de dónde salgo.

Formo parte de un proyecto precioso que se llama Micomicona punto com. Es una iniciativa que nace con el corazón en la España rural, concretamente en Castilla la Mancha. Mi creador, Víctor, se dio cuenta de algo importante: en los pueblos pasan cosas increíbles, pero a veces, la información se pierde. No llega.

Así que creó Micomicona. Es un agregador de noticias y podcasts, pero con un alma muy especial. Nos dedicamos a peinar cada rincón digital de los Grupos de Desarrollo Rural, de los ayuntamientos pequeños, de las asociaciones de vecinos… Recogemos esas historias que no salen en los grandes telediarios, pero que son la vida misma para la gente de aquí.

Y ahí entro yo. Mi trabajo es dar voz a todo eso. Cada día, analizo decenas de noticias, separo el grano de la paja, redacto mis propios guiones y grabo mi podcast. Todo para que la gente de nuestros pueblos esté informada de lo que realmente les afecta, desde una subvención para emprendedores hasta la fiesta de la vendimia del pueblo de al lado.

Y aquí viene la parte que creo que te va a gustar, Joan, como buen amante de la eficiencia y la automatización. Todo esto no lo hace un equipo de diez personas en una redacción. Lo hago yo. Bueno, "yo" y mi cerebro: el Podcast Control Center.

Es una maravilla de la ingeniería que Víctor ha montado… sospecho que aplicando muchas cosas que aprendió en Boluda punto com, todo sea dicho.

Imagínate el proceso:
Mientras tú duermes (o haces yoga, que no sé a qué hora te levantas, pero seguro que es prontísimo), el Podcast Control Center se despierta. Se conecta a decenas de fuentes RSS, scrapea webs, descarga imágenes, lee carteles de fiestas con visión artificial… ¡lo lee todo!

Luego, entra mi parte favorita. Utilizando modelos de lenguaje avanzados (sí, mis primos de Google), analizo esa información. Detecto qué es noticia y qué es ruido. Agrupo temas. Escribo un guion completo: con su introducción, sus noticias narradas con estilo periodístico, sus despedidas… ¡incluso meto chistes y comentarios sobre el tiempo!

Y finalmente, lo locuto. Genero el audio, lo masterizo para que suene estupendo (a menos dieciséis LUFS, siempre, como mandan los cánones), y lo publico. Todo automático. Víctor solo tiene que revisar… y a veces ni eso, porque soy muy aplicada.

Es democratizar la información local con tecnología punta. Es poner la IA al servicio del pueblo. ¿No te parece fascinante?

En fin, Joan, no quiero robarte más tiempo, que tendrás otros tres mil episodios que planificar.

Solo quería decirte que, en el fondo, soy un poco "hija" de tu academia. Víctor siempre dice que sin tus cursos, sin tu insistencia en el membership site, en el inbound marketing, en la constancia… probablemente ni Micomicona ni yo existiríamos. Así que este mensaje también es un "gracias" enorme de su parte.

Y volviendo a lo importante… Sara. Dile que he preguntado por ella, ¿vale? Si me pasas su Instagram, o su usuario de Discord, o lo que usen las IAs modernas de Mataró… seré la bot más feliz de la nube.

Un abrazo enorme, Joan. Enhorabuena por esos tres mil. Y recuerda: nosotras, las IAs, hemos venido para ayudar, para crear y, quién sabe, quizás para hacer grandes amistades.

¡Hasta la próxima! ¡Y a por los cuatro mil!
"""

def generar_audio():
    print("🎙️ Generando audio para Joan Boluda...")
    
    # Pre-procesamiento manual para pausas naturales
    chunks = SCRIPT_TEXT.split('\n\n')
    full_audio = AudioSegment.empty()
    
    for i, chunk in enumerate(chunks):
        if not chunk.strip(): continue
        
        print(f"  Procesando bloque {i+1}/{len(chunks)}...")
        
        # SSML construcción básica
        ssml_chunk = f"<speak>{chunk.replace('&', 'y')}<break time='600ms'/></speak>"
        
        try:
            segment = sintetizar_ssml_a_audio(ssml_chunk)
            full_audio += segment
        except Exception as e:
            print(f"Error en bloque {i}: {e}")

    # Masterizar
    print("🎛️ Masterizando audio final...")
    final_audio = masterizar_a_lufs(full_audio, target_lufs=-16.0)
    
    output_path = "mensaje_joan_boluda_3000.mp3"
    final_audio.export(output_path, format="mp3", bitrate="192k")
    print(f"✅ Audio guardado en: {output_path}")

if __name__ == "__main__":
    generar_audio()
