import html
import json
import os
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from models.commit_result import CommitResult
from services.commit_generation_service import CommitGenerationService
from storage.history import HistoryStorage
from utils.validators import validate_generation_input

load_dotenv()


def get_config(key: str, default: str | None = None) -> str | None:
    """Read a config value from Streamlit secrets first, then the environment.

    On Streamlit Cloud values live in st.secrets; locally they come from .env
    via python-dotenv. Accessing st.secrets raises when no secrets file exists,
    so the lookup is guarded.
    """
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


COMMIT_STYLE_OPTIONS = [
    "conventional",
    "simple_english",
    "simple_spanish",
    "formal_business",
    "gitmoji",
    "release_notes",
]

OUTPUT_LANGUAGE_OPTIONS = ["english", "spanish"]
UI_LANGUAGE_OPTIONS = ["en", "es"]

CHANGE_TYPE_OPTIONS = [
    "automatic",
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "test",
    "chore",
    "perf",
    "build",
    "ci",
    "revert",
]

FORMALITY_OPTIONS = ["direct", "technical", "formal"]

st.set_page_config(
    page_title="Commit Writer",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

UI_TEXT = {
    "en": {
        "interface_language": "Interface language",
        "sidebar_title": "Configuration",
        "sidebar_subtitle": "Adjust the output before generating the commit.",
        "commit_style": "Commit style",
        "output_language": "Output language",
        "change_type": "Type",
        "scope": "Optional scope",
        "scope_placeholder": "auth, ui, readme",
        "formality": "Formality",
        "alternatives": "Alternatives",
        "save_history": "Save to local history",
        "provider": "Provider",
        "model": "Model",
        "no_api": "No API connected",
        "hero_kicker": "Uses external LLM API",
        "hero_subtitle": "Turn informal descriptions into clear, consistent commit messages ready to use in your repository.",
        "hero_stat_styles_title": "6 styles",
        "hero_stat_styles_body": "Conventional, simple, formal, gitmoji and release notes.",
        "hero_stat_json_title": "Fast generation",
        "hero_stat_json_body": "Get commit options in seconds.",
        "hero_stat_llm_title": "Multi LLM",
        "hero_stat_llm_body": "Supports multiple LLM providers and models through a compatible architecture.",
        "result_title": "Generated result",
        "recommended_commit": "Recommended commit",
        "full_command": "Full command",
        "semver": "Suggested SemVer",
        "explanation": "Explanation",
        "result_alternatives": "Alternatives",
        "examples_title": "Example",
        "examples_intro": "Use this case as a quick reference for the expected format.",
        "example_input": "Input:",
        "help_title": "Quick help for commit types",
        "history_title": "Local history",
        "history_disabled": "Local history is disabled through HISTORY_ENABLED=false.",
        "history_empty": "There are no records in local history yet.",
        "footer": "Commit Writer · © 2026 Juan Diego Castellanos · github.com/juandiegoc30",
        "description": "Change description",
        "description_placeholder": "Example: I fixed the language selector, now it is a toggle and uses SVG icons instead of emojis",
        "generate": "Generate commit",
        "clear": "Clear",
        "estimated_time": "Estimated time: one call to the LLM provider",
        "generating": "Generating commit...",
        "regenerate": "Regenerate",
        "regenerating": "Regenerating commit...",
        "error_info": "Check the .env file, the API key, the configured model, and whether the provider supports chat completions.",
        "copy_commit": "Copy commit",
        "copy_command": "Copy command",
        "copy_alternative": "Copy alternative {index}",
        "copy_success": "Copied",
        "copy_failure": "Could not copy automatically",
        "semver_short": "SemVer",
        "help_body": """
- `feat`: new functionality.
- `fix`: bug fix.
- `docs`: documentation.
- `style`: formatting, visual styles or changes that do not alter behavior.
- `refactor`: internal restructuring without functional change.
- `test`: tests.
- `perf`: performance.
- `build`: packaging, dependencies or build system changes.
- `ci`: CI/CD or automation changes.
- `chore`: general maintenance.
- `revert`: revert a previous change.
        """.strip(),
    },
    "es": {
        "interface_language": "Idioma de interfaz",
        "sidebar_title": "Configuración",
        "sidebar_subtitle": "Ajusta la salida antes de generar el commit.",
        "commit_style": "Estilo de commit",
        "output_language": "Idioma de salida",
        "change_type": "Tipo",
        "scope": "Scope opcional",
        "scope_placeholder": "auth, ui, readme",
        "formality": "Formalidad",
        "alternatives": "Alternativas",
        "save_history": "Guardar en historial local",
        "provider": "Proveedor",
        "model": "Modelo",
        "no_api": "Sin API conectada",
        "hero_kicker": "Usa una API LLM externa",
        "hero_subtitle": "Convierte descripciones informales en mensajes de commit claros, consistentes y listos para usar en tu repositorio.",
        "hero_stat_styles_title": "6 estilos",
        "hero_stat_styles_body": "Conventional, simple, formal, gitmoji y release notes.",
        "hero_stat_json_title": "Generación rápida",
        "hero_stat_json_body": "Obtén opciones de commit en segundos.",
        "hero_stat_llm_title": "Multi LLM",
        "hero_stat_llm_body": "Soporta multiples proveedores y modelos LLM.",
        "result_title": "Resultado generado",
        "recommended_commit": "Commit recomendado",
        "full_command": "Comando completo",
        "semver": "SemVer sugerido",
        "explanation": "Explicación",
        "result_alternatives": "Alternativas",
        "examples_title": "Ejemplo",
        "examples_intro": "Usa este caso como referencia rápida del formato esperado.",
        "example_input": "Entrada:",
        "help_title": "Ayuda rápida sobre tipos de commit",
        "history_title": "Historial local",
        "history_disabled": "El historial local está desactivado mediante HISTORY_ENABLED=false.",
        "history_empty": "Todavía no hay registros en el historial local.",
        "footer": "Commit Writer · © 2026 Juan Diego Castellanos · github.com/juandiegoc30",
        "description": "Descripción del cambio",
        "description_placeholder": "Ejemplo: arreglé el selector de idioma, ahora es un toggle y usa íconos SVG en vez de emojis",
        "generate": "Generar commit",
        "clear": "Limpiar",
        "estimated_time": "Tiempo estimado: una llamada al proveedor LLM",
        "generating": "Generando commit...",
        "regenerate": "Regenerar",
        "regenerating": "Regenerando commit...",
        "error_info": "Revisa el archivo .env, la API key, el modelo configurado y que el proveedor soporte chat completions.",
        "copy_commit": "Copiar commit",
        "copy_command": "Copiar comando",
        "copy_alternative": "Copiar alternativa {index}",
        "copy_success": "Copiado",
        "copy_failure": "No se pudo copiar automáticamente",
        "semver_short": "SemVer",
        "help_body": """
- `feat`: nueva funcionalidad.
- `fix`: corrección de errores.
- `docs`: documentación.
- `style`: formato, estilos visuales o cambios que no alteran comportamiento.
- `refactor`: reestructuración interna sin cambio funcional.
- `test`: pruebas.
- `perf`: rendimiento.
- `build`: empaquetado, dependencias o sistema de construcción.
- `ci`: integración continua o automatización de despliegue.
- `chore`: mantenimiento general.
- `revert`: reversión de un cambio anterior.
        """.strip(),
    },
}

STYLE_LABELS = {
    "en": {
        "conventional": "Conventional Commits",
        "simple_english": "Simple English commit",
        "simple_spanish": "Simple Spanish commit",
        "formal_business": "Formal business commit",
        "gitmoji": "Gitmoji commit",
        "release_notes": "Release note style",
    },
    "es": {
        "conventional": "Conventional Commits",
        "simple_english": "Commit simple en inglés",
        "simple_spanish": "Commit simple en español",
        "formal_business": "Commit formal para entorno empresarial",
        "gitmoji": "Gitmoji commit",
        "release_notes": "Release note style",
    },
}

OUTPUT_LANGUAGE_LABELS = {
    "en": {"english": "English", "spanish": "Spanish"},
    "es": {"english": "Inglés", "spanish": "Español"},
}

CHANGE_TYPE_LABELS = {
    "en": {
        "automatic": "Automatic",
        "feat": "feat",
        "fix": "fix",
        "docs": "docs",
        "style": "style",
        "refactor": "refactor",
        "test": "test",
        "chore": "chore",
        "perf": "perf",
        "build": "build",
        "ci": "ci",
        "revert": "revert",
    },
    "es": {
        "automatic": "Automático",
        "feat": "feat",
        "fix": "fix",
        "docs": "docs",
        "style": "style",
        "refactor": "refactor",
        "test": "test",
        "chore": "chore",
        "perf": "perf",
        "build": "build",
        "ci": "ci",
        "revert": "revert",
    },
}

FORMALITY_LABELS = {
    "en": {"direct": "Direct", "technical": "Technical", "formal": "Formal"},
    "es": {"direct": "Directo", "technical": "Técnico", "formal": "Formal"},
}

STYLE_ALIASES = {
    "conventional": "conventional",
    "Conventional Commits": "conventional",
    "simple_english": "simple_english",
    "Commit simple en inglés": "simple_english",
    "Simple English commit": "simple_english",
    "simple_spanish": "simple_spanish",
    "Commit simple en español": "simple_spanish",
    "Simple Spanish commit": "simple_spanish",
    "formal_business": "formal_business",
    "Commit formal para entorno empresarial": "formal_business",
    "Formal business commit": "formal_business",
    "gitmoji": "gitmoji",
    "Gitmoji commit": "gitmoji",
    "release_notes": "release_notes",
    "Release note style": "release_notes",
}

LANGUAGE_ALIASES = {
    "english": "english",
    "inglés": "english",
    "English": "english",
    "spanish": "spanish",
    "español": "spanish",
    "Spanish": "spanish",
}

CHANGE_TYPE_ALIASES = {
    "auto": "automatic",
    "automatic": "automatic",
    "automático": "automatic",
    "feat": "feat",
    "fix": "fix",
    "docs": "docs",
    "style": "style",
    "refactor": "refactor",
    "test": "test",
    "chore": "chore",
    "perf": "perf",
    "build": "build",
    "ci": "ci",
    "revert": "revert",
}

FORMALITY_ALIASES = {
    "direct": "direct",
    "directo": "direct",
    "Direct": "direct",
    "technical": "technical",
    "técnico": "technical",
    "Technical": "technical",
    "formal": "formal",
    "Formal": "formal",
}

EXAMPLES_BY_LOCALE = {
    "en": [
        (
            "Checkout validation and totals",
            "I fixed a bunch of checkout issues because sometimes it let people pay with missing fields, it was not recalculating totals properly when quantity changed, and I also cleaned up that flow a bit because it was kind of messy",
            "fix(checkout): validate required fields and recalculate totals correctly",
        ),
    ],
    "es": [
        (
            "Checkout con validaciones y totales",
            "arreglé varias cosas del checkout porque a veces dejaba pagar aunque faltaban campos, no recalculaba bien el total cuando cambiabas la cantidad y de paso ordené un poco ese flujo porque estaba medio enredado",
            "fix(checkout): validate required fields and recalculate totals correctly",
        ),
    ],
}

ERROR_TRANSLATIONS = {
    "es": {
        "Invalid input.": "Entrada inválida.",
        "Change description is required.": "La descripción del cambio es obligatoria.",
        "String should have at least 8 characters": "La descripción debe tener al menos 8 caracteres.",
        "Description must be at least 8 characters long.": "La descripción debe tener al menos 8 caracteres.",
        "Description cannot exceed 1000 characters.": "La descripción no puede superar los 1000 caracteres.",
        "Selected commit style is invalid.": "El estilo de commit seleccionado no es válido.",
        "Output language must be English or Spanish.": "El idioma de salida debe ser inglés o español.",
        "Selected change type is invalid.": "El tipo de cambio seleccionado no es válido.",
        "Scope cannot contain spaces. Use hyphens, for example: language-selector.": "El scope no debe contener espacios. Usa guiones, por ejemplo: language-selector.",
        "Scope cannot exceed 60 characters.": "El scope no debe superar los 60 caracteres.",
        "Selected formality level is invalid.": "El nivel de formalidad seleccionado no es válido.",
        "Number of alternatives can only be 1, 3, or 5.": "El número de alternativas solo puede ser 1, 3 o 5.",
    }
}


def detect_ui_locale() -> str:
    try:
        headers = getattr(getattr(st, "context", None), "headers", {}) or {}
    except Exception:
        return "en"

    accept_language = headers.get("Accept-Language", headers.get("accept-language", ""))
    primary_language = accept_language.split(",", 1)[0].strip().lower()
    return "es" if primary_language.startswith("es") else "en"


BROWSER_UI_LOCALE = detect_ui_locale()
if "ui_locale" not in st.session_state:
    st.session_state.ui_locale = BROWSER_UI_LOCALE

UI_LOCALE = st.session_state.get("ui_locale", BROWSER_UI_LOCALE)
DEFAULT_OUTPUT_LANGUAGE = "spanish" if UI_LOCALE == "es" else "english"


def t(key: str, **kwargs: Any) -> str:
    return UI_TEXT[UI_LOCALE][key].format(**kwargs)


def normalize_option(value: Any, aliases: dict[str, str], default: str) -> str:
    if isinstance(value, str):
        return aliases.get(value, default)
    return default


def commit_style_label(value: Any) -> str:
    canonical_value = normalize_option(value, STYLE_ALIASES, COMMIT_STYLE_OPTIONS[0])
    return STYLE_LABELS[UI_LOCALE][canonical_value]


def output_language_label(value: Any) -> str:
    canonical_value = normalize_option(value, LANGUAGE_ALIASES, DEFAULT_OUTPUT_LANGUAGE)
    return OUTPUT_LANGUAGE_LABELS[UI_LOCALE][canonical_value]


def change_type_label(value: Any) -> str:
    canonical_value = normalize_option(value, CHANGE_TYPE_ALIASES, CHANGE_TYPE_OPTIONS[0])
    return CHANGE_TYPE_LABELS[UI_LOCALE][canonical_value]


def formality_label(value: Any) -> str:
    canonical_value = normalize_option(value, FORMALITY_ALIASES, "technical")
    return FORMALITY_LABELS[UI_LOCALE][canonical_value]


def ui_language_label(value: Any) -> str:
    return "🇬🇧 EN" if value == "en" else "🇪🇸 ES"
    
def current_ui_language_toggle_label() -> str:
    return "🇬🇧 EN" if UI_LOCALE == "en" else "🇪🇸 ES"


def translate_error_message(message: str) -> str:
    if UI_LOCALE == "en":
        return message
    return ERROR_TRANSLATIONS.get("es", {}).get(message, message)

CUSTOM_CSS = """
<style>
    :root {
        --cw-bg: #050915;
        --cw-panel: #0f172a;
        --cw-panel-dark: #07101e;
        --cw-text: #f8fafc;
        --cw-title: #0f172a;
        --cw-muted: #94a3b8;
        --cw-border: rgba(148, 163, 184, 0.24);
        --cw-border-strong: rgba(148, 163, 184, 0.36);
        --cw-primary: #ff4b4b;
        --cw-primary-2: #e53935;
        --cw-primary-soft: #ffecec;
        --cw-code: #07101e;
        --cw-radius-lg: 24px;
        --cw-shadow: 0 22px 70px rgba(0, 0, 0, 0.26);
        --primary-color: #ff4b4b;
        --primary-color-rgb: 255, 75, 75;
        --primaryColor: #ff4b4b;
        --secondaryBackgroundColor: #07101e;
    }

    .stApp > header,
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stDeployButton"],
    .stAppDeployButton,
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 14% 0%, rgba(255, 75, 75, 0.17), transparent 30%),
            radial-gradient(circle at 96% 4%, rgba(14, 165, 233, 0.13), transparent 28%),
            linear-gradient(180deg, #050915 0%, #070b14 100%) !important;
        overflow-y: auto !important;
        overscroll-behavior-y: auto !important;
        min-height: auto !important;
    }

    [data-testid="stAppViewBlockContainer"],
    [data-testid="stMain"],
    section.main,
    .main {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        min-height: auto !important;
    }

    .main .block-container,
    [data-testid="stMainBlockContainer"],
    div.block-container,
    div[data-testid="stAppViewBlockContainer"] > div:first-child {
        max-width: 1220px !important;
        padding-top: 0.18rem !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.84rem !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stElementContainer"] {
        margin-bottom: 0 !important;
        overflow: visible !important;
    }

    /* Sidebar restored to a comfortable vertical rhythm. */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #101827 100%) !important;
        border-right: 1px solid rgba(148, 163, 184, 0.16) !important;
        width: 21rem !important;
        min-width: 21rem !important;
        max-width: 21rem !important;
        flex: 0 0 21rem !important;
        resize: none !important;
    }

    /* Disable sidebar resizing. The drag handle is the last, testid-less child
       div of the sidebar section; its inner div carries `cursor: col-resize`
       via an inline style, and a nested bar brightens on :hover (the glowing
       border). Hiding the wrapper kills the drag area, the resize cursor and
       the hover glow at once. Both selectors are structural (no Emotion hash),
       so they survive Streamlit upgrades. */
    section[data-testid="stSidebar"] > div:not([data-testid]),
    section[data-testid="stSidebar"] div[style*="cursor: col-resize"] {
        display: none !important;
        pointer-events: none !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding: 0.72rem 1.18rem 1.05rem 1.18rem !important;
        overflow-y: auto !important;
        overscroll-behavior-y: contain !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] .stButton {
        width: 100% !important;
        display: flex !important;
        justify-content: flex-end !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] .stButton > button {
        width: auto !important;
        min-width: 4.8rem !important;
        margin-left: auto !important;
        padding-left: 0.70rem !important;
        padding-right: 0.70rem !important;
    }

    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.66rem !important;
    }

    .cw-sidebar-title {
        color: #f8fafc !important;
        font-size: 1.34rem !important;
        line-height: 1.08 !important;
        font-weight: 890 !important;
        letter-spacing: 0.01em !important;
        margin: 0.34rem 0 0 0 !important;
    }

    .cw-sidebar-subtitle {
        color: #a8b3c5 !important;
        font-size: 0.86rem !important;
        line-height: 1.38 !important;
        font-weight: 560 !important;
        margin: 0 0 0.78rem 0 !important;
    }

    .cw-sidebar-divider {
        height: 1px;
        width: 100%;
        background: rgba(148, 163, 184, 0.18);
        margin: 0.05rem 0 0.62rem 0;
    }

    .cw-sidebar-spacer {
        height: 0.42rem;
        width: 100%;
    }

    section[data-testid="stSidebar"] label p,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    .cw-control-label {
        color: #f8fafc !important;
        font-size: 0.86rem !important;
        line-height: 1.24 !important;
        font-weight: 780 !important;
        letter-spacing: -0.018em !important;
        margin: 0 0 0.28rem 0 !important;
        padding: 0 !important;
        overflow: visible !important;
    }

    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        min-height: 1.18rem !important;
        height: auto !important;
        overflow: visible !important;
        padding: 0 !important;
        margin-bottom: 0.18rem !important;
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #f8fafc !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
    section[data-testid="stSidebar"] div[data-testid="stTextInput"] {
        overflow: visible !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] > div {
        overflow: visible !important;
        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }

    div[data-baseweb="select"] > div,
    div[data-testid="stTextArea"] textarea {
        background: var(--cw-panel-dark) !important;
        color: #f8fafc !important;
        border: 1px solid var(--cw-border) !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        min-height: 2.58rem !important;
        height: 2.58rem !important;
        border-radius: 15px !important;
        display: flex !important;
        align-items: center !important;
        padding: 0 0.74rem !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] > div > div,
    section[data-testid="stSidebar"] div[data-baseweb="select"] div[role="button"],
    section[data-testid="stSidebar"] div[data-baseweb="select"] span {
        min-height: 0 !important;
        display: flex !important;
        align-items: center !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        line-height: normal !important;
        font-size: 0.90rem !important;
        font-weight: 620 !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] input {
        font-size: 0.90rem !important;
        line-height: normal !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
        margin-top: 0 !important;
        width: 0.88rem !important;
        height: 0.88rem !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {
        border-color: rgba(255, 75, 75, 0.74) !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within {
        border-color: rgba(255, 75, 75, 0.74) !important;
        box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.28) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
        min-height: 2.58rem !important;
        height: 2.58rem !important;
        border-radius: 15px !important;
        padding: 0 0.74rem !important;
        box-sizing: border-box !important;
        background: var(--cw-panel-dark) !important;
        border: 1px solid var(--cw-border) !important;
        box-shadow: none !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        overflow: hidden !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="base-input"]::before,
    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="base-input"]::after {
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] input {
        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
        min-height: 0 !important;
        height: auto !important;
        padding: 0 !important;
        margin: 0 !important;
        font-size: 0.90rem !important;
        line-height: normal !important;
        font-weight: 620 !important;
        overflow: visible !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [data-baseweb="checkbox"],
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label {
        gap: 0.58rem !important;
        align-items: center !important;
        display: flex !important;
        line-height: 1 !important;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:first-child,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label > div:first-child {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 0 !important;
        position: static !important;
        top: auto !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [data-baseweb="checkbox"] > span,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label > span {
        width: 1rem !important;
        height: 1rem !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        vertical-align: middle !important;
        transform: translateY(-1px) !important;
        flex-shrink: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] input {
        accent-color: rgba(255, 75, 75, 0.98) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [data-baseweb="checkbox"][aria-checked="true"] > span,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] > span,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] input:checked + span {
        background: rgba(255, 75, 75, 0.22) !important;
        border-color: rgba(255, 75, 75, 0.74) !important;
        box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.74) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [data-baseweb="checkbox"][aria-checked="true"] svg,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] svg,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] input:checked + span svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    section[data-testid="stSidebar"] .row-widget.stCheckbox,
    section[data-testid="stSidebar"] .st-emotion-cache-mo6sqg.etdahpg0 {
        border-color: rgba(255, 75, 75, 0.74) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:last-child,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label [data-testid="stMarkdownContainer"] {
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label p {
        color: #f8fafc !important;
        font-size: 0.88rem !important;
        line-height: 1.18 !important;
        font-weight: 750 !important;
        letter-spacing: -0.018em !important;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] svg {
        width: 0.98rem !important;
        height: 0.98rem !important;
        margin-top: 0 !important;
        flex-shrink: 0 !important;
    }

    hr {
        border-color: rgba(148, 163, 184, 0.18) !important;
        margin: 0.74rem 0 0.62rem 0 !important;
    }

    .cw-provider-stack {
        display: grid;
        gap: 0.56rem;
        margin-top: 0.78rem;
    }

    .cw-provider-badge {
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 15px;
        padding: 0.58rem 0.68rem;
        background: rgba(2, 6, 23, 0.34);
    }

    .cw-provider-badge span {
        display: block;
        color: #9caac0 !important;
        font-size: 0.60rem !important;
        line-height: 1 !important;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        font-weight: 820;
        margin-bottom: 0.20rem;
    }

    .cw-provider-badge strong {
        display: block;
        color: #f8fafc !important;
        font-size: 0.84rem !important;
        line-height: 1.2 !important;
        font-weight: 820 !important;
        letter-spacing: -0.02em;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        overflow-wrap: anywhere;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] {
        margin-top: 0 !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSegmentedControl"] div[role="group"] {
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        gap: 0 !important;
        width: 92% !important;
        margin: 0.16rem auto 0 auto !important;
        border: 1px solid rgba(148, 163, 184, 0.24) !important;
        border-radius: 15px !important;
        overflow: hidden !important;
        background: var(--cw-panel-dark) !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSegmentedControl"] div[role="group"]:focus-within {
        border-color: rgba(255, 75, 75, 0.74) !important;
        box-shadow: 0 0 0 1px rgba(255, 75, 75, 0.22) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button {
        min-height: 2.58rem !important;
        height: 2.58rem !important;
        border-radius: 0 !important;
        font-size: 0.90rem !important;
        font-weight: 760 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        border-right: 1px solid rgba(148, 163, 184, 0.20) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button:last-child {
        border-right: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button[aria-selected="true"],
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button[aria-checked="true"],
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button[data-selected="true"],
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] [role="radio"][aria-checked="true"],
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button:focus-visible {
        border-color: rgba(255, 75, 75, 0.74) !important;
        background: rgba(255, 75, 75, 0.22) !important;
        color: #ffffff !important;
        box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.74) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button:hover {
        border-color: rgba(255, 75, 75, 0.74) !important;
        background: rgba(255, 75, 75, 0.16) !important;
    }

    section[data-testid="stSidebar"] [class*="stBaseButton-segmented_control"],
    section[data-testid="stSidebar"] [data-testid^="stBaseButton-segmented_control"] {
        border-color: rgba(255, 75, 75, 0.74) !important;
        color: #ffffff !important;
        /* Streamlit ships these buttons with a light default fill; without this
           the unselected options (1 and 5) render as white boxes. */
        background: transparent !important;
    }

    /* Selected option keeps the red highlight. */
    section[data-testid="stSidebar"] [data-testid="stBaseButton-segmented_controlActive"] {
        background: rgba(255, 75, 75, 0.22) !important;
        box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.74) !important;
    }

    section[data-testid="stSidebar"] [class*="stBaseButton-segmented_control"][aria-checked="true"],
    section[data-testid="stSidebar"] [class*="stBaseButton-segmented_control"][aria-selected="true"] {
        background: rgba(255, 75, 75, 0.22) !important;
        box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.74) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button[aria-pressed="true"] *,
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button[aria-selected="true"] *,
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button[aria-checked="true"] *,
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] [role="radio"][aria-checked="true"] * {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"]:first-of-type {
        margin-top: 0.02rem !important;
        margin-bottom: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"]:first-of-type div[role="group"] {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        width: 100% !important;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"]:first-of-type button {
        position: relative !important;
        gap: 0.38rem !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"]:first-of-type button::before {
        content: "";
        width: 0.95rem;
        height: 0.95rem;
        border-radius: 2px;
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
        display: inline-block;
        flex-shrink: 0;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"]:first-of-type button:nth-child(1)::before {
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'><rect width='60' height='40' fill='%23012169'/><path d='M0 0 L60 40 M60 0 L0 40' stroke='%23fff' stroke-width='8'/><path d='M0 0 L60 40 M60 0 L0 40' stroke='%23c8102e' stroke-width='4'/><path d='M30 0 v40 M0 20 h60' stroke='%23fff' stroke-width='12'/><path d='M30 0 v40 M0 20 h60' stroke='%23c8102e' stroke-width='7'/></svg>");
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"]:first-of-type button:nth-child(2)::before {
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'><rect width='60' height='40' fill='%23c60b1e'/><rect y='10' width='60' height='20' fill='%23ffc400'/></svg>");
    }

    /* Main form and content */
    .cw-hero {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.82);
        border-radius: 26px;
        padding: 1.05rem 1.45rem;
        background:
            radial-gradient(circle at 92% -5%, rgba(255, 75, 75, 0.13), transparent 40%),
            linear-gradient(135deg, #ffffff 0%, #f8fafc 54%, #eef2ff 100%);
        box-shadow: var(--cw-shadow);
        margin: 0 0 0.92rem 0 !important;
        color: var(--cw-title) !important;
        min-height: 196px;
        display: flex;
        align-items: center;
    }

    .cw-hero * { color: inherit !important; }

    .cw-hero-grid {
        width: 100%;
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(380px, 0.88fr);
        gap: 1.05rem;
        align-items: center;
    }

    .cw-hero-copy {
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: auto;
    }

    .cw-kicker {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        padding: 0.34rem 0.64rem;
        border-radius: 999px;
        border: 1px solid #fecaca;
        background: var(--cw-primary-soft);
        color: #991b1b !important;
        font-size: 0.74rem;
        font-weight: 850;
        margin: 0 0 0.40rem 0;
    }

    .cw-title {
        color: #0f172a !important;
        font-size: clamp(2.35rem, 4vw, 3.35rem);
        line-height: 0.98;
        font-weight: 950;
        letter-spacing: -0.07em;
        margin: 0 0 0.34rem 0;
    }

    .cw-subtitle {
        color: #475569 !important;
        font-size: clamp(0.96rem, 1.25vw, 1.08rem);
        line-height: 1.42;
        max-width: 710px;
        margin: 0;
        font-weight: 650;
    }

    .cw-stats {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.76rem;
        align-items: stretch;
        max-width: 500px;
        margin-left: auto;
    }

    .cw-stat-card {
        padding: 0.88rem 0.86rem;
        border-radius: 17px;
        border: 1px solid #e2e8f0;
        background: rgba(255, 255, 255, 0.78);
        min-height: 104px;
        box-shadow: 0 12px 26px rgba(15, 23, 42, 0.06);
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .cw-stat-card strong {
        display: block;
        color: #0f172a !important;
        font-size: 0.90rem;
        line-height: 1.2;
        margin-bottom: 0.31rem;
        letter-spacing: -0.025em;
    }

    .cw-stat-card span {
        display: block;
        color: #64748b !important;
        font-size: 0.76rem;
        line-height: 1.33;
        font-weight: 590;
    }

    div[data-testid="stForm"] {
        background: var(--cw-panel);
        border: 1px solid rgba(148, 163, 184, 0.20);
        border-radius: var(--cw-radius-lg);
        padding: 1.05rem 1.05rem 0.88rem 1.05rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.20);
        backdrop-filter: blur(16px);
    }

    .cw-examples-panel {
        background: var(--cw-panel) !important;
        border: 1px solid rgba(148, 163, 184, 0.20);
        border-radius: var(--cw-radius-lg);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.20);
        backdrop-filter: blur(16px);
        padding: 1.05rem 1.05rem 0.88rem 1.05rem;
    }

    div[data-testid="stForm"] label,
    div[data-testid="stForm"] p,
    div[data-testid="stForm"] span { color: #f8fafc !important; }

    div[data-testid="stTextArea"] textarea {
        min-height: 168px !important;
        border-radius: 14px !important;
        padding: 0.92rem !important;
        line-height: 1.52 !important;
        font-size: 0.88rem !important;
    }

    .stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        height: 2.62rem;
        border-radius: 13px !important;
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
        background: rgba(15, 23, 42, 0.92) !important;
        color: #f8fafc !important;
        font-weight: 750 !important;
        letter-spacing: -0.01em;
        transition: all 160ms ease;
    }

    .stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        border-color: rgba(255, 75, 75, 0.74) !important;
        transform: translateY(-1px);
    }

    div[data-testid="stFormSubmitButton"] button[kind="primary"],
    .stButton button[kind="primary"] {
        border: 0 !important;
        background: linear-gradient(135deg, var(--cw-primary), var(--cw-primary-2)) !important;
        color: #ffffff !important;
        box-shadow: 0 7px 16px rgba(255, 75, 75, 0.18);
    }

    div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
    .stButton button[kind="primary"]:hover {
        box-shadow: 0 9px 18px rgba(255, 75, 75, 0.20) !important;
    }

    .cw-section-title {
        color: #f8fafc !important;
        font-size: 1.26rem;
        font-weight: 850;
        letter-spacing: -0.045em;
        margin: 0.10rem 0 0.65rem 0;
    }

    .cw-section-title-examples {
        padding: 0 !important;
        margin-top: -0.02rem !important;
    }

    .cw-muted,
    .cw-side-intro {
        color: #94a3b8 !important;
        font-size: 0.91rem;
        line-height: 1.47;
    }

    .cw-side-intro {
        padding-top: 0.4rem;
    }

    .cw-code-pill {
        display: block;
        padding: 0.76rem 0.84rem;
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.16);
        background: var(--cw-code);
        color: #e2e8f0 !important;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size: 0.82rem;
        line-height: 1.45;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }

    .cw-example-source {
        color: #94a3b8 !important;
        font-size: 0.91rem;
        margin: 0.15rem 0 0.68rem 0;
        line-height: 1.45;
    }

    .cw-example-source strong {
        color: #f8fafc !important;
    }

    .cw-example-item + .cw-example-item {
        margin-top: 0.88rem;
        padding-top: 0.88rem;
        border-top: 1px solid rgba(148, 163, 184, 0.12);
    }

    .cw-result-label {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        padding: 0.35rem 0.62rem;
        border-radius: 999px;
        background: rgba(255, 75, 75, 0.14);
        color: #fecaca !important;
        border: 1px solid rgba(255, 75, 75, 0.22);
        font-size: 0.74rem;
        font-weight: 850;
        margin: 0.25rem 0 0.56rem 0;
    }

    .cw-alert {
        border-radius: 16px;
        border: 1px solid rgba(245, 158, 11, 0.38);
        background: rgba(146, 64, 14, 0.16);
        color: #fde68a !important;
        padding: 0.92rem 1rem;
        line-height: 1.5;
        margin-top: 0.55rem;
    }

    div[data-testid="stCodeBlock"] pre {
        border-radius: 14px !important;
        border: 1px solid rgba(148, 163, 184, 0.22) !important;
        background: var(--cw-code) !important;
        color: #e5e7eb !important;
    }

    div[data-testid="stExpander"] {
        border-radius: 17px !important;
        border: 1px solid rgba(148, 163, 184, 0.20) !important;
        background: rgba(15, 23, 42, 0.68) !important;
        overflow: hidden;
        margin-bottom: 0.60rem !important;
    }

    div[data-testid="stExpander"] p,
    div[data-testid="stExpander"] li,
    div[data-testid="stExpander"] span { color: #e5e7eb !important; }

    div[data-testid="stExpander"] summary p {
        font-weight: 750 !important;
        color: #f8fafc !important;
    }

    [data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.74);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 16px;
        padding: 0.82rem 1rem;
    }

    [data-testid="stMetric"] label,
    [data-testid="stMetric"] div { color: #f8fafc !important; }

    .cw-footer {
        color: #94a3b8 !important;
        font-size: 0.82rem;
        line-height: 1.2;
        text-align: center;
        padding: 0.62rem 0 1.05rem 0 !important;
        margin: 0 !important;
    }

    .cw-footer a {
        color: #cbd5e1 !important;
        text-decoration: none;
        border-bottom: 1px dotted rgba(203, 213, 225, 0.45);
    }

    .cw-footer a:hover {
        color: #f8fafc !important;
        border-bottom-color: rgba(248, 250, 252, 0.72);
    }



    /* v9 sidebar refinements */
    section[data-testid="stSidebar"] .stSelectbox,
    section[data-testid="stSidebar"] .stTextInput {
        margin-bottom: 0.16rem !important;
        overflow: visible !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
        box-sizing: border-box !important;
        display: flex !important;
        align-items: center !important;
        line-height: 1.15 !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] span,
    section[data-testid="stSidebar"] div[data-testid="stTextInput"] input {
        font-size: 0.90rem !important;
        font-weight: 610 !important;
        letter-spacing: -0.012em !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
        min-height: 2.58rem !important;
        height: 2.58rem !important;
        border-radius: 15px !important;
        padding: 0 0.74rem !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSegmentedControl"] div[role="group"] {
        height: 2.58rem !important;
        margin-top: 0.16rem !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button {
        height: 2.58rem !important;
        min-height: 2.58rem !important;
        font-size: 0.90rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .cw-hero-copy {
        gap: 0 !important;
    }

    .cw-footer {
        margin-top: 0.45rem !important;
        margin-bottom: 0 !important;
    }


    /* v10 targeted fixes */
    .cw-title {
        padding: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0.05rem !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] {
        min-height: 2.58rem !important;
        height: auto !important;
        overflow: visible !important;
        margin-bottom: 0.34rem !important;
        padding-bottom: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
        min-height: 2.58rem !important;
        height: 2.58rem !important;
        border-radius: 15px !important;
        padding: 0 0.74rem !important;
        line-height: 1.2 !important;
        box-sizing: border-box !important;
        display: flex !important;
        align-items: center !important;
    }

    .cw-provider-stack {
        margin-top: 0.82rem !important;
    }

    .cw-provider-badge {
        padding: 0.64rem 0.72rem !important;
    }

    .cw-footer {
        padding-top: 0.56rem !important;
        padding-bottom: 1.05rem !important;
        margin-top: 0.55rem !important;
        margin-bottom: 0 !important;
    }

    .main .block-container,
    [data-testid="stMainBlockContainer"],
    div.block-container,
    div[data-testid="stAppViewBlockContainer"] > div:first-child {
        padding-bottom: 0 !important;
        margin-bottom: 0 !important;
    }



    /* v11 sidebar header and control alignment refinements */
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] [data-testid="stWidgetLabel"] {
        margin-bottom: 0.28rem !important;
        min-height: 1.18rem !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] [data-testid="stWidgetLabel"] p {
        font-size: 0.86rem !important;
        line-height: 1.24 !important;
        font-weight: 780 !important;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] [data-testid="stWidgetLabel"] {
        margin-bottom: 0.28rem !important;
    }

    section[data-testid="stSidebar"] .row-widget.stSelectbox,
    section[data-testid="stSidebar"] .row-widget.stTextInput {
        margin-top: 0 !important;
    }

    .cw-formality-alternatives-row {
        margin-top: 0.05rem !important;
    }

    [data-testid="stAppViewBlockContainer"] {
        padding-bottom: 0.95rem !important;
    }

    @media (max-width: 1080px) {
        .main .block-container { padding-left: 1rem; padding-right: 1rem; }
        .cw-hero-grid { grid-template-columns: 1fr; }
        .cw-stats { grid-template-columns: repeat(3, minmax(0, 1fr)); max-width: 100%; margin-left: 0; }
    }

    @media (max-width: 760px) {
        .cw-hero { padding: 1.1rem; border-radius: 22px; }
        .cw-stats { grid-template-columns: 1fr; }
    }

    /* Final color lock: force Streamlit red on accent/hover/active states. */
    section[data-testid="stSidebar"] [class*="stBaseButton-segmented_control"],
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button {
        border-color: rgba(255, 75, 75, 0.74) !important;
    }

    section[data-testid="stSidebar"] [class*="stBaseButton-segmented_control"][aria-selected="true"],
    section[data-testid="stSidebar"] [class*="stBaseButton-segmented_control"][aria-checked="true"],
    section[data-testid="stSidebar"] [class*="stBaseButton-segmented_control"][aria-pressed="true"],
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button[aria-selected="true"],
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button[aria-checked="true"],
    section[data-testid="stSidebar"] div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
        background-color: rgba(255, 75, 75, 0.24) !important;
        box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.82) !important;
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .row-widget.stCheckbox,
    section[data-testid="stSidebar"] .st-emotion-cache-mo6sqg.etdahpg0 {
        --primaryColor: #ff4b4b !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] input[type="checkbox"] {
        accent-color: #ff4b4b !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [data-baseweb="checkbox"][aria-checked="true"] > span,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] > span,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] input:checked + span {
        background-color: rgba(255, 75, 75, 0.24) !important;
        border-color: rgba(255, 75, 75, 0.82) !important;
        box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.82) !important;
    }

    .stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within,
    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within {
        border-color: rgba(255, 75, 75, 0.74) !important;
        box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.28) !important;
    }

    .cw-result-label {
        background: rgba(255, 75, 75, 0.14) !important;
        color: #ffd6d6 !important;
        border-color: rgba(255, 75, 75, 0.22) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [data-baseweb="checkbox"][aria-checked="true"] svg,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] svg,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] input:checked + span svg,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [data-baseweb="checkbox"][aria-checked="true"] svg path,
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] svg path {
        color: #ffffff !important;
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }

    /* Border cleanup: Description textarea + Help/History expanders. */
    div[data-testid="stTextArea"] [data-baseweb="textarea"] {
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
        border-radius: 16px !important;
        background: var(--cw-code) !important;
        box-shadow: none !important;
        overflow: hidden !important;
    }

    div[data-testid="stTextArea"] [data-baseweb="textarea"] > div {
        border: 0 !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    div[data-testid="stTextArea"] textarea {
        border: 0 !important;
        outline: 0 !important;
        background: transparent !important;
        border-radius: 0 !important;
        box-shadow: none !important;
    }

    div[data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within {
        border-color: rgba(255, 75, 75, 0.74) !important;
        box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.24) !important;
    }

    div[data-testid="stExpander"] {
        border: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
        overflow: visible !important;
    }

    div[data-testid="stExpander"] details {
        border: 1px solid rgba(148, 163, 184, 0.24) !important;
        border-radius: 17px !important;
        background: rgba(15, 23, 42, 0.68) !important;
        overflow: hidden !important;
    }

    div[data-testid="stExpander"] details > summary {
        border: 0 !important;
        box-shadow: none !important;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def build_payload_from_state() -> dict[str, Any]:
    return {
        "change_description": st.session_state.get("change_description", ""),
        "commit_style": normalize_option(
            st.session_state.get("commit_style"), STYLE_ALIASES, COMMIT_STYLE_OPTIONS[0]
        ),
        "output_language": normalize_option(
            st.session_state.get("output_language"), LANGUAGE_ALIASES, DEFAULT_OUTPUT_LANGUAGE
        ),
        "change_type": normalize_option(
            st.session_state.get("change_type"), CHANGE_TYPE_ALIASES, CHANGE_TYPE_OPTIONS[0]
        ),
        "scope": st.session_state.get("scope", ""),
        "formality_level": normalize_option(
            st.session_state.get("formality_level"), FORMALITY_ALIASES, "technical"
        ),
        "alternatives_count": st.session_state.get("alternatives_count", 3),
    }


def reset_form() -> None:
    keys_to_clear = [
        "change_description",
        "scope",
        "last_result",
        "last_request_payload",
        "last_error",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


def copy_button(label: str, value: str, key: str) -> None:
    escaped_label = html.escape(label)
    safe_key = key.replace("-", "_").replace(" ", "_")

    components.html(
        f"""
        <div style="display:flex; gap:10px; align-items:center; margin:.18rem 0 .65rem 0;">
            <button id="btn-{key}"
                style="
                    border:1px solid rgba(255, 75, 75,.35);
                    border-radius:11px;
                    padding:8px 12px;
                    background:rgba(255, 75, 75,.14);
                    color:#fecaca;
                    cursor:pointer;
                    font-size:13px;
                    font-weight:750;
                    font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                ">
                {escaped_label}
            </button>
            <span id="msg-{key}" style="font-size:12px; color:#94a3b8;"></span>
        </div>
        <script>
            const button_{safe_key} = document.getElementById("btn-{key}");
            const message_{safe_key} = document.getElementById("msg-{key}");
            button_{safe_key}.onclick = async () => {{
                try {{
                    await navigator.clipboard.writeText({value!r});
                    message_{safe_key}.innerText = {t("copy_success")!r};
                    setTimeout(() => message_{safe_key}.innerText = "", 1800);
                }} catch (err) {{
                    message_{safe_key}.innerText = {t("copy_failure")!r};
                }}
            }};
        </script>
        """,
        height=48,
    )


def generate_commit(payload: dict[str, Any], save_to_history: bool) -> None:
    try:
        request = validate_generation_input(
            change_description=payload["change_description"],
            commit_style=payload["commit_style"],
            output_language=payload["output_language"],
            change_type=payload["change_type"],
            scope=payload.get("scope"),
            formality_level=payload["formality_level"],
            alternatives_count=payload["alternatives_count"],
        )

        service = CommitGenerationService()
        result = service.generate(request)

        if save_to_history:
            storage = HistoryStorage()
            storage.save(request, result)

        st.session_state.last_result = result.model_dump()
        st.session_state.last_request_payload = payload
        st.session_state.last_error = None

    except Exception as error:
        st.session_state.last_error = str(error)
        st.session_state.last_result = None


def render_hero() -> None:
    st.markdown(
        f"""
        <section class="cw-hero">
            <div class="cw-hero-grid">
                <div class="cw-hero-copy">
                    <div class="cw-kicker">{html.escape(t("hero_kicker"))}</div>
                    <h1 class="cw-title">Commit Writer</h1>
                    <p class="cw-subtitle">
                        {html.escape(t("hero_subtitle"))}
                    </p>
                </div>
                <div class="cw-stats">
                    <div class="cw-stat-card"><strong>{html.escape(t("hero_stat_styles_title"))}</strong><span>{html.escape(t("hero_stat_styles_body"))}</span></div>
                    <div class="cw-stat-card"><strong>{html.escape(t("hero_stat_json_title"))}</strong><span>{html.escape(t("hero_stat_json_body"))}</span></div>
                    <div class="cw-stat-card"><strong>{html.escape(t("hero_stat_llm_title"))}</strong><span>{html.escape(t("hero_stat_llm_body"))}</span></div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_result(result: CommitResult) -> None:
    st.markdown(f'<h2 class="cw-section-title">{html.escape(t("result_title"))}</h2>', unsafe_allow_html=True)

    st.markdown(f'<div class="cw-result-label">{html.escape(t("recommended_commit"))}</div>', unsafe_allow_html=True)
    st.code(result.recommended_commit, language="bash")
    copy_button(t("copy_commit"), result.recommended_commit, "recommended")

    st.markdown(f'<div class="cw-result-label">{html.escape(t("full_command"))}</div>', unsafe_allow_html=True)
    st.code(result.full_command, language="bash")
    copy_button(t("copy_command"), result.full_command, "command")

    col_a, col_b = st.columns([1, 2.2])
    with col_a:
        st.metric(t("semver"), result.semver_suggestion)
    with col_b:
        st.markdown(f'<div class="cw-result-label">{html.escape(t("explanation"))}</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="cw-muted">{html.escape(result.explanation)}</p>', unsafe_allow_html=True)

    if result.alternatives:
        st.markdown(f'<div class="cw-result-label">{html.escape(t("result_alternatives"))}</div>', unsafe_allow_html=True)
        for index, alternative in enumerate(result.alternatives, start=1):
            st.code(alternative, language="bash")
            copy_button(t("copy_alternative", index=index), alternative, f"alt-{index}")

    if result.warnings:
        warnings_html = "<br>".join(f"• {html.escape(warning)}" for warning in result.warnings)
        st.markdown(f'<div class="cw-alert">{warnings_html}</div>', unsafe_allow_html=True)


def render_examples() -> None:
    examples = EXAMPLES_BY_LOCALE[UI_LOCALE]

    st.markdown(
        f'<h2 class="cw-section-title cw-section-title-examples">{html.escape(t("examples_title"))}</h2>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="cw-side-intro">{html.escape(t("examples_intro"))}</p>',
        unsafe_allow_html=True,
    )
    items_html = []
    for title, source, output in examples:
        items_html.append(
            f'''
            <div class="cw-example-item">
                <strong>{html.escape(title)}</strong>
                <p class="cw-example-source"><strong>{html.escape(t("example_input"))}</strong> "{html.escape(source)}"</p>
                <code class="cw-code-pill">{html.escape(output)}</code>
            </div>
            '''
        )

    st.markdown(
        f'<div class="cw-examples-panel">{"".join(items_html)}</div>',
        unsafe_allow_html=True,
    )


def render_help() -> None:
    with st.expander(t("help_title"), expanded=False):
        st.markdown(t("help_body"))


def render_history() -> None:
    history_enabled = os.getenv("HISTORY_ENABLED", "true").strip().lower() == "true"
    if not history_enabled:
        st.info(t("history_disabled"))
        return

    storage = HistoryStorage()
    recent_items = storage.list_recent(limit=6)

    if not recent_items:
        st.caption(t("history_empty"))
        return

    for item in recent_items:
        commit_style_text = commit_style_label(item.get("commit_style", COMMIT_STYLE_OPTIONS[0]))
        output_language_text = output_language_label(item.get("output_language", DEFAULT_OUTPUT_LANGUAGE))
        with st.container(border=True):
            st.markdown(f"**{item['recommended_commit']}**")
            st.caption(
                f"{item['created_at']} · {commit_style_text} · "
                f"{output_language_text} · {t('semver_short')}: {item['semver_suggestion']}"
            )
            st.write(item["original_description"])


def render_history_expander() -> None:
    with st.expander(t("history_title"), expanded=False):
        render_history()


def render_alternatives_toggle() -> None:
    allowed_values = [1, 3, 5]
    current_value = st.session_state.get("alternatives_count", 3)
    if current_value not in allowed_values:
        current_value = 3
        st.session_state.alternatives_count = 3

    if hasattr(st, "segmented_control"):
        selected = st.segmented_control(
            t("alternatives"),
            options=allowed_values,
            default=current_value,
            key="alternatives_count_toggle",
        )
        if selected is not None:
            st.session_state.alternatives_count = int(selected)
    else:
        selected = st.select_slider(
            t("alternatives"),
            options=allowed_values,
            value=current_value,
            key="alternatives_count_slider",
        )
        st.session_state.alternatives_count = int(selected)


def render_sidebar() -> bool:
    st.session_state.commit_style = normalize_option(
        st.session_state.get("commit_style"), STYLE_ALIASES, COMMIT_STYLE_OPTIONS[0]
    )
    st.session_state.output_language = normalize_option(
        st.session_state.get("output_language"), LANGUAGE_ALIASES, DEFAULT_OUTPUT_LANGUAGE
    )
    st.session_state.change_type = normalize_option(
        st.session_state.get("change_type"), CHANGE_TYPE_ALIASES, CHANGE_TYPE_OPTIONS[0]
    )
    st.session_state.formality_level = normalize_option(
        st.session_state.get("formality_level"), FORMALITY_ALIASES, "technical"
    )

    with st.sidebar:
        title_col, toggle_col = st.columns([1.62, 0.68], gap="small")
        with title_col:
            st.markdown(
                f'<div class="cw-sidebar-title">{html.escape(t("sidebar_title"))}</div>',
                unsafe_allow_html=True,
            )

        with toggle_col:
            if st.button(current_ui_language_toggle_label(), key="ui_language_toggle_button"):
                st.session_state.ui_locale = "es" if UI_LOCALE == "en" else "en"
                st.rerun()

        st.markdown(
            f'<p class="cw-sidebar-subtitle">{html.escape(t("sidebar_subtitle"))}</p>'
            '<div class="cw-sidebar-divider"></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="cw-sidebar-spacer"></div>', unsafe_allow_html=True)

        st.selectbox(
            t("commit_style"),
            options=COMMIT_STYLE_OPTIONS,
            format_func=commit_style_label,
            key="commit_style",
        )

        col_lang, col_type = st.columns(2, gap="small")
        with col_lang:
            st.selectbox(
                t("output_language"),
                options=OUTPUT_LANGUAGE_OPTIONS,
                format_func=output_language_label,
                key="output_language",
            )
        with col_type:
            st.selectbox(
                t("change_type"),
                options=CHANGE_TYPE_OPTIONS,
                format_func=change_type_label,
                key="change_type",
            )

        st.text_input(t("scope"), placeholder=t("scope_placeholder"), key="scope")

        col_formality, col_alternatives = st.columns([1, 1], gap="small")
        with col_formality:
            st.selectbox(
                t("formality"),
                options=FORMALITY_OPTIONS,
                format_func=formality_label,
                key="formality_level",
            )
        with col_alternatives:
            render_alternatives_toggle()

        history_default = os.getenv("HISTORY_ENABLED", "true").strip().lower() == "true"
        save_to_history = st.checkbox(t("save_history"), value=history_default)

        st.divider()
        # Only report a provider/model when an API key is actually configured;
        # without one ProviderFactory can't connect, so show a generic notice.
        # Works on Streamlit Cloud (st.secrets) and locally (.env) alike.
        api_connected = bool((get_config("LLM_API_KEY") or "").strip())
        if api_connected:
            provider = get_config("LLM_PROVIDER", "deepseek")
            model = get_config("LLM_MODEL", "deepseek-v4-flash")
            badges = f"""
                <div class="cw-provider-badge">
                    <span>{html.escape(t("provider"))}</span>
                    <strong>{html.escape(provider)}</strong>
                </div>
                <div class="cw-provider-badge">
                    <span>{html.escape(t("model"))}</span>
                    <strong>{html.escape(model)}</strong>
                </div>
            """
        else:
            badges = f"""
                <div class="cw-provider-badge">
                    <strong>{html.escape(t("no_api"))}</strong>
                </div>
            """
        st.markdown(
            f'<div class="cw-provider-stack">{badges}</div>',
            unsafe_allow_html=True,
        )

        return save_to_history

save_history = render_sidebar()
render_hero()

left_column, right_column = st.columns([1.35, 0.85], gap="large")

with left_column:
    with st.form("commit_form", clear_on_submit=False):
        st.text_area(
            t("description"),
            placeholder=t("description_placeholder"),
            key="change_description",
            max_chars=1000,
        )

        form_col_a, form_col_b, form_col_c = st.columns([1, 1, 1.35])
        with form_col_a:
            submitted = st.form_submit_button(t("generate"), use_container_width=True, type="primary")
        with form_col_b:
            clean_clicked = st.form_submit_button(t("clear"), use_container_width=True)
        with form_col_c:
            st.caption(t("estimated_time"))

    if clean_clicked:
        reset_form()
        st.rerun()

    if submitted:
        payload = build_payload_from_state()
        with st.spinner(t("generating")):
            generate_commit(payload, save_to_history=save_history)

    if st.session_state.get("last_error"):
        st.error(translate_error_message(st.session_state.last_error))
        st.info(t("error_info"))

    if st.session_state.get("last_result"):
        result = CommitResult.model_validate(st.session_state.last_result)
        render_result(result)

        if st.button(t("regenerate"), use_container_width=True, type="primary"):
            payload = st.session_state.get("last_request_payload") or build_payload_from_state()
            with st.spinner(t("regenerating")):
                generate_commit(payload, save_to_history=save_history)
            st.rerun()

    render_help()
    render_history_expander()

with right_column:
    render_examples()

footer_text = html.escape(t("footer"))
footer_link = '<a href="https://github.com/juandiegoc30" target="_blank" rel="noopener noreferrer">github.com/juandiegoc30</a>'
footer_html = '<div class="cw-footer">' + footer_text.replace("github.com/juandiegoc30", footer_link) + '</div>'

st.markdown(
    footer_html,
    unsafe_allow_html=True,
)
