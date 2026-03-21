import os
import re
import requests
from requests.auth import HTTPBasicAuth

def get_wp_credentials():
    url = os.getenv('WP_URL', 'https://micomicona.com')
    user = os.getenv('WP_USERNAME')
    password = os.getenv('WP_APP_PASSWORD')
    return url, user, password

def generate_next_title():
    url, user, password = get_wp_credentials()
    if not all([url, user, password]):
        print("    ⚠️ Credenciales de WP incompletas o no configuradas.")
        return None
        
    api_url = f"{url.rstrip('/')}/wp-json/wp/v2/posts"
    # Category 25 is Podcast
    params = {'categories': 25, 'per_page': 1, 'orderby': 'date', 'order': 'desc'}
    
    try:
        response = requests.get(api_url, params=params, auth=HTTPBasicAuth(user, password))
        if response.status_code == 200:
            posts = response.json()
            if posts:
                last_title = posts[0]['title']['raw']
                # Buscar el número en el título: ej "podcast-0070" o "Podcast 0070"
                match = re.search(r'(\d+)$', last_title.strip())
                if match:
                    number_str = match.group(1)
                    next_num = int(number_str) + 1
                    # Mantener los ceros a la izquierda
                    next_number_str = str(next_num).zfill(len(number_str))
                    new_title = last_title.rsplit(number_str, 1)[0] + next_number_str
                    return new_title
                else:
                    return f"{last_title} (Nuevo)"
            else:
                return "podcast-0001"
        else:
            print(f"      ❌ Error obteniendo títulos WP: {response.status_code}")
    except Exception as e:
        print(f"      ❌ Excepción conectando a WP: {e}")
    return "Podcast Diario"

def upload_mp3_to_wp(mp3_path):
    url, user, password = get_wp_credentials()
    if not all([url, user, password]):
        return None
        
    api_url = f"{url.rstrip('/')}/wp-json/wp/v2/media"
    filename = os.path.basename(mp3_path)
    
    try:
        with open(mp3_path, 'rb') as f:
            file_data = f.read()
            
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'audio/mpeg'
        }
        
        print(f"    ☁️ Subiendo {filename} a WordPress Media Library...")
        response = requests.post(
            api_url,
            headers=headers,
            data=file_data,
            auth=HTTPBasicAuth(user, password)
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            uploaded_url = data['source_url']
            print(f"      ✅ MP3 subido correctamente: {uploaded_url}")
            return uploaded_url
        else:
            print(f"      ❌ Error subiendo MP3 a WP: {response.text}")
            return None
    except Exception as e:
        print(f"      ❌ Excepción subiendo MP3: {e}")
        return None

def create_podcast_post(new_title, html_path):
    url, user, password = get_wp_credentials()
    
    if not all([url, user, password]):
         print("      ⚠️ Faltan credenciales. Publicación WP omitida.")
         return False
         
    api_url = f"{url.rstrip('/')}/wp-json/wp/v2/posts"
    status = os.getenv('WP_PUBLISH_STATUS', 'draft') # Por defecto borrador por seguridad
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Envolver en bloque de HTML personalizado de Gutenberg
        gutenberg_content = f"<!-- wp:html -->\n{html_content}\n<!-- /wp:html -->"
        
        payload = {
            'title': new_title,
            'content': gutenberg_content,
            'status': status,
            'categories': [25] # ID de categoría "Podcast"
        }
        
        print(f"    ☁️ Creando entrada '{new_title}' (estado: {status}) en WordPress...")
        response = requests.post(
            api_url,
            json=payload,
            auth=HTTPBasicAuth(user, password)
        )
        
        if response.status_code in [200, 201]:
            post_url = response.json().get('link', '')
            print(f"      ✅ Entrada originada con éxito: {post_url}")
            return True
        else:
            print(f"      ❌ Error creando la entrada de WP: {response.text}")
            return False
    except Exception as e:
        print(f"      ❌ Excepción creando la entrada en WP: {e}")
        return False

def publish_podcast_to_wp(mp3_path, html_path):
    print("\n🌐 INICIANDO PUBLICACIÓN AUTOMÁTICA EN WORDPRESS 🌐")
    next_title = generate_next_title()
    if not next_title:
        print("    ❌ No se pudo determinar el próximo título o faltan credenciales de WP para publicar automáticamente.")
        return False
        
    print(f"    📝 Siguiente título calculado: '{next_title}'")
    
    uploaded_url = upload_mp3_to_wp(mp3_path)
    if uploaded_url:
        create_podcast_post(next_title, html_path)
        return True
    return False
