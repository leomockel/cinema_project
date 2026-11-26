import streamlit as st
from pathlib import Path
import base64
from src.styles.css_loader import load_multiple_css


@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f'''
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* Rendre le header transparent */
    [data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0);
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)



def apply_page_styles(bg_image_path: Path, css_files: list):
    """
    Applique un fond d'écran personnalisé et charge les fichiers CSS pour la page courante.
    """
    # Application du fond d'écran
    try:
        set_png_as_page_bg(bg_image_path)
    except FileNotFoundError:
        st.error(f"Fichier image non trouvé : {bg_image_path}")
    
    # Chargement des CSS spécifiques à la page
    st.session_state.css_loaded = load_multiple_css(css_files)


def show_message(text: str, message_type: str = "info"):
    """
    Affiche une boîte de message personnalisée selon le thème CSS spécifié.
    
    Types disponibles : 'success', 'warning', 'error', 'info'
    """
    # Configuration des thèmes CSS (Vos couleurs + icônes assorties)
    THEMES = {
        "success": {
            "color": "#059669",
            "bg": "rgba(5, 150, 105, 0.8)",
            "icon": "✅"
        },
        "warning": {
            "color": "#D97706",
            "bg": "rgba(217, 119, 6, 0.8)",
            "icon": "⚠️"
        },
        "error": {
            "color": "#DC2626",
            "bg": "rgba(220, 38, 38, 0.8)",
            "icon": "🚨"
        },
        "info": {
            "color": "#0891B2",
            "bg": "rgba(8, 145, 178, 0.8)",
            "icon": "ℹ️"
        }
    }
    
    # Valeur par défaut ('info') si le type fourni est inconnu
    theme = THEMES.get(message_type.lower(), THEMES["info"])
    
    html_code = f"""
    <div style="
        background-color: {theme['bg']};
        border-left: 5px solid {theme['color']};
        color: #FFFFFF;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 10px 0;
        font-family: system-ui, -apple-system, sans-serif;
        display: flex;
        align-items: flex-start;
        gap: 12px;
    ">
        <span style="font-size: 1.2rem; line-height: 1.2;">{theme['icon']}</span>
        <div style="flex-grow: 1; font-size: 0.95rem; line-height: 1.4;">
            <span>{text}</span>
        </div>
    </div>
    """
    
    st.markdown(html_code, unsafe_allow_html=True)