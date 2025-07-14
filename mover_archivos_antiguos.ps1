# Script para mover archivos antiguos a la carpeta archivos_antiguos
# Asegurarse de que la carpeta existe
if (-not (Test-Path "archivos_antiguos")) {
    New-Item -ItemType Directory -Path "archivos_antiguos"
}

# Grupo 1: Archivos de respaldo de app.py
$grupo1 = @(
    "app_backup.py",
    "app_clean.py",
    "app_final.py",
    "app_new.py",
    "app_original.py",
    "app_temp.py",
    "app.py.bak",
    "app.py.new"
)

# Grupo 2: Scripts de corrección que probablemente ya no son necesarios
$grupo2 = @(
    "fix_actualizar_animal.py",
    "fix_actualizar_animal_simple.py",
    "fix_alarmas.py",
    "fix_animal_funcion.py",
    "fix_carbunco.py",
    "fix_database.py",
    "fix_editar_animal.py",
    "fix_editar_animal_route.py",
    "fix_equipos.py",
    "fix_final_carbunco.py",
    "fix_obtener_configuracion_alarmas.py",
    "fix_script.py"
)

# Grupo 3: Scripts de corrección de estructura de base de datos
$grupo3 = @(
    "agregar_campo_calidad.py",
    "agregar_equipo_fix.py",
    "alter_table.py",
    "corregir_campo_usuario_id.py",
    "corregir_estructura_bd.py",
    "corregir_tabla_alarmas.py",
    "corregir_tabla_vacuna.py",
    "crear_tabla_auditoria.py",
    "crear_tabla_vacuna.py",
    "crear_tabla_vacuna_animal.py"
)

# Grupo 4: Scripts de depuración
$grupo4 = @(
    "debug_animal.py",
    "debug_animal_mejorado.py",
    "check_images.py",
    "check_table.py"
)

# Grupo 5: Scripts de datos de prueba
$grupo5 = @(
    "crear_vacunaciones_prueba.py"
)

# Función para mover archivos si existen
function Mover-Archivos-Si-Existen {
    param (
        [string[]]$archivos,
        [string]$destino
    )
    
    foreach ($archivo in $archivos) {
        if (Test-Path $archivo) {
            Write-Host "Moviendo $archivo a $destino"
            Move-Item -Path $archivo -Destination $destino -Force
        } else {
            Write-Host "El archivo $archivo no existe, se omite"
        }
    }
}

# Mover archivos por grupos
Write-Host "Moviendo Grupo 1: Archivos de respaldo de app.py"
Mover-Archivos-Si-Existen -archivos $grupo1 -destino "archivos_antiguos"

Write-Host "`nMoviendo Grupo 2: Scripts de corrección"
Mover-Archivos-Si-Existen -archivos $grupo2 -destino "archivos_antiguos"

Write-Host "`nMoviendo Grupo 3: Scripts de corrección de estructura de base de datos"
Mover-Archivos-Si-Existen -archivos $grupo3 -destino "archivos_antiguos"

Write-Host "`nMoviendo Grupo 4: Scripts de depuración"
Mover-Archivos-Si-Existen -archivos $grupo4 -destino "archivos_antiguos"

Write-Host "`nMoviendo Grupo 5: Scripts de datos de prueba"
Mover-Archivos-Si-Existen -archivos $grupo5 -destino "archivos_antiguos"

Write-Host "`nProceso completado. Los archivos han sido movidos a la carpeta 'archivos_antiguos'"
