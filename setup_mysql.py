#!/usr/bin/env python3
"""
Script para configurar MySQL para el proyecto SalariosPerú
"""

import mysql.connector
import getpass
import sys
from mysql_config import MYSQL_CONFIG

def setup_mysql():
    """Configura MySQL para el proyecto"""
    print("🔧 Configurando MySQL para SalariosPerú...")
    print("=" * 50)
    
    # Solicitar credenciales de root
    root_password = getpass.getpass("Ingresa la contraseña de root de MySQL (deja vacío si no tiene): ")
    
    try:
        # Conectar como root
        print("📡 Conectando a MySQL como root...")
        root_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=root_password
        )
        root_cursor = root_conn.cursor()
        
        # Crear base de datos
        db_name = MYSQL_CONFIG['database']
        print(f"🗄️  Creando base de datos '{db_name}'...")
        root_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        
        # Crear usuario
        user = MYSQL_CONFIG['user']
        password = MYSQL_CONFIG['password']
        print(f"👤 Creando usuario '{user}'...")
        
        # Eliminar usuario si existe
        try:
            root_cursor.execute(f"DROP USER IF EXISTS '{user}'@'localhost'")
        except:
            pass
        
        # Crear nuevo usuario
        root_cursor.execute(f"CREATE USER '{user}'@'localhost' IDENTIFIED BY '{password}'")
        
        # Otorgar permisos
        print(f"🔑 Otorgando permisos al usuario '{user}'...")
        root_cursor.execute(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{user}'@'localhost'")
        root_cursor.execute("FLUSH PRIVILEGES")
        
        root_cursor.close()
        root_conn.close()
        
        # Probar conexión con el nuevo usuario
        print("🧪 Probando conexión con el nuevo usuario...")
        test_conn = mysql.connector.connect(**MYSQL_CONFIG)
        test_cursor = test_conn.cursor()
        
        # Crear tabla de prueba
        print("📊 Creando tabla de salarios...")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS salarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            empresa VARCHAR(255) NOT NULL,
            puesto VARCHAR(500) NOT NULL,
            salario_minimo DECIMAL(10,2),
            salario_maximo DECIMAL(10,2),
            salario_promedio DECIMAL(10,2),
            moneda VARCHAR(10) DEFAULT 'PEN',
            universidad_principal VARCHAR(255),
            url_empresa VARCHAR(500),
            fecha_extraccion DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_empresa (empresa),
            INDEX idx_puesto (puesto),
            INDEX idx_salario (salario_promedio),
            INDEX idx_fecha (fecha_extraccion)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        test_cursor.execute(create_table_query)
        test_conn.commit()
        
        # Insertar datos de prueba
        print("📝 Insertando datos de prueba...")
        insert_test_data = """
        INSERT IGNORE INTO salarios (empresa, puesto, salario_minimo, salario_maximo, salario_promedio, moneda)
        VALUES 
            ('Banco de Crédito del Perú', 'Analista de Sistemas', 3500, 5500, 4500, 'PEN'),
            ('Interbank', 'Desarrollador Backend', 4000, 7000, 5500, 'PEN'),
            ('BBVA Perú', 'Data Scientist', 5000, 8000, 6500, 'PEN')
        """
        
        test_cursor.execute(insert_test_data)
        test_conn.commit()
        
        # Verificar datos
        test_cursor.execute("SELECT COUNT(*) FROM salarios")
        count = test_cursor.fetchone()[0]
        
        test_cursor.close()
        test_conn.close()
        
        print("✅ MySQL configurado exitosamente!")
        print(f"   - Base de datos: {db_name}")
        print(f"   - Usuario: {user}")
        print(f"   - Registros de prueba: {count}")
        print("\n📋 Configuración:")
        print(f"   Host: {MYSQL_CONFIG['host']}")
        print(f"   Usuario: {MYSQL_CONFIG['user']}")
        print(f"   Contraseña: {MYSQL_CONFIG['password']}")
        print(f"   Base de datos: {MYSQL_CONFIG['database']}")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error de MySQL: {e}")
        
        if e.errno == 1045:  # Access denied
            print("\n💡 Sugerencias:")
            print("1. Verifica que MySQL esté ejecutándose:")
            print("   brew services start mysql")
            print("2. Si olvidaste la contraseña de root:")
            print("   mysql_secure_installation")
            
        elif e.errno == 2003:  # Can't connect
            print("\n💡 MySQL no está ejecutándose. Inicia el servicio:")
            print("   brew services start mysql")
            
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def check_mysql_status():
    """Verifica el estado de MySQL"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM salarios")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print(f"✅ MySQL está funcionando correctamente")
        print(f"   Registros en la tabla: {count}")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error de conexión a MySQL: {e}")
        return False

def check_mysql_config():
    """Verifica la configuración detallada de MySQL"""
    print("🔍 Verificando configuración MySQL...")
    print("=" * 50)
    
    try:
        print(f"✅ Archivo de configuración encontrado")
        print(f"   Host: {MYSQL_CONFIG['host']}")
        print(f"   Usuario: {MYSQL_CONFIG['user']}")
        print(f"   Base de datos: {MYSQL_CONFIG['database']}")
        
        # Intentar conexión
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            print(f"✅ Conexión exitosa")
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", (MYSQL_CONFIG['database'],))
            table_count = cursor.fetchone()[0]
            print(f"   Tablas en la base de datos: {table_count}")
            
            # Verificar tabla salarios
            cursor.execute("SHOW TABLES LIKE 'salarios'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM salarios")
                record_count = cursor.fetchone()[0]
                print(f"   Registros en tabla salarios: {record_count}")
                
                # Obtener algunos ejemplos
                if record_count > 0:
                    cursor.execute("SELECT empresa, puesto, salario_promedio FROM salarios LIMIT 3")
                    examples = cursor.fetchall()
                    print(f"   Ejemplos de datos:")
                    for emp, puesto, salario in examples:
                        print(f"     • {emp}: {puesto} - S/{salario:.0f}")
            else:
                print("   Tabla 'salarios' no existe aún")
            
            conn.close()
            return True
            
        except mysql.connector.Error as e:
            print(f"❌ Error de conexión: {e}")
            return False
            
    except ImportError:
        print("❌ Archivo mysql_config.py no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def reset_mysql_config():
    """Reinicia la configuración de MySQL"""
    print("🔄 Reiniciando configuración MySQL...")
    print("=" * 50)
    
    try:
        # Conectar y eliminar base de datos
        root_password = getpass.getpass("Ingresa la contraseña de root de MySQL: ")
        
        root_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=root_password
        )
        root_cursor = root_conn.cursor()
        
        # Eliminar base de datos y usuario
        print(f"🗑️  Eliminando base de datos '{MYSQL_CONFIG['database']}'...")
        root_cursor.execute(f"DROP DATABASE IF EXISTS {MYSQL_CONFIG['database']}")
        
        print(f"👤 Eliminando usuario '{MYSQL_CONFIG['user']}'...")
        root_cursor.execute(f"DROP USER IF EXISTS '{MYSQL_CONFIG['user']}'@'localhost'")
        
        root_conn.commit()
        root_conn.close()
        
        print("✅ Configuración anterior eliminada")
        print("💡 Ejecuta 'python setup_mysql.py' para reconfigurar")
        
    except Exception as e:
        print(f"❌ Error al reiniciar configuración: {e}")

def main():
    """Función principal con manejo de argumentos"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'check':
            check_mysql_config()
        elif command == 'status':
            check_mysql_status()
        elif command == 'reset':
            reset_mysql_config()
        else:
            print("Comandos disponibles:")
            print("  python setup_mysql.py        - Configuración automática")
            print("  python setup_mysql.py check  - Verificar configuración detallada")
            print("  python setup_mysql.py status - Verificar estado básico")
            print("  python setup_mysql.py reset  - Reiniciar configuración")
    else:
        setup_mysql()

if __name__ == "__main__":
    main() 