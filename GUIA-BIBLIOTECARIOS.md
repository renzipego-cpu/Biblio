# Guía de uso para el personal de biblioteca

Sistema de préstamos — Biblioteca Escolar
Dirección de la web: `renix13.pythonanywhere.com` (o la que use tu escuela)
Este instructivo explica todo lo que hacen los bibliotecarios día a día.

---

## 1. Ingresar por primera vez

1. Abrí la web y tocá **Iniciar sesión** (arriba a la derecha).
2. Entrá con la cuenta de bibliotecaria:
   - **Correo:** `admin@escuela.edu`
   - **Contraseña:** `admin123`
3. **Cambiá la contraseña ya**: andá a **Mi cuenta → Configuración**, escribí una nueva y tocá **Actualizar contraseña**. No compartas esta cuenta: todo lo que hace una cuenta admin queda bajo su responsabilidad.

Con esa cuenta ves el menú **Administración** en la barra lateral y podés usar el **modo mostrador** (punto 6).

---

## 2. Mapa de las herramientas

| Herramienta | Dirección | Para qué sirve |
|---|---|---|
| Panel de administración | `renix13.pythonanywhere.com/admin` | Todo en tablas: pedidos, inventario, usuarios, vencidos |
| Modo mostrador (kiosco) | `renix13.pythonanywhere.com/mostrador` | Pantalla grande para la compu del mostrador: entregar, devolver y ver vencidos en tres toques |
| Estadísticas | `renix13.pythonanywhere.com/admin/estadisticas` | Los más pedidos, pedidos por mes, totales |

El resto de la web es para los alumnos: buscador, catálogo y sus propios pedidos.

---

## 3. El ciclo de vida de un préstamo

Es importante entender los cuatro estados antes de operar:

```
[Alumno solicita]
       |
       v
  EN PROCESO  ---- (el alumno puede cancelarlo)
       |
       v
   ENTREGADO  ----- (con N° de inventario y fecha de devolución)
       |
       v
    DEVUELTO   ---- (el stock vuelve a estar disponible)

En cualquier momento el bibliotecario puede marcar CANCELADO
(solo se recomienda si hubo un error).
```

**Reglas que el sistema impone solo:**

- Máximo **5 unidades pedidas a la vez** por alumno (contando cantidades).
- Un alumno no puede pedir el mismo elemento dos veces mientras tenga un pedido activo de él.
- Al pedir, el stock baja; al devolver o cancelar, sube.
- No se puede marcar dos veces el mismo estado, ni re-entregar algo ya devuelto. Si el alumno lo necesita de nuevo, **que haga un pedido nuevo**.
- No se puede cancelar un pedido ya **Entregado** (el alumno ya tiene el elemento en su poder; devolvélo normalmente).

---

## 4. Entregar un pedido (desde el panel)

1. Andá a **Administración**.
2. En la tabla **Pedidos**, localizá el pedido (podés usar el buscador de arriba con el **DNI, nombre del alumno o título del elemento**).
3. En la columna **Cambiar estado** del pedido:
   - Escribí el **N° de inventario** del ejemplar físico que le das (es **obligatorio** para entregar).
   - Elegí la **fecha de devolución** si querés otra distinta a la que aparece (si la dejas vacía, el sistema pone 7 días).
   - Seleccioná **Entregado** en la lista.
   - Tocá **Guardar**.
4. El alumno recibe automáticamente una notificación con la fecha de devolución.

> Si tocás Entregado sin N° de inventario, el sistema te lo va a pedir de nuevo. No entrega "a medias".

---

## 5. Registrar una devolución

1. En **Administración → Pedidos**, buscá al alumno por DNI o nombre.
2. Cambiá el estado a **Devuelto** y tocá **Guardar**.
3. El sistema, automáticamente:
   - devuelve las unidades al stock,
   - le avisa al alumno ("Registramos la devolución"),
   - si había alguien en la **cola de reserva** de ese elemento, le llega el aviso de que ya está disponible.

El alumno también ve la devolución reflejada en su **Historial de pedidos**.

---

## 6. El modo mostrador (recomendado para el día a día)

Es la pantalla pensada para la compu (o tablet) del mostrador, con botones grandes. Dejala abierta todo el día.

### 6.1 Entregar con el mostrador

1. Abrí `renix13.pythonanywhere.com/mostrador`.
2. Tocá **Entregar**.
3. Escribí el **DNI o el nombre** del alumno y **Buscar**.
4. Aparece el alumno con sus pedidos en proceso.
5. En cada pedido: cargá el **N° inventario**, controlá la fecha de devolución (viene con +7 días) y tocá **Entregar** (botón verde).
6. Volvés automáticamente al menú para atender al siguiente.

### 6.2 Recibir una devolución con el mostrador

1. Tocá **Devolver**.
2. Buscá al alumno por DNI o nombre.
3. Tocá **Recibir devolución** en el elemento que trae. Listo: stock restaurado, alumno notificado.

### 6.3 Pedidos vencidos

1. Tocá **Vencidos** (si hay, el botón se pone rojo con la cantidad).
2. Ves la lista: alumno, DNI, elemento y fecha en que venció.
3. Tocá **Copiar** en cada fila para llevarte el texto listo para pegar en un correo o mensaje.

---

## 7. Rutinas recomendadas

