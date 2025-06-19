import os
import sys
sys.path.append('backend')

from sqlalchemy import create_engine, text

# Configuración
DATABASE_URL = "postgresql://losdelfondosql_user:PvDDXaQUDSmRWaa4yL3Fq2zC1BkmRtAn@dpg-d16b2kumcj7s73bv3peg-a.oregon-postgres.render.com/losdelfondosql"
engine = create_engine(DATABASE_URL)

def fix_database():
    print("Arreglando la base de datos...")
    
    try:
        with engine.connect() as conn:
            # Agregar la columna created_at si no existe
            conn.execute(text("""
                ALTER TABLE usuarios 
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()
            """))
            
            # Agregar la columna is_active si no existe
            conn.execute(text("""
                ALTER TABLE usuarios 
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
            """))
            
            conn.commit()
            print("✅ Columnas agregadas exitosamente")
            
            # Verificar estructura
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'usuarios' 
                ORDER BY ordinal_position
            """))
            
            print("\nEstructura actual de la tabla usuarios:")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = fix_database()
    if success:
        print("\n🎉 Base de datos arreglada. Ahora puedes reiniciar tu aplicación.")
    else:
        print("\n❌ Hubo problemas al arreglar la base de datos.")