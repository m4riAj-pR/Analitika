from app.db.database import run_query

def migrate():
    print("Iniciando migración para soporte UTM...")
    
    # Lista de columnas a agregar
    columns = [
        ("utm_source", "VARCHAR(100)"),
        ("utm_medium", "VARCHAR(100)"),
        ("utm_campaign", "VARCHAR(100)"),
        ("utm_term", "VARCHAR(100)"),
        ("utm_content", "VARCHAR(100)")
    ]
    
    for col_name, col_type in columns:
        try:
            # Verificar si la columna ya existe
            check = run_query(f"SHOW COLUMNS FROM clicks LIKE '{col_name}'", fetch=True)
            if not check:
                print(f"Agregando columna {col_name}...")
                run_query(f"ALTER TABLE clicks ADD COLUMN {col_name} {col_type} DEFAULT NULL")
            else:
                print(f"La columna {col_name} ya existe.")
        except Exception as e:
            print(f"Error agregando {col_name}: {e}")
            
    print("Migración UTM completada.")

if __name__ == "__main__":
    migrate()