**Al abrir la biblioteca (mañana):**
1. Abrí el **mostrador** en la compu del mostrador.
2. Mirá si el botón **Vencidos** tiene número rojo. Si hay, contactá a esos alumnos (botón Copiar).
3. Revisá la tabla de pedidos **En proceso**: son los que vinieron a buscar durante la mañana.

**Al cerrar:**
1. Entregá o devolvé lo que quedó pendiente en el día.
2. Un vistazo a **Estadísticas** si tenés que armar un informe mensual.

---

## 8. Gestionar el inventario

### Agregar un elemento nuevo
En **Administración → Inventario**, completá el formulario de arriba:

| Campo | Qué poner | Es obligatorio |
|---|---|---|
| Título | Nombre del libro o equipo | Sí |
| Autor / detalle | Autor del libro, o marca/modelo/lúmenes en equipos | No |
| Descripción | Sinopsis o características (la usa el buscador) | No |
| Género | Categoría (sirve para los filtros del catálogo) | No (va a "Varios") |
| Año | Año de edición o de compra | No |
| Stock | Cuántas unidades hay | No (va 1) |
| Tipo | Libro, Proyector, Material, Audiovisual, Equipo u Otro | No (va Libro) |

Tocá **Agregar** y aparece en el catálogo al instante, disponible para los alumnos.

### Corregir el stock
Si entra o sale una unidad que no pasó por un pedido (compra nueva, reposición, baja):
1. En la columna **Stock** de la tabla, escribí el número nuevo directamente en el campo.
2. Tocá el botón de guardar al lado.

El sistema recalcula solo si queda disponible o agotado.

### Eliminar un elemento
Botón **Eliminar** (pide confirmación). 
> Recomendación: eliminá solo si el elemento ya no existe físicamente. Si está prestado, esperá la devolución. Los pedidos históricos conservan el título, así que el historial no se rompe.

---

## 9. Reservas: cómo funcionan solas

Cuando un elemento está **No disponible**, el alumno puede **Reservarlo**. Vos no manejás nada a mano:

- Cada elemento mantiene su cola de reservas en orden de llegada.
- Cuando marcás la **devolución**, el primer alumno de la cola recibe una notificación automática: "Se liberó X, podés solicitarla ahora".
- A partir de ahí es del primero que pida (la reserva no bloquea el elemento para nadie).
- El alumno puede cancelar su reserva cuando quiera desde **Mis reservas**.
- Los alumnos ven su posición en la cola ("#2 de 3 en la cola").

---

## 10. Usuarios y socios

En **Administración → Usuarios** ves todos: nombre, DNI, correo, si son socios y si son administradores.

- **Socio:** es solo una membrecía simbólica que el alumno activa él mismo desde su perfil. No cambia permisos.
- Solo el personal de biblioteca debería tener la marca **Admin** (hoy en día, cuentas admin se crean editando `data.json`; consultá con quien administra el sistema antes de crear más).

---

## 11. Estadísticas

En **Administración → botón Estadísticas** encontrás:
- **Tarjetas de totales:** pedidos históricos, usuarios, elementos y vencidos (el de vencidos se pinta rojo si hay).
- **Los 5 más pedidos:** con barras, ideal para justificar compras.
- **Pedidos por mes** (últimos 6 meses): para ver la actividad del año.

Sirve como insumo para informes de dirección o cooperadora.

---

## 12. Problemas frecuentes

| Situación | Qué hacer |
|---|---|
| Marqué Entregado antes de tiempo / con error | Cambiá el estado de vuelta a **En proceso** o **Cancelado**: el stock se recalcula solo. |
| Me equivoqué y marqué Devuelto antes de tiempo | El sistema **no permite re-entregar** un pedido ya devuelto (protege el stock). Queda como registro de la devolución; el alumno puede hacer un pedido nuevo cuando lo necesite. |
| Marqué Entregado pero el alumno nunca lo retiró | Cambiá el estado a **Cancelado**: devuelve el stock al instante. |
| El alumno no encuentra el libro en el buscador | Probá sin tildes ("matematica") y con una sola palabra ("sapiens"). También busca en la descripción ("python"). |
| El alumno dice que no recibe notificaciones | Que toque la **campanita** arriba; ahí quedan todas. Se marcan como leídas al abrirlas. |
| Un alumno olvidó su contraseña | Hoy la única forma es que lo gestione quien administra el sistema (requiere acceso al servidor). Está en el listado de mejoras pendientes. |
| Un docente quiere un proyector para el jueves | Los pedidos son para el momento; no hay reserva con fecha futura (pendiente en el listado de ideas). Que lo pida ese día, o lo reserva si está prestado. |
| Cerré sin querer la sesión del mostrador | Volvé a entrar con la cuenta de bibliotecaria y reabrí `/mostrador`. |

---

## 13. Cuidados del sistema (importante)

1. **Cambiá la contraseña del admin** el primer día (punto 1).
2. **Copia de seguridad:** los datos viven en un archivo (`data.json`) en el servidor. Una vez por mes, entrá a PythonAnywhere → Files → `Biblio` → botón de descarga junto a `data.json`, y guardalo en la compu de la biblioteca.
3. No reveles la contraseña de bibliotecaria a los alumnos: con ella se puede modificar inventario y pedidos.
4. Si un cambio de estado no hace lo que esperabas, releé el punto 3: **el sistema no permite cambios duplicados ni fuera de orden** para proteger los datos.

---

*Guía escrita para el proyecto escolar "Biblioteca Escolar". Si agregás funciones nuevas, actualizá esta guía junto con el `README.md`.*
