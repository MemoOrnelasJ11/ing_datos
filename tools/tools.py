#aquí debe ir toda la lógica de las funciones y rutas para usar en el main
#importar todas las librerias
import pandas as pd
import os
import sys
import sqlite3
import requests
import time
import tempfile
import glob
import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi
from pathlib import Path
from dotenv import load_dotenv #pip install python-dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account #pip install google-auth
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from mimetypes import guess_type
#pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib

#Base folder path
BASE_DIR = Path(__file__).resolve().parent.parent

#ruta de descargas de bases de kaggle
RUTA_CARPETA_BASES_KAGGLE = BASE_DIR / "datasets"

KAGGLE_JSON_PATH = os.path.expanduser('~/Documents/IA/4_semestre/ing_de_datos/ing_datos/config/kaggle.json')

#ruta de base de datos sqlite3
RUTA_CARPETA_BASE_SQL= BASE_DIR / "bases"

#Id de carpetas en Drive
DRIVE_IDS = {
"MASTER_DRIVE_FOLDER_ID" : "1wjvk7lnyanYCKSsIGLgaltP-Sn7r0Ri_",
"KAGGLE_DRIVE_FOLDER_ID" : "1mvSPBrSxSdz0wff0DRgmHj-smOPYchg_",
"DB_DRIVE_FOLDER_ID" : "1G3x289C1O8Lt-0aRm8KQUnXNl37_aVd7"
}


#métodos para utilizar, para cada función hay que ir agregando la lógica de cómo debe funcionar cada cada función
class drive:
    
    @staticmethod
    def cargar_archivo(drive_folder, ruta):
        load_dotenv()
        BASE_DIR = Path(__file__).resolve().parent.parent
        CREDENTIALS_PATH = BASE_DIR / "config" / "credentials.json"

        SCOPES = ["https://www.googleapis.com/auth/drive"]

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH),
            SCOPES
        )

        creds = flow.run_local_server(port=0)

        service = build(
            "drive",
            "v3",
            credentials=creds
        )

        # Carpeta de Drive
        FOLDER_ID = drive_folder

        ruta = Path(ruta).expanduser()

        file_name = os.path.basename(ruta)
        mime_type, _ = guess_type(file_name)

        if mime_type is None:
            mime_type = "application/octet-stream"

        # Subir archivo
        file_metadata = {
            "name": file_name,
            "parents": [FOLDER_ID]
        }

        media = MediaFileUpload(
            ruta,
            mimetype= mime_type #mime_type.
        )

        archivo = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name"
        ).execute()

        print("Archivo subido:", archivo["id"])
        return archivo["id"]

    @staticmethod
    def leer_archivo(drive_file_id):
        load_dotenv()

        BASE_DIR = Path(__file__).resolve().parent.parent
        CREDENTIALS_PATH = BASE_DIR / "config" / "credentials.json"

        SCOPES = ["https://www.googleapis.com/auth/drive"]

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH),
            SCOPES
        )

        creds = flow.run_local_server(port=0)

        service = build(
            "drive",
            "v3",
            credentials=creds
        )

        #obtener info del archivo, para leer dependiendo
        metadata = service.files().get(
        fileId=drive_file_id,
        fields="id, name, mimeType"
        ).execute()

        file_name = metadata["name"]
        mime_type = metadata["mimeType"]

        cache_dir = Path(tempfile.gettempdir()) / "drive_cache"

        cache_dir.mkdir(exist_ok=True)

        cache_path = cache_dir / file_name

        request = service.files().get_media(
            fileId=drive_file_id
        )

        with open(cache_path, "wb") as archivo:
            archivo.write(request.execute())

        # ─────────────────────────────────────────────
        # CSV
        # ─────────────────────────────────────────────

        if file_name.lower().endswith(".csv"):

            df = pd.read_csv(cache_path)

            cache_path.unlink(missing_ok=True)

            return df

        # ─────────────────────────────────────────────
        # SQLite
        # ─────────────────────────────────────────────

        elif file_name.lower().endswith(".db"):

            conexion = sqlite3.connect(cache_path)

            return conexion

        # ─────────────────────────────────────────────
        # PDF
        # ─────────────────────────────────────────────

        elif file_name.lower().endswith(".pdf"):

            with open(cache_path, "rb") as archivo:
                contenido = archivo.read()

            cache_path.unlink(missing_ok=True)

            return contenido

        # ─────────────────────────────────────────────
        # Otros archivos
        # ─────────────────────────────────────────────

        else:

            with open(cache_path, "rb") as archivo:
                contenido = archivo.read()

            cache_path.unlink(missing_ok=True)

            return contenido

        #request = service.files().get_media(fileId=drive_file_id)

        #contenido = request.execute()

        #return contenido
    
