#aquí debe ir toda la lógica de las funciones y rutas para usar en el main
#importar todas las librerias
import pandas as pd
import os
import sys
import sqlite3
import requests
import time
from pathlib import Path
from dotenv import load_dotenv #pip install python-dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account #pip install google-auth
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from mimetypes import guess_type
#pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib

#ruta de descargas de bases de kaggle
RUTA_CARPETA_BASES_KAGGLE= ''

#ruta de base de datos sqlite3
RUTA_CARPETA_BASE_SQL= '.db'

DRIVE_FOLDER_ID = '1wjvk7lnyanYCKSsIGLgaltP-Sn7r0Ri_'

load_dotenv()
#api_google = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

#creds = service_account.Credentials.from_service_account_file(api_google)


SCOPES = ["https://www.googleapis.com/auth/drive"]

flow = InstalledAppFlow.from_client_secrets_file(
    "config/credentials.json",
    SCOPES
)

creds = flow.run_local_server(port=0)

service = build(
    "drive",
    "v3",
    credentials=creds
)

# Carpeta de Drive
FOLDER_ID = DRIVE_FOLDER_ID
ruta = '~/Documents/IA/4_semestre/ing_de_datos/ing_datos/data.csv'
#mime_type, _ = guess_type(ruta)

# Subir archivo
file_metadata = {
    "name": "data.csv",
    "parents": [FOLDER_ID]
}

media = MediaFileUpload(
    "data.csv",
    mimetype= "text/csv" #mime_type.
)

archivo = service.files().create(
    body=file_metadata,
    media_body=media,
    fields="id"
).execute()

print("Archivo subido:", archivo["id"])



#métodos para utilizar, para cada función hay que ir agregando la lógica de cómo debe funcionar cada cada función
class drive:
    @staticmethod
    def leer_archivo():
        return

    @staticmethod
    def cargar_archivo():
        return

class sql:
    @staticmethod
    def crear_tabla():
        return

    @staticmethod
    def consultar_datos():
        return

    @staticmethod
    def borrar_tabla():
        return

class kaggle:
    @staticmethod
    def consultar_bases_datos():
        return

    @staticmethod
    def descargar_datos():
        return

class data:
    @staticmethod
    def test_a():
        print(5)
        return 