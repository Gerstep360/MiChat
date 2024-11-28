import os
import shutil  # Para eliminar directorios con contenido
import sqlite3  # Para trabajar con la base de datos SQLite

# Rutas de los archivos y directorios a eliminar
sesion = "flask_session"
cache = "__pycache__"
bd = "database.db"
upload = "static/uploads"
usuarios="usuarios.txt"
# Función para eliminar un archivo o directorio
def eliminar_elemento(ruta):
    if os.path.exists(ruta):  # Verificar si existe
        if os.path.isfile(ruta):  # Si es archivo
            try:
                os.remove(ruta)
                print(f"El archivo {ruta} ha sido eliminado.")
            except Exception as e:
                print(f"No se pudo eliminar el archivo {ruta}: {e}")
        elif os.path.isdir(ruta):  # Si es directorio
            try:
                shutil.rmtree(ruta)  # Eliminar directorio con contenido
                print(f"El directorio {ruta} y su contenido han sido eliminados.")
            except Exception as e:
                print(f"No se pudo eliminar el directorio {ruta}: {e}")
    else:
        print(f"{ruta} no existe.")

# Función para vaciar todas las tablas de una base de datos SQLite
def vaciar_base_de_datos(ruta_bd):
    if os.path.exists(ruta_bd):  # Verificar si la base de datos existe
        try:
            conexion = sqlite3.connect(ruta_bd)
            cursor = conexion.cursor()
            
            # Obtener los nombres de todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tablas = cursor.fetchall()
            
            # Vaciar cada tabla
            for tabla in tablas:
                nombre_tabla = tabla[0]
                cursor.execute(f"DELETE FROM {nombre_tabla};")
                print(f"Datos de la tabla '{nombre_tabla}' eliminados.")
            
            # Reiniciar sqlite_sequence para restablecer autoincrementos
            cursor.execute("DELETE FROM sqlite_sequence;")
            print(f"Datos de la tabla 'sqlite_sequence' eliminados y autoincrementos reiniciados.")
            
            # Confirmar cambios y cerrar conexión
            conexion.commit()
            conexion.close()
            print(f"Todas las tablas de la base de datos '{ruta_bd}' han sido vaciadas.")
        except Exception as e:
            print(f"Error al vaciar la base de datos '{ruta_bd}': {e}")
    else:
        print(f"La base de datos '{ruta_bd}' no existe.")

# Eliminar elementos
eliminar_elemento(sesion)
eliminar_elemento(cache)
eliminar_elemento(upload)
eliminar_elemento(usuarios)
# Vaciar la base de datos
vaciar_base_de_datos(bd)
