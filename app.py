import json
import os
import secrets
from datetime import date, timedelta
from functools import wraps
import unicodedata

from flask import (Flask, Response, abort, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

app = Flask(__name__)
# La clave secreta se toma de una variable de entorno; nunca se sube a git.
app.secret_key = os.environ.get("BIBLIOTECA_SECRET_KEY", secrets.token_hex(32))

HASH_PREFIXES = ("pbkdf2", "scrypt")


def es_hash(password_guardada):
    return password_guardada.startswith(HASH_PREFIXES)
MAX_PEDIDOS_ACTIVOS = 5
DIAS_PRESTAMO = 7


# ---------------- Persistencia (JSON) ----------------
def cargar_datos():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_datos(datos):
    """Escritura atómica: primero a un archivo temporal y después se
    reemplaza, para no corruptar data.json si el proceso se corta."""
    temporal = DATA_FILE + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(temporal, DATA_FILE)


def nuevo_id(datos, clave, coleccion):
    """Devuelve el siguiente ID disponible, recalcúlándolo por si
    falta el contador en data.json."""
    if clave not in datos:
        datos[clave] = max((x["id"] for x in coleccion), default=0) + 1
    return datos[clave]


# ---------------- Seguridad ----------------
def verificar_password(guardada, ingresada):
    """Verifica la contraseña. Acepta el formato viejo en texto plano
    y lo migra a hash automáticamente al primer login exitoso."""
    if es_hash(guardada):
        return check_password_hash(guardada, ingresada)
    return guardada == ingresada


@app.before_request
def verificar_csrf():
    """CSRF: todo POST debe traer el token de sesión."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    if request.method == "POST":
        token_sesion = session.get("csrf_token")
        token_form = request.form.get("csrf_token")
        if not token_sesion or token_form != token_sesion:
            abort(403, description="Token CSRF inválido o ausente.")


@app.after_request
def cabeceras_seguridad(respuesta):
    """Cabeceras HTTP de seguridad básicas."""
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    respuesta.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data:"
    )
    return respuesta


# ---------------- Helpers ----------------
def normalizar_texto(texto):
    """Pasa a minúsculas y quita tildes, para que buscando
    'matematica' o 'FISICA' se encuentren 'Matemática' o 'Física'."""
    texto = texto.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')


def notificar(datos, usuario_id, mensaje):
    """Crea una notificación para un usuario."""
    u = next((u for u in datos["usuarios"] if u["id"] == usuario_id), None)
    if u is None:
        return
    u.setdefault("notificaciones", [])
    u["notificaciones"].append({
        "id": datos.get("siguiente_noti_id", 1),
        "mensaje": mensaje,
        "fecha": date.today().strftime("%d/%m/%Y"),
        "leida": False,
    })
    datos["siguiente_noti_id"] = datos.get("siguiente_noti_id", 1) + 1


def liberar_item(datos, item_id, cantidad):
    """Devuelve stock y avisa al primero en la cola de reservas."""
    item = next((i for i in datos["items"] if i["id"] == item_id), None)
    if not item:
        return
    item["stock"] = item.get("stock", 0) + cantidad
    item["disponible"] = True
    reserva = next((r for r in datos.get("reservas", [])
                    if r["item_id"] == item_id), None)
    if reserva:
        datos["reservas"].remove(reserva)
        notificar(datos, reserva["usuario_id"],
                  f'Se liberó "{item["titulo"]}": tu reserva está lista, podés solicitarla ahora.')


def usuario_actual():
    if "usuario_id" not in session:
        return None
    datos = cargar_datos()
    for u in datos["usuarios"]:
        if u["id"] == session["usuario_id"]:
            return u
    return None


def login_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not usuario_actual():
            flash("Tenés que iniciar sesión.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = usuario_actual()
        if not u or not u.get("admin"):
            flash("No tenés permisos de administrador.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper


@app.context_processor
def inyectar_usuario():
    u = usuario_actual()
    pedidos = []
    if u:
        datos = cargar_datos()
        pedidos = [p for p in datos["pedidos"]
                   if p["usuario_id"] == u["id"]][:5]
    notis = 0
    if u:
        notis = sum(1 for n in u.get("notificaciones", []) if not n.get("leida"))
    return {"usuario": u, "pedidos_recientes": pedidos,
            "notis_no_leidas": notis,
            "csrf_token": session["csrf_token"]}


# ---------------- Páginas ----------------
@app.route("/")
def index():
    datos = cargar_datos()
    items = datos["items"]
    return render_template(
        "index.html",
        libros=[i for i in items if i["tipo"] == "libro"][:5],
        proyectores=[i for i in items if i["tipo"] == "proyector"][:5],
        materiales=[i for i in items if i["tipo"] == "material"][:5],
        audiovisuales=[i for i in items if i["tipo"] == "audiovisual"][:5],
        equipos=[i for i in items if i["tipo"] == "equipo"][:5],
        otros=[i for i in items if i["tipo"] == "otro"][:5],
        favoritos=(usuario_actual() or {}).get("favoritos", []),
        reservas_usuario=[r["item_id"] for r in datos.get("reservas", [])
                          if r["usuario_id"] == session.get("usuario_id")],
    )


@app.route("/catalogo")
def catalogo():
    datos = cargar_datos()
    q = request.args.get("q", "").strip().lower()
    tipo = request.args.get("tipo", "todos")
    genero = request.args.get("genero", "").strip()
    orden = request.args.get("orden", "titulo")

    items = datos["items"]
    if tipo != "todos":
        items = [i for i in items if i["tipo"] == tipo]
    if genero:
        items = [i for i in items if i.get("genero") == genero]
    if q:
        q_norm = normalizar_texto(q)
        items = [i for i in items
                 if q_norm in normalizar_texto(i["titulo"])
                 or q_norm in normalizar_texto(i["autor"])]
    if orden == "disponibilidad":
        items = sorted(items, key=lambda i: not i["disponible"])
    elif orden == "anio":
        items = sorted(items, key=lambda i: i.get("anio", 0), reverse=True)
    else:
        items = sorted(items, key=lambda i: i["titulo"].lower())

    generos = sorted({i.get("genero") for i in datos["items"] if i.get("genero")})
    u = usuario_actual()
    favoritos = u.get("favoritos", []) if u else []
    reservas_usuario = [r["item_id"] for r in datos.get("reservas", [])
                        if r["usuario_id"] == session.get("usuario_id")]
    return render_template("catalogo.html", items=items, q=q, tipo=tipo,
                           genero=genero, generos=generos, orden=orden,
                           favoritos=favoritos, reservas_usuario=reservas_usuario)


@app.route("/item/<int:item_id>")
def detalle(item_id):
    datos = cargar_datos()
    item = next((i for i in datos["items"] if i["id"] == item_id), None)
    if not item:
        abort(404)
    uid = session.get("usuario_id")
    u = usuario_actual()
    return render_template(
        "detalle.html",
        item=item,
        es_favorito=bool(u and item_id in u.get("favoritos", [])),
        reservado=any(r for r in datos.get("reservas", [])
                      if r["item_id"] == item_id and r["usuario_id"] == uid),
        ocupacion=[p for p in datos["pedidos"]
                   if p["item_id"] == item_id and p["estado"] == "Entregado"],
    )


# ---------------- Préstamos ----------------
@app.route("/solicitar/<int:item_id>", methods=["POST"])
@login_requerido
def solicitar(item_id):
    datos = cargar_datos()
    item = next((i for i in datos["items"] if i["id"] == item_id), None)
    if not item:
        abort(404)
    cantidad = request.form.get("cantidad", "1")
    try:
        cantidad = int(cantidad)
    except ValueError:
        cantidad = 0
    if cantidad < 1:
        flash("La cantidad tiene que ser al menos 1.", "error")
        return redirect(request.referrer or url_for("index"))
    if cantidad > item.get("stock", 1):
        flash(f'Solo quedan {item.get("stock", 0)} unidades de "{item["titulo"]}".', "error")
        return redirect(request.referrer or url_for("index"))

    ya_pedido = any(p for p in datos["pedidos"]
                    if p["item_id"] == item_id
                    and p["usuario_id"] == session["usuario_id"]
                    and p["estado"] in ("En proceso", "Entregado"))
    if ya_pedido:
        flash("Ya tenés un pedido activo de este elemento.", "error")
        return redirect(request.referrer or url_for("index"))

    # Límite de unidades activas por usuario (sumando cantidades)
    activas = sum(p.get("cantidad", 1) for p in datos["pedidos"]
                  if p["usuario_id"] == session["usuario_id"]
                  and p["estado"] in ("En proceso", "Entregado"))
    if activas + cantidad > MAX_PEDIDOS_ACTIVOS:
        flash(f"Alcanzaste el máximo de {MAX_PEDIDOS_ACTIVOS} unidades pedidas a la vez. "
              "Devolvé algo antes de pedir más.", "error")
        return redirect(request.referrer or url_for("index"))

    datos["pedidos"].append({
        "id": nuevo_id(datos, "siguiente_pedido_id", datos["pedidos"]),
        "item_id": item_id,
        "item_titulo": item["titulo"],
        "item_tipo": item["tipo"],
        "cantidad": cantidad,
        "inventario": None,
        "usuario_id": session["usuario_id"],
        "fecha": date.today().strftime("%d/%m/%Y"),
        "estado": "En proceso",
    })
    datos["siguiente_pedido_id"] += 1
    item["stock"] = item.get("stock", 1) - cantidad
    item["disponible"] = item["stock"] > 0
    guardar_datos(datos)
    flash(f"{cantidad} × \"{item['titulo']}\" solicitado correctamente.", "ok")
    return redirect(request.referrer or url_for("index"))


# ---------------- Reservas, favoritos y notificaciones ----------------
@app.route("/reservar/<int:item_id>", methods=["POST"])
@login_requerido
def reservar(item_id):
    datos = cargar_datos()
    item = next((i for i in datos["items"] if i["id"] == item_id), None)
    if not item:
        abort(404)
    if item["disponible"]:
        flash("Está disponible: podés solicitarlo directamente.", "error")
        return redirect(request.referrer or url_for("index"))
    if any(r for r in datos.get("reservas", [])
           if r["item_id"] == item_id and r["usuario_id"] == session["usuario_id"]):
        flash("Ya tenés una reserva para este elemento.", "error")
        return redirect(request.referrer or url_for("index"))
    datos.setdefault("reservas", []).append({
        "id": nuevo_id(datos, "siguiente_reserva_id", datos.get("reservas", [])),
        "item_id": item_id,
        "item_titulo": item["titulo"],
        "usuario_id": session["usuario_id"],
        "fecha": date.today().strftime("%d/%m/%Y"),
    })
    datos["siguiente_reserva_id"] = datos.get("siguiente_reserva_id", 1) + 1
    guardar_datos(datos)
    flash(f'Reservaste "{item["titulo"]}". Te avisamos cuando se libere.', "ok")
    return redirect(request.referrer or url_for("index"))


@app.route("/mis-reservas")
@login_requerido
def mis_reservas():
    datos = cargar_datos()
    reservas = [r for r in datos.get("reservas", [])
                if r["usuario_id"] == session["usuario_id"]]
    return render_template("reservas.html", reservas=reservas)


@app.route("/reservar/cancelar/<int:reserva_id>", methods=["POST"])
@login_requerido
def cancelar_reserva(reserva_id):
    datos = cargar_datos()
    antes = len(datos.get("reservas", []))
    datos["reservas"] = [r for r in datos.get("reservas", [])
                         if not (r["id"] == reserva_id
                                 and r["usuario_id"] == session["usuario_id"])]
    if len(datos["reservas"]) == antes:
        flash("Esa reserva no existe o no es tuya.", "error")
    else:
        flash("Reserva cancelada.", "ok")
    guardar_datos(datos)
    return redirect(url_for("mis_reservas"))


@app.route("/favoritos")
@login_requerido
def favoritos():
    datos = cargar_datos()
    u = usuario_actual()
    items = [i for i in datos["items"] if i["id"] in u.get("favoritos", [])]
    return render_template("favoritos.html", items=items, favoritos=u.get("favoritos", []))


@app.route("/favoritos/toggle/<int:item_id>", methods=["POST"])
@login_requerido
def favorito_toggle(item_id):
    datos = cargar_datos()
    u = next((u for u in datos["usuarios"] if u["id"] == session["usuario_id"]), None)
    if not u or not any(i for i in datos["items"] if i["id"] == item_id):
        abort(404)
    u.setdefault("favoritos", [])
    if item_id in u["favoritos"]:
        u["favoritos"].remove(item_id)
        flash("Sacado de favoritos.", "ok")
    else:
        u["favoritos"].append(item_id)
        flash("Agregado a favoritos.", "ok")
    guardar_datos(datos)
    return redirect(request.referrer or url_for("index"))


@app.route("/notificaciones")
@login_requerido
def notificaciones():
    datos = cargar_datos()
    u = next(u for u in datos["usuarios"] if u["id"] == session["usuario_id"])
    # Copias para conservar el estado "no leída" al renderizar
    notis = [dict(n) for n in reversed(u.get("notificaciones", []))]
    for n in u.get("notificaciones", []):
        n["leida"] = True
    guardar_datos(datos)
    return render_template("notificaciones.html", notificaciones=notis)


@app.route("/calendario")
@login_requerido
def calendario():
    import calendar as cal
    datos = cargar_datos()
    item_id = request.args.get("item", type=int)
    hoy = date.today()
    mes = request.args.get("mes", default=hoy.month, type=int)
    anio = request.args.get("anio", default=hoy.year, type=int)
    if mes is None:
        mes = hoy.month
    if anio is None:
        anio = hoy.year
    # Navegación prev/siguiente mes
    if mes < 1:
        mes, anio = 12, anio - 1
    elif mes > 12:
        mes, anio = 1, anio + 1
    if not 1900 <= anio <= 2100:
        flash("El año consultado no es válido.", "error")
        mes, anio = hoy.month, hoy.year

    ocupables = [i for i in datos["items"]
                 if i["tipo"] in ("proyector", "equipo", "audiovisual")]
    item = next((i for i in ocupables if i["id"] == item_id), None)
    if not item and ocupables:
        item = ocupables[0]

    dias_ocupados = set()
    if item:
        for p in datos["pedidos"]:
            if p["item_id"] != item["id"] or p["estado"] != "Entregado":
                continue
            if not p.get("fecha_devolucion"):
                continue
            d1 = None
            d2 = None
            try:
                d1 = date(*reversed([int(x) for x in p["fecha"].split("/")]))
                d2 = date(*reversed([int(x) for x in p["fecha_devolucion"].split("/")]))
            except (ValueError, TypeError):
                continue  # fecha corrupta: se ignora ese pedido
            if (d1.year == anio and d1.month == mes) or (d2.year == anio and d2.month == mes):
                inicio = d1.day if d1.year == anio and d1.month == mes else 1
                fin = d2.day if d2.year == anio and d2.month == mes \
                    else cal.monthrange(anio, mes)[1]
                dias_ocupados.update(range(inicio, fin + 1))

    return render_template(
        "calendario.html",
        item=item, ocupables=ocupables, mes=mes, anio=anio,
        semanas=cal.monthcalendar(anio, mes),
        dias_ocupados=dias_ocupados,
        nombre_mes=["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
                    "Diciembre"][mes],
    )


@app.route("/mis-pedidos")
@login_requerido
def mis_pedidos():
    datos = cargar_datos()
    pedidos = []
    # Fecha de devolución con aviso de vencido (tolera fechas corruptas)
    hoy = date.today()
    for p in datos["pedidos"]:
        if p["usuario_id"] != session["usuario_id"]:
            continue
        p = dict(p)
        if p["estado"] == "Entregado" and p.get("fecha_devolucion"):
            try:
                d, m, a = (int(x) for x in p["fecha_devolucion"].split("/"))
                p["vencido"] = hoy > date(a, m, d)
            except (ValueError, TypeError):
                p["vencido"] = False
        pedidos.append(p)
    return render_template("pedidos.html", pedidos=pedidos)


@app.route("/cancelar/<int:pedido_id>", methods=["POST"])
@login_requerido
def cancelar(pedido_id):
    datos = cargar_datos()
    pedido = next((p for p in datos["pedidos"] if p["id"] == pedido_id), None)
    if not pedido or pedido["usuario_id"] != session["usuario_id"]:
        flash("Ese pedido no existe o no es tuyo.", "error")
        return redirect(url_for("mis_pedidos"))
    if pedido["estado"] != "En proceso":
        flash("Solo se pueden cancelar pedidos que estén en proceso.", "error")
        return redirect(url_for("mis_pedidos"))
    liberar_item(datos, pedido["item_id"], pedido.get("cantidad", 1))
    pedido["estado"] = "Cancelado"
    guardar_datos(datos)
    flash("Pedido cancelado.", "ok")
    return redirect(url_for("mis_pedidos"))


# ---------------- Auth ----------------
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        datos = cargar_datos()
        nombre = request.form.get("nombre", "").strip()
        dni = request.form.get("dni", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not all([nombre, dni, email, password]):
            flash("Completá todos los campos.", "error")
            return redirect(url_for("registro"))
        if len(password) < 4:
            flash("La contraseña tiene que tener al menos 4 caracteres.", "error")
            return redirect(url_for("registro"))
        if any(u["email"] == email for u in datos["usuarios"]):
            flash("Ese correo ya está registrado.", "error")
            return redirect(url_for("registro"))
        nuevo = {
            "id": nuevo_id(datos, "siguiente_usuario_id", datos["usuarios"]),
            "nombre": nombre, "dni": dni, "email": email,
            "password": generate_password_hash(password),
            "admin": False, "socio": False,
            "metodo_pago": "Sin definir",
            "favoritos": [], "notificaciones": [],
        }
        datos["usuarios"].append(nuevo)
        datos["siguiente_usuario_id"] += 1
        guardar_datos(datos)
        # Higiene de sesión: no arrastrar datos de una sesión previa
        session.clear()
        session["usuario_id"] = nuevo["id"]
        return redirect(url_for("gracias"))
    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        datos = cargar_datos()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        u = next((u for u in datos["usuarios"] if u["email"] == email), None)
        if u and verificar_password(u["password"], password):
            # Migrar contraseñas viejas en texto plano a hash
            if not es_hash(u["password"]):
                u["password"] = generate_password_hash(password)
                guardar_datos(datos)
            session.clear()
            session["usuario_id"] = u["id"]
            flash(f'¡Hola, {u["nombre"]}!', "ok")
            return redirect(url_for("index"))
        flash("Correo o contraseña incorrectos.", "error")
        return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "ok")
    return redirect(url_for("index"))


@app.route("/hacerse-socio", methods=["POST"])
@login_requerido
def hacerse_socio():
    datos = cargar_datos()
    u = next(u for u in datos["usuarios"] if u["id"] == session["usuario_id"])
    u["socio"] = True
    guardar_datos(datos)
    flash("¡Ahora sos socio!", "ok")
    return redirect(url_for("index"))


@app.route("/cuenta", methods=["GET", "POST"])
@login_requerido
def cuenta():
    if request.method == "POST":
        datos = cargar_datos()
        u = next(u for u in datos["usuarios"] if u["id"] == session["usuario_id"])
        u["nombre"] = request.form.get("nombre", u["nombre"]).strip() or u["nombre"]
        u["dni"] = request.form.get("dni", u["dni"]).strip() or u["dni"]
        nueva_pass = request.form.get("password", "").strip()
        if nueva_pass:
            u["password"] = generate_password_hash(nueva_pass)
        u["metodo_pago"] = request.form.get("metodo_pago", u.get("metodo_pago", "—"))
        guardar_datos(datos)
        flash("Datos actualizados.", "ok")
        return redirect(url_for("cuenta"))
    return render_template("cuenta.html")


# ---------------- Admin ----------------
@app.route("/admin")
@admin_requerido
def admin():
    datos = cargar_datos()
    return render_template("admin.html", items=datos["items"],
                           pedidos=datos["pedidos"],
                           usuarios=datos["usuarios"])


@app.route("/admin/item/nuevo", methods=["POST"])
@admin_requerido
def admin_nuevo_item():
    datos = cargar_datos()
    titulo = request.form.get("titulo", "").strip()
    if not titulo:
        flash("El elemento necesita un título.", "error")
        return redirect(url_for("admin"))
    try:
        stock = max(0, int(request.form.get("stock", "1")))
    except ValueError:
        stock = 1
    try:
        anio = int(request.form.get("anio") or 0) or date.today().year
    except ValueError:
        anio = date.today().year
    datos["items"].append({
        "id": nuevo_id(datos, "siguiente_item_id", datos["items"]),
        "tipo": request.form.get("tipo", "libro"),
        "titulo": titulo,
        "autor": request.form.get("autor", "").strip(),
        "descripcion": request.form.get("descripcion", "").strip(),
        "sinopsis": request.form.get("descripcion", "").strip(),
        "genero": request.form.get("genero", "Varios").strip() or "Varios",
        "anio": anio,
        "stock": stock,
        "disponible": stock > 0,
        "portada": "\U0001F4D6",
        "color": "#e8dcc8",
    })
    datos["siguiente_item_id"] += 1
    guardar_datos(datos)
    flash("Elemento agregado.", "ok")
    return redirect(url_for("admin"))


@app.route("/admin/item/eliminar/<int:item_id>", methods=["POST"])
@admin_requerido
def admin_eliminar_item(item_id):
    datos = cargar_datos()
    datos["items"] = [i for i in datos["items"] if i["id"] != item_id]
    guardar_datos(datos)
    flash("Elemento eliminado.", "ok")
    return redirect(url_for("admin"))


@app.route("/admin/pedido/<int:pedido_id>/estado", methods=["POST"])
@admin_requerido
def admin_estado_pedido(pedido_id):
    datos = cargar_datos()
    pedido = next((p for p in datos["pedidos"] if p["id"] == pedido_id), None)
    nuevo_estado = request.form.get("estado")
    if not pedido or nuevo_estado not in ("En proceso", "Entregado", "Devuelto", "Cancelado"):
        return redirect(url_for("admin"))

    estado_anterior = pedido["estado"]

    # Evitar repetir efectos si el estado no cambia realmente
    if estado_anterior == nuevo_estado:
        flash("El pedido ya estaba en ese estado.", "error")
        return redirect(url_for("admin"))
    if estado_anterior == "Devuelto" and nuevo_estado == "Entregado":
        flash("Ese pedido ya fue devuelto: para volver a llevarlo, "
              "el alumno tiene que hacer un pedido nuevo.", "error")
        return redirect(url_for("admin"))

    # Al entregar hay que registrar el número de inventario
    if nuevo_estado == "Entregado":
        inventario = request.form.get("inventario", "").strip()
        if not inventario:
            flash("Para marcar como Entregado primero cargá el número de inventario.", "error")
            return redirect(url_for("admin"))
        pedido["inventario"] = inventario
        # Fecha de devolución: la que cargue el admin o 7 días por defecto
        if not pedido.get("fecha_devolucion"):
            try:
                d, m, a = (int(x) for x in request.form.get("fecha_devolucion", "").split("-")[::-1])
                date(a, m, d)  # valida la fecha
                pedido["fecha_devolucion"] = f"{d:02d}/{m:02d}/{a}"
            except (ValueError, TypeError):
                f = date.today() + timedelta(days=DIAS_PRESTAMO)
                pedido["fecha_devolucion"] = f.strftime("%d/%m/%Y")
        notificar(datos, pedido["usuario_id"],
                  f'Tu pedido de "{pedido["item_titulo"]}" fue entregado. '
                  f'Devolución: {pedido["fecha_devolucion"]}.')

    pedido["estado"] = nuevo_estado
    # Restaurar stock una sola vez: solo si el pedido estaba ocupando unidades
    if nuevo_estado in ("Devuelto", "Cancelado") \
            and estado_anterior in ("En proceso", "Entregado"):
        liberar_item(datos, pedido["item_id"], pedido.get("cantidad", 1))
        if nuevo_estado == "Devuelto" and estado_anterior == "Entregado":
            notificar(datos, pedido["usuario_id"],
                      f'Registramos la devolución de "{pedido["item_titulo"]}". ¡Gracias!')
    guardar_datos(datos)
    flash("Estado actualizado.", "ok")
    return redirect(url_for("admin"))


# ---------------- Páginas estáticas y SEO ----------------
@app.route("/gracias")
@login_requerido
def gracias():
    return render_template("gracias.html")


@app.route("/privacidad")
def privacidad():
    return render_template("privacidad.html")


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/sitemap.xml")
def sitemap():
    base = request.url_root.rstrip("/")
    rutas = [("/", "1.0"), ("/catalogo", "0.9"), ("/faq", "0.6"),
             ("/privacidad", "0.4"), ("/login", "0.4"), ("/registro", "0.4")]
    lineas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for ruta, prioridad in rutas:
        lineas.append(f"  <url><loc>{base}{ruta}</loc>"
                      f"<priority>{prioridad}</priority></url>")
    lineas.append("</urlset>")
    return Response("\n".join(lineas), mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    return Response(
        "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /cuenta\n"
        "Disallow: /mis-pedidos\nSitemap: " + request.url_root.rstrip("/")
        + "/sitemap.xml\n",
        mimetype="text/plain")


@app.route("/llms.txt")
def llms():
    return Response(
        "# Biblioteca Escolar\n\n"
        "> Sistema web de préstamos de la biblioteca escolar. "
        "Permite buscar y solicitar libros, proyectores, materiales, "
        "equipos audiovisuales y más.\n\n"
        "## Secciones\n- / : inicio\n- /catalogo : búsqueda y filtros\n"
        "- /faq : preguntas frecuentes\n- /privacidad : privacidad\n",
        mimetype="text/plain")


@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("404.html"), 404


@app.errorhandler(403)
def acceso_denegado(e):
    return render_template("403.html", descripcion=e.description), 403


@app.errorhandler(500)
def error_interno(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)
