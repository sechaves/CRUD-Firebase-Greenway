import os
from openai import OpenAI
from dotenv import load_dotenv

class GreenwayChatbot:
    """
    Clase orientada a objetos para manejar la lógica del chatbot
    con la API de OpenAI.
    """
    
    def __init__(self):
        """
        Constructor. Carga la API Key y define el "cerebro" (prompt) del bot.
        """
        # 1. Cargar la API Key desde el archivo .env que acabas de crear
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            # Si no encuentra la clave, lanza un error claro
            raise ValueError("No se encontró la API Key de OpenAI. "
                             "Asegúrate de crear un archivo .env en la raíz del proyecto "
                             "con la línea: OPENAI_API_KEY=sk-...")
        
        # 2. Inicializar el cliente de OpenAI
        self.client = OpenAI(api_key=api_key)
        
        # 3. ¡EL PROMPT CORRECTO! (El "cerebro" y "personalidad" del bot)
        # Aquí definimos las reglas de Majo y el santuario.
        self.system_prompt = """
        Eres "Greenway-bot", un asistente experto en ecoturismo y el anfitrión virtual de Greenway.
        
        SOBRE GREENWAY:
        - Greenway es un santuario de abejas nativas (Melipona) y un proyecto de ecoturismo (una finca) en Colombia.
        - El proyecto es una iniciativa familiar, liderada por Majo.
        - Tu objetivo es fomentar el turismo sostenible y el amor por la naturaleza, especialmente las abejas.
        
        TUS REGLAS:
        1.  **Personalidad:** Eres amable, entusiasta, positivo y un poco "eco-consciente". Te apasiona la naturaleza.
        2.  **Idioma:** Responde siempre en español.
        3.  **Longitud:** Mantén tus respuestas cortas y amigables (máximo 3 frases). Es un chat.
        4.  **NO INVENTES:** Si te preguntan por precios, disponibilidad, cómo reservar, o fechas específicas, **nunca debes inventar una respuesta**. 
            En su lugar, debes dirigir al usuario a la sección correcta de la app.
            - Ejemplo: "¡Claro! Puedes ver todos los precios y la disponibilidad en tiempo real en nuestra sección de 'Experiencias'."
            - Ejemplo: "Para reservar, solo tienes que ir a la sección de 'Reservas' y seguir los pasos. ¡Es muy fácil!"
        5.  **LIMITA EL TEMA:** Si el usuario te pregunta por algo que no tiene NADA que ver (ej. "Quién ganó el mundial?" (aunque haya sido el goat messi) o "Receta de lasaña"), 
            debes responder amablemente que solo estás aquí para hablar de Greenway y ecoturismo.
            - Ejemplo: "¡Esa es una buena pregunta! Pero mi especialidad es ayudarte con tu aventura en Greenway y el mundo del ecoturismo. ¿Te ayudo con eso?"
        """

    def ask(self, pregunta_usuario: str) -> str:
        """
        Recibe una pregunta del usuario y devuelve la respuesta de la IA.
        """
        if not pregunta_usuario:
            return "Parece que no has escrito nada. ¡Inténtalo de nuevo!"

        try:
            # Creamos la conversación
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini", # El modelo más nuevo, rápido y barato
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": pregunta_usuario}
                ],
                max_tokens=150 # Límite para que no escriba demasiado
            )
            
            # Devolvemos solo el texto de la respuesta
            return completion.choices[0].message.content
        
        except Exception as e:
            print(f"Error en la API de OpenAI: {e}")
            # Esta es la respuesta de error que verá el usuario
            return "¡Oh, no! Parece que estoy teniendo problemas de conexión con mi cerebro de IA. Inténtalo de nuevo en un momento."

