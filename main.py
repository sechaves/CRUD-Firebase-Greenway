import sys
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
from data.firebase_config import auth, db
from data.firebase_admin import admin_auth
from domain.models import Usuario, Propietaria, Admin, Persona

# --- Inicialización del Chatbot (Opcional) ---
try:
    from domain.openai_chatbot import GreenwayChatbot
    chatbot_importado = True
except ImportError:
    print("Advertencia: No se encontró 'openai_chatbot'. El bot estará desactivado.")
    chatbot_importado = False
except Exception as e:
    print(f"Advertencia: Error al importar chatbot: {e}. El bot estará desactivado.")
    chatbot_importado = False

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = "clave_secreta" 

chatbot = None
if chatbot_importado:
    try:
        chatbot = GreenwayChatbot()
        print("Chatbot de OpenAI inicializado con éxito.")
    except ValueError as e:
        print(f"Error al inicializar el chatbot: {e}")
    except Exception as e:
        print(f"Error inesperado al inicializar el chatbot: {e}")

# --- Control de Caché ---
@app.after_request
def prevent_caching(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# --- Decoradores ---
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
                return f(*args, **kwargs)
            if session['role'] != role_name:
                flash(f'Esta página es solo para rol: {role_name}.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return wrapper_role
    return decorator

# --- Rutas de Auth ---
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
    email = request.form['email']
    password = request.form['password']
    nombre = request.form['nombre']
    # telefono = request.form['telefono'] # Asegúrate si tu form tiene telefono o no
    rol_elegido = request.form.get('rol')

    if not rol_elegido:
        flash('Debes seleccionar un tipo de cuenta.', 'danger')
        return redirect(url_for('register'))

    try:
        user_auth_data = auth.create_user_with_email_and_password(email, password)
        user_id = user_auth_data['localId']

        nuevo_usuario = None
        if rol_elegido == 'usuario':
            # Ajusta según los argumentos de tu constructor Usuario
            nuevo_usuario = Usuario(user_id, nombre, email) 
        elif rol_elegido == 'propietaria':
            nuevo_usuario = Propietaria(user_id, nombre, email)

        if nuevo_usuario:
            nuevo_usuario.save_to_db(db)
            if admin_auth:
                admin_auth.set_custom_user_claims(user_id, {'role': nuevo_usuario.rol})

        user_session = auth.sign_in_with_email_and_password(email, password)
        session['user_email'] = user_session['email']
        session['user_id'] = user_session['localId']
        session['role'] = nuevo_usuario.rol 
        
        flash(f'¡Bienvenido, {nombre}! Tu cuenta ha sido creada.', 'success')
        return redirect(url_for('home'))

    except Exception as e:
        error_message = str(e)
        if "EMAIL_EXISTS" in error_message:
            flash('El correo electrónico ya está en uso.', 'danger')
        elif "WEAK_PASSWORD" in error_message:
            flash('La contraseña es muy débil.', 'danger')
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
        session['role'] = decoded_token.get('role', 'usuario')
        
        flash(f'Bienvenido de nuevo. Rol: {session["role"]}', 'info')
        return redirect(url_for('home'))
        
    except Exception as e:
        flash('Credenciales incorrectas.', 'danger')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login'))

# --- Rutas App ---

@app.route('/home')
@login_required
def home():
    try:
        all_experiencias_data = db.child("experiencias").get().val() or {}
        experiencias_list = []
        if all_experiencias_data:
            for experiencia_id, experiencia_info in all_experiencias_data.items():
                experiencia_info['id'] = experiencia_id
                experiencias_list.append(experiencia_info)
        return render_template('home.html', session=session, experiencias=experiencias_list)
    except Exception as e:
        return render_template('home.html', session=session, experiencias=[])

@app.route('/experiencias')
@login_required
def experiencias():
    try:
        all_experiencias_data = db.child("experiencias").get().val() or {}
        experiencias_list = []
        if all_experiencias_data:
            for experiencia_id, experiencia_info in all_experiencias_data.items():
                experiencia_info['id'] = experiencia_id
                experiencias_list.append(experiencia_info)
        return render_template('experiencias.html', session=session, experiencias=experiencias_list)
    except Exception as e:
        flash(f'Error al cargar las experiencias: {e}', 'danger')
        return redirect(url_for('home'))

# --- CHAT (Lógica Simplificada) ---
def build_room_id(user_a: str, user_b: str, exp_id: str) -> str:
    # Ordenamos los IDs para que A->B y B->A sea el mismo chat
    a, b = sorted([user_a, user_b])
    return f"chat_{exp_id}_{a}_{b}"

@app.route('/chats')
@login_required
def chats():
    """
    Solo carga la página HTML. Toda la lógica de tiempo real va en JS.
    """
    owner_id = request.args.get('owner_id')
    exp_id = request.args.get('exp_id')
    # initial_text = request.args.get('initial_text', '') # Lo manejaremos en JS si quieres

    user_id = session.get('user_id')
    room_id = None

    if owner_id and exp_id and user_id:
        room_id = build_room_id(user_id, owner_id, exp_id)

    # NO cargamos mensajes aquí. El JS los cargará de Firebase directamente.
    return render_template('chats.html',
                           session=session,
                           room_id=room_id,
                           owner_id=owner_id,
                           exp_id=exp_id)

# --- Rutas CRUD / Admin (Iguales que antes) ---
@app.route('/crear-experiencia')
@login_required
@role_required('propietaria')
def crear_experiencia_form():
    return render_template('crear_experiencia.html', session=session)

@app.route('/crear-experiencia-submit', methods=['POST'])
@login_required
@role_required('propietaria')
def crear_experiencia_submit():
    try:
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio_noche = request.form['precio']
        propietario_id = session['user_id']
        
        # Lecturas opcionales segun tu form
        lista_de_imagenes = request.form.getlist('imagen_url') 
        maps_embed_url = request.form.get('maps_embed_url', '')

        experiencia_data = {
            'nombre': nombre,
            'descripcion': descripcion,
            'precio_noche': int(precio_noche),
            'propietario_id': propietario_id,
            'imagenes': lista_de_imagenes,
            'maps_embed_url': maps_embed_url
        }

        nuevo_experiencia = db.child("experiencias").push(experiencia_data)
        flash('¡Experiencia registrada con éxito!', 'success')
        return redirect(url_for('experiencia_detalle', experiencia_id=nuevo_experiencia['name']))

    except Exception as e:
        flash(f'Error al crear la experiencia: {e}', 'danger')
        return redirect(url_for('crear_experiencia_form'))

@app.route('/experiencia/<experiencia_id>')
@login_required
def experiencia_detalle(experiencia_id):
    try:
        experiencia_data = db.child("experiencias").child(experiencia_id).get().val()
        if not experiencia_data:
            flash('Esa experiencia no existe.', 'danger')
            return redirect(url_for('home'))
        return render_template('experiencia_detalle.html', 
                               session=session, 
                               experiencia=experiencia_data,
                               experiencia_id=experiencia_id) 
    except Exception as e:
        flash(f'Error al cargar: {e}', 'danger')
        return redirect(url_for('home'))

@app.route('/admin-panel')
@login_required
@role_required('admin')
def admin_panel():
    try:
        all_admins = db.child("admins").get().val() or {}
        all_propietarios = db.child("propietarios").get().val() or {}
        all_usuarios = db.child("usuarios").get().val() or {}
        all_experiencias = db.child("experiencias").get().val() or {} 
        return render_template('admin_panel.html', session=session, 
                               admins=all_admins, propietarios=all_propietarios, 
                               usuarios=all_usuarios, experiencias=all_experiencias)
    except:
        return redirect(url_for('home'))

# Rutas de eliminar/editar (resumidas para no llenar)
# ... Tus rutas admin_delete, admin_edit, update ...

# --- Main ---
if __name__ == '__main__':
    if admin_auth is None:
        print("Error crítico: No se pudo inicializar el SDK Admin.")
    else:
        print("*** Servidor Flask (Sin Sockets) LISTO ***")
        app.run(debug=True, port=5000)