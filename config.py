# Configuración de la aplicación
APP_PASSWORD = 'ykhj uzeu yztv pmfe'

# Configuración de base de datos
DATABASE_URL = "postgresql://losdelfondosql_user:PvDDXaQUDSmRWaa4yL3Fq2zC1BkmRtAn@dpg-d16b2kumcj7s73bv3peg-a.oregon-postgres.render.com/losdelfondosql"

# Configuración de JWT
SECRET_KEY = "c67d978e20f38a9a00db5e4e60de978d93e0e3031b18e6c248e928bd3b9fad5b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuración de correo
SENDER_EMAIL = 'losdelfondo7moetp@gmail.com'
RECIPIENTS = ['losdelfondo7moetp@gmail.com', 'noahchamo@gmail.com']

# Scopes para Gmail API
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]