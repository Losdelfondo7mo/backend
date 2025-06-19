# API Olimpiadas
## Descripción
API Olimpiadas es un backend desarrollado con FastAPI para gestionar productos, usuarios, ventas y autenticación. El proyecto implementa un sistema completo de CRUD (Crear, Leer, Actualizar, Eliminar) para productos y usuarios, con autenticación JWT y soporte para OAuth con varios proveedores (Google, GitHub, Discord).

## Características
- Autenticación y Autorización :
  
  - Sistema de login con JWT (JSON Web Tokens)
  - Soporte para OAuth con múltiples proveedores (Google, GitHub, Discord)
  - Roles de usuario (admin, usuario)
- Gestión de Productos :
  
  - Crear, listar, obtener, actualizar y eliminar productos
  - Categorización de productos
  - Soporte para imágenes de productos
- Gestión de Usuarios :
  
  - Registro y autenticación de usuarios
  - Perfiles de usuario con información personal
  - Soporte para avatares de usuario
- Gestión de Ventas :
  
  - Registro de ventas con productos y usuarios asociados
  - Diferentes estados de pedido (pendiente, confirmado, denegado, entregado)
  - Seguimiento de fechas de confirmación y entrega
- Analítica :
  
  - Seguimiento de visitas al sitio
  - Registro de información de usuario y páginas visitadas
## Tecnologías Utilizadas
- FastAPI : Framework web moderno y de alto rendimiento para Python
- SQLAlchemy : ORM (Object-Relational Mapping) para interactuar con la base de datos
- Pydantic : Validación de datos y serialización
- PostgreSQL : Base de datos relacional
- JWT : Autenticación basada en tokens
- Passlib : Hashing seguro de contraseñas
- OAuth : Autenticación con proveedores externos
- ## Estructura del Proyecto
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py       # Endpoints de autenticación
│   │   │   ├── productos.py  # Endpoints de productos
│   │   │   ├── usuarios.py   # Endpoints de usuarios
│   │   │   └── ventas.py     # Endpoints de ventas
│   │   └── router.py         # Router principal de la API
│   ├── config/
│   │   └── settings.py       # Configuración de la aplicación
│   ├── core/
│   │   └── security.py       # Funciones de seguridad y autenticación
│   ├── db/
│   │   ├── base.py           # Definición base para modelos SQLAlchemy
│   │   └── session.py        # Configuración de la sesión de base de datos
│   ├── models/
│   │   ├── producto.py       # Modelo de producto
│   │   ├── usuario.py        # Modelo de usuario
│   │   ├── venta.py          # Modelo de venta
│   │   └── visita.py         # Modelo de visita
│   ├── schemas/
│   │   ├── oauth.py          # Esquemas para OAuth
│   │   ├── producto.py       # Esquemas para productos
│   │   ├── token.py          # Esquemas para tokens
│   │   ├── usuario.py        # Esquemas para usuarios
│   │   └── venta.py          # Esquemas para ventas
│   └── services/
│       ├── email_service.py  # Servicio de correo electrónico
│       └── oauth_service.py  # Servicio de OAuth
├── main.py                   # Punto de entrada de la aplicación
├── requirements.txt          # Dependencias del proyecto
└── reset_db.py               # Script para resetear la base de datos
## Requisitos
- Python 3.8+
- PostgreSQL
- Dependencias listadas en requirements.txt
## Instalación
1. Clonar el repositorio:
```
git clone https://github.com/tu-usuario/
olimpiadas.git
cd olimpiadas/backend
```
2. Crear un entorno virtual e instalar dependencias:
```
python -m venv venv
venv\Scripts\activate  # En Windows
source venv/bin/activate  # En Unix/
MacOS
pip install -r requirements.txt
```
3. Configurar variables de entorno:
Crea un archivo .env en la raíz del proyecto con el siguiente contenido:

```
# Configuración de la base de datos
database_url=postgresql://
usuario:contraseña@localhost/nombre_db

# Configuración JWT
SECRET_KEY=tu_clave_secreta_muy_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de correo electrónico
app_password=tu_contraseña_de_app_gmail
sender_email=tu_email@gmail.com

# Configuración OAuth (opcional)
google_client_id=tu_client_id_de_google
google_client_secret=tu_client_secret_de
_google
github_client_id=tu_client_id_de_github
github_client_secret=tu_client_secret_de
_github
discord_client_id=tu_client_id_de_discor
d
discord_client_secret=tu_client_secret_d
e_discord
oauth_redirect_base_url=http://
localhost:8000
```
## Inicialización de la Base de Datos
Para inicializar o resetear la base de datos, puedes usar el script reset_db.py :

```
python reset_db.py
```
Este script eliminará todas las tablas existentes y las recreará, además de crear un usuario administrador predeterminado:

- Usuario: admin
- Contraseña: admin123
## Ejecución
Para iniciar el servidor de desarrollo:

```
python main.py
```
O usando uvicorn directamente:

```
uvicorn main:app --reload --host 0.0.0.
0 --port 8000
```
La API estará disponible en http://localhost:8000 .

## Documentación de la API
FastAPI genera automáticamente documentación interactiva para la API:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
## Endpoints Principales
### Autenticación
- POST /api/auth/token - Obtener token JWT (login)
- POST /api/auth/register - Registrar nuevo usuario
- GET /api/auth/me - Obtener información del usuario actual
- GET /api/auth/oauth/{provider} - Iniciar flujo OAuth
- GET /api/auth/oauth/{provider}/callback - Callback de OAuth
### Productos
- GET /api/productos/ - Listar todos los productos
- POST /api/productos/ - Crear un nuevo producto
- GET /api/productos/{producto_id} - Obtener un producto específico
- PUT /api/productos/{producto_id} - Actualizar un producto
- DELETE /api/productos/{producto_id} - Eliminar un producto
### Usuarios
- GET /api/usuarios/ - Listar todos los usuarios
- POST /api/usuarios/ - Crear un nuevo usuario
- GET /api/usuarios/{usuario_id} - Obtener un usuario específico
- PUT /api/usuarios/{usuario_id} - Actualizar un usuario
- DELETE /api/usuarios/{usuario_id} - Eliminar un usuario
### Ventas
- GET /api/ventas/ - Listar todas las ventas
- POST /api/ventas/ - Crear una nueva venta
- GET /api/ventas/{venta_id} - Obtener una venta específica
- PUT /api/ventas/{venta_id} - Actualizar una venta
- DELETE /api/ventas/{venta_id} - Eliminar una venta
## Contribución
Si deseas contribuir a este proyecto, por favor:

1. Haz un fork del repositorio
2. Crea una rama para tu característica ( git checkout -b feature/nueva-caracteristica )
3. Haz commit de tus cambios ( git commit -am 'Añadir nueva característica' )
4. Haz push a la rama ( git push origin feature/nueva-caracteristica )
5. Crea un nuevo Pull Request

## Contacto
Para cualquier consulta o sugerencia, por favor contacta a:

- Email: losdelfondo7moetp@gmail.com
