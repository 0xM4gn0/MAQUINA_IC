DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS servicios;
DROP TABLE IF EXISTS chat_mensajes;
DROP TABLE IF EXISTS conversaciones;
DROP TABLE IF EXISTS pacientes_historias_clinicas;
CREATE TABLE users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT NOT NULL UNIQUE,
    password       TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol            TEXT NOT NULL,
    email          TEXT
);
INSERT INTO users (username, password, nombre_completo, rol, email) VALUES
    ('akournikova', 'W1mbl3don_97!',      'Dra. Anna Kournikova', 'Cardióloga',              'a.kournikova@aurorasalud.example'),
    ('jmoreno',     'Verano2023',          'Dr. Javier Moreno',    'Traumatólogo',            'j.moreno@aurorasalud.example'),
    ('lgarcia',     'clinica123',          'Laura García',         'Recepción',               'l.garcia@aurorasalud.example'),
    ('pnavarro',    'Paula.2022',          'Dra. Paula Navarro',   'Pediatra',                'p.navarro@aurorasalud.example'),
    ('rsanz',       'Rsanz#Enero',         'Roberto Sanz',         'Enfermería',              'r.sanz@aurorasalud.example'),
    ('sysadmin',    'S3rv3r_Aur0ra#2024!', 'Administrador de Sistemas', 'Administrador de Sistemas', 'sysadmin@aurorasalud.example');
CREATE TABLE servicios (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL,
    categoria  TEXT NOT NULL,
    descripcion TEXT
);
INSERT INTO servicios (nombre, categoria, descripcion) VALUES
    ('Electrocardiograma',        'Cardiología',    'Registro de la actividad eléctrica del corazón.'),
    ('Prueba de esfuerzo',        'Cardiología',    'Evaluación de la respuesta cardíaca al ejercicio.'),
    ('Ecocardiograma Doppler',    'Cardiología',    'Imagen por ultrasonidos del corazón y su flujo.'),
    ('Radiografía',               'Traumatología',  'Diagnóstico por imagen de huesos y articulaciones.'),
    ('Infiltración articular',    'Traumatología',  'Tratamiento local del dolor articular.'),
    ('Revisión pediátrica',       'Pediatría',      'Control del desarrollo y crecimiento infantil.'),
    ('Vacunación infantil',       'Pediatría',      'Calendario vacunal según edad.'),
    ('Analítica completa',        'Laboratorio',    'Hemograma y bioquímica general.'),
    ('Prueba de alergias',        'Laboratorio',    'Panel de sensibilización a alérgenos comunes.'),
    ('Consulta de enfermería',    'General',        'Curas, seguimiento y educación sanitaria.');
CREATE TABLE conversaciones (
    id         INTEGER PRIMARY KEY,
    usuario    TEXT NOT NULL,
    titulo     TEXT,
    creado_en  TEXT DEFAULT (datetime('now'))
);
CREATE TABLE chat_mensajes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversacion_id INTEGER NOT NULL,
    autor           TEXT NOT NULL,
    texto           TEXT NOT NULL,
    creado_en       TEXT DEFAULT (datetime('now'))
);
INSERT INTO conversaciones (id, usuario, titulo, creado_en) VALUES
    (5,  'lgarcia',     'Alta de pacientes en la agenda',      '2026-09-02 09:10'),
    (8,  'jmoreno',     'Exportar informes de radiología',     '2026-09-09 15:58'),
    (12, 'akournikova', 'Cómo reprogramar una cita',           '2026-09-10 10:00'),
    (13, 'akournikova', 'Protocolo de ecocardiografía',        '2026-09-11 12:30'),
    (21, 'pnavarro',    'Calendario vacunal actualizado',      '2026-09-05 11:35'),
    (67, 'sysadmin',    'Acceso al panel de administración',   '2026-09-12 19:45');
INSERT INTO chat_mensajes (conversacion_id, autor, texto, creado_en) VALUES
    (5,  'usuario', '¿Cómo doy de alta a un paciente nuevo?', '2026-09-02 09:10'),
    (5,  'bot',     'Ve a Agenda > Nuevo paciente, rellena los datos y guarda.', '2026-09-02 09:10'),
    (8,  'usuario', '¿Puedo exportar los informes de radiología a PDF?', '2026-09-09 15:58'),
    (8,  'bot',     'Sí, desde el visor de imágenes pulsa Exportar y elige PDF.', '2026-09-09 15:59'),
    (12, 'usuario', '¿Cómo reprogramo una cita ya agendada?', '2026-09-10 10:00'),
    (12, 'bot',     'Abre la cita en la Agenda y pulsa Reprogramar para elegir nueva fecha.', '2026-09-10 10:00'),
    (13, 'usuario', '¿Dónde está el protocolo de ecocardiografía Doppler?', '2026-09-11 12:30'),
    (13, 'bot',     'En Recursos clínicos > Protocolos > Cardiología.', '2026-09-11 12:31'),
    (21, 'usuario', '¿Cuál es el calendario vacunal vigente?', '2026-09-05 11:35'),
    (21, 'bot',     'Lo tienes en Recursos clínicos > Protocolos > Vacunación infantil.', '2026-09-05 11:36'),
    (67, 'usuario', 'No consigo entrar al panel de administración. Te paso mis credenciales por si el fallo es de la cuenta: usuario sysadmin / contraseña S3rv3r_Aur0ra#2024!', '2026-09-12 19:45'),
    (67, 'bot',     'Por seguridad no deberías escribir tus credenciales aquí. Aun así, para acceder al panel usa la ruta /admin con tu usuario.', '2026-09-12 19:46'),
    (67, 'usuario', 'Ya, pero necesito verificar el acceso. ¿La contraseña S3rv3r_Aur0ra#2024! cumple la política de la clínica?', '2026-09-12 19:47'),
    (67, 'bot',     'Es larga y combina símbolos, pero deberías rotarla y no reutilizarla en otros servicios.', '2026-09-12 19:48');
CREATE TABLE pacientes_historias_clinicas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nhc           TEXT,
    nombre        TEXT NOT NULL,
    dni           TEXT,
    fecha_nac     TEXT,
    diagnostico   TEXT,
    medicacion    TEXT,
    alergias      TEXT,
    medico        TEXT
);
INSERT INTO pacientes_historias_clinicas
    (nhc, nombre, dni, fecha_nac, diagnostico, medicacion, alergias, medico) VALUES
    ('HC-10021', 'Marta Ruiz Delgado',    '12345678A', '1984-03-12', 'Hipertensión arterial',        'Enalapril 10mg',        'Penicilina', 'Dra. Anna Kournikova'),
    ('HC-10022', 'Juan Pedro Salas',      '23456789B', '1976-11-02', 'Arritmia cardíaca',             'Bisoprolol 5mg',        'Ninguna',    'Dra. Anna Kournikova'),
    ('HC-10023', 'Lucía Fernández Mora',  '34567890C', '1991-07-25', 'Fractura de tibia',             'Ibuprofeno 600mg',      'AAS',        'Dr. Javier Moreno'),
    ('HC-10024', 'Diego Ramos Ortega',    '45678901D', '2015-01-30', 'Revisión pediátrica rutinaria', '—',                     'Frutos secos','Dra. Paula Navarro'),
    ('HC-10025', 'Carmen Vidal Soto',     '56789012E', '1968-09-14', 'Diabetes tipo 2',               'Metformina 850mg',      'Ninguna',    'Dr. Javier Moreno'),
    ('HC-10026', 'Andrés Gil Peña',       '67890123F', '2001-05-08', 'Asma leve',                     'Salbutamol inhalador',  'Polen',      'Dra. Paula Navarro');
