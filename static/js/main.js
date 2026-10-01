// Iconos Lucide (si el CDN no carga, el resto de la página sigue andando)
if (window.lucide) {
    lucide.createIcons();
}

// CSRF: inyectar token oculto en todos los formularios POST
document.querySelectorAll('form[method="post"]').forEach((form) => {
    if (!form.querySelector('[name="csrf_token"]')) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'csrf_token';
        input.value = document.body.dataset.csrf;
        form.appendChild(input);
    }
});

// Modo oscuro
const temaToggle = document.getElementById('tema-toggle');
temaToggle?.addEventListener('click', () => {
    const html = document.documentElement;
    const oscuro = html.dataset.tema === 'oscuro';
    html.dataset.tema = oscuro ? '' : 'oscuro';
    localStorage.setItem('tema', oscuro ? 'claro' : 'oscuro');
});

// Menú móvil
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebar-overlay');
const abrir = () => {
    sidebar.classList.add('abierto');
    overlay.hidden = false;
};
const cerrar = () => {
    sidebar.classList.remove('abierto');
    overlay.hidden = true;
};
document.getElementById('sidebar-abrir')?.addEventListener('click', abrir);
document.getElementById('sidebar-cerrar')?.addEventListener('click', cerrar);
overlay?.addEventListener('click', cerrar);

// Volver arriba
const botonArriba = document.getElementById('volver-arriba');
window.addEventListener('scroll', () => {
    botonArriba.hidden = window.scrollY < 400;
});
botonArriba?.addEventListener('click', () =>
    window.scrollTo({ top: 0, behavior: 'smooth' }));

// Ver / ocultar contraseña
document.querySelectorAll('.campo-password').forEach((campo) => {
    const input = campo.querySelector('input');
    const boton = campo.querySelector('button');
    boton.addEventListener('click', () => {
        const visible = input.type === 'text';
        input.type = visible ? 'password' : 'text';
        boton.setAttribute('aria-label', visible ? 'Mostrar contraseña' : 'Ocultar contraseña');
        boton.classList.toggle('activo', !visible);
    });
});

// Botón de copiar
document.querySelectorAll('.btn-copiar').forEach((boton) => {
    const textoOriginal = boton.innerHTML;
    boton.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(boton.dataset.copiar);
            boton.innerHTML = 'Copiado';
        } catch {
            boton.innerHTML = 'No se pudo copiar';
        }
        setTimeout(() => { boton.innerHTML = textoOriginal; }, 1500);
    });
});

// Confirmaciones
document.querySelectorAll('form[data-confirmar]').forEach((form) => {
    form.addEventListener('submit', (e) => {
        if (!confirm(form.dataset.confirmar)) e.preventDefault();
    });
});

// Miniventana de cantidad al solicitar
const modal = document.getElementById('modal-cantidad');
const modalTitulo = document.getElementById('modal-item-nombre');
const modalStock = document.getElementById('modal-stock');
const modalInput = document.getElementById('modal-cantidad-input');
let formActivo = null;

function abrirModal(form) {
    formActivo = form;
    const max = parseInt(form.dataset.max, 10) || 1;
    modalTitulo.textContent = form.dataset.titulo;
    modalStock.textContent = max;
    modalInput.max = max;
    modalInput.value = 1;
    modal.hidden = false;
    modalInput.select();
}

function cerrarModal() {
    modal.hidden = true;
    formActivo = null;
}

document.querySelectorAll('form.js-solicitar').forEach((form) => {
    form.addEventListener('submit', (e) => {
        // Si ya tiene cantidad (viene del modal), deja pasar el submit
        if (form.querySelector('input[name="cantidad"]')) return;
        e.preventDefault();
        abrirModal(form);
    });
});

document.getElementById('modal-confirmar')?.addEventListener('click', () => {
    if (!formActivo) return;
    let cantidad = parseInt(modalInput.value, 10);
    const max = parseInt(modalInput.max, 10) || 1;
    if (isNaN(cantidad) || cantidad < 1) cantidad = 1;
    if (cantidad > max) cantidad = max;
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'cantidad';
    input.value = cantidad;
    formActivo.appendChild(input);
    const form = formActivo;
    cerrarModal();
    form.submit();  // .submit() nativo no vuelve a disparar el listener
});

modalInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById('modal-confirmar').click();
});

modal?.querySelectorAll('[data-cerrar-modal]').forEach((el) =>
    el.addEventListener('click', cerrarModal));
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal && !modal.hidden) cerrarModal();
});
