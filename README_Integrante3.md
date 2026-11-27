# Integrante 3 — Global Electronic Retail
Complemento para PcatedraFinalDMD, rama main. Copiar el contenido de este ZIP a la raíz del clon; no reemplaza archivos de integrantes 1 y 2. No incluye PBIX nativo.

## Windows / PowerShell
Requiere Git, Python 3.11+, Docker Desktop iniciado y Power BI Desktop.
```powershell
git clone https://github.com/teomirandaonce/PcatedraFinalDMD.git
cd PcatedraFinalDMD
# Copiar aquí el contenido del ZIP antes de continuar.
git switch -c integrante3-finanzas
if (!(Test-Path .env)) { Copy-Item .env.example .env }
docker compose up -d --wait
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/etl_carga.py
.\.venv\Scripts\python.exe src/validar_carga.py
Get-Content -Raw sql/03_vistas_powerbi.sql | docker exec -i dwh_global_retail psql -v ON_ERROR_STOP=1 -U dwh_admin -d global_retail_dwh
Get-Content -Raw sql/04_validacion_kpis.sql | docker exec -i dwh_global_retail psql -v ON_ERROR_STOP=1 -U dwh_admin -d global_retail_dwh
```
Ejecutar por bloques y detenerse ante errores. Comandos para valores por defecto de .env; adaptar usuario/base/puerto si se cambiaron. Si ya existe una base del equipo, omitir clonación/carga local y conectarse a la instancia autorizada. No publicar credenciales ni exponer PostgreSQL a Internet; los valores de ejemplo del repositorio deben cambiarse fuera del laboratorio.

## Power BI
Servidor localhost:5432 (o puerto configurado); base global_retail_dwh; autenticación de base de datos con usuario powerbi_reader y clave de docs/conexion_powerbi.md del repositorio. Modo Importar. Seleccionar las cinco tablas del esquema dwh, no la vista plana. Seguir docs/integrante3_powerbi.txt. Crear cada medida de powerbi/medidas_DAX.txt individualmente. Importar powerbi/Tema_Finanzas.json. Ejecutar powerbi/prueba_DAX.txt por bloques. Guardar el PBIX grupal acordado con integrante 4.

## Evidencias y publicación
Las imágenes y HTML incluidos son prototipos de referencia, no evidencias de Power BI. Capturar modelo, consultas SQL, seis medidas y página Finanzas en Power BI, sin filtros y con 2020 seleccionado. Guardar en Evidencias/Integrante 3. Comparar con CSV de docs. Los valores globales coinciden con docs/conexion_powerbi.md del repositorio; la conexión y el motor DAX no fueron ejecutados en este entorno.
```powershell
git add README_Integrante3.md powerbi sql/04_validacion_kpis.sql docs/integrante3_powerbi.txt docs/referencia_*.csv docs/Informe_Integrante3.docx 'Evidencias/Integrante 3'
git commit -m "Implementa KPIs y documentación de Finanzas - integrante 3"
git push -u origin integrante3-finanzas
```
Si no tienes permiso de escritura, realiza un fork y abre un pull request. No subir .env. Coordinar el PBIX con integrante 4 antes del merge.
