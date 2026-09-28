#aquí debe ir toda la lógica de las funciones y rutas para usar en el main

#ruta de descargas de bases de kaggle
RUTA_CARPETA_BASES_KAGGLE= ''

#ruta de base de datos sqlite3
RUTA_CARPETA_BASE_SQL= '.db'

#métodos para utilizar, para cada función hay que ir agregando la lógica de cómo debe funcionar cada cada función
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