# 🔧 Configuración de MySQL para SalariosPerú

## 📋 Pasos para Configurar MySQL

### 1. **Verificar instalación de MySQL**
```bash
mysql --version
# Debería mostrar: mysql Ver 9.3.0 for macos15.2 on arm64 (Homebrew)
```

### 2. **Iniciar MySQL**
Intenta uno de estos comandos:
```bash
# Opción 1: Con brew services
brew services start mysql

# Opción 2: Con sudo si el anterior falla
sudo brew services start mysql

# Opción 3: Directamente
sudo /usr/local/mysql/support-files/mysql.server start
```

### 3. **Configurar MySQL (primera vez)**
```bash
# Ejecutar script de configuración segura
mysql_secure_installation
```

Responde las preguntas:
- **Validate password policy?** → `n` (No)
- **Remove anonymous users?** → `y` (Sí)
- **Disallow root login remotely?** → `y` (Sí)  
- **Remove test database?** → `y` (Sí)
- **Reload privilege tables?** → `y` (Sí)

### 4. **Configurar automáticamente con nuestro script**
```bash
python setup_mysql.py
```

### 5. **Verificar configuración**
```bash
python setup_mysql.py check
```

## 🐛 Solución de Problemas Comunes

### Problema: "Bootstrap failed: 5: Input/output error"
**Solución:**
```bash
# 1. Detener MySQL si está corriendo
brew services stop mysql

# 2. Limpiar archivos temporales
sudo rm -rf /tmp/mysql.sock*

# 3. Reiniciar
brew services start mysql
```

### Problema: "Can't connect to MySQL server"
**Solución:**
```bash
# Verificar que MySQL esté corriendo
brew services list | grep mysql

# Si no está activo, iniciarlo
brew services start mysql

# Verificar puerto
lsof -i :3306
```

### Problema: "Access denied for user 'root'"
**Solución:**
```bash
# Resetear password de root
sudo mysql -u root
```

En MySQL:
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY '';
FLUSH PRIVILEGES;
EXIT;
```

## ⚡ Comandos Rápidos

### Ejecutar scraper simple (sin MySQL)
```bash
python scraper_simple.py
```

### Verificar datos en SQLite
```bash
sqlite3 salarios_simple.db "SELECT COUNT(*) FROM salarios;"
```

### Conectar a MySQL manualmente
```bash
mysql -u salarios_user -p salarios_peru_db
# Password: salarios_pass123
```

### Consultas útiles en MySQL
```sql
-- Ver todas las tablas
SHOW TABLES;

-- Ver estructura de tabla
DESCRIBE salarios;

-- Contar registros
SELECT COUNT(*) FROM salarios;

-- Ver datos recientes
SELECT * FROM salarios ORDER BY fecha_extraccion DESC LIMIT 5;
```

## 🔄 Flujo de Trabajo Recomendado

1. **Primera vez:**
   ```bash
   # Configurar MySQL
   python setup_mysql.py
   
   # Ejecutar scraper
   python scraper_simple.py
   ```

2. **Uso diario:**
   ```bash
   # Verificar MySQL
   python setup_mysql.py check
   
   # Ejecutar scraper
   python scraper_simple.py
   ```

## 📊 Archivos Generados

- `salarios_simple.csv` - Datos en formato CSV
- `salarios_simple.db` - Base de datos SQLite
- `salarios_peru_db` - Base de datos MySQL (si está configurada)

## ⚙️ Configuración de Conexión

Los datos de conexión están en `mysql_config.py`:
- **Host:** localhost
- **Usuario:** salarios_user  
- **Contraseña:** salarios_pass123
- **Base de datos:** salarios_peru_db

¡Modifica estos valores según tus necesidades! 