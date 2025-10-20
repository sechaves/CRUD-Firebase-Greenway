from flask import Flask, render_template, request, redirect, url_for, session
from data.firebase_config import auth, db

app = Flask(__name__)
app.secret_key = "clave_secreta"

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']
    nombre = request.form['nombre']

    try:
        user = auth.create_user_with_email_and_password(email, password)
        db.child("usuarios").child(user['localId']).set({"nombre": nombre, "email": email})
        return redirect(url_for('login'))
    except Exception as e:
        return f"Error creando usuario: {e}"

@app.route('/signin', methods=['POST'])
def signin():
    email = request.form['email']
    password = request.form['password']
    try:
        # 1. Inicia sesión
        user = auth.sign_in_with_email_and_password(email, password)
        
        # 2. Guarda AMBOS datos en la sesión
        session['user_email'] = user['email']
        session['user_id'] = user['localId'] # <--- ¡LA CLAVE QUE FALTABA!
        
        return redirect(url_for('home'))
    except:
        return "Credenciales incorrectas"

@app.route('/home')
def home():
    if 'user_email' in session: # <--- Comprueba la nueva clave
        # Pasa el email a la plantilla (tu home.html ya lo usa)
        return render_template('home.html', session=session)
    else:
        return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    session.pop('user_email', None) # Limpia la nueva clave
    session.pop('user_id', None)    # Limpia la nueva clave
    session.pop('user', None)       # Limpia la clave antigua por si acaso
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    # 1. Comprueba si el usuario está logueado
    if 'user_email' not in session:
        return redirect(url_for('login')) # <--- ¡ARREGLADO EL BUCLE!
    
    # 2. Si está logueado, ahora sí podemos buscar sus datos
    try:
        user_id = session['user_id'] # Ahora sí existe
        user_data = db.child("usuarios").child(user_id).get().val()
        
        if not user_data:
             return redirect(url_for('logout'))
             
        return render_template('profile.html', user=user_data, session=session)
    except Exception as e:
        print(f"Error al cargar perfil: {e}")
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
