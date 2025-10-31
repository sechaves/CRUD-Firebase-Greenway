class Persona:
    """
    Superclase para todos los tipos de usuarios.
    Define los atributos y métodos comunes.
    """
    def __init__(self, user_id: str, nombre: str, email: str):
        if not all([user_id, nombre, email]):
            raise ValueError("ID, nombre y email no pueden estar vacíos")
        
        self.user_id = user_id
        self.nombre = nombre
        self.email = email
        self.rol = "persona" # Rol base
        self.db_node = "personas" # Nodo base

    def to_dict(self) -> dict:
        """Convierte la instancia en un diccionario para guardarlo en Firebase."""
        return {
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol
        }

    def save_to_db(self, db):
        """
        Guarda la instancia en el nodo de la base de datos que le corresponde.
        """
        try:
            print(f"Guardando en: {self.db_node}/{self.user_id}")
            db.child(self.db_node).child(self.user_id).set(self.to_dict())
        except Exception as e:
            print(f"Error al guardar en la DB: {e}")
            raise

    @staticmethod
    def get_db_node_by_role(rol: str) -> str:
        """Método estático para saber en qué nodo buscar según el rol."""
        if rol == 'admin':
            return 'admins'
        elif rol == 'propietaria':
            return 'propietarios'
        else:
            return 'usuarios'

    @staticmethod
    def get_user_data_by_role(db, rol: str, user_id: str) -> dict:
        """
        Método estático para obtener los datos de un usuario
        buscando en el nodo correcto.
        """
        nodo = Persona.get_db_node_by_role(rol)
        try:
            return db.child(nodo).child(user_id).get().val()
        except Exception as e:
            print(f"Error al obtener datos del usuario {user_id} en {nodo}: {e}")
            return None


class Usuario(Persona):
    """
    Subclase para Usuarios normales.
    Hereda de Persona y define su rol y nodo de DB.
    """
    def __init__(self, user_id: str, nombre: str, email: str):
        super().__init__(user_id, nombre, email)
        self.rol = "usuario"
        self.db_node = "usuarios"


class Propietaria(Persona):
    """
    Subclase para Propietarios.
    Hereda de Persona y define su rol y nodo de DB.
    """
    def __init__(self, user_id: str, nombre: str, email: str):
        super().__init__(user_id, nombre, email)
        self.rol = "propietaria"
        self.db_node = "propietarios"


class Admin(Persona):
    """
    Subclase para Administradores.
    Hereda de Persona y define su rol y nodo de DB.
    """
    def __init__(self, user_id: str, nombre: str, email: str):
        super().__init__(user_id, nombre, email)
        self.rol = "admin"
        self.db_node = "admins"

