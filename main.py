import sys
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify 

# SDKs de Firebase (Cliente y Admin)
from data.firebase_config import auth, db
from data.firebase_admin import admin_auth

# --- Importa el Model (POO) y el Chatbot (POO) ---
from domain.models import Usuario, Propietaria, Admin, Persona
try:
    from domain.openai_chatbot import GreenwayChatbot
    chatbot_importado = True
except ImportError:
    print("Advertencia: No se encontró 'openai_chatbot'. El bot estará desactivado.")
    chatbot_importado = False
except Exception as e:
    print(f"Advertencia: Error al importar chatbot: {e}. El bot estará desactivado.")
    chatbot_importado = False
# -----------------------------------------------

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = "clave_secreta" 

# --- Inicializa el chatbot ---
chatbot = None
if chatbot_importado:
    try:
        chatbot = GreenwayChatbot()
        print("Chatbot de OpenAI inicializado con éxito.")
    except ValueError as e:
        print(f"Error al inicializar el chatbot: {e}")
    except Exception as e:
        print(f"Error inesperado al inicializar el chatbot: {e}")
# -------------------------------------------------------------------

# =================================================================
# FUNCIÓN ANTI-CACHÉ
# =================================================================
@app.after_request
def prevent_caching(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# =================================================================
# DECORADORES DE AUTENTICACIÓN
# =================================================================

def login_required(f):
    @wraps(f)
    def wrapper_login(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para ver esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper_login

def anonymous_required(f):
    @wraps(f)
    def wrapper_anon(*args, **kwargs):
        if 'user_id' in session: 
            return redirect(url_for('home')) 
        return f(*args, **kwargs)
    return wrapper_anon

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def wrapper_role(*args, **kwargs):
            if 'role' not in session:
                flash('No tienes permiso para ver esta página.', 'danger')
                return redirect(url_for('home'))
            
            if session['role'] == 'admin':
                return f(*args, **kwargs) # Admin puede ver todo

            if session['role'] != role_name:
                flash(f'Esta página es solo para rol: {role_name}.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return wrapper_role
    return decorator

# =================================================================
# RUTAS DE AUTENTICACIÓN (PÁGINAS "DE AFUERA")
# =================================================================

@app.route('/')
@anonymous_required
def login():
    return render_template('login.html')

@app.route('/register')
@anonymous_required
def register():
    return render_template('register.html')

@app.route('/signup', methods=['POST'])
@anonymous_required
def signup():
    """
    Ruta de registro actualizada con lógica POO.
    Lee el botón de radio y crea la instancia de clase correcta.
    """
    email = request.form['email']
    password = request.form['password']
    nombre = request.form['nombre']
    # ¡NUEVO! Lee el rol del botón de radio
    rol_elegido = request.form.get('rol') # 'usuario' o 'propietaria'

    if not rol_elegido:
        flash('Debes seleccionar un tipo de cuenta.', 'danger')
        return redirect(url_for('register'))

    try:
        # 1. Crear usuario en Firebase Authentication (común para todos)
        user_auth_data = auth.create_user_with_email_and_password(email, password)
        user_id = user_auth_data['localId']
        
        # 2. Lógica POO: Instanciar la clase correcta
        nuevo_usuario = None
        if rol_elegido == 'usuario':
            nuevo_usuario = Usuario(user_id, nombre, email)
        elif rol_elegido == 'propietaria':
            nuevo_usuario = Propietaria(user_id, nombre, email)
        
        if nuevo_usuario:
            # 3. Guardar en el nodo correcto de la DB (usuarios/ o propietarios/)
            nuevo_usuario.save_to_db(db)
            
            # 4. Asignar el Custom Claim (Rol) para la seguridad
            if admin_auth:
                admin_auth.set_custom_user_claims(user_id, {'role': nuevo_usuario.rol})
        
        # 5. Iniciar sesión automáticamente
        user_session = auth.sign_in_with_email_and_password(email, password)
        session['user_email'] = user_session['email']
        session['user_id'] = user_session['localId']
        session['role'] = nuevo_usuario.rol # Asigna el rol elegido a la sesión
        
        # 6. Notificación de éxito
        flash(f'¡Bienvenido, {nombre}! Tu cuenta de {nuevo_usuario.rol} ha sido creada.', 'success')
        return redirect(url_for('home'))

    except Exception as e:
        error_message = str(e)
        if "EMAIL_EXISTS" in error_message:
            flash('El correo electrónico ya está en uso.', 'danger')
        elif "WEAK_PASSWORD" in error_message:
            flash('La contraseña es muy débil. Debe tener al menos 6 caracteres.', 'danger')
        else:
            flash(f'Error al crear la cuenta: {e}', 'danger')
        return redirect(url_for('register'))


@app.route('/signin', methods=['POST'])
@anonymous_required
def signin():
    email = request.form['email']
    password = request.form['password']
    
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        id_token = user['idToken']
        decoded_token = admin_auth.verify_id_token(id_token)
        
        session['user_email'] = user['email']
        session['user_id'] = user['localId']
        session['role'] = decoded_token.get('role', 'usuario') # Rol de los Claims
        
        flash(f'Bienvenido de nuevo. Rol: {session["role"]}', 'info')
        return redirect(url_for('home'))
        
    except Exception as e:
        flash('Credenciales incorrectas. Por favor, inténtalo de nuevo.', 'danger')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login'))

@app.route('/reset-password')
@anonymous_required
def reset_password():
    return render_template('reset_password.html')

@app.route('/reset-password-request', methods=['POST'])
@anonymous_required
def reset_password_request():
    email = request.form['email']
    try:
        auth.send_password_reset_email(email)
        flash('¡Correo enviado! Revisa tu bandeja de entrada (y spam).', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash('Error al enviar el correo. ¿Email correcto?', 'danger')
        return redirect(url_for('reset_password'))

# =================================================================
# RUTAS DE APLICACIÓN (PÁGINAS "DE ADENTRO")
# =================================================================

@app.route('/home')
@login_required
def home():
    try:
        all_hospedajes_data = db.child("hospedajes").get().val()
        hospedajes_list = []
        if all_hospedajes_data:
            for lugar_id, lugar_info in all_hospedajes_data.items():
                lugar_info['id'] = lugar_id
                hospedajes_list.append(lugar_info)
        
        return render_template('home.html', session=session, hospedajes=hospedajes_list)
    except Exception as e:
        print(f"Error cargando hospedajes para home: {e}")
        return render_template('home.html', session=session, hospedajes=[])

@app.route('/alojamientos')
@login_required
def alojamientos():
    try:
        all_hospedajes_data = db.child("hospedajes").get().val()
        hospedajes_list = []
        if all_hospedajes_data:
            for lugar_id, lugar_info in all_hospedajes_data.items():
                lugar_info['id'] = lugar_id
                hospedajes_list.append(lugar_info)
        
        return render_template('alojamientos.html', session=session, hospedajes=hospedajes_list)
    except Exception as e:
        flash(f'Error al cargar los alojamientos: {e}', 'danger')
        return redirect(url_for('home'))
    
@app.route('/profile')
@login_required
def profile():
    """
    Ruta de perfil actualizada con lógica POO.
    Busca al usuario en el nodo correcto ('usuarios', 'propietarios', 'admins')
    usando el rol guardado en la sesión.
    """
    try:
        user_id = session['user_id']
        user_rol = session['role']
        
        # Usamos la clase Persona para encontrar al usuario en el nodo correcto
        user_data = Persona.get_user_data_by_role(db, user_rol, user_id)
        
        if not user_data:
            flash('No se pudieron cargar los datos del usuario.', 'danger')
            return redirect(url_for('home'))
                
        return render_template('profile.html', user=user_data, session=session)
    
    except Exception as e:
        flash(f'Error al cargar perfil: {e}', 'danger')
        return redirect(url_for('home'))

@app.route('/settings')
@login_required
def settings():
    return redirect(url_for('profile'))


@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """
    Actualiza el perfil del usuario en el nodo correcto.
    """
    try:
        user_id = session['user_id']
        user_rol = session['role']
        nuevo_nombre = request.form['nombre']
        
        if not nuevo_nombre or len(nuevo_nombre.strip()) == 0:
            flash('El nombre no puede estar vacío.', 'danger')
            return redirect(url_for('profile'))

        # Lógica POO: Usamos el método estático para saber dónde guardar
        nodo_db = Persona.get_db_node_by_role(user_rol)
        db.child(nodo_db).child(user_id).update({"nombre": nuevo_nombre.strip()})
        
        flash('Tu nombre ha sido actualizado con éxito.', 'success')
    except Exception as e:
        flash(f'Error al actualizar el perfil: {e}', 'danger')
    
    return redirect(url_for('profile'))


@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """
    Elimina al usuario de Auth y de su nodo correspondiente en la DB.
    """
    try:
        user_id = session['user_id']
        user_rol = session['role']
        
        # 1. Eliminar de Firebase Authentication (SDK Admin)
        admin_auth.delete_user(user_id)
        
        # 2. Eliminar del nodo correcto en Realtime Database (POO)
        nodo_db = Persona.get_db_node_by_role(user_rol)
        db.child(nodo_db).child(user_id).remove()
        
        # 3. Limpiar la sesión (hacer logout)
        session.clear()
        
        flash('Tu cuenta ha sido eliminada permanentemente.', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        flash(f'Error al eliminar tu cuenta: {e}', 'danger')
        return redirect(url_for('profile'))


# --- Rutas de Admin y Propietario ---

@app.route('/admin-panel')
@login_required
@role_required('admin')
def admin_panel():
    """
    Ruta de admin actualizada con lógica POO.
    Trae los datos de los 3 nodos separados.
    """
    try:
        all_admins = db.child("admins").get().val() or {}
        all_propietarios = db.child("propietarios").get().val() or {}
        all_usuarios = db.child("usuarios").get().val() or {}
        
        return render_template('admin_panel.html', 
                               session=session, 
                               admins=all_admins,
                               propietarios=all_propietarios,
                               usuarios=all_usuarios)
    except Exception as e:
        flash(f'Error al cargar el panel de admin: {e}', 'danger')
        return redirect(url_for('home'))


@app.route('/crear-lugar')
@login_required
@role_required('propietaria')
def crear_lugar_form():
    return render_template('crear_lugar.html', session=session)


@app.route('/crear-lugar-submit', methods=['POST'])
@login_required
@role_required('propietaria')
def crear_lugar_submit():
    try:
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio_noche = request.form['precio']
        propietario_id = session['user_id']
        
        placeholder_img = "https://cf.bstatic.com/xdata/images/hotel/max1024x768/658391731.jpg?k=8a8c5a5fe9ce371b31ecbf4e8db05f2a3d1fde897d80338c9e8a758980d8521d&o=&hp=1"

        lugar_data = {
            'nombre': nombre,
            'descripcion': descripcion,
            'precio_noche': int(precio_noche),
            'propietario_id': propietario_id,
            'imagen_url': placeholder_img
        }
        
        nuevo_lugar = db.child("hospedajes").push(lugar_data)
        
        flash('¡Lugar registrado con éxito!', 'success')
        return redirect(url_for('lugar_detalle', lugar_id=nuevo_lugar['name']))
        
    except Exception as e:
        flash(f'Error al crear el lugar: {e}', 'danger')
        return redirect(url_for('crear_lugar_form'))


@app.route('/lugar/<lugar_id>')
@login_required
def lugar_detalle(lugar_id):
    try:
        lugar_data = db.child("hospedajes").child(lugar_id).get().val()
        
        if not lugar_data:
            flash('Ese lugar no existe.', 'danger')
            return redirect(url_for('home'))
            
        return render_template('lugar_detalle.html', session=session, lugar=lugar_data)
        
    except Exception as e:
        flash(f'Error al cargar el lugar: {e}', 'danger')
        return redirect(url_for('home'))

# =================================================================
# RUTA DEL CHATBOT
# =================================================================

@app.route('/ask-chatbot', methods=['POST'])
@login_required
def ask_chatbot():
    if chatbot is None:
        return jsonify({'error': 'El chatbot no está configurado (API Key).'}), 500

    try:
        data = request.get_json()
        pregunta = data.get('pregunta')
        if not pregunta:
            return jsonify({'error': 'No se recibió ninguna pregunta.'}), 400

        respuesta = chatbot.ask(pregunta)
        
        return jsonify({'respuesta': respuesta})

    except Exception as e:
        print(f"Error en el chatbot: {e}")
        return jsonify({'error': 'Error interno al procesar tu pregunta.'}), 500

# =================================================================
# INICIO DE LA APP
# =================================================================

if __name__ == '__main__':
    # Verificaciones de arranque
    if admin_auth is None:
        print("Error crítico: No se pudo inicializar el SDK de Admin (serviceAccountKey.json).")
    elif chatbot is None and chatbot_importado:
        print("Error crítico: No se pudo inicializar el Chatbot (API Key .env).")
    else:
        print("************************************")
        print("SDK de Admin de Firebase inicializado con éxito.")
        if chatbot_importado: print("Chatbot de OpenAI inicializado con éxito.")
        print("*** Servidor Flask v3.0 (POO) LISTO ***")
        print("************************************")
        app.run(debug=True, port=5000)

