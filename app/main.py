import sys
import os
from functools import wraps
# Asegúrate de que todas las importaciones de Flask estén aquí
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify 

# --- Añadir el proyecto raíz al path ---
# Esto le dice a Python dónde encontrar la carpeta 'data' y 'domain'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
# -----------------------------------------------------------------

# SDKs de Firebase (Cliente y Admin)
from data.firebase_config import auth, db
from data.firebase_admin import admin_auth

# --- ¡Importa el cerebro de OpenAI! ---
from domain.openai_chatbot import GreenwayChatbot
# -----------------------------------------------

app = Flask(__name__)
app.secret_key = "clave_secreta" 

# --- ¡Inicializa el chatbot UNA SOLA VEZ cuando arranca la app! ---
try:
    chatbot = GreenwayChatbot()
    print("Chatbot de OpenAI inicializado con éxito.")
except ValueError as e:
    print(f"Error al inicializar el chatbot: {e}")
    print("Asegúrate de que tu archivo .env está en la raíz del proyecto.")
    chatbot = None # El bot no funcionará, pero la app arrancará
# -------------------------------------------------------------------

# =================================================================
# FUNCIÓN ANTI-CACHÉ
# =================================================================
@app.after_request
def prevent_caching(response: Response) -> Response:
    """
    Le dice al navegador que NO guarde ninguna página en caché.
    Resuelve el bug de la "flecha atrás" después de cerrar sesión.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# =================================================================
# DECORADORES DE AUTENTICACIÓN
# =================================================================

def login_required(f):
    """
    Decorador para rutas que REQUIEREN que el usuario esté logueado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para ver esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def anonymous_required(f):
    """
    Decorador para rutas que NO deben verse si el usuario YA está logueado.
    (Ej: /login, /register)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session: 
            return redirect(url_for('home')) 
        return f(*args, **kwargs)
    return decorated_function

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
    email = request.form['email']
    password = request.form['password']
    nombre = request.form['nombre']

    try:
        # 1. Crear usuario en Auth
        user = auth.create_user_with_email_and_password(email, password)
        user_id = user['localId']
        
        # 2. Guardar datos en Realtime DB
        db.child("usuarios").child(user_id).set({"nombre": nombre, "email": email})
        
        # 3. Asignar ROL "usuario" por defecto
        if admin_auth:
            admin_auth.set_custom_user_claims(user_id, {'role': 'usuario'})
        
        # 4. Iniciar sesión automáticamente
        user_session = auth.sign_in_with_email_and_password(email, password)
        session['user_email'] = user_session['email']
        session['user_id'] = user_session['localId']
        session['role'] = 'usuario' # Le damos el rol por defecto en la sesión
        
        # 5. Notificación de éxito
        flash(f'¡Bienvenido, {nombre}! Tu cuenta ha sido creada.', 'success')
        return redirect(url_for('home'))

    except Exception as e:
        error_message = str(e)
        if "EMAIL_EXISTS" in error_message:
            flash('El correo electrónico ya está en uso.', 'danger')
        elif "WEAK_PASSWORD" in error_message:
            flash('La contraseña es muy débil. Debe tener al menos 6 caracteres.', 'danger')
        else:
            flash(f'Error al crear la cuenta. {e}', 'danger')
        return redirect(url_for('register'))


@app.route('/signin', methods=['POST'])
@anonymous_required
def signin():
    email = request.form['email']
    password = request.form['password']
    
    try:
        # 1. Inicia sesión
        user = auth.sign_in_with_email_and_password(email, password)
        
        # 2. Obtener el token para leer los ROLES (Claims)
        id_token = user['idToken']
        decoded_token = admin_auth.verify_id_token(id_token)
        
        # 3. Guarda datos en la sesión
        session['user_email'] = user['email']
        session['user_id'] = user['localId']
        session['role'] = decoded_token.get('role', 'usuario') # Lee el rol (o 'usuario' si no hay)
        
        # 4. Notificación de éxito
        flash(f'Bienvenido de nuevo. Rol: {session["role"]}', 'info')
        return redirect(url_for('home'))
        
    except Exception as e:
        flash('Credenciales incorrectas. Por favor, inténtalo de nuevo.', 'danger')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear() # Limpia toda la sesión
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login'))

# --- Rutas de Reseteo de Contraseña ---

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
        flash('¡Correo enviado! Revisa tu bandeja de entrada (y spam) para el enlace de reseteo.', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash('Error al enviar el correo. ¿Estás seguro de que el email es correcto?', 'danger')
        return redirect(url_for('reset_password'))

# =================================================================
# RUTAS DE APLICACIÓN (PÁGINAS "DE ADENTRO")
# =================================================================

@app.route('/home')
@login_required
def home():
    return render_template('home.html', session=session)
    
@app.route('/profile')
@login_required
def profile():
    try:
        user_id = session['user_id']
        user_data = db.child("usuarios").child(user_id).get().val()
        
        if not user_data:
            flash('No se pudieron cargar los datos del usuario.', 'danger')
            return redirect(url_for('home'))
            
        # Pasamos 'user_data' como 'user' a la plantilla
        return render_template('profile.html', user=user_data, session=session)
    
    except Exception as e:
        flash(f'Error al cargar perfil: {e}', 'danger')
        return redirect(url_for('home'))

@app.route('/settings')
@login_required
def settings():
    # Vamos a fusionar settings con profile, así que redirigimos
    return redirect(url_for('profile'))


@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """
    Actualiza el nombre del usuario en la Realtime Database.
    """
    try:
        user_id = session['user_id']
        nuevo_nombre = request.form['nombre']
        
        if not nuevo_nombre or len(nuevo_nombre.strip()) == 0:
            flash('El nombre no puede estar vacío.', 'danger')
            return redirect(url_for('profile'))

        db.child("usuarios").child(user_id).update({"nombre": nuevo_nombre.strip()})
        
        flash('Tu nombre ha sido actualizado con éxito.', 'success')
    except Exception as e:
        flash(f'Error al actualizar el perfil: {e}', 'danger')
    
    return redirect(url_for('profile'))


@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """
    Elimina al usuario de Authentication Y de la Realtime Database.
    """
    try:
        user_id = session['user_id']
        
        # 1. Eliminar de Firebase Authentication (SDK Admin)
        admin_auth.delete_user(user_id)
        
        # 2. Eliminar de Realtime Database (SDK Cliente)
        db.child("usuarios").child(user_id).remove()
        
        # 3. Limpiar la sesión (hacer logout)
        session.clear()
        
        flash('Tu cuenta ha sido eliminada permanentemente.', 'success')
        return redirect(url_for('login')) # Mandar al login
        
    except Exception as e:
        flash(f'Error al eliminar tu cuenta: {e}', 'danger')
        return redirect(url_for('profile')) # Devolver al perfil si algo falla

# =================================================================
# RUTA DEL CHATBOT
# =================================================================

@app.route('/ask-chatbot', methods=['POST'])
@login_required
def ask_chatbot():
    """
    Recibe una pregunta del usuario, la procesa con OpenAI
    y devuelve una respuesta JSON.
    """
    if chatbot is None:
        return jsonify({'error': 'El chatbot no está configurado correctamente (falta API Key).'}), 500

    try:
        data = request.get_json()
        pregunta = data.get('pregunta')
        if not pregunta:
            return jsonify({'error': 'No se recibió ninguna pregunta.'}), 400

        # --- ¡Aquí usamos el cerebro de OpenAI! ---
        respuesta = chatbot.ask(pregunta)
        # -------------------------------------------
        
        return jsonify({'respuesta': respuesta})

    except Exception as e:
        print(f"Error en el chatbot: {e}")
        return jsonify({'error': 'Hubo un error interno al procesar tu pregunta.'}), 500

# =================================================================
# INICIO DE LA APP
# =================================================================

if __name__ == '__main__':
    # Verificaciones de arranque
    if admin_auth is None:
        print("Error crítico: No se pudo inicializar el SDK de Admin de Firebase.")
        print("La aplicación no puede arrancar sin 'serviceAccountKey.json'.")
    elif chatbot is None:
        print("Error crítico: No se pudo inicializar el Chatbot de OpenAI.")
        print("La aplicación no puede arrancar sin una API Key en el archivo .env.")
    else:
        # Solo si todo está bien, corre la app
        app.run(debug=True, port=5000)

