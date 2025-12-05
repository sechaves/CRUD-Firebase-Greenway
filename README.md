# 🌿 GREENWAY - Plataforma de Ecoturismo

![Estado del Proyecto](https://img.shields.io/badge/Estado-Finalizado-success?style=for-the-badge)
![Versión](https://img.shields.io/badge/Versión-1.0.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.13-yellow?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-lightgrey?style=for-the-badge&logo=flask)
![Firebase](https://img.shields.io/badge/Firebase-Realtime_DB-orange?style=for-the-badge&logo=firebase)

**Greenway** es una aplicación web full-stack diseñada para conectar a turistas con experiencias locales de ecoturismo en el municipio de El Santuario. La plataforma permite la gestión de reservas, comunicación en tiempo real y administración de contenidos mediante roles de seguridad.

---

## 🚀 Características Principales

### 👤 Gestión de Usuarios y Roles (RBAC)
* **Autenticación Segura:** Registro e inicio de sesión mediante **Firebase Auth**.
* **Roles Diferenciados:**
    * **Usuario:** Puede explorar, buscar y chatear con anfitriones.
    * **Propietaria:** Puede crear, editar y eliminar sus experiencias.
    * **Admin:** Panel de control total, moderación de usuarios y contenido.

### 💬 Chat en Tiempo Real (Arquitectura NoSQL)
* Implementación de mensajería instantánea sin sockets tradicionales.
* Sincronización directa **Cliente <-> Firebase Realtime Database**.
* Estructura de datos basada en objetos JSON anidados.
* Historial persistente y notificaciones visuales inmediatas.

### 🤖 Asistente Virtual con IA
* Chatbot integrado potenciado por **OpenAI (GPT)**.
* Disponible 24/7 en toda la aplicación para resolver dudas de los viajeros.

### 🌎 Experiencia de Usuario (UX)
* **Geolocalización:** Integración de mapas interactivos con Google Maps Embed API.
* **Búsqueda Inteligente:** Filtrado de experiencias en tiempo real.
* **Galería Dinámica:** Carrusel de imágenes con soporte para múltiples fotos y fallback automático.

---

## 🛠️ Stack Tecnológico

El proyecto fue construido utilizando una arquitectura **MVC (Modelo-Vista-Controlador)** adaptada a microframeworks.

| Área | Tecnología | Descripción |
| :--- | :--- | :--- |
| **Backend** | Python + Flask | Lógica del servidor y rutas. |
| **Base de Datos** | Firebase Realtime DB | Base de datos NoSQL basada en la nube. |
| **Auth** | Firebase Authentication | Gestión de identidad y seguridad. |
| **Frontend** | HTML5, CSS3, JS | Interfaz de usuario responsiva. |
| **Estilos** | Bootstrap 5 | Framework de diseño y componentes. |
| **IA** | OpenAI API | Procesamiento de lenguaje natural. |
| **Deploy** | Render | Infraestructura como servicio (PaaS). |

---

## 📂 Estructura del Proyecto

```text
GREENWAY/
│
├── app/
│   ├── static/              # Archivos públicos (CSS, JS, Imágenes)
│   └── templates/           # Plantillas HTML (Jinja2)
│       ├── base.html        # Layout maestro
│       ├── home.html        # Página principal
│       ├── chats.html       # Lógica del chat
│       └── ...
│
├── data/
│   ├── firebase_config.py   # Configuración del SDK Cliente
│   └── firebase_admin.py    # Configuración del SDK Admin
│
├── domain/
│   ├── models.py            # Modelos de Clases (POO)
│   └── openai_chatbot.py    # Lógica del Bot
│
├── main.py                  # Controlador Principal (App Entry Point)
├── requirements.txt         # Dependencias
└── serviceAccountKey.json   # Credenciales (No incluidas en repo)
```

🎥 Sustentación y Demo

Mira la demostración completa del funcionamiento del Frontend, la arquitectura y el flujo de usuario en el siguiente video:

[![Ver Video de Sustentación](https://img.youtube.com/vi/SuZTOu1oG5Y/0.jpg)](https://youtu.be/SuZTOu1oG5Y)

> *Clic en la imagen para ver el video en YouTube.*
