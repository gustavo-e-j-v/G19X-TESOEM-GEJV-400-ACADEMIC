"""
Tema visual de la documentación interactiva (/docs).

Paleta inspirada en un control de videojuegos: grafito oscuro con acento
turquesa. Cada sección (tag) de la API es un panel, y sus endpoints se
acomodan como tarjetas en dos columnas; al abrir una tarjeta ocupa todo el
ancho para que el formulario y la respuesta se lean cómodos.

Para cambiar los colores basta con editar las variables de :root en CSS.
No toca la lógica de la API ni la autenticación: solo agrega estilos y un
encabezado a la página que genera FastAPI.
"""

import os
import re
from html import escape

from fastapi.openapi.docs import get_swagger_ui_html

from config import AUTH_DISABLED

FUENTES_HTML = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=IBM+Plex+Mono:wght@400;500;600&family=Sora:wght@400;500;600;700&display=swap">'
)

CSS = r"""
/* ===================== Paleta y tipografía ===================== */
:root {
  --bg: #12151a;
  --bg-2: #171b21;
  --card: #1e232a;
  --card-2: #262c34;
  --line: #323943;
  --text: #e8ecf0;
  --dim: #9ba5b0;
  --mute: #6c7782;

  --accent: #30c4c9;
  --accent-ink: #0b1417;
  --accent-soft: rgba(48, 196, 201, 0.14);

  --get: #30c4c9;
  --post: #5ad7a8;
  --put: #e8b04f;
  --patch: #9b8cf0;
  --delete: #ef6f61;

  --radius: 14px;
  --font: 'Sora', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Consolas, monospace;
  color-scheme: dark;
}

html, body { background: var(--bg); }
body {
  margin: 0;
  color: var(--text);
  font-family: var(--font);
  -webkit-font-smoothing: antialiased;
}

/* ===================== Encabezado ===================== */
.hero {
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid var(--line);
  background:
    radial-gradient(900px 280px at 88% -30%, rgba(48, 196, 201, 0.22), transparent 62%),
    linear-gradient(180deg, #1a2026, #14181d);
}
.hero::after {
  content: "";
  position: absolute;
  right: -70px;
  top: -90px;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  border: 1px solid rgba(48, 196, 201, 0.28);
  box-shadow: 0 0 0 30px rgba(48, 196, 201, 0.05), 0 0 0 68px rgba(48, 196, 201, 0.03);
  pointer-events: none;
}
.hero-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  max-width: 1180px;
  margin: 0 auto;
  padding: 44px 24px 36px;
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: flex-end;
  justify-content: space-between;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  border: 1px solid rgba(48, 196, 201, 0.35);
  border-radius: 999px;
  background: rgba(48, 196, 201, 0.08);
  color: var(--accent);
  font: 500 12px var(--mono);
}
.chip::before {
  content: "";
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 3px rgba(48, 196, 201, 0.25);
}
.chip-warn {
  margin-left: 8px;
  border-color: rgba(239, 111, 97, 0.45);
  background: rgba(239, 111, 97, 0.1);
  color: #f3b3a8;
}
.chip-warn::before { background: var(--delete); box-shadow: 0 0 0 3px rgba(239, 111, 97, 0.25); }
.hero h1 {
  margin: 16px 0 10px;
  font: 700 34px/1.15 var(--font);
  letter-spacing: -0.02em;
}
.hero p {
  margin: 0;
  max-width: 620px;
  color: var(--dim);
  font-size: 14px;
  line-height: 1.65;
}
.hero-links { display: flex; flex-wrap: wrap; gap: 10px; }
.hero-btn {
  display: inline-flex;
  align-items: center;
  padding: 10px 18px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  color: var(--text);
  font: 600 13px var(--font);
  text-decoration: none;
  transition: border-color 0.15s, background 0.15s;
}
.hero-btn:hover { border-color: var(--accent); background: var(--accent-soft); }
.hero-btn-primary { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }
.hero-btn-primary:hover { background: #4fd3d7; border-color: #4fd3d7; }

/* ===================== Contenedor general ===================== */
.swagger-ui { font-family: var(--font); color: var(--text); }
.swagger-ui .wrapper { max-width: 1180px; padding: 0 24px; }
.swagger-ui .information-container { display: none; }
.swagger-ui a { color: var(--accent); }
.swagger-ui a.nostyle, .swagger-ui a.nostyle:visited { color: inherit; }

/* Barra de acceso (Authorize) */
.swagger-ui .scheme-container {
  margin: 0;
  padding: 24px 0 4px;
  background: transparent;
  box-shadow: none;
}
.swagger-ui .scheme-container .schemes {
  display: flex;
  align-items: center;
  gap: 16px;
  box-sizing: border-box;
  width: min(1132px, calc(100% - 48px));
  margin: 0 auto;
  padding: 14px 18px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}
.swagger-ui .scheme-container .schemes::before {
  content: "Acceso protegido con Microsoft Entra ID. Inicia sesión para probar los endpoints.";
  flex: 1;
  color: var(--dim);
  font-size: 13px;
  line-height: 1.5;
}
.swagger-ui .scheme-container .auth-wrapper { flex: 0 0 auto; }
.swagger-ui .btn.authorize {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  background: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 10px;
  color: var(--accent-ink);
  font: 600 13px var(--font);
  box-shadow: none;
}
.swagger-ui .btn.authorize svg { fill: var(--accent-ink); }
.swagger-ui .btn.authorize:hover { background: #4fd3d7; border-color: #4fd3d7; }

/* ===================== Secciones (tags) como paneles ===================== */
.swagger-ui .opblock-tag-section {
  margin: 28px 0 0;
  padding: 4px 20px 20px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: 18px;
}
.swagger-ui .opblock-tag {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  padding: 18px 0 14px;
  border: 0;
  color: var(--text);
  font: 700 18px var(--font);
}
.swagger-ui .opblock-tag::before {
  content: "";
  flex: 0 0 5px;
  height: 22px;
  border-radius: 3px;
  background: var(--accent);
}
.swagger-ui .opblock-tag:hover { background: transparent; }
.swagger-ui .opblock-tag small {
  flex: 1;
  color: var(--dim);
  font: 400 13px var(--font);
}
.swagger-ui .opblock-tag small .markdown p,
.swagger-ui .opblock-tag small p { margin: 0; color: var(--dim); }
.swagger-ui .opblock-tag svg { fill: var(--dim); }

/* ===================== Endpoints como tarjetas en dos columnas ===================== */
.swagger-ui div:has(> span > .opblock) {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  align-items: start;
}
.swagger-ui span:has(> .opblock.is-open) { grid-column: 1 / -1; }

.swagger-ui .opblock,
.swagger-ui .opblock.opblock-get,
.swagger-ui .opblock.opblock-post,
.swagger-ui .opblock.opblock-put,
.swagger-ui .opblock.opblock-delete,
.swagger-ui .opblock.opblock-patch {
  margin: 0;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: none;
  overflow: hidden;
  transition: border-color 0.15s;
}
.swagger-ui .opblock:hover { border-color: rgba(48, 196, 201, 0.55); }
.swagger-ui .opblock.is-open { border-color: rgba(48, 196, 201, 0.55); }

.swagger-ui .opblock .opblock-summary {
  padding: 14px 12px 14px 16px;
  border: 0;
  align-items: flex-start;
}
.swagger-ui .opblock.is-open .opblock-summary { border-bottom: 1px solid var(--line); }

.swagger-ui .opblock .opblock-summary-control {
  display: grid;
  grid-template-columns: auto 1fr auto;
  grid-template-areas: "metodo . flecha" "texto texto texto";
  gap: 10px 12px;
  align-items: center;
  flex: 1;
  min-width: 0;
  padding: 0;
  background: none;
  border: 0;
  cursor: pointer;
  text-align: left;
  font-family: var(--font);
  color: var(--text);
}
.swagger-ui .opblock .opblock-summary-method {
  grid-area: metodo;
  min-width: 0;
  padding: 4px 10px;
  border-radius: 8px;
  color: var(--accent-ink);
  font: 700 11px var(--mono);
  letter-spacing: 0.06em;
  text-shadow: none;
}
.swagger-ui .opblock .opblock-summary-path-description-wrapper {
  grid-area: texto;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
  min-width: 0;
  padding: 0;
}
.swagger-ui .opblock .opblock-summary-path {
  flex: none;
  max-width: 100%;
  padding: 0;
  color: var(--text);
  font: 600 13px var(--mono);
  word-break: break-all;
}
.swagger-ui .opblock .opblock-summary-description {
  padding: 0;
  color: var(--dim);
  font: 400 13px var(--font);
  text-align: left;
}
.swagger-ui .opblock .authorization__btn { padding: 0 2px 0 8px; opacity: 0.8; }
.swagger-ui .opblock .authorization__btn svg { fill: var(--dim); }

.swagger-ui .opblock-get .opblock-summary-method { background: var(--get); }
.swagger-ui .opblock-post .opblock-summary-method { background: var(--post); }
.swagger-ui .opblock-put .opblock-summary-method { background: var(--put); }
.swagger-ui .opblock-patch .opblock-summary-method { background: var(--patch); }
.swagger-ui .opblock-delete .opblock-summary-method { background: var(--delete); }

/* ===================== Contenido de una tarjeta abierta ===================== */
.swagger-ui .opblock-body { background: transparent; }
.swagger-ui .opblock .opblock-section-header {
  padding: 12px 20px;
  background: var(--card-2);
  border-bottom: 1px solid var(--line);
  box-shadow: none;
}
.swagger-ui .opblock .opblock-section-header h4,
.swagger-ui .opblock .opblock-section-header label,
.swagger-ui .opblock .opblock-section-header label span { color: var(--text); font-family: var(--font); }
.swagger-ui .opblock-description-wrapper,
.swagger-ui .opblock-external-docs-wrapper,
.swagger-ui .opblock-title_normal {
  padding: 14px 20px;
  color: var(--dim);
  font-family: var(--font);
}
.swagger-ui .opblock-description-wrapper p,
.swagger-ui .opblock-external-docs-wrapper p,
.swagger-ui .opblock-title_normal p { color: var(--dim); font-size: 13px; }
.swagger-ui .opblock .opblock-section { padding-bottom: 6px; }

.swagger-ui table thead tr td,
.swagger-ui table thead tr th {
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  color: var(--dim);
  font: 600 12px var(--font);
}
.swagger-ui table tbody tr td { padding: 12px; border-bottom: 1px solid var(--line); color: var(--text); }
.swagger-ui .parameters-col_description p,
.swagger-ui .response-col_description p,
.swagger-ui .markdown p,
.swagger-ui .renderedMarkdown p { color: var(--dim); font-size: 13px; }
.swagger-ui .parameter__name, .swagger-ui .parameter__type,
.swagger-ui .parameter__in, .swagger-ui .response-col_status,
.swagger-ui .response-col_links { color: var(--text); font-family: var(--font); }
.swagger-ui .parameter__name.required::after { color: var(--delete); }
.swagger-ui .parameter__type, .swagger-ui .parameter__in { color: var(--mute); font-family: var(--mono); font-size: 12px; }
.swagger-ui .responses-inner h4, .swagger-ui .responses-inner h5 { color: var(--text); font-family: var(--font); }
.swagger-ui .tab li { color: var(--dim); font-family: var(--font); }
.swagger-ui .tab li.active { color: var(--text); }
.swagger-ui .tab li button.tablinks { color: inherit; font-family: var(--font); background: none; }
.swagger-ui label { color: var(--text); font-family: var(--font); }

/* Formularios y botones */
.swagger-ui input[type=text], .swagger-ui input[type=password], .swagger-ui input[type=search],
.swagger-ui input[type=email], .swagger-ui input[type=file], .swagger-ui textarea, .swagger-ui select {
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 13px;
}
.swagger-ui input:focus, .swagger-ui textarea:focus, .swagger-ui select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}
.swagger-ui select { background-color: var(--bg); }
.swagger-ui .btn {
  border-radius: 8px;
  background: transparent;
  border: 1px solid var(--line);
  color: var(--text);
  font: 600 13px var(--font);
  box-shadow: none;
}
.swagger-ui .btn:hover { box-shadow: none; border-color: var(--accent); }
.swagger-ui .btn.try-out__btn { border-color: var(--accent); color: var(--accent); }
.swagger-ui .btn.try-out__btn.cancel { border-color: var(--delete); color: var(--delete); }
.swagger-ui .btn.execute { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }
.swagger-ui .btn.execute:hover { background: #4fd3d7; }
.swagger-ui .btn-group .btn.btn-clear { border-color: var(--line); color: var(--dim); }
.swagger-ui .execute-wrapper { padding: 14px 20px; }

/* Bloques de código y respuestas */
.swagger-ui .highlight-code > .microlight,
.swagger-ui .highlight-code pre,
.swagger-ui pre.microlight,
.swagger-ui .example pre,
.swagger-ui pre {
  background: #0e1115 !important;
  border: 1px solid var(--line);
  border-radius: 10px;
  font-family: var(--mono);
  font-size: 12.5px;
}
.swagger-ui .responses-table .response-col_description__inner pre { margin: 0; }
.swagger-ui .copy-to-clipboard { background: var(--accent); border-radius: 8px; }
.swagger-ui .live-responses-table .response-col_status { color: var(--text); }
.swagger-ui .response-controls .response-control-media-type__accept-message { color: var(--accent); }
.swagger-ui .opblock-body .opblock-section-request-body .opblock-section-header { background: var(--card-2); }

/* Esquemas (modelos) */
.swagger-ui section.models {
  margin: 28px 0 40px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: 18px;
}
.swagger-ui section.models.is-open h4 { border-bottom: 1px solid var(--line); }
.swagger-ui section.models h4 { color: var(--text); font: 700 16px var(--font); }
.swagger-ui section.models h4 svg { fill: var(--dim); }
.swagger-ui section.models .model-container {
  margin: 10px 20px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 10px;
}
.swagger-ui .model-box, .swagger-ui .model { color: var(--text); font-family: var(--mono); }
.swagger-ui .model .property.primitive { color: var(--dim); }
.swagger-ui .model-title { color: var(--text); font-family: var(--font); }
.swagger-ui .prop-type { color: var(--accent); }
.swagger-ui .prop-format { color: var(--mute); }
.swagger-ui section.models .model-container .model-box-control,
.swagger-ui .model-toggle::after { filter: invert(0.75); }

/* ===================== Ventana de autorización ===================== */
.swagger-ui .dialog-ux .backdrop-ux { background: rgba(5, 8, 10, 0.72); }
.swagger-ui .dialog-ux .modal-ux {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 18px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.55);
  color: var(--text);
}
.swagger-ui .dialog-ux .modal-ux-header { border-bottom: 1px solid var(--line); padding: 16px 20px; }
.swagger-ui .dialog-ux .modal-ux-header h3 { color: var(--text); font: 700 18px var(--font); }
.swagger-ui .dialog-ux .modal-ux-content { color: var(--dim); padding: 20px; }
.swagger-ui .dialog-ux .modal-ux-content p,
.swagger-ui .dialog-ux .modal-ux-content h4,
.swagger-ui .dialog-ux .modal-ux-content h6,
.swagger-ui .dialog-ux .modal-ux-content label,
.swagger-ui .dialog-ux .modal-ux-content code { color: var(--dim); font-family: var(--font); }
.swagger-ui .dialog-ux .modal-ux-content h4 { color: var(--text); font-size: 15px; }
.swagger-ui .auth-container { border-bottom: 1px solid var(--line); }
.swagger-ui .auth-container:last-of-type { border-bottom: 0; }
.swagger-ui .auth-container h4 { color: var(--text); }
.swagger-ui .auth-container .wrapper { padding: 0; }
.swagger-ui .dialog-ux .close-modal svg { fill: var(--dim); }
.swagger-ui .dialog-ux .scopes h2 { color: var(--text); }
.swagger-ui .dialog-ux .scope-def p, .swagger-ui .dialog-ux .scope-def .name { color: var(--dim); }
.swagger-ui .auth-btn-wrapper { padding-top: 14px; }
.swagger-ui .auth-btn-wrapper .btn.modal-btn.auth { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }
.swagger-ui .auth-btn-wrapper .btn.modal-btn.auth svg { fill: var(--accent-ink); }
.swagger-ui .errors-wrapper { background: rgba(239, 111, 97, 0.12); border: 1px solid rgba(239, 111, 97, 0.4); border-radius: 10px; }
.swagger-ui .errors-wrapper .error-wrapper, .swagger-ui .errors-wrapper hgroup h4 { color: #f3b3a8; }

/* ===================== Ajustes finos ===================== */

/* Los íconos de Swagger se pintan con currentColor: se colorean con "color" */
.swagger-ui .opblock-tag .expand-operation,
.swagger-ui .opblock-tag .expand-operation svg,
.swagger-ui .opblock-control-arrow,
.swagger-ui .opblock-control-arrow svg,
.swagger-ui .authorization__btn,
.swagger-ui .authorization__btn svg,
.swagger-ui section.models h4 svg,
.swagger-ui .model-box-control svg,
.swagger-ui .dialog-ux .close-modal svg { color: var(--dim); }
.swagger-ui .authorization__btn.locked,
.swagger-ui .authorization__btn.locked svg { color: var(--accent); }
.swagger-ui .opblock-control-arrow:hover svg,
.swagger-ui .expand-operation:hover svg { color: var(--text); }
.swagger-ui .btn.authorize, .swagger-ui .btn.authorize svg { color: var(--accent-ink); }

/* Colores de método: misma especificidad que Swagger, y se carga después */
.swagger-ui .opblock.opblock-get .opblock-summary-method { background: var(--get); }
.swagger-ui .opblock.opblock-post .opblock-summary-method { background: var(--post); }
.swagger-ui .opblock.opblock-put .opblock-summary-method { background: var(--put); }
.swagger-ui .opblock.opblock-patch .opblock-summary-method { background: var(--patch); }
.swagger-ui .opblock.opblock-delete .opblock-summary-method { background: var(--delete); }

/* Foco visible con el color de acento */
.swagger-ui .opblock-summary-control:focus-visible,
.swagger-ui .expand-operation:focus-visible,
.swagger-ui .opblock-control-arrow:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 8px; }

/* Selector de tipo de contenido y esquemas */
.swagger-ui .response-control-media-type--accept-controller select { border-color: var(--accent); }
.swagger-ui section.models h4 { padding: 14px 20px; margin: 0; cursor: pointer; }
.swagger-ui section.models .model-container { margin: 10px 20px; }

/* Ventana de autorización: tipografía, campos, casillas y enlaces */
.swagger-ui .dialog-ux .modal-ux :not(input):not(svg):not(path):not(textarea) { font-family: var(--font); }
.swagger-ui .dialog-ux .modal-ux-content p,
.swagger-ui .dialog-ux .modal-ux-content label,
.swagger-ui .dialog-ux .modal-ux-content .scope-def p { font-size: 13px; line-height: 1.55; }
.swagger-ui .dialog-ux .auth-container input[type=text],
.swagger-ui .dialog-ux .auth-container input[type=password] { width: 100%; box-sizing: border-box; padding: 9px 12px; }
.swagger-ui .dialog-ux .scopes h2 a, .swagger-ui .dialog-ux .modal-ux-content a { color: var(--accent); }
.swagger-ui .checkbox input[type=checkbox] + label > .item { background-color: var(--bg) !important; box-shadow: 0 0 0 1px var(--line); }
.swagger-ui .checkbox input[type=checkbox]:checked + label > .item { background-color: var(--accent) !important; box-shadow: 0 0 0 1px var(--accent); }
.swagger-ui .dialog-ux .modal-ux-content code {
  padding: 2px 8px; border-radius: 6px; background: var(--accent-soft); color: var(--accent); font-family: var(--mono);
}
.swagger-ui .auth-btn-wrapper .btn.modal-btn { padding: 9px 18px; }
.swagger-ui .dialog-ux .modal-ux { max-width: 640px; }
.swagger-ui .dialog-ux .modal-ux-content { max-height: calc(100vh - 170px); }

/* ===================== Pantallas angostas ===================== */
@media (max-width: 860px) {
  .swagger-ui div:has(> span > .opblock) { grid-template-columns: minmax(0, 1fr); }
  .hero h1 { font-size: 26px; }
  .hero-inner { padding: 32px 20px 28px; }
  .swagger-ui .wrapper { padding: 0 16px; }
  .swagger-ui .scheme-container .schemes { flex-wrap: wrap; width: calc(100% - 32px); }
  .swagger-ui .opblock-tag-section { padding: 2px 14px 14px; }
  .swagger-ui .opblock-tag { flex-wrap: wrap; row-gap: 4px; }
  .swagger-ui .opblock-tag small { order: 3; flex: 1 1 100%; }
  .swagger-ui .opblock-tag .expand-operation { margin-left: auto; }
}

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: var(--card-2); border-radius: 8px; border: 2px solid var(--bg); }
::-webkit-scrollbar-track { background: var(--bg); }
"""


