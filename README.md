# Biblioteca Escolar

Sitio web de préstamos para la biblioteca de la escuela. Permite buscar y solicitar libros, proyectores, materiales, equipos audiovisuales y más, con sistema de usuarios, reservas, favoritos, notificaciones y un panel de administración para la bibliotecaria.

Proyecto escolar hecho con **Flask + HTML/CSS/JS**, sin base de datos: todo se guarda en `data.json`.

## Cómo correrlo

```powershell
# 1. Crear y activar el entorno virtual
python -m venv venv
.\venv\Scripts\python.exe -m pip install flask

# 2. Arrancar el servidor
.\venv\Scripts\python.exe app.py
```

Después abrir http://127.0.0.1:5000 en el navegador.

**Cuenta de administración de prueba:** `admin@escuela.edu` / `admin123`

## Qué incluye

- Catálogo con buscador, filtros por categoría/género y ordenamiento
- Solicitar préstamos con cantidad (miniventana) y control de stock
- Reservas con aviso cuando se libera lo que esperás
- Favoritos por usuario
- Notificaciones (entregas, devoluciones, reservas liberadas)
- Fecha de devolución con aviso de vencido
- Calendario de ocupación de proyectores y equipos
- Panel de admin: gestión de pedidos (con N° de inventario obligatorio), inventario y usuarios
- Modo oscuro, menú móvil, ver/ocultar contraseña
- Seguridad: contraseñas con hash, CSRF en formularios, cabeceras HTTP, límite de préstamos
- Páginas extras: FAQ, privacidad, 404, gracias; `sitemap.xml`, `robots.txt`, `llms.txt`

## Estructura

```
├── app.py              # Backend Flask
├── data.json           # Datos (items, usuarios, pedidos, reservas)
├── IDEAS.txt           # Lista de mejoras pensadas y hechas
├── templates/          # HTML (Jinja2)
└── static/
    ├── css/style.css   # Estilos (tema claro/oscuro)
    └── js/main.js      # Modo oscuro, modal, menú móvil, etc.
```

## Producción

### Opción recomendada: PythonAnywhere (gratis y con disco persistente)

Como los datos se guardan en `data.json`, conviene un hosting con archivos persistentes. En Render gratis el disco se reinicia en cada despliegue (se perderían los pedidos); PythonAnywhere los mantiene.

1. **Subir el código a GitHub**
   - Crear un repositorio nuevo (por ejemplo `biblioteca-escolar`) y subir todo el contenido de esta carpeta.
2. **Crear cuenta gratis** en [pythonanywhere.com](https://www.pythonanywhere.com)
3. En la pestaña **Files** abrir una consola (**Consoles → Bash**) y clonar:
   ```
   git clone https://github.com/TUUSUARIO/biblioteca-escolar
   ```
4. Instalar las dependencias:
   ```
   pip3.10 install --user -r ~/biblioteca-escolar/requirements.txt
   ```
5. Pestaña **Web → Add a new web app → Manual configuration → Python 3.10**
6. En **Web → Code → WSGI file**: borrar todo y dejar:
   ```python
   import os
   import sys

   os.environ["BIBLIOTECA_SECRET_KEY"] = "una-clave-larga-que-solo-vos-sabes"

   path = "/home/TUUSUARIO/biblioteca-escolar"
   if path not in sys.path:
       sys.path.insert(0, path)

   from app import app as application
   ```
7. En **Web → Code → Source code** poner la carpeta del proyecto y **Reload** la app.
8. Ya está online en `TUUSUARIO.pythonanywhere.com` (con HTTPS incluido).

### Dominio propio

1. Comprarlo en un registrador (Nic.ar para `.com.ar`, o Namecheap/DonWeb para `.com`, ~USD 10-15/año).
2. En el panel del dominio, crear un registro **CNAME** apuntando a `TUUSUARIO.pythonanywhere.com` (o el que indique el hosting).
3. Configurarlo en el hosting (en PythonAnywhere requiere plan pago; en Render se configura desde el dashboard del servicio).
4. El HTTPS del dominio propio lo emite el hosting automáticamente (Let's Encrypt).

> Importante: nunca subir `BIBLIOTECA_SECRET_KEY` al repositorio. En PythonAnywhere se define en el archivo WSGI, que no forma parte del repo.
