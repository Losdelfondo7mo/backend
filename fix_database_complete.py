import os
from sqlalchemy import create_engine, text

# Configuración - usando la URL de producción de Render
DATABASE_URL = "postgresql://losdelfondosql_user:PvDDXaQUDSmRWaa4yL3Fq2zC1BkmRtAn@dpg-d16b2kumcj7s73bv3peg-a.oregon-postgres.render.com/losdelfondosql"
engine = create_engine(DATABASE_URL)

def fix_database():
    print("🔧 MIGRACIÓN COMPLETA DE BASE DE DATOS")
    print("Arreglando todas las columnas faltantes...\n")
    
    try:
        with engine.connect() as conn:
            # ===== TABLA USUARIOS =====
            print("👤 Arreglando tabla USUARIOS...")
            
            # Verificar columnas existentes en usuarios
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'usuarios' AND column_name IN ('created_at', 'is_active')
            """))
            existing_user_columns = [row[0] for row in result.fetchall()]
            
            # Agregar created_at a usuarios
            if 'created_at' not in existing_user_columns:
                print("  ➕ Agregando usuarios.created_at...")
                conn.execute(text("""
                    ALTER TABLE usuarios 
                    ADD COLUMN created_at TIMESTAMP DEFAULT NOW()
                """))
                print("  ✅ usuarios.created_at agregada")
            else:
                print("  ℹ️  usuarios.created_at ya existe")
            
            # Agregar is_active a usuarios
            if 'is_active' not in existing_user_columns:
                print("  ➕ Agregando usuarios.is_active...")
                conn.execute(text("""
                    ALTER TABLE usuarios 
                    ADD COLUMN is_active BOOLEAN DEFAULT TRUE
                """))
                print("  ✅ usuarios.is_active agregada")
            else:
                print("  ℹ️  usuarios.is_active ya existe")
            
            # Actualizar valores NULL en usuarios
            conn.execute(text("""
                UPDATE usuarios 
                SET created_at = NOW() 
                WHERE created_at IS NULL
            """))
            
            conn.execute(text("""
                UPDATE usuarios 
                SET is_active = TRUE 
                WHERE is_active IS NULL
            """))
            
            # ===== TABLA VISITAS =====
            print("\n📊 Arreglando tabla VISITAS...")
            
            # Verificar si la tabla visitas existe
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'visitas'
                )
            """))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                print("  ➕ Creando tabla visitas completa...")
                conn.execute(text("""
                    CREATE TABLE visitas (
                        id SERIAL PRIMARY KEY,
                        ip_address VARCHAR(45) NOT NULL,
                        user_agent TEXT,
                        fecha_visita TIMESTAMP DEFAULT NOW() NOT NULL,
                        pagina_visitada VARCHAR(255),
                        usuario_id INTEGER
                    )
                """))
                print("  ✅ Tabla visitas creada")
            else:
                # Verificar columnas existentes en visitas
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'visitas' AND column_name = 'fecha_visita'
                """))
                existing_visit_columns = [row[0] for row in result.fetchall()]
                
                # Agregar fecha_visita a visitas si no existe
                if 'fecha_visita' not in existing_visit_columns:
                    print("  ➕ Agregando visitas.fecha_visita...")
                    conn.execute(text("""
                        ALTER TABLE visitas 
                        ADD COLUMN fecha_visita TIMESTAMP DEFAULT NOW() NOT NULL
                    """))
                    print("  ✅ visitas.fecha_visita agregada")
                else:
                    print("  ℹ️  visitas.fecha_visita ya existe")
            
            conn.commit()
            print("\n💾 Todos los cambios guardados exitosamente")
            
            # ===== VERIFICACIÓN FINAL =====
            print("\n📋 VERIFICACIÓN FINAL:")
            
            # Verificar estructura de usuarios
            print("\n👤 Estructura de tabla USUARIOS:")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'usuarios' 
                ORDER BY ordinal_position
            """))
            
            for row in result:
                nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {row[3]}" if row[3] else ""
                print(f"  📌 {row[0]}: {row[1]} {nullable}{default}")
            
            # Verificar estructura de visitas
            print("\n📊 Estructura de tabla VISITAS:")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'visitas' 
                ORDER BY ordinal_position
            """))
            
            for row in result:
                nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {row[3]}" if row[3] else ""
                print(f"  📌 {row[0]}: {row[1]} {nullable}{default}")
                
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 SCRIPT DE MIGRACIÓN COMPLETA DE BASE DE DATOS")
    print("Este script arreglará TODAS las columnas faltantes en producción.")
    print("\n🔍 Problemas detectados:")
    print("  - usuarios.created_at no existe")
    print("  - usuarios.is_active no existe")
    print("  - visitas.fecha_visita no existe")
    print("\n⚠️  IMPORTANTE: Este script modificará la base de datos de producción.")
    
    confirm = input("\n¿Continuar con la migración? (s/N): ").lower().strip()
    
    if confirm in ['s', 'si', 'sí', 'y', 'yes']:
        success = fix_database()
        
        if success:
            print("\n🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
            print("✅ Todas las columnas faltantes han sido agregadas")
            print("✅ Los datos existentes se mantuvieron intactos")
            print("✅ La aplicación ahora debería funcionar correctamente")
            print("🔄 Render redesplegará automáticamente la aplicación")
            print("\n🚀 Tu aplicación estará lista en unos minutos.")
        else:
            print("\n❌ Hubo problemas durante la migración.")
            print("🔍 Revisa los errores anteriores.")
            print("💬 Si el problema persiste, contacta soporte.")
    else:
        print("\n❌ Migración cancelada.")
        print("⚠️  Los errores de base de datos continuarán hasta que ejecutes la migración.")