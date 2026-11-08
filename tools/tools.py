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
import json
from datetime import datetime
#pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib

#Base folder path
BASE_DIR = Path(__file__).resolve().parent.parent

#ruta de descargas de bases de kaggle
RUTA_CARPETA_BASES_KAGGLE = BASE_DIR / "datasets"

KAGGLE_JSON_PATH = os.path.expanduser('~/Documents/IA/4_semestre/ing_de_datos/ing_datos/config/kaggle.json')
os.environ["KAGGLE_CONFIG_DIR"] = os.path.dirname(KAGGLE_JSON_PATH)

#ruta de base de datos sqlite3
RUTA_CARPETA_BASE_SQL= BASE_DIR / "bases"

#ruta de extraccion y transformacion
RUTA_EXTRACCION_LOGS  = BASE_DIR / "Extraccion_de_Datos" / "Logs"
RUTA_TRANSF_PROCESSED = BASE_DIR / "Transformacion_de_Datos" / "Processed"
RUTA_TRANSF_LOGS      = BASE_DIR / "Transformacion_de_Datos" / "Logs"
RUTA_TRANSF_REPORTES  = BASE_DIR / "Transformacion_de_Datos" / "Reportes"

LOG_EXTRACCION = RUTA_EXTRACCION_LOGS / "extraccion_log.jsonl"
LOG_TRANSF = RUTA_TRANSF_LOGS / "transformacion_log.jsonl"

DATASETS = {
    "adilshamim8"      : {"db": RUTA_CARPETA_BASE_SQL / "tabla_1.db", "raw": "data"},
    "samithsachidanandan"  : {"db": RUTA_CARPETA_BASE_SQL / "tabla_2.db", "raw": "data"},
    "saurabhbadole"     : {"db": RUTA_CARPETA_BASE_SQL / "tabla_3.db", "raw": "data"},
}

ETIQUETAS = list(DATASETS.keys())

#Id de carpetas en Drive
DRIVE_IDS = {
"MASTER_DRIVE_FOLDER_ID" : "1wjvk7lnyanYCKSsIGLgaltP-Sn7r0Ri_",
"KAGGLE_DRIVE_FOLDER_ID" : "1mvSPBrSxSdz0wff0DRgmHj-smOPYchg_",
"DB_DRIVE_FOLDER_ID" : "1G3x289C1O8Lt-0aRm8KQUnXNl37_aVd7", 
"EXTRACCION_LOGS_ID":  "1t6DEBNjjOtVoVvw2CSzNHg3AVL0gvAXh",
"TRANSF_PROCESSED_ID": "1xe5T4tOB3oHyt8Cz_1dtYWCuF8qmmd5k",
"TRANSF_LOGS_ID":      "1YFTogvNdjPP2-vFpdaklLrpRGBCcDYZQ",
"TRANSF_REPORTES_ID":  "1FnBt_IdYpPzjMs4u19nDrRI9setpmKPL"
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
        conexion = sqlite3.connect(ruta_db)

        df.to_sql(
            nombre_tabla,
            conexion,
            if_exists="replace",
            index=False
        )
        conexion.close()


    @staticmethod
    def query(db_id:str, query:str ):

        conexion = drive.leer_archivo(db_id)
        df = pd.read_sql_query(query, conexion)

        conexion.close()
        return df

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

class logs:            
    @staticmethod
    def crear_cdc(ruta, etiqueta = None, reemplazar = False, **estado):
        ruta = Path(ruta).expanduser()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        actual={}

        if ruta.exists() and not reemplazar:
            with open(ruta, encoding="utf-8") as f:
                actual = json.load(f)

        if estado or reemplazar or not ruta.exists():
            if etiqueta:
                actual["etiqueta"] = etiqueta
            actual.update(estado)
            actual["actualizado_en"] = datetime.now().isoformat(timespec="seconds")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(actual, f, indent=2, ensure_ascii=False, default=str)
        return actual

    @staticmethod
    def escribir_log(ruta, **evento):
        ruta = Path(ruta).expanduser()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        registro = {"timestamp": datetime.now().isoformat(timespec="seconds"), **evento}
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")


class transformacion:
    """Funciones genéricas de la capa TRANSFORMED (bitácora, limpieza, calidad y validación).
    Las REGLAS de cada dataset se definen en el notebook; aquí solo vive la mecánica reutilizable."""

    @staticmethod
    def registrar(bitacora, paso, filas_antes, filas_despues, filas_afectadas, decision, justificacion, columnas=None):
        """Agrega un paso a la bitácora con filas antes, después, afectadas y eliminadas."""
        bitacora.append({
            "paso": len(bitacora) + 1,
            "transformacion": paso,
            "columnas": ", ".join(columnas) if columnas else "",
            "filas_antes": int(filas_antes),
            "filas_despues": int(filas_despues),
            "filas_eliminadas": int(filas_antes - filas_despues),
            "filas_afectadas": int(filas_afectadas),
            "decision": decision,
            "justificacion": justificacion,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })

    @staticmethod
    def limpiar_texto(df, columnas, mayusculas=()):
        """strip + colapsa espacios dobles; pasa a MAYÚSCULAS las columnas de códigos.
        Regresa (df, filas_afectadas)."""
        df = df.copy()
        cambio = pd.Series(False, index=df.index)
        for c in columnas:
            original = df[c]
            limpio = original.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
            if c in mayusculas:
                limpio = limpio.str.upper()
            cambio |= (limpio.fillna("<NA>") != original.astype("string").fillna("<NA>"))
            df[c] = limpio
        return df, int(cambio.sum())

    @staticmethod
    def medir_calidad(df, columnas, obligatorias, reglas):
        """Mide completitud, unicidad y consistencia/validez. Regresa un dict plano {(dimension, metrica): valor}."""
        m = {}
        m[("General", "filas")] = len(df)
        for c in columnas:
            m[("Completitud", f"nulos_{c}")] = int(df[c].isna().sum())
        m[("Completitud", "nulos_totales")] = int(df[columnas].isna().sum().sum())
        m[("Completitud", "filas_con_nulo_en_obligatorias")] = int(df[obligatorias].isna().any(axis=1).sum())
        m[("Unicidad", "duplicados_exactos")] = int(df.duplicated(subset=columnas).sum())
        for nombre, regla in reglas.items():
            m[("Consistencia", nombre)] = int(regla(df).fillna(False).sum())
        return m

    @staticmethod
    def tabla_calidad(antes, despues):
        """Arma la tabla antes vs. después a partir de dos salidas de medir_calidad."""
        filas = []
        for (dim, met), v_antes in antes.items():
            v_desp = despues.get((dim, met))
            filas.append({"dimension": dim, "metrica": met, "antes": v_antes, "despues": v_desp,
                          "diferencia": None if v_desp is None else v_desp - v_antes})
        return pd.DataFrame(filas)

    @staticmethod
    def validar_duckdb(ruta_parquet, obligatorias):
        """DESCRIBE del Parquet + conteo de filas y nulos en columnas obligatorias, con DuckDB."""
        import duckdb  # pip install duckdb
        ruta = str(ruta_parquet)
        con = duckdb.connect()
        esquema = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{ruta}')").df()
        nulos = ", ".join(f'SUM(CASE WHEN "{c}" IS NULL THEN 1 ELSE 0 END) AS nulos_{c}' for c in obligatorias)
        conteo = con.execute(f"SELECT COUNT(*) AS filas, {nulos} FROM read_parquet('{ruta}')").df()
        con.close()
        return esquema, conteo
