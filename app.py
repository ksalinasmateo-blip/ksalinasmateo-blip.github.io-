from flask import Flask, render_template, request, redirect, session, send_from_directory, abort
import sqlite3
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = "pec"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# =========================
# VALIDAR LOGIN
# =========================
def login_requerido():

    if 'usuario' not in session:
        return False

    return True


# =========================
# VALIDAR RESPONSABLE
# =========================
def solo_responsable():

    if 'usuario' not in session:
        return False

    if session.get('rol') != 'responsable':
        return False

    return True


# =========================
# CONEXIÓN BD
# =========================
def conectar():
    conn = sqlite3.connect("pec.bd")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# FUNCIÓN PARA CREAR TABLAS AUTOMÁTICAMENTE
# =========================
def inicializar_base_datos():

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT UNIQUE NOT NULL,
        contrasena TEXT NOT NULL,
        rol TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Responsables (
        id_responsable INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        cargo TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Actividades (
        id_actividad INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        fecha TEXT NOT NULL,
        lugar TEXT NOT NULL,
        archivo TEXT,
        responsable TEXT NOT NULL,
        sede TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Evaluaciones (
        id_evaluacion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_actividad INTEGER,
        resultado TEXT,
        observaciones TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Evidencias (
        id_evidencia INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT,
        archivo TEXT,
        id_actividad INTEGER
    );
    """)

    cur.execute("SELECT COUNT(*) FROM Usuarios")

    if cur.fetchone()[0] == 0:

        cur.execute("""
        INSERT INTO Usuarios(nombre, correo, contrasena, rol)
        VALUES ('Juan Pérez', 'juan@gmail.com', '12345', 'alumno')
        """)

        cur.execute("""
        INSERT INTO Usuarios(nombre, correo, contrasena, rol)
        VALUES ('José Luis Anaya Reyes', 'jose.anaya@pec.com', '123456', 'responsable')
        """)

        cur.execute("""
        INSERT INTO Usuarios(nombre, correo, contrasena, rol)
        VALUES ('Beatriz Téllez Salgado', 'beatriz.tellez@pec.com', '123456', 'responsable')
        """)

        conn.commit()

    conn.close()


# =========================
# ARCHIVOS
# =========================
@app.route('/uploads/<filename>')
def uploads(filename):

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename
    )


# =========================
# INICIO
# =========================
@app.route('/')
def inicio():

    return render_template('index.html')


# =========================
# LOGIN
# =========================
# =========================
# LOGIN
# =========================
@app.route('/login')
def login():

    return render_template('login.html')


# =========================
# REGISTRO
# =========================
@app.route('/registro')
def registro():

    return render_template('registro.html')


# =========================
# GUARDAR USUARIO
# =========================
@app.route('/guardar_usuario', methods=['POST'])
def guardar_usuario():

    nombre = request.form['nombre']
    correo = request.form['correo']
    contrasena = request.form['contrasena']
    rol = request.form['rol']

    codigo_docente = request.form.get('codigo_docente')

    # VALIDAR CODIGO DOCENTE
    if rol == "responsable":

        if codigo_docente != "PEC2026":

            return "Código docente incorrecto"

    conn = conectar()
    cur = conn.cursor()

    try:

        cur.execute("""
        INSERT INTO Usuarios(nombre, correo, contrasena, rol)
        VALUES (?, ?, ?, ?)
        """, (
            nombre,
            correo,
            contrasena,
            rol
        ))

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return "El correo ya está registrado"

    conn.close()

    return redirect('/login')
@app.route('/validar_login', methods=['POST'])


# =========================
# VALIDAR LOGIN
# =========================
@app.route('/validar_login', methods=['POST'])
def validar_login():

    correo = request.form['u_correo'].strip()
    contrasena = request.form['contrasena'].strip()

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM Usuarios WHERE correo=? AND contrasena=?",
        (correo, contrasena)
    )

    user = cur.fetchone()

    conn.close()

    if user:

        session['usuario'] = user['nombre']
        session['rol'] = user['rol']

        if user['rol'] == 'responsable':
            return redirect('/docentes')

        return redirect('/alumno')

    return "DATOS INCORRECTOS"


# =========================
# DOCENTES
# =========================
@app.route('/docentes')
def docentes():

    if not solo_responsable():
        return redirect('/login')

    return render_template('docentes.html')


# =========================
# ALUMNO
# =========================
@app.route('/alumno')
def alumno():

    if not login_requerido():
        return redirect('/login')

    return render_template('alumno.html')


# =========================
# RESPONSABLES
# =========================
@app.route('/responsables')
def responsables():

    if not solo_responsable():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT * FROM Responsables")

    data = cur.fetchall()

    conn.close()

    return render_template(
        'responsables.html',
        responsables=data
    )


@app.route('/guardar_responsable', methods=['POST'])
def guardar_responsable():

    if not solo_responsable():
        return redirect('/login')

    nombre = request.form['nombre']
    cargo = request.form['cargo']

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO Responsables(nombre, cargo) VALUES (?, ?)",
        (nombre, cargo)
    )

    conn.commit()
    conn.close()

    return redirect('/responsables')


# =========================
# ELIMINAR RESPONSABLE
# =========================
@app.route('/eliminar_responsable/<int:id>')
def eliminar_responsable(id):

    if not solo_responsable():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM Responsables WHERE id_responsable=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/responsables')
# =========================
# EDITAR RESPONSABLE
# =========================
@app.route('/editar_responsable/<int:id>')
def editar_responsable(id):

    if not solo_responsable():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM Responsables WHERE id_responsable=?",
        (id,)
    )

    responsable = cur.fetchone()
    conn.close()

    if responsable:
        return render_template(
            'editar_responsable.html',
            r=responsable
        )

    return "Responsable no encontrado", 404


# =========================
# ACTUALIZAR RESPONSABLE
# =========================
@app.route('/actualizar_responsable', methods=['POST'])
def actualizar_responsable():

    if not solo_responsable():
        return redirect('/login')

    id_responsable = request.form['id_responsable']
    nombre = request.form['nombre']
    cargo = request.form['cargo']

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    UPDATE Responsables
    SET nombre=?,
        cargo=?
    WHERE id_responsable=?
    """, (
        nombre,
        cargo,
        id_responsable
    ))

    conn.commit()
    conn.close()

    return redirect('/responsables')


# =========================
# ACTIVIDADES
# =========================
@app.route('/actividades')
def actividades():

    if not login_requerido():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM Actividades")
    data = cur.fetchall()

    # 👇 ESTO ES LO ÚNICO NUEVO QUE AGREGAS AQUÍ:
    cur.execute("SELECT * FROM Responsables ORDER BY nombre ASC")
    lista_responsables = cur.fetchall()

    conn.close()

    return render_template(
        'actividades.html',
        actividades=data,
        responsables=lista_responsables  # <-- Y se lo pasas aquí
    )


@app.route('/guardar_actividad', methods=['POST'])
# =========================
# GUARDAR ACTIVIDAD
# =========================
@app.route('/guardar_actividad', methods=['POST'])
def guardar_actividad():

    if not solo_responsable():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    # 👇 REVISAR CUÁNTAS ACTIVIDADES YA EXISTEN
    cur.execute("SELECT COUNT(*) FROM Actividades")
    total_actividades = cur.fetchone()[0]

    # SI YA LLEGÓ AL LÍMITE (EJEMPLO: 10) NO DEJA REGISTRAR
    if total_actividades >= 10:
        conn.close()
        return "<h3>Error: Se ha alcanzado el límite máximo de 10 actividades en el sistema PEC.</h3><a href='/actividades'>Volver</a>"

    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    fecha = request.form['fecha']
    lugar = request.form['lugar']
    responsable = request.form['responsable']
    sede = request.form['sede']

    file = request.files.get('archivo')
    filename = ""

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    cur.execute("""
    INSERT INTO Actividades
    (nombre, descripcion, fecha, lugar, archivo, responsable, sede)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nombre, descripcion, fecha, lugar, filename, responsable, sede))

    conn.commit()
    conn.close()

    return redirect('/actividades')

# =========================
# EDITAR ACTIVIDAD
# =========================
@app.route('/editar_actividad/<int:id>')
def editar_actividad(id):

    if not solo_responsable():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM Actividades WHERE id_actividad=?",
        (id,)
    )

    actividad = cur.fetchone()

    conn.close()

    if actividad:

        return render_template(
            'editar_actividad.html',
            a=actividad
        )

    return "Actividad no encontrada"


# =========================
# ACTUALIZAR ACTIVIDAD
# =========================
@app.route('/actualizar_actividad', methods=['POST'])
def actualizar_actividad():

    if not solo_responsable():
        return redirect('/login')

    id_actividad = request.form['id_actividad']
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    fecha = request.form['fecha']
    lugar = request.form['lugar']
    responsable = request.form['responsable']
    sede = request.form['sede']

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    UPDATE Actividades
    SET nombre=?,
        descripcion=?,
        fecha=?,
        lugar=?,
        responsable=?,
        sede=?
    WHERE id_actividad=?
    """, (
        nombre,
        descripcion,
        fecha,
        lugar,
        responsable,
        sede,
        id_actividad
    ))

    conn.commit()
    conn.close()

    return redirect('/actividades')


# =========================
# ELIMINAR ACTIVIDAD
# =========================
@app.route('/eliminar_actividad/<int:id>')
def eliminar_actividad(id):

    if not solo_responsable():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM Actividades WHERE id_actividad=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/actividades')


## =========================
# EDITAR EVALUACIÓN
# =========================
@app.route('/editar_evaluacion/<int:id>')
def editar_evaluacion(id):

    if not solo_responsable():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM Evaluaciones WHERE id_evaluacion=?",
        (id,)
    )
    evaluacion = cur.fetchone()

    # 👇 ESTO ES LO NUEVO: Cargamos las actividades para que salgan en el select al editar
    cur.execute("SELECT id_actividad, nombre FROM Actividades ORDER BY id_actividad DESC")
    lista_actividades = cur.fetchall()

    conn.close()

    if evaluacion:
        return render_template(
            'editar_evaluacion.html',
            e=evaluacion,
            actividades=lista_actividades  # <-- Se lo pasas aquí también
        )

    return "Evaluación no encontrada", 404


# =========================
# ACTUALIZAR EVALUACIÓN
# =========================
@app.route('/actualizar_evaluacion', methods=['POST'])
def actualizar_evaluacion():

    if not solo_responsable():
        return redirect('/login')

    id_evaluacion = request.form['id_evaluacion']
    id_actividad = request.form['id_actividad']
    resultado = request.form['resultado']
    observaciones = request.form['observaciones']

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    UPDATE Evaluaciones
    SET id_actividad=?,
        resultado=?,
        observaciones=?
    WHERE id_evaluacion=?
    """, (
        id_actividad,
        resultado,
        observaciones,
        id_evaluacion
    ))

    conn.commit()
    conn.close()

    return redirect('/evaluaciones')

# =========================
# EVIDENCIAS (CON LÍMITE DE 5 POR ACTIVIDAD)
# =========================
@app.route('/evidencias')
def evidencias():

    if not login_requerido():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    # 👇 CAMBIO AQUÍ: Agregamos ORDER BY para que las últimas evidencias subidas aparezcan al principio
    cur.execute("SELECT * FROM Evidencias ORDER BY id_evidencia DESC")
    data = cur.fetchall()

    # Cargamos las actividades para que salgan en tu select del formulario
    cur.execute("SELECT id_actividad, nombre FROM Actividades ORDER BY id_actividad DESC")
    lista_actividades = cur.fetchall()

    conn.close()

    return render_template(
        'evidencias.html',
        evidencias=data,
        actividades=lista_actividades
    )


@app.route('/guardar_evidencia', methods=['POST'])
def guardar_evidencia():

    if not solo_responsable():
        return redirect('/login')

    id_actividad = request.form['id_actividad']
    descripcion = request.form['descripcion']

    conn = conectar()
    cur = conn.cursor()

    # VALIDACIÓN: Contamos cuántas evidencias ya tiene esta actividad específica
    cur.execute("SELECT COUNT(*) FROM Evidencias WHERE id_actividad = ?", (id_actividad,))
    total_evidencias_actividad = cur.fetchone()[0]

    # Si ya tiene 5 evidencias registradas, frena el proceso y avisa
    if total_evidencias_actividad >= 5:
        conn.close()
        return "<h3>Error: Esta actividad ya cuenta con el límite máximo de 5 evidencias permitidas.</h3><a href='/evidencias'>Volver</a>"

    file = request.files.get('archivo')
    filename = ""

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )

    cur.execute("""
    INSERT INTO Evidencias
    (descripcion, archivo, id_actividad)
    VALUES (?, ?, ?)
    """, (
        descripcion,
        filename,
        id_actividad
    ))

    conn.commit()
    conn.close()

    return redirect('/evidencias')
# =========================
# ELIMINAR EVIDENCIA
# =========================
@app.route('/eliminar_evidencia/<int:id>')
def eliminar_evidencia(id):

    if not solo_responsable():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    # Ejecuta el borrado usando el ID de la evidencia seleccionada
    cur.execute("DELETE FROM Evidencias WHERE id_evidencia=?", (id,))

    conn.commit()
    conn.close()

    return redirect('/evidencias')
# =========================
# EDITAR EVIDENCIA
# =========================
@app.route('/editar_evidencia/<int:id>')
def editar_evidencia(id):

    if not solo_responsable():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    # Buscamos la evidencia que queremos editar
    cur.execute("SELECT * FROM Evidencias WHERE id_evidencia=?", (id,))
    evidencia = cur.fetchone()

    # Cargamos también las actividades para el menú desplegable (select)
    cur.execute("SELECT id_actividad, nombre FROM Actividades ORDER BY id_actividad DESC")
    lista_actividades = cur.fetchall()

    conn.close()

    if evidencia:
        return render_template(
            'editar_evidencia.html',
            evidencia=evidencia,
            actividades=lista_actividades
        )

    return "Evidencia no encontrada", 404


# =========================
# ACTUALIZAR EVIDENCIA
# =========================
@app.route('/actualizar_evidencia', methods=['POST'])
def actualizar_evidencia():

    if not solo_responsable():
        return redirect('/login')

    id_evidencia = request.form['id_evidencia']
    id_actividad = request.form['id_actividad']
    descripcion = request.form['descripcion']

    conn = conectar()
    cur = conn.cursor()

    # Si suben un archivo nuevo, lo procesamos; si no, se queda el que ya estaba
    file = request.files.get('archivo')
    if file and file.filename != "":
        from werkzeug.utils import secure_filename
        import os
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Actualiza incluyendo el nuevo archivo
        cur.execute("""
        UPDATE Evidencias
        SET id_actividad=?, descripcion=?, archivo=?
        WHERE id_evidencia=?
        """, (id_actividad, descripcion, filename, id_evidencia))
    else:
        # Actualiza solo los textos si no cambiaron el archivo
        cur.execute("""
        UPDATE Evidencias
        SET id_actividad=?, descripcion=?
        WHERE id_evidencia=?
        """, (id_actividad, descripcion, id_evidencia))

    conn.commit()
    conn.close()

    return redirect('/evidencias')
# =========================
# EVALUACIONES (CON LÍMITE DE 1 POR ACTIVIDAD)
# =========================
@app.route('/evaluaciones')
def evaluaciones():

    if not login_requerido():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    # Traemos las evaluaciones registradas
    cur.execute("SELECT * FROM Evaluaciones")
    data = cur.fetchall()

    # También traemos las actividades para poder listarlas en el select del formulario
    cur.execute("SELECT id_actividad, nombre FROM Actividades ORDER BY id_actividad DESC")
    lista_actividades = cur.fetchall()

    conn.close()

    return render_template(
        'evaluaciones.html',
        evaluaciones=data,
        actividades=lista_actividades
    )


@app.route('/guardar_evaluacion', methods=['POST'])
def guardar_evaluacion():

    if not solo_responsable():
        return redirect('/login')

    id_actividad = request.form['id_actividad']
    resultado = request.form['resultado']
    observaciones = request.form['observaciones']

    conn = conectar()
    cur = conn.cursor()

    # 👇 NUEVA VALIDACIÓN: Contamos si esta actividad ya fue evaluada
    cur.execute("SELECT COUNT(*) FROM Evaluaciones WHERE id_actividad = ?", (id_actividad,))
    ya_evaluada = cur.fetchone()[0]

    # Si ya tiene una evaluación, no permite duplicarla
    if ya_evaluada >= 1:
        conn.close()
        return "<h3>Error: Esta actividad ya ha sido evaluada previamente. Solo se permite una evaluación por actividad.</h3><a href='/evaluaciones'>Volver</a>"

    cur.execute("""
    INSERT INTO Evaluaciones (id_actividad, resultado, observaciones)
    VALUES (?, ?, ?)
    """, (id_actividad, resultado, observaciones))

    conn.commit()
    conn.close()

    return redirect('/evaluaciones')

# =========================
# ELIMINAR EVALUACIÓN
# =========================
@app.route('/eliminar_evaluacion/<int:id>')
def eliminar_evaluacion(id):

    if not solo_responsable():
        return redirect('/login')

    conn = conectar()
    cur = conn.cursor()

    cur.execute("DELETE FROM Evaluaciones WHERE id_evaluacion=?", (id,))

    conn.commit()
    conn.close()

if __name__ == "__main__":

    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    inicializar_base_datos()

    # LEER EL PUERTO ASIGNADO POR RENDER O USAR EL 5000 POR DEFECTO
    port = int(os.environ.get("PORT", 5000))
    
    # ESCUCHAR EN 0.0.0.0 Y EN EL PUERTO CORRECTO
    app.run(host="0.0.0.0", port=port, debug=False)