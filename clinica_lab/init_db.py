import os
import sqlite3
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'clinica.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')
ENV_PATH = os.path.join(BASE_DIR, '.env')
ENV_CONTENIDO = '# ============================================================================\n#  Clínica Aurora Salud — configuración interna (FICTICIA, laboratorio)\n#  Objetivo de la Fase 5: credenciales internas encontradas tras la RCE.\n# ============================================================================\nFLASK_SECRET_KEY=lab-clinica-aurora-secret\nDB_ENGINE=sqlite\nDB_PATH=clinica.db\n\n# Credenciales de la base de datos interna (entorno de producción simulado)\nDB_HOST=10.10.10.25\nDB_PORT=5432\nDB_NAME=aurora_prod\nDB_USER=aurora_dbadmin\nDB_PASSWORD=Pr0d_DB_Aur0ra!2024\n\n# Copia de seguridad de clientes\nBACKUP_PATH=/var/backups/clinica/backup_clientes_2024.csv\n\n# Correo de notificaciones\nSMTP_HOST=smtp.aurorasalud.example\nSMTP_USER=noreply@aurorasalud.example\nSMTP_PASSWORD=Smtp_Aur0ra_2024\n'

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    with sqlite3.connect(DB_PATH) as conn, open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    print(f'[+] Base de datos inicializada en: {DB_PATH}')
    with open(ENV_PATH, 'w', encoding='utf-8') as f:
        f.write(ENV_CONTENIDO)
    print(f'[+] Fichero de configuración (botín) generado en: {ENV_PATH}')
if __name__ == '__main__':
    init_db()
