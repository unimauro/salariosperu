"""
Configuración para MySQL - SalariosPerú
"""

# Configuración de MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'salarios_user',
    'password': 'salarios_pass123',
    'database': 'salarios_peru_db'
}

# Configuración alternativa para desarrollo local
MYSQL_CONFIG_LOCAL = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Cambiar por tu password de root
    'database': 'salarios_peru_db'
}

def get_mysql_config(use_root=False):
    """
    Retorna la configuración de MySQL
    
    Args:
        use_root (bool): Si usar configuración con usuario root
    
    Returns:
        dict: Configuración de MySQL
    """
    if use_root:
        return MYSQL_CONFIG_LOCAL
    return MYSQL_CONFIG 