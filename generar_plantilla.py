# generar_plantilla.py
import openpyxl

def crear_plantilla_productos_excel():
    # Crear un nuevo libro de trabajo
    wb = openpyxl.Workbook()
    # Seleccionar la hoja activa
    ws = wb.active
    ws.title = "Productos" # Nombrar la hoja

    # Definir los encabezados de las columnas
    headers = [
        "Nombre",
        "Categoría",
        "Precio Dólar",
        "Precio Bs",
        "Stock",
        "Descripción",
        "Porcentaje Ganancia",
        "Precio Individual Dólar",
        "Precio Individual Bs"
    ]

    # Escribir los encabezados en la primera fila
    ws.append(headers)

    # Opcional: Ajustar el ancho de las columnas para mayor legibilidad
    column_widths = {
        'A': 25, 'B': 15, 'C': 15, 'D': 15, 'E': 10,
        'F': 30, 'G': 20, 'H': 25, 'I': 25
    }
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width

    # Guardar el libro de trabajo en la ruta deseada
    # Asegúrate de que la carpeta 'inventario/static/inventario' exista
    # Si no existe, debes crearla manualmente o adaptar la ruta.
    file_path = 'inventario/static/inventario/plantilla_productos.xlsx'
    
    try:
        wb.save(file_path)
        print(f"Plantilla '{file_path}' creada exitosamente.")
    except Exception as e:
        print(f"Error al guardar la plantilla: {e}")
        print("Asegúrate de que la carpeta 'inventario/static/inventario' exista y tengas permisos de escritura.")


if __name__ == "__main__":
    crear_plantilla_productos_excel()