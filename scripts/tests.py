#importamos funciones para utilzar en nuestro flujo
import sys
import os
import pandas as pd
from pathlib import Path

ruta_utils = os.path.expanduser('~/Documents/IA/4_semestre/ing_de_datos/ing_datos/tools')
sys.path.append(ruta_utils)

import tools
print(f"Tools importado correctamente")
print(f"Los métodos alojados en las herramientas son {dir(tools)}")

#MASTER_DRIVE_FOLDER_ID = '1wjvk7lnyanYCKSsIGLgaltP-Sn7r0Ri_'


#ruta = Path('~/Documents/IA/4_semestre/ing_de_datos/ing_datos/data.csv').expanduser()
# ruta = '~/Documents/IA/4_semestre/ing_de_datos/ing_datos/data.csv'
# test = tools.drive.cargar_archivo(MASTER_DRIVE_FOLDER_ID, ruta)

MASTER_DRIVE_FOLDER_ID = tools.DRIVE_IDS["MASTER_DRIVE_FOLDER_ID"]
print(MASTER_DRIVE_FOLDER_ID)