import cloudinary
import cloudinary.uploader
import cloudinary.api
import os

# Configurar Cloudinary directamente
cloudinary.config(
    cloud_name='duprq4d7r',
    api_key='733488446127983',
    api_secret='lDD3Wy5Vi5Hsd3eGkeAPU-EPErg'
)

def upload_file(file, folder="animales"):
    """
    Sube un archivo a Cloudinary
    Args:
        file: Archivo a subir (objeto FileStorage de Flask)
        folder: Carpeta en Cloudinary donde se guardará el archivo
    Returns:
        URL pública de la imagen
    """
    try:
        if not file:
            return None
            
        # Subir archivo a Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type="auto"
        )
        
        # Retornar la URL segura (HTTPS)
        return result['secure_url']
    except Exception as e:
        print(f"Error al subir archivo a Cloudinary: {str(e)}")
        return None

def delete_file(public_id):
    """
    Elimina un archivo de Cloudinary
    Args:
        public_id: ID público del archivo en Cloudinary
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    except Exception as e:
        print(f"Error al eliminar archivo de Cloudinary: {str(e)}")
        return False

def get_public_id_from_url(url):
    """
    Extrae el public_id de una URL de Cloudinary
    Args:
        url: URL de Cloudinary
    Returns:
        str: public_id del archivo
    """
    try:
        # La URL tiene este formato: https://res.cloudinary.com/cloud_name/image/upload/vCappa100..$$567890/folder/filename.ext
        parts = url.split('/')
        # El public_id es todo lo que viene después de vCappa100..$$567890/
        version_index = next(i for i, part in enumerate(parts) if part.startswith('v'))
        public_id = '/'.join(parts[version_index + 1:])
        # Eliminar la extensión del archivo
        public_id = os.path.splitext(public_id)[0]
        return public_id
    except Exception as e:
        print(f"Error al extraer public_id de URL: {str(e)}")
        return None 