class sql:
    @staticmethod
    def crear_db(df, ruta_db, nombre_tabla:str):
        
        ruta_db = Path(ruta_db).expanduser()
        conexion = sqlite3.connect(df)

        df.to_sql(
            nombre_tabla,
            conexion,
            if_exists="replace",
            index=False
        )
        conexion.close()


    @staticmethod
    def query(db_id:str, query:str ):
        df = drive.leer_archivo(db_id)
        cursor = df.cursor()
        cursor.execute(query)
        resultado = cursor.fetchall()
        return resultado


class kaggle:
            
    @staticmethod
    #Busca datasets en Kaggle por texto e imprime la lista de resultados
    def consultar_bases_datos(busqueda: str) -> list:
        
        api = KaggleApi()
        api.authenticate()

        results = api.dataset_list(
            search=busqueda
        )
        print(f"Buscando datasets en Kaggle: {busqueda}")

        for dataset in results[:15]:
            print(dataset.ref)

    @staticmethod
    def _carpeta_dataset(ref: str) -> str:
        return os.path.join(RUTA_CARPETA_BASES_KAGGLE, ref.replace('/', '_'))

    @staticmethod
    def _leer_csv(ruta_csv: str) -> pd.DataFrame:
        try:
            return pd.read_csv(ruta_csv)
        except UnicodeDecodeError:
            return pd.read_csv(ruta_csv, encoding="latin-1")
        
    @staticmethod
    def descargar_datos(ref: str, archivo: str = None, forzar: bool = False) -> pd.DataFrame:
        carpeta = kaggle._carpeta_dataset(ref)
        def buscar_csvs():
            csvs = sorted(glob.glob(os.path.join(carpeta, '*.csv')))
            if archivo:
                csvs = [c for c in csvs if os.path.basename(c) == archivo]
            return csvs

        csvs = buscar_csvs()
        if csvs and not forzar:
            print(f"'{ref}' Se encuentra descargado.")
        else:
            api = KaggleApi()
            api.authenticate()
            os.makedirs(carpeta, exist_ok=True)
            print(f"Descargando: {ref} en la carpeta {carpeta}")
            try:
                api.dataset_download_files(ref, path=carpeta, unzip=True, quiet=True)
            except Exception as e:
                print(f"Error al descargar el dataset {ref}: {e}")
                return 
            csvs = buscar_csvs()
            if not csvs:
                print(f"Descarga completada, pero no hay CSV en {carpeta}.")
                return 
            print(f"Descarga exitosa: {ref}")

        ruta_csv = csvs[0]
        df = kaggle._leer_csv(ruta_csv)
        print(f"  Carpeta       : {carpeta}")
        print(f"  Archivos CSV  : {len(csvs)} (usado: {os.path.basename(ruta_csv)})")
        print(f"  Dimensiones   : {df.shape[0]:,} filas x {df.shape[1]} columnas")
        print(f"  Columnas      : {list(df.columns)}")

    @staticmethod
    def cargar_dataframe(ref: str, archivo: str = None) -> pd.DataFrame:
        carpeta = kaggle._carpeta_dataset(ref)
        csvs = sorted(glob.glob(os.path.join(carpeta, '*.csv')))
        if archivo:
            csvs = [c for c in csvs if os.path.basename(c) == archivo]
        if not csvs:
            print(f"No hay CSV de '{ref}' en {carpeta}. Ejecuta primero kaggle.descargar_datos().")
            return None
        return kaggle._leer_csv(csvs[0])
 
class kaggle2:
    @staticmethod
    def consultar_kaggle(busqueda:str):
        load_dotenv()
        BASE_DIR = Path(__file__).resolve().parent.parent
        CREDENTIALS_PATH = BASE_DIR / "config" / "kaggle.json"
        if os.path.exists(CREDENTIALS_PATH):
            os.environ['KAGGLE_CONFIG_DIR'] = BASE_DIR
            print('kaggle.json encontrado, iniciado sesión')
        else:
            from getpass import getpass
            os.environ['KAGGLE_USERNAME'] = input('Usuario de Kaggle: ')
            os.environ['KAGGLE_KEY'] = getpass('API de Kaggle')
            print('Credenciales cargadas en la sesión')

        datasets = kaggle.api.dataset_list(search=busqueda, sort_by='votes', file_type='csv')

        for i, ds in enumerate(datasets[:15]):
            tamano = getattr(ds, 'size', None) or getattr(ds, 'totalBytes', None) or 'N/D'
            votos  = getattr(ds, 'voteCount', 'N/D')
            print(f'{i+1}. {ds.ref}')
            print(f'   {ds.title}  |  {tamano}  |  votos: {votos}')