def _encabezado(app) -> str:
    titulo = escape(app.title)
    version = escape(str(app.version))
    descripcion = escape(app.description or "")
    frontend = escape(os.getenv("FRONTEND_URL", "http://localhost:5173"))
    openapi = escape(app.openapi_url or "/openapi.json")
    aviso_local = '<span class="chip chip-warn">Modo local · sin autenticación</span>' if AUTH_DISABLED else ""
    return f"""
<header class="hero">
  <div class="hero-inner">
    <div class="hero-text">
      <span class="chip">API REST · v{version}</span>{aviso_local}
      <h1>{titulo}</h1>
      <p>{descripcion}</p>
    </div>
    <nav class="hero-links">
      <a class="hero-btn hero-btn-primary" href="{frontend}" target="_blank" rel="noopener">Abrir aplicación</a>
      <a class="hero-btn" href="{openapi}" target="_blank" rel="noopener">OpenAPI JSON</a>
    </nav>
  </div>
</header>
"""


def construir_docs_html(app) -> str:
    """Genera la página de Swagger UI de FastAPI con el tema y el encabezado propios."""
    respuesta = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} · Documentación",
        oauth2_redirect_url="/oauth2-redirect",
        init_oauth=getattr(app, "swagger_ui_init_oauth", None),
        swagger_ui_parameters={
            "docExpansion": "list",          # secciones abiertas y tarjetas cerradas al entrar
            "defaultModelsExpandDepth": 0,   # esquemas colapsados
            "displayRequestDuration": True,
            "syntaxHighlight": {"theme": "nord"},
        },
    )
    html = respuesta.body.decode("utf-8")

    # Si FastAPI cambiara la estructura del HTML, se devuelve la página original
    # (sin tema) en vez de romper la documentación.
    if "</head>" not in html:
        return html

    html = html.replace("</head>", f"{FUENTES_HTML}<style>{CSS}</style></head>", 1)
    html = re.sub(r"<body[^>]*>", lambda m: m.group(0) + _encabezado(app), html, count=1)
    return html
