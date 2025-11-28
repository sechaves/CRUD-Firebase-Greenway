class Persona:
    def __init__(self, user_id: str, nombre: str, email: str, telefono: str = ""):
        # Validación básica (El teléfono puede ser opcional al inicio, por eso el default "")
        if not all([user_id, nombre, email]):
            raise ValueError("ID, nombre y email no pueden estar vacíos")

        self.user_id = user_id
        self.nombre = nombre
        self.email = email
        self.telefono = telefono
        self.foto_url = ""  # ¡Campo nuevo para la foto de perfil!
        
        # Valores por defecto (se sobreescriben en las clases hijas)
        self.rol = "persona"
        self.db_node = "personas"

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "email": self.email,
            "telefono": self.telefono,
            "rol": self.rol,
            "foto_url": self.foto_url # Guardamos la foto también
        }

    def save_to_db(self, db):
        """
        Guarda la instancia en el nodo de la base de datos que le corresponde.
        """
        try:
            # print(f"Guardando en: {self.db_node}/{self.user_id}") # Debug opcional
            db.child(self.db_node).child(self.user_id).set(self.to_dict())
            return True
        except Exception as e:
            print(f"Error al guardar en la DB: {e}")
            return False # Retornamos False si falla

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


# --- CLASES HIJAS ---

class Usuario(Persona):
    def __init__(self, user_id: str, nombre: str, email: str, telefono: str = ""):
        super().__init__(user_id, nombre, email, telefono)
        self.rol = "usuario"
        self.db_node = "usuarios"


class Propietaria(Persona):
    def __init__(self, user_id: str, nombre: str, email: str, telefono: str = ""):
        super().__init__(user_id, nombre, email, telefono)
        self.rol = "propietaria"
        self.db_node = "propietarios"


class Admin(Persona):
    def __init__(self, user_id: str, nombre: str, email: str, telefono: str = ""):
        super().__init__(user_id, nombre, email, telefono)
        self.rol = "admin"
        self.db_node = "admins"