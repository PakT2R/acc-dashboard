#!/usr/bin/env python3
"""
ACC Web Dashboard - Streamlit Application
Piattaforma web per la gestione e visualizzazione dati ACC
Versione ottimizzata per deployment GitHub/Cloud
"""

import streamlit as st
import sqlite3
import json
import pandas as pd
import os
import requests
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, List, Tuple

# Configurazione pagina
st.set_page_config(
    page_title="TFL3 Standings Dashboard",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

class ACCWebDashboard:
    """Classe principale per il dashboard web ACC"""
    

    # ==================== SEZIONE 1: METODI CORE (CONDIVISI) ====================

    def __init__(self):
        """Inizializza il dashboard con gestione ambiente"""
        self.config = self.load_config()
        self.db_path = self.get_database_path()
        #self.is_github_deployment = self.detect_github_deployment()
        
        # Verifica esistenza database
        if not self.check_database():
            self.show_database_error()
            st.stop()
        
        # CSS personalizzato
        self.inject_custom_css()
    
    def detect_github_deployment(self) -> bool:
        """Rileva se l'app è in esecuzione su GitHub/Cloud"""
        # Controlla variabili d'ambiente tipiche dei servizi cloud
        cloud_indicators = [
            'STREAMLIT_SHARING',         # Streamlit Cloud (legacy)
            'STREAMLIT_CLOUD',           # Streamlit Cloud (nuovo)
            'STREAMLIT_SERVER_HEADLESS', # Streamlit in produzione
            'HEROKU',                    # Heroku
            'RAILWAY_ENVIRONMENT',       # Railway
            'RENDER',                    # Render
            'GITHUB_ACTIONS',            # GitHub Actions
            'VERCEL',                    # Vercel
            'NETLIFY',                   # Netlify
        ]
        
        return any(os.getenv(indicator) for indicator in cloud_indicators)
    
    def get_database_path(self) -> str:
        """Ottiene il percorso del database considerando l'ambiente"""
        # Priorità: variabile d'ambiente > config file > default
        db_path = (
            os.getenv('ACC_DATABASE_PATH') or 
            self.config.get('database', {}).get('path') or 
            'acc_stats.db'
        )
        
        return db_path
    
    def load_config(self) -> dict:
        """Carica configurazione con fallback per GitHub"""
        config_sources = [
            'acc_config.json',   # Locale
            'acc_config_d.json', # GitHub
        ]
        
        # Configurazione di default
        default_config = {
            "community": {
                "name": os.getenv('ACC_COMMUNITY_NAME', "Community Name"),
                "description": os.getenv('ACC_COMMUNITY_DESC', "Community Desc")
            },
            "database": {
                "path": os.getenv('ACC_DATABASE_PATH', "acc_stats.db")
            }
        }
        
        # Prova a caricare da file
        for config_file in config_sources:
            if Path(config_file).exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        file_config = json.load(f)
                    
                    # Merge con default, priorità al file
                    merged_config = default_config.copy()
                    self._deep_merge(merged_config, file_config)
                    
                    # 🎯 IMPOSTA IL FLAG BASANDOSI SUL FILE CARICATO
                    self.is_github_deployment = (config_file == 'acc_config_d.json')
                    
                    return merged_config
                    
                except Exception as e:
                    continue
        
        # Se nessun file trovato, assume cloud per sicurezza
        self.is_github_deployment = True
        return default_config
    
    def _deep_merge(self, base_dict: dict, update_dict: dict):
        """Merge ricorsivo di dizionari"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def check_database(self) -> bool:
        """Verifica esistenza e validità del database"""
        if not Path(self.db_path).exists():
            return False
        
        try:
            # Test connessione e tabelle principali
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verifica tabelle essenziali
            required_tables = ['drivers', 'sessions', 'championships']
            for table in required_tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    conn.close()
                    return False
            
            conn.close()
            return True
            
        except Exception:
            return False

    def inject_custom_css(self):
        """Inietta CSS personalizzato con miglioramenti per mobile"""
        st.markdown("""
        <style>
        /* CSS esistente + miglioramenti */
        .main-header {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(90deg, #1f4e79, #2d5a87);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #1f4e79;
            margin-bottom: 1rem;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f4e79;
            margin: 0;
        }
        
        .metric-label {
            font-size: 1.1rem;
            color: #666;
            margin: 0;
        }
        
        .championship-header {
            background: linear-gradient(135deg, #2d2d2d, #1e1e1e);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            margin: 1rem 0;
        }
        
        .competition-header {
            background: linear-gradient(135deg, #3d3d3d, #2a2a2a);
            color: white;
            padding: 0.8rem;
            border-radius: 6px;
            text-align: center;
            margin: 1rem 0;
        }
        
        .session-header {
            background: #f0f2f6;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            border-left: 3px solid #1f4e79;
            margin: 0.5rem 0;
        }
        
        .environment-indicator {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.8rem;
            z-index: 1000;
        }
        
        .github-badge {
            background: #24292e;
            color: white;
        }
        
        .local-badge {
            background: #28a745;
            color: white;
        }
        
        .fun-header {
            background: linear-gradient(90deg, #28a745, #20c997);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            margin: 1rem 0;
        }

        .social-buttons button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3) !important;
            transition: all 0.3s ease;
        }
        
        /* Responsive improvements */
        @media (max-width: 768px) {
            .metric-value {
                font-size: 2rem;
            }
            
            .main-header h1 {
                font-size: 1.8rem;
            }
            
            .main-header h3 {
                font-size: 1.2rem;
            }
        }
        
        /* Fix per tabelle su mobile */
        .dataframe {
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .dataframe {
                font-size: 0.8rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    def safe_sql_query(self, query: str, params: List = None) -> pd.DataFrame:
        """Esegue query SQL con gestione errori"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn, params=params or [])
            conn.close()
            return df
        except Exception as e:
            st.error(f"❌ Errore nella query: {e}")
            return pd.DataFrame()

    def format_lap_time(self, lap_time_ms: Optional[int]) -> str:
        """Converte tempo giro da millisecondi a formato MM:SS.sss"""
        if not lap_time_ms or lap_time_ms <= 0:
            return "N/A"
        
        # Filtri anti-anomalie
        if lap_time_ms > 3600000 or lap_time_ms < 30000:
            return "N/A"
        
        minutes = lap_time_ms // 60000
        seconds = (lap_time_ms % 60000) / 1000
        return f"{minutes}:{seconds:06.3f}"
    
    def get_database_stats(self) -> Dict:
        """Ottiene statistiche generali dal database con gestione errori migliorata"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Statistiche base con fallback
            stats = {}
            
            # Query sicure con gestione errori
            safe_queries = {
                'total_drivers': 'SELECT COUNT(*) FROM drivers WHERE trust_level > 0',
                'guest_drivers': 'SELECT COUNT(*) FROM drivers WHERE trust_level = 0',
                'total_leagues': 'SELECT COUNT(*) FROM leagues',
                'total_sessions': 'SELECT COUNT(*) FROM sessions',
                'total_valid_laps': '''SELECT COUNT(*) FROM laps
                                     WHERE is_valid_for_best = 1''',
            }
            
            for key, query in safe_queries.items():
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    stats[key] = result[0] if result else 0
                except Exception as e:
                    st.warning(f"⚠️ Error in query {key}: {e}")
                    stats[key] = 0
            
            # Ultima gara di campionato
            try:
                cursor.execute('''SELECT MAX(date_start) FROM competitions 
                                WHERE championship_id IS NOT NULL AND is_completed = 1''')
                stats['last_championship_race'] = cursor.fetchone()[0]
            except Exception:
                stats['last_championship_race'] = None
            
            # Detentore del titolo - pilota vincitore dell'ultimo campionato completato
            try:
                cursor.execute('''
                    SELECT d.last_name 
                    FROM championship_standings cs
                    JOIN drivers d ON cs.driver_id = d.driver_id
                    JOIN championships ch ON cs.championship_id = ch.championship_id
                    WHERE cs.position = 1 AND ch.is_completed = 1
                    ORDER BY ch.end_date DESC
                    LIMIT 1
                ''')
                result = cursor.fetchone()
                stats['title_holder'] = result[0] if result else None
            except Exception:
                stats['title_holder'] = None
            
            # Prossima competizione prevista
            try:
                cursor.execute('''
                    SELECT c.name, c.date_start, c.track_name, ch.name as championship_name
                    FROM competitions c
                    LEFT JOIN championships ch ON c.championship_id = ch.championship_id
                    WHERE c.is_completed = 0 AND c.date_start IS NOT NULL
                    ORDER BY c.date_start ASC
                    LIMIT 1
                ''')
                result = cursor.fetchone()
                if result:
                    stats['next_competition'] = {
                        'name': result[0],
                        'date': result[1],
                        'track': result[2],
                        'championship': result[3]
                    }
                else:
                    stats['next_competition'] = None
            except Exception:
                stats['next_competition'] = None
            
            conn.close()
            return stats
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero statistiche: {e}")
            # Ritorna statistiche vuote invece di crashare
            return {
                'total_drivers': 0,
                'guest_drivers': 0,
                'total_leagues': 0,
                'total_sessions': 0,
                'total_valid_laps': 0,
                'last_championship_race': None,
                'title_holder': None,
                'next_competition': None
            }
    
    def get_session_results(self, session_id: str) -> pd.DataFrame:
        """Ottiene risultati sessione"""
        query = """
            SELECT
                sr.position,
                sr.race_number,
                d.last_name as driver,
                COALESCE(cm.car_name, sr.car_model) as car,
                sr.lap_count,
                sr.best_lap,
                sr.total_time,
                sr.is_spectator,
                d.trust_level
            FROM session_results sr
            JOIN drivers d ON sr.driver_id = d.driver_id
            LEFT JOIN car_models cm ON sr.car_model = cm.car_model
            WHERE sr.session_id = ?
            ORDER BY
                CASE WHEN sr.position IS NULL THEN 1 ELSE 0 END,
                sr.position
        """

        return self.safe_sql_query(query, [session_id])

    def format_session_date(self, session_date: str) -> str:
        """Formatta data sessione per visualizzazione"""
        try:
            date_obj = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
            return date_obj.strftime('%d/%m/%Y')
        except:
            return session_date[:10] if session_date else 'N/A'

    def format_session_type(self, session_type: str) -> str:
        """Formatta tipo sessione per visualizzazione compatta"""
        session_mapping = {
            'R1': 'Gara', 'R2': 'Gara', 'R3': 'Gara', 'R4': 'Gara', 'R5': 'Gara',
            'R6': 'Gara', 'R7': 'Gara', 'R8': 'Gara', 'R9': 'Gara', 'R': 'Gara',
            'Q1': 'Qualifiche', 'Q2': 'Qualifiche', 'Q3': 'Qualifiche', 'Q4': 'Qualifiche',
            'Q5': 'Qualifiche', 'Q6': 'Qualifiche', 'Q7': 'Qualifiche', 'Q8': 'Qualifiche',
            'Q9': 'Qualifiche', 'Q': 'Qualifiche',
            'FP1': 'Prove', 'FP2': 'Prove', 'FP3': 'Prove', 'FP4': 'Prove', 'FP5': 'Prove',
            'FP6': 'Prove', 'FP7': 'Prove', 'FP8': 'Prove', 'FP9': 'Prove', 'FP': 'Prove'
        }
        
        return session_mapping.get(session_type, session_type)
    

    # ==================== HOMEPAGE ====================

    def show_environment_indicator(self):
        """Mostra indicatore ambiente (solo in sviluppo locale)"""
        if not self.is_github_deployment:
            st.markdown("""
            <div class="environment-indicator local-badge">
                🏠 Locale
            </div>
            """, unsafe_allow_html=True)

    def show_community_banner(self):
        """Mostra banner community con link social"""
        try:
            # Verifica se il banner esiste
            banner_path = "banner.jpg"
            if Path(banner_path).exists():
                # Converti l'immagine in base64 per embedding CSS
                import base64
                with open(banner_path, "rb") as img_file:
                    img_base64 = base64.b64encode(img_file.read()).decode()

                community_name = self.config['community']['name']
                community_description = self.config['community'].get('description', 'ACC Server Dashboard')

                # Banner con background image e testo sovrapposto via CSS puro
                st.markdown(f"""
                <div style="
                    background-image: url(data:image/jpeg;base64,{img_base64});
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    height: 300px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                    margin: 2rem 0;
                    border-radius: 15px;
                    position: relative;
                ">
                    <div style="
                        background: rgba(0,0,0,0.4);
                        padding: 2rem;
                        border-radius: 15px;
                        color: white;
                    ">
                        <h1 style="margin: 0; font-size: 3rem; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">🏁 {community_name}</h1>
                        <h3 style="margin: 0.5rem 0 0 0; font-size: 1.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">{community_description}</h3>
                    </div>
                </div>

                <style>
                @media (max-width: 768px) {{
                    div[data-testid="stMarkdownContainer"] h1 {{
                        font-size: 2rem !important;
                    }}
                    div[data-testid="stMarkdownContainer"] h3 {{
                        font-size: 1.2rem !important;
                    }}
                }}
                </style>
                """, unsafe_allow_html=True)

                # Link social (solo se configurati)
                social_config = self.config.get('social', {})
                discord_url = social_config.get('discord')
                simgrid_url = social_config.get('simgrid')

                if discord_url or simgrid_url:
                    social_buttons = []

                    if simgrid_url:
                        social_buttons.append(f'<a href="{simgrid_url}" target="_blank" style="text-decoration: none; margin: 0 1rem;"><button style="background: linear-gradient(90deg, #5865f2, #7289da); color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 25px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">🏆 SimGrid Community</button></a>')

                    if discord_url:
                        social_buttons.append(f'<a href="{discord_url}" target="_blank" style="text-decoration: none; margin: 0 1rem;"><button style="background: linear-gradient(90deg, #5865f2, #7289da); color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 25px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">💬 Join Discord</button></a>')

                    st.markdown(f"""
                    <div style="text-align: center; margin: 1rem 0;">
                        {''.join(social_buttons)}
                    </div>
                    """, unsafe_allow_html=True)

            else:
                # Fallback con il riquadro blu originale se non c'è il banner
                community_name = self.config['community']['name']
                community_description = self.config['community'].get('description', 'ACC Server Dashboard')
                st.markdown(f"""
                <div class="main-header">
                    <h1>🏁 {community_name}</h1>
                    <h3>{community_description}</h3>
                </div>
                """, unsafe_allow_html=True)

                # Link social (solo se configurati)
                social_config = self.config.get('social', {})
                discord_url = social_config.get('discord')
                simgrid_url = social_config.get('simgrid')

                if discord_url or simgrid_url:
                    social_buttons = []

                    if simgrid_url:
                        social_buttons.append(f'<a href="{simgrid_url}" target="_blank" style="text-decoration: none; margin: 0 1rem;"><button style="background: linear-gradient(90deg, #5865f2, #7289da); color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 25px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">🏆 SimGrid Community</button></a>')

                    if discord_url:
                        social_buttons.append(f'<a href="{discord_url}" target="_blank" style="text-decoration: none; margin: 0 1rem;"><button style="background: linear-gradient(90deg, #5865f2, #7289da); color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 25px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">💬 Join Discord</button></a>')

                    st.markdown(f"""
                    <div style="text-align: center; margin: 1rem 0;">
                        {''.join(social_buttons)}
                    </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            # Fallback in caso di errore
            pass

    def show_database_error(self):
        """Mostra errore database con istruzioni specifiche per l'ambiente"""
        st.error("❌ **Database non disponibile**")

        if self.is_github_deployment:
            st.markdown("""
            ### 🔄 Database in aggiornamento

            Il database potrebbe essere in fase di aggiornamento.
            Riprova tra qualche minuto.

            **Per gli amministratori:**
            - Verifica che il file `acc_stats.db` sia presente nel repository
            - Controlla che il file non sia danneggiato
            - Assicurati che contenga le tabelle necessarie
            """)
        else:
            st.markdown(f"""
            ### 🚀 Setup Locale

            **Database non trovato:** `{self.db_path}`

            **Istruzioni:**
            1. Esegui il manager principale per creare il database
            2. Verifica che il percorso nel file di configurazione sia corretto
            3. Assicurati che il database contenga dati

            **File di configurazione cercati:**
            - `acc_config.json` (locale)
            - `acc_config_d.json` (template)
            """)

    def show_daily_article(self):
        """Mostra la rassegna stampa caricata da GitHub"""
        import requests

        st.subheader("📰 Rassegna Stampa")

        try:
            # URL GitHub raw per daily_article.html
            github_config = self.config.get('github', {})
            username = github_config.get('username', 'PakT2R')
            repo = github_config.get('repository', 'tfl3-dashboard')
            branch = github_config.get('branch', 'main')

            article_url = f"https://raw.githubusercontent.com/{username}/{repo}/{branch}/daily_article.html"

            # Carica articolo da GitHub
            response = requests.get(article_url, timeout=5)

            if response.status_code == 200:
                # Mostra HTML dell'articolo
                st.components.v1.html(response.text, height=800, scrolling=True)
            else:
                st.info("📝 Nessun articolo disponibile al momento. Torna presto per nuovi aggiornamenti!")

        except requests.exceptions.RequestException as e:
            # In caso di errore di rete, mostra messaggio generico
            st.info("📝 Articolo temporaneamente non disponibile. Riprova più tardi!")
        except Exception as e:
            # Altri errori: mostra in locale, ignora in produzione
            if not self.is_github_deployment:
                st.warning(f"⚠️ Errore caricamento articolo: {str(e)}")

    def show_homepage(self):
        """Mostra la homepage con statistiche generali"""
        # Indicatore ambiente (solo locale)
        self.show_environment_indicator()

        # Banner Enigma Overdrive - QUESTA È LA RIGA DA AGGIUNGERE
        self.show_community_banner()
        
        # Info deployment per admin (solo in locale)
        if not self.is_github_deployment:
            with st.expander("ℹ️ System Info", expanded=False):
                st.write(f"**Database:** `{self.db_path}`")
                st.write(f"**Configuration:** Loaded")
                st.write(f"**Environment:** Local Development")
        
        # Ottieni statistiche
        stats = self.get_database_stats()
        
        if not any(stats.values()):
            st.warning("⚠️ No data available in database")
            return

        # TFL Introduction Text
        st.markdown("""<div style="background: linear-gradient(135deg, #6c757d 0%, #5a6268 50%, #495057 100%); padding: 40px 30px; border-radius: 20px; margin: 20px 0; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3); text-align: center; color: white; border: 3px solid rgba(255, 255, 255, 0.15);">
<p style="font-size: 2.5rem; font-weight: 900; margin: 0 0 25px 0; text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.4); letter-spacing: 1px; line-height: 1.2;">🏁 One night a week, one season together 🏁</p>
<div style="background: rgba(255, 255, 255, 0.25); padding: 2px; margin: 25px auto; width: 80%; border-radius: 5px;"></div>
<p style="font-size: 1.2rem; margin: 20px 0; font-weight: 500; text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.4);">Welcome to the official dashboard of the <strong>Tier Friends League</strong></p>
<p style="font-size: 1.1rem; margin: 25px 0 15px 0; font-weight: 600; text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.4);">Use the menu to view:</p>
<div style="background: rgba(255, 255, 255, 0.15); padding: 20px; border-radius: 12px; margin: 20px auto; max-width: 600px; backdrop-filter: blur(10px);">
<p style="margin: 10px 0; font-size: 1.05rem; font-weight: 500;">⏱️ <strong>Time Attack</p>
<p style="margin: 10px 0; font-size: 1.05rem; font-weight: 500;">📊 <strong>Standings and Results</p>
<p style="margin: 10px 0; font-size: 1.05rem; font-weight: 500;">🏎️ <strong>Daily Casual Races</p>
<p style="margin: 10px 0; font-size: 1.05rem; font-weight: 500;">📈 <strong>Best Recorded Laps</p>
<p style="margin: 10px 0; font-size: 1.05rem; font-weight: 500;">👤 <strong>Driver Information</p>
</div>
<div style="background: rgba(255, 255, 255, 0.25); padding: 2px; margin: 25px auto; width: 80%; border-radius: 5px;"></div>
<p style="font-size: 1.3rem; margin: 20px 0 10px 0; font-weight: 700; text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.4);">⏰ Race every Wednesday at 10:00 PM</p>
<p style="font-size: 1.1rem; margin: 15px 0 0 0; font-weight: 600; font-style: italic; text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.4);">Organized by Terronia Racing 🏴</p>
</div>""", unsafe_allow_html=True)

        # Link to rulebook
        st.markdown("""<div style="text-align: center; margin: 25px 0;">
<a href="https://htmlpreview.github.io/?https://github.com/PakT2R/tfl3-dashboard/blob/main/tfl3_regolamento.html" target="_blank" style="text-decoration: none;">
<div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            display: inline-block; padding: 18px 50px; border-radius: 50px;
            box-shadow: 0 6px 25px rgba(40, 167, 69, 0.4);
            border: 3px solid rgba(255, 255, 255, 0.3);
            transition: all 0.3s ease;
            cursor: pointer;">
<p style="color: white; font-size: 1.3rem; font-weight: 700; margin: 0;
          text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);">
📖 Read the Complete TFL3 Rulebook
</p>
</div>
</a>
</div>""", unsafe_allow_html=True)

        # Statistiche principali
        st.markdown("---")
        st.subheader("📊 Database Statistics")

        st.markdown(f"""
        - 👥 **Registered Drivers:** {stats['total_drivers']}
        - 👻 **Guest Drivers:** {stats['guest_drivers']}
        - 🏆 **Leagues:** {stats['total_leagues']}
        - 🎮 **Total Sessions:** {stats['total_sessions']}
        - ⏱️ **Valid Laps:** {stats['total_valid_laps']}
        """)

        # Rassegna Stampa
        st.markdown("---")
        self.show_daily_article()

    # [Tutte le altre funzioni rimangono identiche]


    # ==================== TIME ATTACK ====================

    def show_time_attack_report(self):
        """Mostra il report Time Attack con selezione competizione"""
        st.header("Time Attack")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Ottieni TUTTE le competizioni (come in Standings)
            # Ordinate per data (più recenti prima)
            cursor.execute("""
                SELECT
                    c.competition_id,
                    c.name,
                    c.track_name,
                    c.round_number,
                    c.date_start,
                    c.date_end,
                    c.weekend_format,
                    c.is_completed,
                    (SELECT COUNT(*) FROM sessions WHERE competition_id = c.competition_id AND is_time_attack = 1) as session_count,
                    (SELECT COUNT(*) FROM time_attack_results WHERE competition_id = c.competition_id) as results_count,
                    l.name as league_name,
                    ch.tier_number,
                    ch.name as tier_name
                FROM competitions c
                LEFT JOIN championships ch ON c.championship_id = ch.championship_id
                LEFT JOIN leagues l ON ch.league_id = l.league_id
                GROUP BY c.competition_id
                ORDER BY
                    CASE WHEN c.date_start IS NULL THEN 1 ELSE 0 END,
                    c.date_start DESC,
                    c.round_number DESC
            """)

            competitions = cursor.fetchall()

            if not competitions:
                st.warning("❌ No competitions found in database")
                conn.close()
                return

            # Prepara opzioni per selectbox
            competition_options = []
            competition_map = {}
            default_index = 0

            for idx, (comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed, session_count, results_count, league_name, tier_number, tier_name) in enumerate(competitions):
                # Formato display
                round_str = f"R{round_num} - " if round_num else ""
                status_str = " ✅" if is_completed else " 🔄"
                date_str = f" ({date_start[:10]})" if date_start else ""

                display_name = f"{round_str}{name} - {track}{date_str}{status_str}"

                competition_options.append(display_name)
                competition_map[display_name] = (comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed, session_count, results_count, league_name, tier_number, tier_name)

            # Trova default index: più recente con risultati Time Attack o sessioni Time Attack
            first_with_data_idx = None
            for idx, (comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed, session_count, results_count, league_name, tier_number, tier_name) in enumerate(competitions):
                if (session_count > 0 or results_count > 0) and first_with_data_idx is None:
                    first_with_data_idx = idx
                    break

            # Seleziona la più recente con dati Time Attack, altrimenti la prima in lista
            if first_with_data_idx is not None:
                default_index = first_with_data_idx
            else:
                default_index = 0  # Fallback alla prima competizione

            # Selectbox competizione
            selected_competition = st.selectbox(
                "🏁 Select Competition:",
                options=competition_options,
                index=default_index,
                key="ta_competition_select"
            )

            if selected_competition:
                comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed, session_count, results_count, league_name, tier_number, tier_name = competition_map[selected_competition]

                # Header competizione
                round_str = f"Round {round_num} - " if round_num else ""
                # Calcola data fine (meno un giorno) per il display
                from datetime import datetime, timedelta
                if date_end:
                    try:
                        date_end_obj = datetime.fromisoformat(date_end.replace('Z', '+00:00'))
                        date_end_display = (date_end_obj - timedelta(days=1)).strftime('%Y-%m-%d')
                    except:
                        date_end_display = date_end[:10] if len(date_end) >= 10 else 'N/A'
                else:
                    date_end_display = 'N/A'

                date_range = f"{date_start[:10] if date_start else 'N/A'} - {date_end_display}"

                # League and tier info
                league_str = f"{league_name}" if league_name else "No League"
                tier_str = f"Tier {tier_number} - {tier_name}" if tier_number and tier_name else (f"Tier {tier_number}" if tier_number else "")

                st.markdown(f"""
                <div class="competition-header">
                    <p style="margin: 0 0 8px 0; font-size: 1.3rem; font-weight: 600; color: #FF6B35;">{league_str}</p>
                    <p style="margin: 0 0 15px 0; font-size: 1.1rem; font-weight: 500; color: #4ECDC4;">{tier_str}</p>
                    <h3>⏱️ {round_str}{name}</h3>
                    <p>📍 {track} | 📅 {date_range}</p>
                </div>
                """, unsafe_allow_html=True)

                # Query Time Attack results
                cursor.execute("""
                    SELECT
                        d.last_name,
                        tar.best_lap_time,
                        tar.best_split1,
                        tar.best_split2,
                        tar.best_split3,
                        tar.points,
                        s.session_date,
                        COALESCE(cm.car_name, tar.car_model) as car_name
                    FROM time_attack_results tar
                    JOIN drivers d ON tar.driver_id = d.driver_id
                    LEFT JOIN sessions s ON tar.session_id = s.session_id
                    LEFT JOIN car_models cm ON tar.car_model = cm.car_model
                    WHERE tar.competition_id = ?
                        AND tar.best_lap_time IS NOT NULL
                        AND tar.best_lap_time > 30000
                        AND tar.best_lap_time < 3600000
                    ORDER BY tar.best_lap_time ASC
                """, (comp_id,))

                ta_results = cursor.fetchall()
                conn.close()

                if not ta_results:
                    st.info("ℹ️ No Time Attack results recorded for this competition")
                    return

                # Formatta risultati per visualizzazione
                st.subheader("⏱️ Time Attack Leaderboard")

                # Determina se la competizione è scaduta (data sistema >= date_end, usando timezone italiano)
                from datetime import datetime, timedelta
                is_expired = False
                if date_end:
                    try:
                        end_date = datetime.strptime(date_end, '%Y-%m-%d')
                        now_italy = datetime.now(ZoneInfo("Europe/Rome")).replace(tzinfo=None)
                        is_expired = now_italy >= end_date
                    except:
                        is_expired = False

                # Crea DataFrame
                data = []
                prev_time = None
                for idx, (driver, lap_time, split1, split2, split3, points, session_date, car_name) in enumerate(ta_results, 1):
                    # Calcola gap rispetto al pilota che precede
                    if idx > 1 and prev_time is not None:
                        gap_ms = lap_time - prev_time
                        gap_seconds = gap_ms / 1000.0
                        gap_str = f"+{gap_seconds:.3f}s"
                    else:
                        gap_str = "-"
                    prev_time = lap_time

                    # Formatta splits (da milliseconds a secondi)
                    def format_split(split_ms):
                        if split_ms is None or split_ms == 0:
                            return "-"
                        return f"{split_ms / 1000:.3f}s"

                    split1_str = format_split(split1)
                    split2_str = format_split(split2)
                    split3_str = format_split(split3)

                    # Formatta data con ora
                    if session_date:
                        try:
                            from datetime import datetime
                            date_obj = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
                            date_str = date_obj.strftime('%d/%m/%Y %H:%M')
                        except:
                            date_str = session_date[:16] if len(session_date) >= 16 else session_date[:10] if session_date else 'N/A'
                    else:
                        date_str = 'N/A'

                    data.append({
                        "Pos": str(idx),
                        "Driver": driver,
                        "Car": car_name if car_name else "-",
                        "Points": f"{points:.1f}" if points and points > 0 else "0.0",
                        "Best Lap": self.format_lap_time(lap_time),
                        "Gap": gap_str,
                        "S1": split1_str,
                        "S2": split2_str,
                        "S3": split3_str,
                        "Date": date_str
                    })

                df = pd.DataFrame(data)

                # Calcola altezza per mostrare almeno 15 piloti senza scroll
                # ~35px per riga + ~38px per header
                min_rows = 15
                row_height = 35
                header_height = 38
                num_rows = len(df)
                display_rows = max(min_rows, num_rows)
                table_height = (display_rows * row_height) + header_height

                # Applica colore alla colonna Points: verde se scaduta (punti definitivi), rosso altrimenti (punti provvisori)
                points_style = 'color: #44BB44; font-weight: bold' if is_expired else 'color: #FF4444; font-weight: bold'
                styled_df = df.style.map(lambda x: points_style, subset=['Points'])

                st.dataframe(
                    styled_df,
                    width='stretch',
                    hide_index=True,
                    height=table_height
                )

                # Grafico scostamento dal tempo medio
                st.markdown("---")

                import plotly.graph_objects as go

                # Calcola tempo medio
                avg_time = sum(r[1] for r in ta_results) / len(ta_results) / 1000  # in secondi
                avg_time_str = self.format_lap_time(int(avg_time * 1000))

                st.subheader(f"📊 Deviation from Average Lap Time ({avg_time_str})")

                # Prepara dati piloti con scostamento (ordinati dal più veloce al più lento)
                pilot_data = []
                for driver, lap_time, split1, split2, split3, points, session_date, car_name in ta_results:
                    time_sec = lap_time / 1000
                    deviation = time_sec - avg_time
                    pilot_data.append({'driver': driver, 'deviation': deviation})

                # Ordina dal più lento (in alto) al più veloce (in basso) per visualizzazione
                pilot_data.reverse()

                drivers = [p['driver'] for p in pilot_data]
                deviations = [p['deviation'] for p in pilot_data]
                colors = ['#44BB44' if d < 0 else '#FF4444' for d in deviations]

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    y=drivers,
                    x=deviations,
                    orientation='h',
                    marker_color=colors,
                    text=[f"{d:+.3f}s" for d in deviations],
                    textposition='outside',
                    textfont=dict(color='white', size=11),
                    hovertemplate='%{y}<br>%{x:+.3f}s<extra></extra>'
                ))

                fig.update_layout(
                    xaxis_title='Deviation from Average (seconds)',
                    yaxis_title='',
                    height=max(400, len(drivers) * 30 + 100),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    showlegend=False,
                    xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='white'),
                    bargap=0.3
                )

                st.plotly_chart(fig, width='stretch')

                st.caption("🟢 Faster than avg | 🔴 Slower than avg")

        except Exception as e:
            st.error(f"❌ Error loading Time Attack data: {e}")


    # ==================== RACE RESULTS ====================

    def get_competition_results(self, competition_id: int) -> pd.DataFrame:
        """Ottiene risultati competizione con dettagli completi"""
        query = """
            SELECT
                d.last_name as driver,
                cs.race_points,
                cs.pole_points,
                cs.fastest_lap_points,
                cs.time_attack_points,
                cs.points_bonus,
                cs.points_dropped,
                cs.total_points,
                cs.guests_beaten,
                cs.beaten_by_guests,
                d.trust_level
            FROM competition_standings cs
            JOIN drivers d ON cs.driver_id = d.driver_id
            WHERE cs.competition_id = ?
                AND d.trust_level > 0
            ORDER BY cs.total_points DESC,
                     cs.race_points DESC
        """

        return self.safe_sql_query(query, [competition_id])
    
    def get_competition_sessions(self, competition_id: int) -> List[Tuple]:
        """Ottiene sessioni della competizione con nome del pilota che ha fatto il best lap"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    s.session_id,
                    s.session_type,
                    s.session_date,
                    s.session_order,
                    s.total_drivers,
                    s.best_lap_overall,
                    d.last_name as best_lap_driver
                FROM sessions s
                LEFT JOIN session_results sr ON s.session_id = sr.session_id
                    AND s.best_lap_overall = sr.best_lap
                    AND sr.is_spectator = FALSE
                LEFT JOIN drivers d ON sr.driver_id = d.driver_id
                WHERE s.competition_id = ?
                    AND (s.is_time_attack IS NULL OR s.is_time_attack = 0)
                ORDER BY s.session_order, s.session_date
            """, (competition_id,))

            sessions = cursor.fetchall()
            conn.close()

            return sessions

        except Exception as e:
            st.error(f"❌ Errore nel recupero sessioni: {e}")
            return []
    
    def show_race_results(self):
        """Mostra il report Race Results con selezione competizione"""
        st.header("Race Results")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Ottieni TUTTE le competizioni (come in Time Attack)
            # Ordinate per data (più recenti prima)
            cursor.execute("""
                SELECT
                    c.competition_id,
                    c.name,
                    c.track_name,
                    c.round_number,
                    c.date_start,
                    c.date_end,
                    c.weekend_format,
                    c.is_completed,
                    (SELECT COUNT(*) FROM sessions WHERE competition_id = c.competition_id AND (is_time_attack = 0 OR is_time_attack IS NULL)) as session_count,
                    (SELECT COUNT(*) FROM competition_standings WHERE competition_id = c.competition_id) as results_count,
                    l.name as league_name,
                    ch.tier_number,
                    ch.name as tier_name
                FROM competitions c
                LEFT JOIN championships ch ON c.championship_id = ch.championship_id
                LEFT JOIN leagues l ON ch.league_id = l.league_id
                GROUP BY c.competition_id
                ORDER BY
                    CASE WHEN c.date_start IS NULL THEN 1 ELSE 0 END,
                    c.date_start DESC,
                    c.round_number DESC
            """)

            competitions = cursor.fetchall()

            if not competitions:
                st.warning("❌ No competitions found in database")
                conn.close()
                return

            # Prepara opzioni per selectbox
            competition_options = []
            competition_map = {}
            default_index = 0

            for idx, (comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed, session_count, results_count, league_name, tier_number, tier_name) in enumerate(competitions):
                # Formato display
                round_str = f"R{round_num} - " if round_num else ""
                status_str = " ✅" if is_completed else " 🔄"
                date_str = f" ({date_start[:10]})" if date_start else ""

                display_name = f"{round_str}{name} - {track}{date_str}{status_str}"

                competition_options.append(display_name)
                competition_map[display_name] = (comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed, session_count, results_count, league_name, tier_number, tier_name)

            # Trova default index: più recente con risultati o sessioni
            first_with_data_idx = None
            for idx, (comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed, session_count, results_count, league_name, tier_number, tier_name) in enumerate(competitions):
                if (session_count > 0 or results_count > 0) and first_with_data_idx is None:
                    first_with_data_idx = idx
                    break

            # Seleziona la più recente con dati, altrimenti la prima in lista
            if first_with_data_idx is not None:
                default_index = first_with_data_idx
            else:
                default_index = 0  # Fallback alla prima competizione

            # Selectbox competizione
            selected_competition = st.selectbox(
                "🏁 Select Competition:",
                options=competition_options,
                index=default_index,
                key="race_results_competition_select"
            )

            if selected_competition:
                comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed, session_count, results_count, league_name, tier_number, tier_name = competition_map[selected_competition]

                # Header competizione
                round_str = f"Round {round_num} - " if round_num else ""
                # Mostra solo data fine (senza meno un giorno)
                date_display = date_end[:10] if date_end else 'N/A'

                # League and tier info
                league_str = f"{league_name}" if league_name else "No League"
                tier_str = f"Tier {tier_number} - {tier_name}" if tier_number and tier_name else (f"Tier {tier_number}" if tier_number else "")

                st.markdown(f"""
                <div class="competition-header">
                    <p style="margin: 0 0 8px 0; font-size: 1.3rem; font-weight: 600; color: #FF6B35;">{league_str}</p>
                    <p style="margin: 0 0 15px 0; font-size: 1.1rem; font-weight: 500; color: #4ECDC4;">{tier_str}</p>
                    <h3>🏁 {round_str}{name}</h3>
                    <p>📍 {track} | 📋 {weekend_format} | 📅 {date_display}</p>
                </div>
                """, unsafe_allow_html=True)

                # Competition Leaderboard
                st.subheader("🏁 Competition Leaderboard")
                results_df = self.get_competition_results(comp_id)

                if not results_df.empty:
                    # Formatta risultati per visualizzazione
                    results_display = results_df.copy()

                    # Aggiungi posizione basata sull'ordine (già ordinato per punti nella query)
                    results_display['Pos'] = range(1, len(results_display) + 1)
                    results_display['Pos'] = results_display['Pos'].apply(lambda x: str(x))

                    # Formatta i valori numerici
                    # Race points: "0.0" per membri con 0 punti, "-" per guest con 0 punti, altrimenti valore
                    results_display['race_points'] = results_display.apply(
                        lambda row: "0.0" if pd.notna(row['race_points']) and row['race_points'] == 0 and row['trust_level'] > 0
                        else ("-" if pd.notna(row['race_points']) and row['race_points'] == 0
                        else (f"{row['race_points']:.1f}" if pd.notna(row['race_points']) else "-")),
                        axis=1
                    )
                    results_display['pole_points'] = results_display['pole_points'].apply(lambda x: f"{int(x)}" if pd.notna(x) and x > 0 else "-")
                    results_display['fastest_lap_points'] = results_display['fastest_lap_points'].apply(lambda x: f"{int(x)}" if pd.notna(x) and x > 0 else "-")
                    results_display['time_attack_points'] = results_display['time_attack_points'].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x > 0 else "-")
                    # Bonus: mostra + se positivo, - se negativo, "-" se zero/null
                    results_display['points_bonus'] = results_display['points_bonus'].apply(
                        lambda x: f"+{x:.1f}" if pd.notna(x) and x > 0 else (f"-{abs(x):.1f}" if pd.notna(x) and x < 0 else "-")
                    )
                    results_display['points_dropped'] = results_display['points_dropped'].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x > 0 else "-")
                    # Total points: "0.0" per membri con 0 punti, "-" per guest con 0 punti, altrimenti valore
                    results_display['total_points'] = results_display.apply(
                        lambda row: "0.0" if pd.notna(row['total_points']) and row['total_points'] == 0 and row['trust_level'] > 0
                        else ("-" if pd.notna(row['total_points']) and row['total_points'] == 0
                        else (f"{row['total_points']:.1f}" if pd.notna(row['total_points']) else "-")),
                        axis=1
                    )
                    results_display['guests_beaten'] = results_display['guests_beaten'].apply(lambda x: f"{int(x)}" if pd.notna(x) and x > 0 else "-")
                    results_display['beaten_by_guests'] = results_display['beaten_by_guests'].apply(lambda x: f"{int(x)}" if pd.notna(x) and x > 0 else "-")

                    # Seleziona colonne da mostrare nell'ordine richiesto
                    columns_to_show = [
                        'Pos', 'driver', 'total_points', 'time_attack_points', 'race_points', 'pole_points',
                        'fastest_lap_points', 'points_dropped', 'points_bonus',
                        'guests_beaten', 'beaten_by_guests'
                    ]

                    # Rinomina colonne con i nomi corti
                    column_names = {
                        'Pos': 'Pos',
                        'driver': 'Driver',
                        'total_points': 'Total Pts',
                        'race_points': 'Race Pts',
                        'pole_points': 'Pole Pts',
                        'fastest_lap_points': 'FLap Pts',
                        'time_attack_points': 'TA Pts',
                        'points_dropped': 'Drop Pts',
                        'points_bonus': 'Bonus G Pts',
                        'guests_beaten': 'G+',
                        'beaten_by_guests': 'G-'
                    }

                    results_display = results_display[columns_to_show]
                    results_display.columns = [column_names[col] for col in columns_to_show]

                    # Applica stile: Total Pts in grassetto e verde, colonne statistiche con sfondo chiaro
                    def highlight_competition_columns(s):
                        # Colonne statistiche con sfondo chiaro
                        stats_cols = ['G+', 'G-']
                        if s.name in stats_cols:
                            return ['background-color: #f0f2f6;' for _ in s]
                        # Total Pts in grassetto e verde
                        elif s.name == 'Total Pts':
                            return ['font-weight: bold; color: green;' for _ in s]
                        else:
                            return ['' for _ in s]

                    styled_results = results_display.style.apply(highlight_competition_columns, axis=0)

                    st.dataframe(
                        styled_results,
                        width='stretch',
                        hide_index=True,
                        height=35 * min(25, len(results_display)) + 38
                    )
                else:
                    st.info("ℹ️ No race results recorded for this competition")

                # Sessioni della competizione
                st.markdown("---")
                st.subheader("📊 Session Results")

                sessions = self.get_competition_sessions(comp_id)

                if sessions:
                    for session_id, session_type, session_date, session_order, total_drivers, best_lap_overall, best_lap_driver in sessions:
                        # Format data
                        try:
                            date_obj = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
                            date_str = date_obj.strftime('%d/%m/%Y %H:%M')
                        except:
                            date_str = session_date[:16] if session_date else 'N/A'

                        # Header sessione
                        best_lap_text = f'⚡ Best: {self.format_lap_time(best_lap_overall)} ({best_lap_driver})' if best_lap_overall and best_lap_driver else (f'⚡ Best: {self.format_lap_time(best_lap_overall)}' if best_lap_overall else '')
                        st.markdown(f"""
                        <div style="background: #5a5a5a; padding: 12px 16px; border-radius: 8px; margin: 15px 0 10px 0; border-left: 4px solid #888;">
                            <p style="margin: 0; color: #ffffff; font-size: 1.05rem; font-weight: 600;">
                                🏁 {session_type} <span style="font-weight: 400; opacity: 0.9;">- {date_str} | 👥 {total_drivers} drivers{f' | {best_lap_text}' if best_lap_text else ''}</span>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Risultati sessione
                        session_results_df = self.get_session_results(session_id)

                        if not session_results_df.empty:
                            # Formatta risultati sessione
                            session_display = session_results_df.copy()

                            # Usa solo numeri per le posizioni
                            session_display['Pos'] = session_display['position'].apply(
                                lambda x: str(int(x)) if pd.notna(x) else "NC"
                            )

                            # Formatta tempo giro
                            session_display['Best Lap'] = session_display['best_lap'].apply(
                                lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
                            )

                            # Formatta tempo totale
                            session_display['Total Time'] = session_display['total_time'].apply(
                                lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
                            )

                            # Crea colonna Type con icona (persona per registrati, ghost per guest)
                            session_display['Type'] = session_display['trust_level'].apply(
                                lambda x: "👤" if x > 0 else "👻"
                            )

                            # Formatta colonna Car
                            session_display['Car'] = session_display['car'].apply(
                                lambda x: x if pd.notna(x) else "-"
                            )

                            # Seleziona colonne da mostrare (Driver prima di Num#)
                            columns_to_show = ['Pos', 'driver', 'race_number', 'Car', 'Type', 'lap_count', 'Best Lap', 'Total Time', 'trust_level']
                            column_names = {
                                'Pos': 'Pos',
                                'driver': 'Driver',
                                'race_number': 'Num#',
                                'Car': 'Car',
                                'Type': 'Type',
                                'lap_count': 'Laps',
                                'Best Lap': 'Best Lap',
                                'Total Time': 'Total Time',
                                'trust_level': 'trust_level'  # Manteniamo per lo stile
                            }

                            session_display = session_display[columns_to_show]
                            session_display.columns = [column_names[col] for col in columns_to_show]

                            # Rimuovi colonna trust_level dalla visualizzazione finale
                            final_columns = ['Pos', 'Driver', 'Num#', 'Car', 'Type', 'Laps', 'Best Lap', 'Total Time']
                            session_display_final = session_display.drop(columns=['trust_level'])
                            session_display_final.columns = final_columns

                            # Configurazione larghezza colonne: colonne strette per Pos, Num#, Type, Laps
                            st.dataframe(
                                session_display_final,
                                width='stretch',
                                hide_index=True,
                                height=35 * min(25, len(session_display_final)) + 38,
                                column_config={
                                    "Pos": st.column_config.TextColumn("Pos", width="small"),
                                    "Num#": st.column_config.TextColumn("Num#", width="small"),
                                    "Type": st.column_config.TextColumn("Type", width="small"),
                                    "Laps": st.column_config.TextColumn("Laps", width="small")
                                }
                            )
                        else:
                            st.warning(f"⚠️ No results found for {session_type}")
                else:
                    st.info("ℹ️ No sessions found for this competition")

            conn.close()

        except Exception as e:
            st.error(f"❌ Error loading Race Results data: {e}")


    # ==================== STANDINGS ====================

    def get_championship_standings(self, championship_id: int) -> pd.DataFrame:
        """Ottiene classifica campionato con tutti i dettagli"""
        query = """
            SELECT
                cs.position,
                d.last_name as driver,
                cs.total_points,
                cs.competitions_participated,
                cs.wins,
                cs.podiums,
                cs.poles,
                cs.fastest_laps,
                cs.gross_points,
                cs.points_dropped,
                cs.base_points,
                cs.participation_multiplier,
                cs.participation_bonus,
                COALESCE(SUM(CASE WHEN mp.is_active = 1 THEN mp.penalty_points ELSE 0 END), 0) as manual_penalties
            FROM championship_standings cs
            JOIN drivers d ON cs.driver_id = d.driver_id
            LEFT JOIN manual_penalties mp ON cs.championship_id = mp.championship_id
                AND cs.driver_id = mp.driver_id AND mp.is_active = 1
            WHERE cs.championship_id = ?
            GROUP BY cs.championship_id, cs.driver_id, cs.position, d.last_name,
                     cs.total_points, cs.competitions_participated, cs.wins, cs.podiums,
                     cs.poles, cs.fastest_laps, cs.gross_points, cs.points_dropped,
                     cs.base_points, cs.participation_multiplier, cs.participation_bonus
            ORDER BY cs.position
        """
        
        return self.safe_sql_query(query, [championship_id])
    
    def show_leagues_report(self):
        """Mostra il report leagues"""
        st.header("Standings")

        # Ottieni lista leagues con conteggio standing
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    l.league_id,
                    l.name,
                    l.season,
                    l.start_date,
                    l.end_date,
                    l.total_tiers,
                    l.is_completed,
                    l.description,
                    COUNT(ls.driver_id) as standings_count
                FROM leagues l
                LEFT JOIN league_standings ls ON l.league_id = ls.league_id
                GROUP BY l.league_id
                ORDER BY
                    CASE WHEN l.start_date IS NULL THEN 1 ELSE 0 END,
                    l.start_date DESC,
                    l.league_id DESC
            """)

            leagues = cursor.fetchall()

            if not leagues:
                st.warning("❌ No leagues found in database")
                conn.close()
                return

            # Prepara opzioni per selectbox
            league_options = []
            league_map = {}
            default_league_index = 0  # Default: prima league

            for league_id, name, season, start_date, end_date, total_tiers, is_completed, description, standings_count in leagues:
                # Formato display
                status_str = " ✅" if is_completed else " 🔄"
                season_str = f" - {season}" if season else ""
                display_name = f"{name}{season_str}{status_str}"
                league_options.append(display_name)
                league_map[display_name] = league_id

            # Trova default index: più recente con classifica calcolata
            first_with_standings_idx = None

            for idx, (league_id, name, season, start_date, end_date, total_tiers, is_completed, description, standings_count) in enumerate(leagues):
                if standings_count > 0 and first_with_standings_idx is None:
                    first_with_standings_idx = idx
                    break

            # Seleziona la più recente con standing, altrimenti la prima in lista
            if first_with_standings_idx is not None:
                default_league_index = first_with_standings_idx
            else:
                default_league_index = 0  # Fallback alla prima league

            # Selectbox league
            st.subheader("Leagues")
            selected_league_display = st.selectbox(
                "🌟 Select a League:",
                league_options,
                index=default_league_index,
                key="league_selector"
            )

            selected_league_id = league_map[selected_league_display]

            # Ottieni dettagli league selezionata
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name, season, start_date, end_date, total_tiers, is_completed, description
                FROM leagues
                WHERE league_id = ?
            """, (selected_league_id,))

            league_info = cursor.fetchone()

            if league_info:
                name, season, start_date, end_date, total_tiers, is_completed, description = league_info

                # Header league con stile championship-header
                status_icon = "✅" if is_completed else "🔄"

                # Costruisci l'HTML completo
                header_html = f"""
                <div class="championship-header">
                    <h2>🌟 {name} {status_icon}</h2>
                """

                if description:
                    header_html += f"<p style='margin-top: 10px;'>{description}</p>"

                # Info aggiuntive
                info_parts = []
                if total_tiers:
                    info_parts.append(f"🎯 {total_tiers} Tiers")

                if start_date and end_date:
                    try:
                        start = datetime.fromisoformat(start_date.replace('Z', '+00:00')).strftime('%d/%m/%Y')
                        end = datetime.fromisoformat(end_date.replace('Z', '+00:00')).strftime('%d/%m/%Y')
                        info_parts.append(f"📅 {start} - {end}")
                    except:
                        pass

                if info_parts:
                    header_html += f"<p style='margin-top: 10px;'>{' | '.join(info_parts)}</p>"

                header_html += "</div>"

                st.markdown(header_html, unsafe_allow_html=True)

                # Classifica league
                st.subheader("🌟 League Standings")

                query_standings = """
                    SELECT
                        ls.position,
                        d.last_name as driver,
                        ls.tier1_points,
                        ls.tier2_points,
                        ls.tier3_points,
                        ls.tier4_points,
                        ls.total_final_points,
                        ls.consistency_cv,
                        ls.consistency_bonus,
                        ls.tiers_participated,
                        ls.total_wins,
                        ls.total_podiums,
                        ls.total_poles,
                        ls.total_fastest_laps
                    FROM league_standings ls
                    JOIN drivers d ON ls.driver_id = d.driver_id
                    WHERE ls.league_id = ?
                    ORDER BY ls.position ASC
                """

                df_standings = pd.read_sql_query(query_standings, conn, params=(selected_league_id,))

                if not df_standings.empty:
                    # Formatta colonne
                    df_display = df_standings.copy()
                    df_display['position'] = df_display['position'].astype(int)

                    # Rinomina colonne (nell'ordine originale della query)
                    df_display.columns = ['Pos', 'Driver', 'Tier 1 Pts', 'Tier 2 Pts', 'Tier 3 Pts', 'Tier 4 Pts',
                                         'Total Pts', 'CV%', 'Consist Pts', 'n Tiers', 'n Wins', 'n Pods', 'n Poles', 'n FLaps']

                    # Formatta valori numerici: trattini per zeri, decimali per valori > 0
                    df_display['Tier 1 Pts'] = df_display['Tier 1 Pts'].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x > 0 else "-")
                    df_display['Tier 2 Pts'] = df_display['Tier 2 Pts'].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x > 0 else "-")
                    df_display['Tier 3 Pts'] = df_display['Tier 3 Pts'].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x > 0 else "-")
                    df_display['Tier 4 Pts'] = df_display['Tier 4 Pts'].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x > 0 else "-")
                    df_display['Total Pts'] = df_display['Total Pts'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "0.0")
                    # CV% in percentuale (moltiplicato per 100)
                    df_display['CV%'] = df_display['CV%'].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) and x > 0 else "-")
                    df_display['Consist Pts'] = df_display['Consist Pts'].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x > 0 else "-")
                    # Formatta statistiche: trattini per zeri
                    df_display['n Tiers'] = df_display['n Tiers'].apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else "-")
                    df_display['n Wins'] = df_display['n Wins'].apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else "-")
                    df_display['n Pods'] = df_display['n Pods'].apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else "-")
                    df_display['n Poles'] = df_display['n Poles'].apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else "-")
                    df_display['n FLaps'] = df_display['n FLaps'].apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else "-")

                    # Riordina colonne: Pos, Driver, Total Pts, Tier 1-4, CV%, Consist, n Tiers, n Wins, n Pods, n Poles, n FLaps
                    column_order = ['Pos', 'Driver', 'Total Pts', 'Tier 1 Pts', 'Tier 2 Pts', 'Tier 3 Pts', 'Tier 4 Pts',
                                   'CV%', 'Consist Pts', 'n Tiers', 'n Wins', 'n Pods', 'n Poles', 'n FLaps']
                    df_display = df_display[column_order]

                    # Applica stile: Total Pts in grassetto e verde, colonne statistiche con sfondo chiaro
                    def highlight_league_columns(s):
                        # Colonne statistiche con sfondo chiaro (incluso CV%)
                        stats_cols = ['CV%', 'n Tiers', 'n Wins', 'n Pods', 'n Poles', 'n FLaps']
                        if s.name in stats_cols:
                            return ['background-color: #f0f2f6;' for _ in s]
                        # Total Pts in grassetto e verde
                        elif s.name == 'Total Pts':
                            return ['font-weight: bold; color: green;' for _ in s]
                        else:
                            return ['' for _ in s]

                    styled_league = df_display.style.apply(highlight_league_columns, axis=0)

                    # Configura larghezza colonne (in pixel)
                    column_config = {
                        'Pos': st.column_config.TextColumn('Pos', width=60),
                        'Driver': st.column_config.TextColumn('Driver', width=150),
                        'Total Pts': st.column_config.TextColumn('Total Pts', width=80),
                        'Tier 1 Pts': st.column_config.TextColumn('Tier 1 Pts', width=80),
                        'Tier 2 Pts': st.column_config.TextColumn('Tier 2 Pts', width=80),
                        'Tier 3 Pts': st.column_config.TextColumn('Tier 3 Pts', width=80),
                        'Tier 4 Pts': st.column_config.TextColumn('Tier 4 Pts', width=80),
                        'CV%': st.column_config.TextColumn('CV%', width=70),
                        'Consist Pts': st.column_config.TextColumn('Consist Pts', width=90),
                        'n Tiers': st.column_config.TextColumn('n Tiers', width=70),
                        'n Wins': st.column_config.TextColumn('n Wins', width=70),
                        'n Pods': st.column_config.TextColumn('n Pods', width=70),
                        'n Poles': st.column_config.TextColumn('n Poles', width=70),
                        'n FLaps': st.column_config.TextColumn('n FLaps', width=70)
                    }

                    # Mostra tabella
                    st.dataframe(
                        styled_league,
                        width='stretch',
                        hide_index=True,
                        height=35 * len(df_display) + 38
                    )
                else:
                    st.info("No standings available for this league yet")

                # Selezione tier (championships)
                st.markdown("---")
                st.subheader("Tiers")

                # Ottieni championships (tier) della lega con conteggio standing
                cursor.execute("""
                    SELECT
                        c.championship_id,
                        c.name,
                        c.tier_number,
                        c.start_date,
                        c.end_date,
                        c.is_completed,
                        c.description,
                        COUNT(cs.driver_id) as standings_count
                    FROM championships c
                    LEFT JOIN championship_standings cs ON c.championship_id = cs.championship_id
                    WHERE c.league_id = ? AND c.championship_type = 'tier'
                    GROUP BY c.championship_id
                    ORDER BY
                        CASE WHEN c.start_date IS NULL THEN 1 ELSE 0 END,
                        c.start_date DESC,
                        c.championship_id DESC
                """, (selected_league_id,))

                tier_championships = cursor.fetchall()

                if tier_championships:
                    # Prepara opzioni per selectbox tier
                    tier_options = ["Select a tier..."]
                    tier_map = {}
                    default_tier_index = 1  # Default al primo tier (dopo "Select a tier...")

                    for idx, (champ_id, champ_name, tier_num, date_start, date_end, is_completed, desc, standings_count) in enumerate(tier_championships):
                        # Formato display
                        status_str = " ✅" if is_completed else " 🔄"
                        date_str = f" ({date_start[:10]})" if date_start else ""
                        display_name = f"Tier {tier_num} - {champ_name}{date_str}{status_str}"

                        tier_options.append(display_name)
                        tier_map[display_name] = champ_id

                    # Trova default index: più recente con classifica calcolata
                    first_with_standings_idx = None

                    for idx, (champ_id, champ_name, tier_num, date_start, date_end, is_completed, desc, standings_count) in enumerate(tier_championships):
                        if standings_count > 0 and first_with_standings_idx is None:
                            first_with_standings_idx = idx + 1  # +1 per "Select a tier..."
                            break

                    # Seleziona il più recente con standing, altrimenti il primo in lista
                    if first_with_standings_idx is not None:
                        default_tier_index = first_with_standings_idx
                    else:
                        default_tier_index = 1  # Fallback al primo tier

                    # Selectbox tier
                    selected_tier = st.selectbox(
                        "🏆 Select a Tier:",
                        options=tier_options,
                        index=default_tier_index,
                        key="tier_select"
                    )

                    if selected_tier and selected_tier != "Select a tier...":
                        tier_championship_id = tier_map[selected_tier]

                        # Trova info tier selezionato
                        selected_tier_info = next(
                            (t for t in tier_championships if t[0] == tier_championship_id),
                            None
                        )

                        if selected_tier_info:
                            champ_id, champ_name, tier_num, date_start, date_end, is_completed, desc, standings_count = selected_tier_info

                            # Header tier championship
                            tier_header = f"""
                            <div class="championship-header">
                                <h3>🏆 Tier {tier_num} - {champ_name}</h3>
                            """

                            if desc:
                                tier_header += f"<p>{desc}</p>"

                            if date_start and date_end:
                                tier_header += f"<p>📅 {date_start} - {date_end}</p>"

                            tier_header += "</div>"

                            st.markdown(tier_header, unsafe_allow_html=True)

                            # Classifica tier championship
                            st.subheader("🏆 Tier Standings")
                            standings_df = self.get_championship_standings(tier_championship_id)

                            if not standings_df.empty:
                                # Ottieni drop_worst_results e total_rounds per questo championship
                                cursor.execute("""
                                    SELECT COALESCE(ps.drop_worst_results, 0) as drop_worst,
                                           ch.total_rounds
                                    FROM competitions c
                                    LEFT JOIN points_systems ps ON c.points_system_json = ps.name
                                    JOIN championships ch ON c.championship_id = ch.championship_id
                                    WHERE c.championship_id = ?
                                    LIMIT 1
                                """, (tier_championship_id,))

                                result = cursor.fetchone()
                                drop_worst = result[0] if result else 0
                                total_rounds = result[1] if result and result[1] else 0

                                # Calcola il numero minimo di gare che vengono conteggiate
                                counted_races = max(0, total_rounds - drop_worst) if total_rounds > 0 else 0

                                # Formatta classifica per visualizzazione
                                standings_display = standings_df.copy()

                                # Aggiungi medaglie per primi 3
                                standings_display['Pos'] = standings_display['position'].apply(
                                    lambda x: "🥇" if x == 1 else "🥈" if x == 2 else "🥉" if x == 3 else str(x)
                                )

                                # Formatta points_dropped PRIMA di convertire competitions_participated in stringa
                                def format_dropped_points(row):
                                    races = row['competitions_participated']
                                    dropped_pts = row['points_dropped']

                                    if pd.notna(dropped_pts) and dropped_pts > 0:
                                        return f"-{dropped_pts:.1f}"
                                    elif counted_races > 0 and races > counted_races:
                                        return "0.0"
                                    else:
                                        return "-"

                                standings_display['points_dropped'] = standings_display.apply(format_dropped_points, axis=1)

                                # Formatta i valori numerici - usa "-" per zero/null
                                standings_display['competitions_participated'] = standings_display['competitions_participated'].apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else "-")
                                standings_display['wins'] = standings_display['wins'].apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else "-")
                                standings_display['podiums'] = standings_display['podiums'].apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else "-")
                                standings_display['poles'] = standings_display['poles'].apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else "-")
                                standings_display['fastest_laps'] = standings_display['fastest_laps'].apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else "-")
                                standings_display['gross_points'] = standings_display['gross_points'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "0.0")
                                standings_display['manual_penalties'] = standings_display['manual_penalties'].apply(lambda x: f"-{x:.0f}" if pd.notna(x) and x > 0 else "-")
                                standings_display['total_points'] = standings_display['total_points'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "0.0")

                                # Seleziona colonne da mostrare nell'ordine richiesto: Pos, Driver, Total, Gross, Drop, Pen | n Comps, n Wins, n Pods, n Poles, n FLaps
                                columns_to_show = [
                                    'Pos', 'driver', 'total_points', 'gross_points', 'points_dropped',
                                    'manual_penalties', 'competitions_participated', 'wins', 'podiums',
                                    'poles', 'fastest_laps'
                                ]

                                # Rinomina colonne con i nomi corti
                                column_names = {
                                    'Pos': 'Pos',
                                    'driver': 'Driver',
                                    'total_points': 'Total Pts',
                                    'gross_points': 'Gross Pts',
                                    'points_dropped': 'Drop Pts',
                                    'manual_penalties': 'Pen Pts',
                                    'competitions_participated': 'n Comps',
                                    'wins': 'n Wins',
                                    'podiums': 'n Pods',
                                    'poles': 'n Poles',
                                    'fastest_laps': 'n FLaps'
                                }

                                standings_display = standings_display[columns_to_show]
                                standings_display.columns = [column_names[col] for col in columns_to_show]

                                # Applica stile: Total Pts in grassetto e verde, colonne statistiche con sfondo chiaro
                                def highlight_columns(s):
                                    # Colonne statistiche con sfondo chiaro
                                    stats_cols = ['n Comps', 'n Wins', 'n Pods', 'n Poles', 'n FLaps']
                                    if s.name in stats_cols:
                                        return ['background-color: #f0f2f6;' for _ in s]
                                    # Total Pts in grassetto e verde
                                    elif s.name == 'Total Pts':
                                        return ['font-weight: bold; color: green;' for _ in s]
                                    else:
                                        return ['' for _ in s]

                                styled_standings = standings_display.style.apply(highlight_columns, axis=0)

                                # Configura larghezza colonne (in pixel)
                                column_config = {
                                    'Pos': st.column_config.TextColumn('Pos', width=60),
                                    'Driver': st.column_config.TextColumn('Driver', width=150),
                                    'Total Pts': st.column_config.TextColumn('Total Pts', width=80),
                                    'Gross Pts': st.column_config.TextColumn('Gross Pts', width=80),
                                    'Drop Pts': st.column_config.TextColumn('Drop Pts', width=70),
                                    'Pen Pts': st.column_config.TextColumn('Pen Pts', width=70),
                                    'n Comps': st.column_config.TextColumn('n Comps', width=70),
                                    'n Wins': st.column_config.TextColumn('n Wins', width=60),
                                    'n Pods': st.column_config.TextColumn('n Pods', width=60),
                                    'n Poles': st.column_config.TextColumn('n Poles', width=70),
                                    'n FLaps': st.column_config.TextColumn('n FLaps', width=70)
                                }

                                # Mostra tabella senza indice e con altezza dinamica
                                st.dataframe(
                                    styled_standings,
                                    width='stretch',
                                    hide_index=True,
                                    height=35 * len(standings_display) + 38
                                )

                            else:
                                st.warning("⚠️ Tier championship leaderboard not yet calculated")
                else:
                    st.info("ℹ️ No tier championships found for this league")

                # Grafico andamento partecipanti giornalieri
                st.markdown("---")
                st.subheader("📈 Daily Participation Trend")

                try:
                    # Query per ottenere le date di fine competizione
                    cursor.execute("""
                        SELECT DISTINCT c.date_end, c.name
                        FROM competitions c
                        WHERE c.championship_id IN (
                            SELECT championship_id
                            FROM championships
                            WHERE league_id = ?
                        )
                        AND c.date_end IS NOT NULL
                        ORDER BY c.date_end ASC
                    """, (selected_league_id,))

                    competition_end_dates = cursor.fetchall()

                    # Query per contare partecipanti unici per giorno (separati per registrati e guest)
                    cursor.execute("""
                        SELECT
                            SUBSTR(s.filename, 1, 6) as date_str,
                            COUNT(DISTINCT CASE WHEN d.trust_level > 0 THEN sr.driver_id END) as registered_participants,
                            COUNT(DISTINCT CASE WHEN d.trust_level = 0 THEN sr.driver_id END) as guest_participants
                        FROM sessions s
                        JOIN session_results sr ON s.session_id = sr.session_id
                        JOIN drivers d ON sr.driver_id = d.driver_id
                        WHERE s.competition_id IN (
                            SELECT competition_id
                            FROM competitions
                            WHERE championship_id IN (
                                SELECT championship_id
                                FROM championships
                                WHERE league_id = ?
                            )
                        )
                        GROUP BY SUBSTR(s.filename, 1, 6)
                        ORDER BY date_str ASC
                    """, (selected_league_id,))

                    participation_data = cursor.fetchall()

                    if participation_data:
                        # Converti i dati per il grafico
                        dates = []
                        registered = []
                        guests = []

                        for date_str, reg_count, guest_count in participation_data:
                            # Converti YYMMDD in formato leggibile
                            try:
                                # Aggiungi "20" per completare l'anno (es. 251015 -> 20251015)
                                full_date_str = "20" + date_str
                                date_obj = datetime.strptime(full_date_str, "%Y%m%d")
                                formatted_date = date_obj.strftime("%d/%m/%Y")
                                dates.append(formatted_date)
                                registered.append(reg_count if reg_count else 0)
                                guests.append(guest_count if guest_count else 0)
                            except:
                                # Se la conversione fallisce, usa la stringa originale
                                dates.append(date_str)
                                registered.append(reg_count if reg_count else 0)
                                guests.append(guest_count if guest_count else 0)

                        # Crea il grafico con Plotly
                        fig = go.Figure()

                        # Linea per piloti registrati - BLU SOLIDA
                        fig.add_trace(go.Scatter(
                            x=dates,
                            y=registered,
                            mode='lines+markers',
                            name='Registered Drivers',
                            line=dict(color='#007bff', width=3),
                            marker=dict(size=8, color='#007bff'),
                            hovertemplate='<b>Registered:</b> %{y}<extra></extra>'
                        ))

                        # Linea per piloti guest - ROSSO LONGDASH
                        fig.add_trace(go.Scatter(
                            x=dates,
                            y=guests,
                            mode='lines+markers',
                            name='Guest Drivers',
                            line=dict(color='#dc3545', width=3, dash='longdash'),
                            marker=dict(size=8, color='#dc3545', symbol='diamond'),
                            hovertemplate='<b>Guests:</b> %{y}<extra></extra>'
                        ))

                        # Aggiungi shapes (linee verticali) per le date di fine competizione
                        shapes = []
                        added_dates = set()  # Per evitare duplicati
                        for date_end, comp_name in competition_end_dates:
                            try:
                                # Converti date_end (YYYY-MM-DD) in formato visualizzato nel grafico (dd/mm/YYYY)
                                if 'T' in date_end or 'Z' in date_end:
                                    date_obj = datetime.fromisoformat(date_end.replace('Z', '+00:00'))
                                else:
                                    date_obj = datetime.strptime(date_end, "%Y-%m-%d")

                                formatted_date = date_obj.strftime("%d/%m/%Y")

                                # Aggiungi shape solo se la data esiste nell'asse X e non è già presente
                                if formatted_date in dates and formatted_date not in added_dates:
                                    shapes.append(dict(
                                        type="line",
                                        x0=formatted_date,
                                        x1=formatted_date,
                                        y0=0,
                                        y1=1,
                                        yref="paper",
                                        line=dict(
                                            color="rgba(255, 165, 0, 0.6)",
                                            width=2,
                                            dash="dash"
                                        )
                                    ))
                                    added_dates.add(formatted_date)
                            except Exception as e:
                                # Se la conversione fallisce, salta questa data
                                pass

                        fig.update_layout(
                            title={
                                'text': 'Daily Unique Participants (Registered vs Guests)',
                                'x': 0.5,
                                'xanchor': 'center'
                            },
                            xaxis_title="Date",
                            yaxis_title="Number of Unique Participants",
                            hovermode='x unified',
                            template='plotly_dark',
                            height=500,
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            ),
                            xaxis=dict(
                                tickangle=-45,
                                tickmode='auto',
                                nticks=20
                            ),
                            yaxis=dict(
                                rangemode='tozero'
                            ),
                            shapes=shapes
                        )

                        st.plotly_chart(fig, width='stretch')

                        # Statistiche aggiuntive
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            avg_registered = sum(registered) / len(registered)
                            st.metric("Avg Registered", f"{avg_registered:.1f}")
                        with col2:
                            avg_guests = sum(guests) / len(guests)
                            st.metric("Avg Guests", f"{avg_guests:.1f}")
                        with col3:
                            max_registered = max(registered)
                            st.metric("Peak Registered", f"{max_registered}")
                        with col4:
                            max_guests = max(guests)
                            st.metric("Peak Guests", f"{max_guests}")

                    else:
                        st.info("ℹ️ No participation data available for this league yet")

                except Exception as e:
                    st.error(f"❌ Error loading participation trend: {e}")

            conn.close()

        except Exception as e:
            st.error(f"❌ Error loading leagues: {e}")


    # ==================== ALL SESSIONS ====================

    def format_session_datetime(self, session_date: str) -> str:
        """Formatta data e ora sessione per visualizzazione"""
        try:
            date_obj = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
            return date_obj.strftime('%d/%m/%Y %H:%M')
        except:
            return session_date[:16] if session_date else 'N/A'

    def get_sessions_statistics(self, date_from: date, date_to: date) -> Dict:
        """Ottiene statistiche sessioni per il periodo specificato - VERSIONE CORRETTA"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Converti date in string per query SQL
            date_from_str = date_from.strftime('%Y-%m-%d')
            date_to_str = (date_to + timedelta(days=1)).strftime('%Y-%m-%d')  # Include tutto il giorno 'to'
            
            # CORREZIONE: Statistiche sessioni separate dai driver
            # 1. Statistiche sessioni (senza JOIN con session_results)
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_sessions,
                    COUNT(CASE WHEN competition_id IS NOT NULL THEN 1 END) as official_sessions,
                    COUNT(CASE WHEN competition_id IS NULL THEN 1 END) as non_official_sessions
                FROM sessions s
                WHERE DATE(s.session_date) >= ? AND DATE(s.session_date) < ?
            ''', (date_from_str, date_to_str))
            
            session_result = cursor.fetchone()
            total_sessions, official, non_official = session_result
            
            # 2. Piloti unici separatamente
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT sr.driver_id) as unique_drivers
                FROM sessions s
                JOIN session_results sr ON s.session_id = sr.session_id
                WHERE DATE(s.session_date) >= ? AND DATE(s.session_date) < ?
            ''', (date_from_str, date_to_str))
            
            driver_result = cursor.fetchone()
            unique_drivers = driver_result[0] if driver_result else 0
            
            # Circuito con più sessioni (rimane invariato)
            cursor.execute('''
                SELECT 
                    track_name,
                    COUNT(*) as session_count
                FROM sessions s
                WHERE DATE(s.session_date) >= ? AND DATE(s.session_date) < ?
                GROUP BY track_name
                ORDER BY session_count DESC
                LIMIT 1
            ''', (date_from_str, date_to_str))
            
            track_result = cursor.fetchone()
            most_used_track = track_result[0] if track_result else "N/A"
            most_used_count = track_result[1] if track_result else 0
            
            # Ultima sessione (rimane invariato)
            cursor.execute('''
                SELECT 
                    track_name,
                    session_date,
                    session_type
                FROM sessions s
                WHERE DATE(s.session_date) >= ? AND DATE(s.session_date) < ?
                ORDER BY s.session_date DESC
                LIMIT 1
            ''', (date_from_str, date_to_str))
            
            last_result = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_sessions': total_sessions or 0,
                'unique_drivers': unique_drivers or 0,
                'official_sessions': official or 0,
                'non_official_sessions': non_official or 0,
                'most_used_track': most_used_track,
                'most_used_count': most_used_count,
                'last_session_track': last_result[0] if last_result else "N/A",
                'last_session_date': last_result[1] if last_result else None,
                'last_session_type': last_result[2] if last_result else "N/A"
            }
            
        except Exception as e:
            st.error(f"❌ Error retrieving sessions statistics: {e}")
            return {}
    
    def get_sessions_list_with_details(self, date_from: date, date_to: date) -> pd.DataFrame:
        """Ottiene lista sessioni con dettagli per il periodo specificato"""
        date_from_str = date_from.strftime('%Y-%m-%d')
        date_to_str = (date_to + timedelta(days=1)).strftime('%Y-%m-%d')
        
        query = '''
            SELECT
                s.session_id,
                s.session_type,
                s.track_name,
                s.session_date,
                s.total_drivers,
                s.competition_id,
                s.is_time_attack,
                -- Fastest driver info (migliore giro)
                fastest.driver_name as fastest_name,
                fastest.best_lap as fastest_time,
                -- Competition info se disponibile
                c.name as competition_name,
                c.round_number
            FROM sessions s
            LEFT JOIN (
                SELECT
                    sr.session_id,
                    d.last_name as driver_name,
                    sr.best_lap
                FROM session_results sr
                JOIN drivers d ON sr.driver_id = d.driver_id
                WHERE sr.best_lap > 0
                AND sr.best_lap = (
                    SELECT MIN(sr2.best_lap)
                    FROM session_results sr2
                    WHERE sr2.session_id = sr.session_id
                    AND sr2.best_lap > 0
                )
                GROUP BY sr.session_id
            ) fastest ON s.session_id = fastest.session_id
            LEFT JOIN competitions c ON s.competition_id = c.competition_id
            WHERE DATE(s.session_date) >= ? AND DATE(s.session_date) < ?
            ORDER BY s.session_date DESC
        '''
        
        return self.safe_sql_query(query, [date_from_str, date_to_str])
    
    def get_session_info(self, session_id: str) -> Optional[Tuple]:
        """Ottiene informazioni base della sessione"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    s.session_type,
                    s.track_name,
                    s.session_date,
                    s.total_drivers,
                    s.competition_id,
                    c.name as competition_name,
                    c.round_number
                FROM sessions s
                LEFT JOIN competitions c ON s.competition_id = c.competition_id
                WHERE s.session_id = ?
            ''', (session_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result
            
        except Exception as e:
            st.error(f"❌ Error retrieving session info: {e}")
            return None
    
    def show_sessions_report(self):
        """Mostra il report Sessions con filtri e statistiche"""
        st.header("📅 Sessions")

        # Calcola date di default (ultima settimana) usando timezone italiana
        today = datetime.now(ZoneInfo("Europe/Rome")).date()
        week_ago = today - timedelta(days=7)
        
        # Filtri data in colonne
        col1, col2 = st.columns(2)
        
        with col1:
            date_from = st.date_input(
                "📅 From Date:",
                value=week_ago,
                key="sessions_date_from"
            )
        
        with col2:
            date_to = st.date_input(
                "📅 To Date:",
                value=today,
                key="sessions_date_to"
            )
        
        # Validazione date
        if date_from > date_to:
            st.error("❌ 'From Date' must be before or equal to 'To Date'")
            return
        
        # Ottieni statistiche per il periodo selezionato
        st.markdown("---")
        sessions_stats = self.get_sessions_statistics(date_from, date_to)

        if not any(sessions_stats.values()):
            st.warning(f"⚠️ No sessions found in the selected period ({date_from} - {date_to})")
            return
        
        # Ottieni lista sessioni per selezione
        sessions_list = self.get_sessions_list_with_details(date_from, date_to)
        
        if sessions_list.empty:
            st.warning("⚠️ No sessions found for the selected period")
            return
        
        # SELECTBOX SESSIONE (come nel Best Lap Report)
        session_options = ["📊 General Summary"]
        session_map = {}
        
        # Prepara opzioni ordinate per data/ora decrescente (più recenti prima)
        sessions_sorted = sessions_list.sort_values('session_date', ascending=False)
        
        for idx, row in sessions_sorted.iterrows():
            session_id = row['session_id']
            track_name = row['track_name']
            
            # Formatta data e ora per visualizzazione
            try:
                date_obj = datetime.fromisoformat(row['session_date'].replace('Z', '+00:00'))
                datetime_str = date_obj.strftime('%d/%m/%Y %H:%M')
            except:
                datetime_str = row['session_date'][:16] if row['session_date'] else 'N/A'
            
            # Status: Time Attack, Official, o Unofficial
            if pd.notna(row.get('is_time_attack')) and row['is_time_attack'] == 1:
                status = "⏱️ Time Attack"
            elif pd.notna(row['competition_id']):
                status = "🏆"
            else:
                status = "❌"

            # Formato: session_id - track - datetime - status
            display_name = f"{session_id} - {track_name} - {datetime_str} {status}"
            
            session_options.append(display_name)
            session_map[display_name] = session_id
        
        # Selectbox per selezione sessione
        selected_session_option = st.selectbox(
            "🎮 Select Session:",
            options=session_options,
            index=0,  # General Summary selezionato di default
            key="session_select"
        )
        
        # Mostra contenuto basato sulla selezione
        if selected_session_option == "📊 General Summary":
            # Mostra riepilogo generale (tabella di tutte le sessioni)
            st.markdown("---")
            st.subheader("📋 Sessions List Summary")
            self.show_sessions_summary_table(sessions_list, sessions_stats)

            # Grafico partecipazione giornaliera (solo in General Summary)
            st.markdown("---")
            self.show_daily_participation_chart(date_from, date_to)

        elif selected_session_option in session_map:
            # Mostra dettagli della sessione specifica
            selected_session_id = session_map[selected_session_option]
            st.markdown("---")
            self.show_session_details(selected_session_id)

    def show_sessions_summary_table(self, sessions_list: pd.DataFrame, sessions_stats: Dict = None):
        """Mostra tabella riassuntiva di tutte le sessioni (General Summary)"""
        if sessions_list.empty:
            st.warning("⚠️ No sessions found")
            return
        
        # Prepara display sessioni per tabella riassuntiva
        display_df = sessions_list.copy()
        
        # Nome sessione = session_id
        display_df['Session'] = display_df['session_id']
        
        # Tipo sessione formattato
        display_df['Type'] = display_df['session_type'].apply(
            lambda x: self.format_session_type(x) if pd.notna(x) else "N/A"
        )
        
        # Status: Time Attack, Official, o Unofficial
        display_df['Status'] = display_df.apply(
            lambda row: "⏱️ Time Attack" if pd.notna(row.get('is_time_attack')) and row['is_time_attack'] == 1
            else ("🏆 Official" if pd.notna(row['competition_id']) else "❌ Unofficial"),
            axis=1
        )
        
        # Data formattata con ora
        display_df['Date & Time'] = display_df['session_date'].apply(
            lambda x: self.format_session_datetime(x) if pd.notna(x) else "N/A"
        )
        
        # Fastest driver info formattata
        display_df['Fastest'] = display_df['fastest_name'].fillna("N/A")

        # Best time formattata
        display_df['Best Time'] = display_df['fastest_time'].apply(
            lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
        )
        
        # Seleziona colonne finali per display
        columns_to_show = ['Session', 'Type', 'Status', 'track_name', 'Date & Time', 'total_drivers', 'Fastest', 'Best Time']
        column_names = {
            'Session': 'Session',
            'Type': 'Type',
            'Status': 'Status',
            'track_name': 'Track',
            'Date & Time': 'Date & Time',
            'total_drivers': 'Drivers',
            'Fastest': 'Fastest',
            'Best Time': 'Best Time'
        }
        
        final_display = display_df[columns_to_show].copy()
        final_display.columns = [column_names[col] for col in columns_to_show]
        
        # Mostra tabella completa
        st.dataframe(
            final_display,
            width='stretch',
            hide_index=True,
            height=500
        )
        
        # Info riassuntive
        total_sessions = len(final_display)
        time_attack_count = len(display_df[(pd.notna(display_df.get('is_time_attack'))) & (display_df['is_time_attack'] == 1)])
        official_count = len(display_df[pd.notna(display_df['competition_id']) & ((pd.isna(display_df.get('is_time_attack'))) | (display_df['is_time_attack'] == 0))])
        unofficial_count = total_sessions - official_count - time_attack_count

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.info(f"📊 **{total_sessions}** total sessions")

        with col2:
            st.success(f"🏆 **{official_count}** official race")

        with col3:
            st.info(f"⏱️ **{time_attack_count}** time attack")

        with col4:
            st.warning(f"❌ **{unofficial_count}** unofficial")

        # Statistiche dettagliate (dopo la tabella)
        if sessions_stats:
            st.markdown("---")
            st.subheader("📊 Period Statistics")

            # Formatta data ultima sessione
            if sessions_stats.get('last_session_date'):
                try:
                    last_date = datetime.fromisoformat(sessions_stats['last_session_date'].replace('Z', '+00:00'))
                    last_date_str = last_date.strftime('%d/%m/%Y %H:%M')
                except:
                    last_date_str = sessions_stats['last_session_date'][:16] if sessions_stats['last_session_date'] else "N/A"
            else:
                last_date_str = "N/A"

            # Elenco compatto statistiche
            st.markdown(f"""
            - 🎮 **Total Sessions:** {sessions_stats['total_sessions']}
            - 🏆 **Official Sessions:** {official_count}
            - ⏱️ **Time Attack Sessions:** {time_attack_count}
            - ❌ **Unofficial Sessions:** {unofficial_count}
            - 👥 **Unique Drivers:** {sessions_stats['unique_drivers']}
            - 🏁 **Most Used Track:** {sessions_stats['most_used_track']}
            - 📊 **Sessions on Most Used Track:** {sessions_stats['most_used_count']}
            - 📍 **Last Session Track:** {sessions_stats['last_session_track']}
            - 📅 **Last Session Date:** {last_date_str}
            """)

    def show_daily_participation_chart(self, date_from: date, date_to: date):
        """Mostra grafico andamento partecipazione giornaliera nel periodo selezionato"""
        st.subheader("📈 Daily Participation Trend")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Converti date per query SQL
            date_from_str = date_from.strftime('%Y-%m-%d')
            date_to_str = (date_to + timedelta(days=1)).strftime('%Y-%m-%d')

            # Query per contare partecipanti unici per giorno (separati per registrati e guest) + numero sessioni
            cursor.execute("""
                SELECT
                    DATE(s.session_date) as session_day,
                    COUNT(DISTINCT CASE WHEN d.trust_level > 0 THEN sr.driver_id END) as registered_participants,
                    COUNT(DISTINCT CASE WHEN d.trust_level = 0 THEN sr.driver_id END) as guest_participants,
                    COUNT(DISTINCT s.session_id) as total_sessions
                FROM sessions s
                JOIN session_results sr ON s.session_id = sr.session_id
                JOIN drivers d ON sr.driver_id = d.driver_id
                WHERE DATE(s.session_date) >= ? AND DATE(s.session_date) < ?
                GROUP BY DATE(s.session_date)
                ORDER BY session_day ASC
            """, (date_from_str, date_to_str))

            participation_data = cursor.fetchall()
            conn.close()

            if participation_data:
                # Converti i dati per il grafico
                dates = []
                registered = []
                guests = []
                sessions = []

                for session_day, reg_count, guest_count, session_count in participation_data:
                    # Formatta data per visualizzazione
                    try:
                        date_obj = datetime.strptime(session_day, "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%d/%m/%Y")
                        dates.append(formatted_date)
                        registered.append(reg_count if reg_count else 0)
                        guests.append(guest_count if guest_count else 0)
                        sessions.append(session_count if session_count else 0)
                    except:
                        # Se la conversione fallisce, usa la stringa originale
                        dates.append(session_day)
                        registered.append(reg_count if reg_count else 0)
                        guests.append(guest_count if guest_count else 0)
                        sessions.append(session_count if session_count else 0)

                # Crea il grafico con Plotly
                fig = go.Figure()

                # Linea per piloti registrati (asse Y sinistro) - BLU DOT (punteggiata)
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=registered,
                    mode='lines+markers',
                    name='Registered Drivers',
                    line=dict(color='#007bff', width=3, dash='dot'),
                    marker=dict(size=8, color='#007bff'),
                    hovertemplate='<b>Registered:</b> %{y}<extra></extra>',
                    yaxis='y'
                ))

                # Linea per piloti guest (asse Y sinistro) - ROSSO SOLIDA
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=guests,
                    mode='lines+markers',
                    name='Guest Drivers',
                    line=dict(color='#dc3545', width=3),
                    marker=dict(size=8, color='#dc3545', symbol='diamond'),
                    hovertemplate='<b>Guests:</b> %{y}<extra></extra>',
                    yaxis='y'
                ))

                # Linea per numero sessioni (asse Y destro) - VERDE SOLIDA
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=sessions,
                    mode='lines+markers',
                    name='Sessions',
                    line=dict(color='#28a745', width=2),
                    marker=dict(size=6, color='#28a745', symbol='square'),
                    hovertemplate='<b>Sessions:</b> %{y}<extra></extra>',
                    yaxis='y2'
                ))

                fig.update_layout(
                    title={
                        'text': 'Daily Participation & Sessions Trend',
                        'x': 0.5,
                        'xanchor': 'center'
                    },
                    xaxis_title="Date",
                    hovermode='x unified',
                    template='plotly_dark',
                    height=500,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    xaxis=dict(
                        tickangle=-45,
                        tickmode='auto',
                        nticks=20
                    ),
                    yaxis=dict(
                        title="Number of Unique Participants",
                        rangemode='tozero',
                        side='left'
                    ),
                    yaxis2=dict(
                        title="Number of Sessions",
                        rangemode='tozero',
                        side='right',
                        overlaying='y',
                        showgrid=False
                    )
                )

                st.plotly_chart(fig, width='stretch')

                # Statistiche aggiuntive
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                with col1:
                    avg_registered = sum(registered) / len(registered) if registered else 0
                    st.metric("Avg Registered", f"{avg_registered:.1f}")
                with col2:
                    max_registered = max(registered) if registered else 0
                    st.metric("Peak Registered", f"{max_registered}")
                with col3:
                    avg_guests = sum(guests) / len(guests) if guests else 0
                    st.metric("Avg Guests", f"{avg_guests:.1f}")
                with col4:
                    max_guests = max(guests) if guests else 0
                    st.metric("Peak Guests", f"{max_guests}")
                with col5:
                    avg_sessions = sum(sessions) / len(sessions) if sessions else 0
                    st.metric("Avg Sessions/Day", f"{avg_sessions:.1f}")
                with col6:
                    total_sessions = sum(sessions) if sessions else 0
                    st.metric("Total Sessions", f"{total_sessions}")

            else:
                st.info("ℹ️ No participation data available for the selected period")

        except Exception as e:
            st.error(f"❌ Error loading participation trend: {e}")

    def show_session_details(self, session_id: str):
        """Mostra dettagli completi della sessione selezionata (come nel 4Fun report)"""
        # Ottieni info sessione
        session_info = self.get_session_info(session_id)
        
        if not session_info:
            st.error("❌ Session not found")
            return
        
        # Header sessione
        session_type, track_name, session_date, total_drivers, competition_id, competition_name, round_number = session_info
        
        # Formatta data
        try:
            date_obj = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
            date_str = date_obj.strftime('%d/%m/%Y %H:%M')
        except:
            date_str = session_date[:16] if session_date else 'N/A'
        
        # Titolo con info competizione se disponibile
        if competition_name:
            round_str = f"Round {round_number} - " if round_number else ""
            header_title = f"🏆 {round_str}{competition_name} - {session_type}"
            header_class = "competition-header"
        else:
            header_title = f"❌ Unofficial Session - {session_type}"
            header_class = "fun-header"
        
        st.markdown(f"""
        <div class="{header_class}">
            <h3>{header_title}</h3>
            <p>📍 {track_name} | 📅 {date_str} | 👥 {total_drivers} drivers</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Risultati sessione (stesso stile del 4Fun report)
        st.subheader("🏁 Session Results")
        session_results_df = self.get_session_results(session_id)
        
        if not session_results_df.empty:
            # Formatta risultati sessione (stesso codice del 4Fun)
            session_display = session_results_df.copy()
            
            # Aggiungi medaglie per primi 3
            session_display['Pos'] = session_display['position'].apply(
                lambda x: "🥇" if x == 1 else "🥈" if x == 2 else "🥉" if x == 3 else str(int(x)) if pd.notna(x) else "NC"
            )
            
            # Formatta tempo giro
            session_display['Best Lap'] = session_display['best_lap'].apply(
                lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
            )
            
            # Formatta tempo totale
            session_display['Total Time'] = session_display['total_time'].apply(
                lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
            )
            
            # Seleziona colonne da mostrare
            columns_to_show = ['Pos', 'race_number', 'driver', 'lap_count', 'Best Lap', 'Total Time']
            column_names = {
                'Pos': 'Pos',
                'race_number': 'Num#',
                'driver': 'Driver',
                'lap_count': 'Laps',
                'Best Lap': 'Best Lap',
                'Total Time': 'Total Time'
            }
            
            session_display = session_display[columns_to_show]
            session_display.columns = [column_names[col] for col in columns_to_show]
            
            # Mostra tutti i risultati
            st.dataframe(
                session_display,
                width='stretch',
                hide_index=True
            )
            
            # Grafici se ci sono abbastanza dati
            if len(session_results_df) > 3:
                self.show_session_charts(session_results_df, session_type)
                
        else:
            st.warning(f"⚠️ No results found for this session")
    
    def show_session_charts(self, results_df: pd.DataFrame, session_type: str):
        """Mostra grafici per la sessione - VERSIONE MIGLIORATA"""
        if results_df.empty or len(results_df) < 4:
            return
        
        st.markdown("---")
        st.subheader("📊 Session Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # GRAFICO MIGLIORATO: Gap Analysis dal vincitore
            st.subheader("⏱️ Gap Analysis from Winner")
            
            # FILTRO MIGLIORATO: Escludi piloti senza giro valido
            valid_times = results_df[
                (pd.notna(results_df['best_lap'])) & 
                (results_df['best_lap'] > 0) &
                (pd.notna(results_df['position'])) &
                (results_df['position'] > 0) &
                # Escludi tempi anomali (troppo veloci o troppo lenti)
                (results_df['best_lap'] >= 30000) &  # Almeno 30 secondi
                (results_df['best_lap'] <= 600000)   # Massimo 10 minuti
            ].head(10).copy()
            
            if not valid_times.empty:
                # Verifica che ci sia almeno un giro valido
                if len(valid_times) == 0:
                    st.info("⚠️ No drivers with valid lap times found")
                    return
                # Ordina per posizione
                valid_times = valid_times.sort_values('position', ascending=True)
                
                # Calcola gap dal vincitore
                winner_time = valid_times.iloc[0]['best_lap']
                valid_times['gap_seconds'] = (valid_times['best_lap'] - winner_time) / 1000
                
                # Formatta per display
                valid_times['gap_display'] = valid_times['gap_seconds'].apply(
                    lambda x: f"+{x:.3f}s" if x > 0 else "Leader"
                )
                
                # Converti tempi in formato MM:SS.sss per tooltip
                valid_times['lap_time_formatted'] = valid_times['best_lap'].apply(
                    lambda x: self.format_lap_time(x)
                )
                
                # Crea grafico a barre orizzontale (più leggibile)
                fig_gap = px.bar(
                    valid_times,
                    x='gap_seconds',
                    y='driver',
                    orientation='h',
                    title=f"Gap from Winner - Best Lap Times (Top 10)",
                    color='gap_seconds',
                    color_continuous_scale='RdYlGn_r',  # Rosso = più lento, Verde = più veloce
                    hover_data={
                        'gap_seconds': False,  # Nascondi gap_seconds nel tooltip
                        'gap_display': True,   # Mostra gap formattato
                        'lap_time_formatted': True,  # Mostra tempo giro
                        'position': True       # Mostra posizione
                    }
                )
                
                # Personalizza grafico
                fig_gap.update_layout(
                    height=400, 
                    showlegend=False,
                    xaxis_title="Gap from Winner (seconds)",
                    yaxis_title="Driver"
                )
                
                # Ordina Y axis per posizione (primo in alto)
                fig_gap.update_yaxes(autorange="reversed")
                
                # Aggiungi linea di riferimento a 0 (vincitore)
                fig_gap.add_vline(x=0, line_dash="dash", line_color="green", 
                                 annotation_text="Winner", annotation_position="top")
                
                st.plotly_chart(fig_gap, width='stretch')
                
                # Info aggiuntive sotto il grafico
                winner_name = valid_times.iloc[0]['driver']
                winner_time_formatted = valid_times.iloc[0]['lap_time_formatted']
                max_gap = valid_times['gap_seconds'].max()
                total_valid_drivers = len(valid_times)
                
                st.info(f"🏆 **Winner**: {winner_name} ({winner_time_formatted}) | 📊 **Max Gap**: +{max_gap:.3f}s | 👥 **Valid Times**: {total_valid_drivers} drivers")
                
            else:
                st.warning("❌ No drivers with valid lap times found for gap analysis")
        
        with col2:
            # Grafico giri completati (rimane uguale, è già chiaro)
            st.subheader("🔄 Laps Completed")
            
            laps_data = results_df[
                (pd.notna(results_df['lap_count'])) & 
                (results_df['lap_count'] > 0)
            ].copy()
            
            if not laps_data.empty:
                laps_data = laps_data.sort_values('lap_count', ascending=True)
                
                fig_laps = px.bar(
                    laps_data,
                    x='lap_count',
                    y='driver',
                    orientation='h',
                    title="Laps Completed by Driver",
                    color='lap_count',
                    color_continuous_scale='greens'
                )
                fig_laps.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_laps, width='stretch')
            else:
                st.info("No lap count data for chart")
        
        # GRAFICO AGGIUNTIVO: Distribuzione tempi (se ci sono molti piloti)
        if len(valid_times) > 5:
            st.subheader("📈 Lap Times Distribution")
            
            # Istogramma dei tempi giro
            fig_hist = px.histogram(
                valid_times,
                x='gap_seconds',
                nbins=min(10, len(valid_times)),
                title="Distribution of Gap Times",
                labels={'gap_seconds': 'Gap from Winner (seconds)', 'count': 'Number of Drivers'},
                color_discrete_sequence=['lightblue']
            )
            
            fig_hist.update_layout(
                height=300,
                showlegend=False,
                bargap=0.1
            )
            
            st.plotly_chart(fig_hist, width='stretch')
    

    # ==================== BEST LAPS ====================

    def format_time_duration(self, milliseconds: int) -> str:
        """Formatta durata in millisecondi per gap"""
        if not milliseconds or milliseconds <= 0:
            return "0.000"
        
        if milliseconds < 1000:
            return f"0.{milliseconds:03d}"
        else:
            seconds = milliseconds / 1000
            return f"{seconds:.3f}"
    
    def get_tracks_list(self) -> List[str]:
        """Ottiene lista piste disponibili nel database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT track_name FROM sessions ORDER BY track_name')
            tracks = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return tracks
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero piste: {e}")
            return []
    
    def get_all_tracks_summary(self) -> pd.DataFrame:
        """Ottiene riepilogo record per tutte le piste (solo competizioni ufficiali e piloti TFL)"""

        query = '''
            WITH track_records AS (
                SELECT
                    s.track_name,
                    MIN(l.lap_time) as best_lap
                FROM laps l
                JOIN sessions s ON l.session_id = s.session_id
                JOIN drivers d ON l.driver_id = d.driver_id
                WHERE l.is_valid_for_best = 1
                  AND l.lap_time > 0
                  AND s.competition_id IS NOT NULL
                  AND d.trust_level > 0
                GROUP BY s.track_name
            )
            SELECT
                tr.track_name,
                tr.best_lap,
                d.last_name as driver_name,
                s.session_date,
                s.session_type,
                s.is_time_attack,
                s.competition_id,
                c.name as competition_name,
                ch.name as championship_name
            FROM track_records tr
            JOIN laps l ON tr.best_lap = l.lap_time
            JOIN sessions s ON l.session_id = s.session_id AND s.track_name = tr.track_name
            JOIN drivers d ON l.driver_id = d.driver_id
            LEFT JOIN competitions c ON s.competition_id = c.competition_id
            LEFT JOIN championships ch ON c.championship_id = ch.championship_id
            WHERE l.is_valid_for_best = 1
              AND s.competition_id IS NOT NULL
              AND d.trust_level > 0
            GROUP BY tr.track_name
            ORDER BY tr.best_lap ASC
        '''

        return self.safe_sql_query(query)
    
    def get_track_statistics(self, track_name: str) -> Dict:
        """Ottiene statistiche generali per la pista (solo competizioni ufficiali e piloti TFL)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Statistiche generali
            query = '''
                SELECT
                    COUNT(DISTINCT s.session_id) as total_sessions,
                    COUNT(DISTINCT l.driver_id) as unique_drivers,
                    COUNT(l.id) as total_laps,
                    MIN(l.lap_time) as best_time,
                    AVG(CAST(l.lap_time AS REAL)) as avg_time,
                    MAX(s.session_date) as last_session_date,
                    COUNT(DISTINCT CASE WHEN s.competition_id IS NOT NULL THEN s.session_id END) as official_sessions
                FROM sessions s
                LEFT JOIN laps l ON s.session_id = l.session_id
                LEFT JOIN drivers d ON l.driver_id = d.driver_id
                WHERE s.track_name = ?
                  AND l.is_valid_for_best = 1
                  AND l.lap_time > 0
                  AND s.competition_id IS NOT NULL
                  AND d.trust_level > 0
            '''

            cursor.execute(query, (track_name,))
            result = cursor.fetchone()

            if result:
                sessions, drivers, laps, best, avg, last_session, official_sessions = result

                # Chi detiene il record e quando
                record_query = '''
                    SELECT d.last_name, s.session_date
                    FROM laps l
                    JOIN drivers d ON l.driver_id = d.driver_id
                    JOIN sessions s ON l.session_id = s.session_id
                    WHERE s.track_name = ?
                      AND l.lap_time = ?
                      AND l.is_valid_for_best = 1
                      AND s.competition_id IS NOT NULL
                      AND d.trust_level > 0
                    LIMIT 1
                '''

                cursor.execute(record_query, (track_name, best))
                record_result = cursor.fetchone()
                if record_result:
                    record_holder = record_result[0]
                    record_date = record_result[1]
                else:
                    record_holder = "N/A"
                    record_date = None
                
                stats = {
                    'total_sessions': sessions or 0,
                    'unique_drivers': drivers or 0,
                    'total_laps': laps or 0,
                    'best_time': best,
                    'avg_time': int(avg) if avg else None,
                    'record_holder': record_holder,
                    'record_date': record_date,
                    'last_session_date': last_session,
                    'official_sessions': official_sessions or 0
                }
            else:
                stats = {
                    'total_sessions': 0,
                    'unique_drivers': 0,
                    'total_laps': 0,
                    'best_time': None,
                    'avg_time': None,
                    'record_holder': 'N/A',
                    'record_date': None,
                    'last_session_date': None,
                    'official_sessions': 0
                }
            
            conn.close()
            return stats
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero statistiche pista: {e}")
            return {}
    
    def get_track_leaderboard(self, track_name: str) -> pd.DataFrame:
        """Ottiene classifica best laps per pista (solo competizioni ufficiali e piloti TFL)"""

        query = '''
            WITH driver_best_laps AS (
                SELECT
                    l.driver_id,
                    MIN(l.lap_time) as best_lap
                FROM laps l
                JOIN sessions s ON l.session_id = s.session_id
                JOIN drivers d ON l.driver_id = d.driver_id
                WHERE s.track_name = ?
                  AND l.is_valid_for_best = 1
                  AND l.lap_time > 0
                  AND s.competition_id IS NOT NULL
                  AND d.trust_level > 0
                GROUP BY l.driver_id
            )
            SELECT
                d.last_name as driver_name,
                d.short_name,
                dbl.best_lap,
                s.session_date,
                s.session_type,
                s.is_time_attack,
                s.competition_id,
                c.name as competition_name,
                ch.name as championship_name
            FROM driver_best_laps dbl
            JOIN laps l ON l.driver_id = dbl.driver_id AND l.lap_time = dbl.best_lap
            JOIN sessions s ON l.session_id = s.session_id
            JOIN drivers d ON dbl.driver_id = d.driver_id
            LEFT JOIN competitions c ON s.competition_id = c.competition_id
            LEFT JOIN championships ch ON c.championship_id = ch.championship_id
            WHERE s.track_name = ?
              AND l.is_valid_for_best = 1
              AND s.competition_id IS NOT NULL
              AND d.trust_level > 0
            GROUP BY dbl.driver_id
            ORDER BY dbl.best_lap ASC
            LIMIT 50
        '''

        return self.safe_sql_query(query, [track_name, track_name])
    
    def show_best_laps_report(self):
        """Mostra il report Best Laps per pista"""
        st.header("⚡ Best Laps")

        # Ottieni lista piste
        tracks = self.get_tracks_list()

        if not tracks:
            st.warning("❌ No tracks found in database")
            return

        # Selectbox pista con riepilogo generale come prima opzione
        track_options = ["📊 General Summary"] + tracks
        selected_track = st.selectbox(
            "🏁 Select Track:",
            options=track_options,
            index=0,  # Riepilogo generale selezionato di default
            key="track_select"
        )

        # Box informativo per record ufficiali con link social
        social_config = self.config.get('social', {})
        discord_url = social_config.get('discord', '')
        simgrid_url = social_config.get('simgrid', '')

        # Crea i link ai social in stile discreto
        social_links = []
        if simgrid_url:
            social_links.append(f'<a href="{simgrid_url}" target="_blank" style="text-decoration: none; margin: 0 0.5rem;"><button style="background: #4a90e2; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.9rem; cursor: pointer; transition: opacity 0.2s;">🏆 SimGrid</button></a>')
        if discord_url:
            social_links.append(f'<a href="{discord_url}" target="_blank" style="text-decoration: none; margin: 0 0.5rem;"><button style="background: #7289da; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.9rem; cursor: pointer; transition: opacity 0.2s;">💬 Discord</button></a>')

        if social_links:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 3px solid #6c757d; margin: 1rem 0;">
                <p style="color: #495057; margin: 0 0 0.5rem 0; font-size: 0.95rem; font-weight: 500;">
                    ℹ️ Only registered drivers shown - Join the TFL by registering on SimGrid or joining our Discord server
                </p>
                <div style="text-align: center; margin-top: 0.8rem;">
                    {''.join(social_links)}
                </div>
            </div>
            """, unsafe_allow_html=True)

        if selected_track == "📊 General Summary":
            # Mostra riepilogo generale di tutte le piste
            st.markdown("---")
            st.subheader("🏁 Track Records Summary")
            self.show_all_tracks_summary()

        elif selected_track in tracks:
            # Mostra dettagli della pista specifica
            st.markdown("---")
            self.show_track_details(selected_track)
    
    def show_all_tracks_summary(self):
        """Mostra riepilogo record per tutte le piste (solo competizioni ufficiali e piloti TFL)"""

        summary_df = self.get_all_tracks_summary()
        
        if summary_df.empty:
            st.warning("⚠️ No data available for tracks summary")
            return
        
        # Prepara display summary
        summary_display = summary_df.copy()
        
        # Formatta tempo record
        summary_display['Record'] = summary_display['best_lap'].apply(
            lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
        )
        
        # Ordina per data originale (ISO format) decrescente prima di formattare
        summary_display = summary_display.sort_values('session_date', ascending=False)
        
        # Formatta data
        summary_display['Data'] = summary_display['session_date'].apply(
            lambda x: self.format_session_date(x) if pd.notna(x) else "N/A"
        )
        
        # Nome pista senza decorazioni
        summary_display['Pista'] = summary_display['track_name']

        # Formatta colonna Session Type (nascondi per Time Attack a causa di bug ACC)
        summary_display['Session'] = summary_display.apply(
            lambda row: "-" if row['is_time_attack'] == 1 else row['session_type'],
            axis=1
        )

        # Formatta colonna Race Type (Official Race o Time Attack)
        summary_display['Type'] = summary_display['is_time_attack'].apply(
            lambda x: "⏱️ Time Attack" if x == 1 else "🏁 Official Race"
        )

        # Formatta colonna Competition: concatena competition_name e championship_name
        summary_display['Competition'] = summary_display.apply(
            lambda row: f"{row['competition_name']} - {row['championship_name']}"
            if pd.notna(row.get('competition_name')) and pd.notna(row.get('championship_name'))
            else (row.get('competition_name') if pd.notna(row.get('competition_name'))
                  else (row.get('championship_name') if pd.notna(row.get('championship_name')) else "N/A")),
            axis=1
        )

        # Seleziona colonne finali (Type prima di Session)
        columns_to_show = ['Pista', 'Record', 'driver_name', 'Type', 'Session', 'Data', 'Competition']
        column_names = {
            'Pista': 'Track',
            'Record': 'Record',
            'driver_name': 'Driver',
            'Type': 'Type',
            'Session': 'Session',
            'Data': 'Date',
            'Competition': 'Competition'
        }

        final_display = summary_display[columns_to_show].copy()
        final_display.columns = [column_names[col] for col in columns_to_show]

        # Configura larghezza colonne (in pixel)
        column_config = {
            'Track': st.column_config.TextColumn('Track', width=120),
            'Record': st.column_config.TextColumn('Record', width=90),
            'Driver': st.column_config.TextColumn('Driver', width=120),
            'Type': st.column_config.TextColumn('Type', width=130),
            'Session': st.column_config.TextColumn('Session', width=70),
            'Date': st.column_config.TextColumn('Date', width=90),
            'Competition': st.column_config.TextColumn('Competition', width='large')
        }

        st.dataframe(
            final_display,
            width='content',
            hide_index=True,
            height=400,
            column_config=column_config
        )
        
        # Info aggiuntive
        total_tracks = len(summary_display)
        
        # Trova pilota/i con più record
        driver_records = summary_display['driver_name'].value_counts()
        if not driver_records.empty:
            max_records = driver_records.iloc[0]
            top_holders = driver_records[driver_records == max_records].index.tolist()
            
            if len(top_holders) == 1:
                # Un solo pilota con il massimo
                display_text = top_holders[0]
                record_text = f"{max_records} records held"
            else:
                # Pareggio - mostra tutti
                if len(top_holders) <= 3:
                    # Fino a 3 piloti: mostrali tutti
                    display_text = " • ".join(top_holders)
                    record_text = f"{max_records} records each"
                else:
                    # Più di 3: mostra primi 2 + "e altri X"
                    display_text = f"{top_holders[0]} • {top_holders[1]} • and {len(top_holders)-2} others"
                    record_text = f"{max_records} records each"
        else:
            display_text = "N/A"
            record_text = "0 records"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"📊 **{total_tracks}** tracks with available data")
        
        with col2:
            st.success(f"🏆 **Driver(s) with most records**: {display_text}")
        
        with col3:
            st.info(f"🎯 **{record_text}**")
    
    def show_track_details(self, track_name: str):
        """Mostra dettagli completi per la pista selezionata (solo competizioni ufficiali e piloti TFL)"""

        # Header pista
        st.markdown(f"""
        <div class="championship-header">
            <h2>🏁 {track_name}</h2>
        </div>
        """, unsafe_allow_html=True)

        # Ottieni statistiche generali
        track_stats = self.get_track_statistics(track_name)

        if not any(track_stats.values()):
            st.warning("⚠️ No data available for this track")
            return

        # Classifica Best Laps
        st.markdown("---")
        st.subheader("🏆 Best Laps Leaderboard by Driver")

        leaderboard_df = self.get_track_leaderboard(track_name)

        if not leaderboard_df.empty:
            # Prepara display leaderboard
            leaderboard_display = leaderboard_df.copy()

            # Aggiungi medaglie per i primi 3
            leaderboard_display['Posizione'] = leaderboard_display.reset_index().index + 1
            leaderboard_display['Pos'] = leaderboard_display['Posizione'].apply(
                lambda x: "🥇" if x == 1 else "🥈" if x == 2 else "🥉" if x == 3 else str(x)
            )

            # Formatta tempi
            leaderboard_display['Best Time'] = leaderboard_display['best_lap'].apply(
                lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
            )

            # Calcola gap dal leader
            if len(leaderboard_display) > 1:
                best_time = leaderboard_display.iloc[0]['best_lap']
                leaderboard_display['Gap'] = leaderboard_display['best_lap'].apply(
                    lambda x: f"+{self.format_time_duration(x - best_time)}" if x != best_time else "-"
                )
            else:
                leaderboard_display['Gap'] = "-"

            # Formatta data
            leaderboard_display['Record Date'] = leaderboard_display['session_date'].apply(
                lambda x: self.format_session_date(x) if pd.notna(x) else "N/A"
            )

            # Formatta colonna Session Type (nascondi per Time Attack a causa di bug ACC)
            leaderboard_display['Session'] = leaderboard_display.apply(
                lambda row: "-" if row['is_time_attack'] == 1 else row['session_type'],
                axis=1
            )

            # Formatta colonna Race Type (Official Race o Time Attack)
            leaderboard_display['Type'] = leaderboard_display['is_time_attack'].apply(
                lambda x: "⏱️ Time Attack" if x == 1 else "🏁 Official Race"
            )

            # Formatta colonna Competition: concatena competition_name e championship_name
            leaderboard_display['Competition'] = leaderboard_display.apply(
                lambda row: f"{row['competition_name']} - {row['championship_name']}"
                if pd.notna(row.get('competition_name')) and pd.notna(row.get('championship_name'))
                else (row.get('competition_name') if pd.notna(row.get('competition_name'))
                      else (row.get('championship_name') if pd.notna(row.get('championship_name')) else "N/A")),
                axis=1
            )

            # Seleziona colonne finali (Type prima di Session)
            columns_to_show = ['Pos', 'driver_name', 'Best Time', 'Gap', 'Type', 'Session', 'Record Date', 'Competition']
            column_names = {
                'Pos': 'Pos',
                'driver_name': 'Driver',
                'Best Time': 'Best Time',
                'Gap': 'Gap',
                'Type': 'Type',
                'Session': 'Session',
                'Record Date': 'Date',
                'Competition': 'Competition'
            }

            final_display = leaderboard_display[columns_to_show].copy()
            final_display.columns = [column_names[col] for col in columns_to_show]

            # Configura larghezza colonne (in pixel)
            column_config = {
                'Pos': st.column_config.TextColumn('Pos', width=50),
                'Driver': st.column_config.TextColumn('Driver', width=120),
                'Best Time': st.column_config.TextColumn('Best Time', width=90),
                'Gap': st.column_config.TextColumn('Gap', width=70),
                'Type': st.column_config.TextColumn('Type', width=130),
                'Session': st.column_config.TextColumn('Session', width=70),
                'Date': st.column_config.TextColumn('Date', width=90),
                'Competition': st.column_config.TextColumn('Competition', width='large')
            }

            # Mostra tabella con evidenziazione primi 3
            st.dataframe(
                final_display,
                width='content',
                hide_index=True,
                height=500,
                column_config=column_config
            )

        else:
            st.warning("⚠️ No data available for leaderboard")

        # Statistiche pista (dopo leaderboard)
        st.markdown("---")
        st.subheader("📊 Track Statistics")

        # Prepara valori
        record_holder = track_stats.get('record_holder', 'N/A')
        best_time_str = self.format_lap_time(track_stats['best_time']) if track_stats['best_time'] else "N/A"
        avg_time_str = self.format_lap_time(track_stats['avg_time']) if track_stats['avg_time'] else "N/A"
        official_sessions = track_stats.get('official_sessions', 0)

        # Record date
        record_date = track_stats.get('record_date')
        if record_date:
            try:
                record_date_obj = datetime.fromisoformat(record_date.replace('Z', '+00:00'))
                record_date_formatted = record_date_obj.strftime('%d/%m/%Y')
            except:
                record_date_formatted = "N/A"
        else:
            record_date_formatted = "N/A"

        # Last session date
        last_session = track_stats.get('last_session_date')
        if last_session:
            try:
                last_date = datetime.fromisoformat(last_session.replace('Z', '+00:00'))
                last_text = last_date.strftime('%d/%m/%Y')
            except:
                last_text = "N/A"
        else:
            last_text = "N/A"

        # Elenco compatto statistiche
        st.markdown(f"""
        - 🏆 **Record Holder:** {record_holder}
        - ⚡ **Absolute Record:** {best_time_str}
        - 📅 **Record Date:** {record_date_formatted}
        - 📈 **Average Time:** {avg_time_str}
        - 👥 **Unique Drivers:** {track_stats['unique_drivers']}
        - 🎮 **Total Sessions:** {track_stats['total_sessions']}
        - 🏆 **Total Official Sessions:** {official_sessions}
        - 📅 **Last Session Date:** {last_text}
        """)    


    # ==================== DRIVERS ====================

    def format_competition_info(self, session_type: str, competition_name, championship_name) -> str:
        """Formatta info competizione: FPx - nome_competizione - campionato"""
        import pandas as pd

        parts = []

        # Aggiungi session type breve (FPx, Qx, Rx)
        if session_type and pd.notna(session_type):
            parts.append(session_type)

        # Aggiungi competition name
        if competition_name and pd.notna(competition_name):
            parts.append(competition_name)

        # Aggiungi championship name
        if championship_name and pd.notna(championship_name):
            parts.append(championship_name)

        return " - ".join(parts) if parts else "N/A"

    def format_session_type_with_official_indicator(self, session_type: str, competition_id) -> str:
        """Formatta tipo sessione con indicatore per sessioni ufficiali"""
        import pandas as pd
        formatted_type = self.format_session_type(session_type)

        # Aggiunge pallino verde per sessioni ufficiali, grigio per non ufficiali
        if competition_id is not None and not pd.isna(competition_id):
            return f"🟢 {formatted_type}"
        else:
            return f"⚪ {formatted_type}"

    def get_drivers_list(self) -> List[Dict]:
        """Ottiene lista piloti disponibili nel database ordinata alfabeticamente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT DISTINCT d.driver_id, d.last_name, d.short_name
                FROM drivers d
                WHERE d.trust_level > 0
                AND EXISTS (
                    SELECT 1 FROM laps l WHERE l.driver_id = d.driver_id
                )
                ORDER BY LOWER(d.last_name)
            '''
            cursor.execute(query)
            drivers = []
            for row in cursor.fetchall():
                drivers.append({
                    'driver_id': row[0],
                    'last_name': row[1],
                    'short_name': row[2]
                })
            
            conn.close()
            return drivers
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero piloti: {e}")
            return []
    
    def get_all_drivers_summary(self) -> pd.DataFrame:
        """Ottiene riepilogo generale di tutti i piloti"""
        
        query = '''
            SELECT 
                d.driver_id,
                d.last_name as driver_name,
                d.preferred_race_number as number,
                COALESCE(champ.championships, 0) as championships,
                COALESCE(champ.wins, 0) as wins,
                COALESCE(champ.poles, 0) as poles,
                COALESCE(champ.podiums, 0) as podiums,
                COALESCE(records.records, 0) as records
            FROM drivers d
            LEFT JOIN (
                -- Statistiche da championship_standings
                SELECT 
                    driver_id,
                    SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as championships,
                    SUM(wins) as wins,
                    SUM(poles) as poles,
                    SUM(podiums) as podiums
                FROM championship_standings 
                GROUP BY driver_id
            ) champ ON d.driver_id = champ.driver_id
            LEFT JOIN (
                -- Conteggio record ufficiali detenuti
                SELECT 
                    l.driver_id,
                    COUNT(DISTINCT s.track_name) as records
                FROM laps l
                JOIN sessions s ON l.session_id = s.session_id
                WHERE l.is_valid_for_best = 1 AND l.lap_time > 0
                AND l.lap_time = (
                    SELECT MIN(l2.lap_time) 
                    FROM laps l2 
                    JOIN sessions s2 ON l2.session_id = s2.session_id 
                    WHERE s2.track_name = s.track_name 
                    AND l2.is_valid_for_best = 1 
                    AND l2.lap_time > 0
                )
                GROUP BY l.driver_id
            ) records ON d.driver_id = records.driver_id
            WHERE d.trust_level > 0
            AND EXISTS (
                SELECT 1 FROM laps l WHERE l.driver_id = d.driver_id
            )
            ORDER BY d.last_name
        '''
        
        return self.safe_sql_query(query)
    
    def get_driver_statistics(self, driver_id: int) -> Dict:
        """Ottiene statistiche complete per un pilota"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query per statistiche base
            stats_query = '''
                SELECT 
                    COUNT(DISTINCT l.session_id) as total_sessions,
                    COUNT(DISTINCT CASE WHEN s.competition_id IS NOT NULL THEN l.session_id END) as official_sessions,
                    COUNT(DISTINCT s.track_name) as num_tracks,
                    d.trust_level
                FROM laps l
                JOIN sessions s ON l.session_id = s.session_id
                JOIN drivers d ON l.driver_id = d.driver_id
                WHERE l.driver_id = ?
            '''
            
            cursor.execute(stats_query, [driver_id])
            row = cursor.fetchone()
            
            stats = {
                'total_sessions': row[0] if row[0] else 0,
                'official_sessions': row[1] if row[1] else 0,
                'num_tracks': row[2] if row[2] else 0,
                'trust_level': row[3] if row[3] is not None else 'N/A'
            }
            
            # Query per risultati gare (wins, poles, podiums, championships) da championship_standings
            results_query = '''
                SELECT 
                    SUM(wins) as wins,
                    SUM(poles) as poles,
                    SUM(podiums) as podiums,
                    SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as championships
                FROM championship_standings
                WHERE driver_id = ?
            '''
            
            cursor.execute(results_query, [driver_id])
            row = cursor.fetchone()
            
            if row:
                stats.update({
                    'wins': row[0] if row[0] else 0,
                    'poles': row[1] if row[1] else 0,
                    'podiums': row[2] if row[2] else 0,
                    'championships': row[3] if row[3] else 0
                })
            else:
                stats.update({'wins': 0, 'poles': 0, 'podiums': 0, 'championships': 0})
            
            # Query per bad reports
            bad_reports_query = '''
                SELECT bad_driver_reports FROM drivers WHERE driver_id = ?
            '''
            cursor.execute(bad_reports_query, [driver_id])
            bad_row = cursor.fetchone()
            stats['bad_reports'] = bad_row[0] if bad_row and bad_row[0] else 0
            
            conn.close()
            return stats
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero statistiche pilota: {e}")
            return {}
    
    def get_driver_best_times(self, driver_id: int) -> pd.DataFrame:
        """Ottiene tutti i migliori tempi del pilota per ogni pista"""
        
        query = '''
            WITH driver_track_bests AS (
                SELECT 
                    s.track_name,
                    MIN(l.lap_time) as best_lap,
                    COUNT(CASE WHEN l.is_valid_for_best = 1 THEN 1 END) as valid_laps
                FROM laps l
                JOIN sessions s ON l.session_id = s.session_id
                WHERE l.driver_id = ? AND l.is_valid_for_best = 1 AND l.lap_time > 0
                GROUP BY s.track_name
            ),
            track_records AS (
                SELECT 
                    s.track_name,
                    MIN(l.lap_time) as track_record
                FROM laps l
                JOIN sessions s ON l.session_id = s.session_id
                WHERE l.is_valid_for_best = 1 AND l.lap_time > 0
                GROUP BY s.track_name
            )
            SELECT 
                dtb.track_name,
                dtb.best_lap,
                dtb.valid_laps,
                s.session_date,
                s.session_type,
                s.competition_id,
                CASE WHEN dtb.best_lap = tr.track_record THEN 1 ELSE 0 END as is_record
            FROM driver_track_bests dtb
            JOIN laps l ON dtb.best_lap = l.lap_time
            JOIN sessions s ON l.session_id = s.session_id AND s.track_name = dtb.track_name
            JOIN track_records tr ON dtb.track_name = tr.track_name
            WHERE l.driver_id = ? AND l.is_valid_for_best = 1
            GROUP BY dtb.track_name
            ORDER BY s.session_date DESC
        '''

        return self.safe_sql_query(query, [driver_id, driver_id])

    def show_drivers_report(self):
        """Mostra il report Drivers con selezione generale o per pilota specifico"""
        st.header("👥 Drivers")
        
        # Ottieni lista piloti
        drivers = self.get_drivers_list()
        
        if not drivers:
            st.warning("❌ No drivers found in database")
            return
        
        # Selectbox pilota con riepilogo generale come prima opzione
        driver_options = ["📊 General Summary"] + [f"{driver['last_name']}" for driver in drivers]
        selected_driver = st.selectbox(
            "👤 Select Driver:",
            options=driver_options,
            index=0,  # Riepilogo generale selezionato di default
            key="driver_select"
        )

        # Box informativo per piloti registrati con link social
        social_config = self.config.get('social', {})
        discord_url = social_config.get('discord', '')
        simgrid_url = social_config.get('simgrid', '')

        # Crea i link ai social in stile discreto
        social_links = []
        if simgrid_url:
            social_links.append(f'<a href="{simgrid_url}" target="_blank" style="text-decoration: none; margin: 0 0.5rem;"><button style="background: #4a90e2; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.9rem; cursor: pointer; transition: opacity 0.2s;">🏆 SimGrid</button></a>')
        if discord_url:
            social_links.append(f'<a href="{discord_url}" target="_blank" style="text-decoration: none; margin: 0 0.5rem;"><button style="background: #7289da; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.9rem; cursor: pointer; transition: opacity 0.2s;">💬 Discord</button></a>')

        if social_links:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 3px solid #6c757d; margin: 1rem 0;">
                <p style="color: #495057; margin: 0 0 0.5rem 0; font-size: 0.95rem; font-weight: 500;">
                    ℹ️ Only registered drivers shown - Join the TFL by registering on SimGrid or joining our Discord server
                </p>
                <div style="text-align: center; margin-top: 0.8rem;">
                    {''.join(social_links)}
                </div>
            </div>
            """, unsafe_allow_html=True)

        if selected_driver == "📊 General Summary":
            # Mostra riepilogo generale di tutti i piloti
            st.markdown("---")
            st.subheader("👤 Drivers General Summary")
            self.show_all_drivers_summary()
            
        else:
            # Trova il pilota selezionato
            selected_driver_data = next((d for d in drivers if d['last_name'] == selected_driver), None)
            if selected_driver_data:
                # Mostra dettagli del pilota specifico
                st.markdown("---")
                self.show_driver_details(selected_driver_data)
    
    def show_all_drivers_summary(self):
        """Mostra riepilogo generale di tutti i piloti"""
        
        summary_df = self.get_all_drivers_summary()
        
        if summary_df.empty:
            st.warning("⚠️ No data available for drivers summary")
            return
        
        # Prepara display summary
        summary_display = summary_df.copy()
        
        # Ordina alfabeticamente per nome (case-insensitive)
        summary_display['driver_name_lower'] = summary_display['driver_name'].str.lower()
        summary_display = summary_display.sort_values('driver_name_lower', ascending=True).drop('driver_name_lower', axis=1)
        
        # Seleziona colonne finali con i nomi desiderati
        columns_to_show = ['driver_name', 'number', 'championships', 'wins', 'poles', 'podiums', 'records']
        column_names = {
            'driver_name': '👤 Driver Name',
            'number': '🏁 Car Number',
            'championships': '🏆 Titles Won',
            'wins': '🥇 Wins',
            'poles': '🚩 Poles',
            'podiums': '🏅 Podiums',
            'records': '📊 Records'
        }
        
        final_display = summary_display[columns_to_show].copy()
        final_display.columns = [column_names[col] for col in columns_to_show]
        
        # Riempi valori mancanti con 0
        final_display = final_display.fillna(0)
        
        st.dataframe(
            final_display,
            width='stretch',
            hide_index=True,
            height=400
        )
        
        # Info aggiuntive
        total_drivers = len(summary_display)
        total_championships = summary_display['championships'].sum()
        total_records = summary_display['records'].sum()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"👥 **{total_drivers}** registered drivers")
        
        with col2:
            st.success(f"🏆 **{int(total_championships)}** total championships won")
        
        with col3:
            st.info(f"📊 **{int(total_records)}** track records held")
    
    def show_driver_details(self, driver_data: Dict):
        """Mostra dettagli completi per il pilota selezionato"""
        
        # Header pilota
        driver_name = driver_data['last_name']
        st.markdown(f"""
        <div class="championship-header">
            <h2>👤 {driver_name}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Ottieni statistiche generali del pilota
        driver_stats = self.get_driver_statistics(driver_data['driver_id'])
        
        if not any(driver_stats.values()):
            st.warning("⚠️ No data available for this driver")
            return
        
        # Prima riga: Info base
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{driver_data['driver_id']}</p>
                <p class="metric-label">🆔 Driver ID</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            short_name = driver_data.get('short_name', 'N/A')
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.5rem;">{short_name}</p>
                <p class="metric-label">📝 Short Name</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_sessions = driver_stats.get('total_sessions', 0)
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{total_sessions}</p>
                <p class="metric-label">🎮 Total Sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            official_sessions = driver_stats.get('official_sessions', 0)
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{official_sessions}</p>
                <p class="metric-label">🏆 Official Sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Seconda riga: Performance
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            championships = driver_stats.get('championships', 0)
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{championships}</p>
                <p class="metric-label">🏆 Titles Won</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            wins = driver_stats.get('wins', 0)
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{wins}</p>
                <p class="metric-label">🥇 Wins</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            poles = driver_stats.get('poles', 0)
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{poles}</p>
                <p class="metric-label">🚩 Poles</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            podiums = driver_stats.get('podiums', 0)
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{podiums}</p>
                <p class="metric-label">🏅 Podiums</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Terza riga: Trust, Reports e Tracks
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            num_tracks = driver_stats.get('num_tracks', 0)
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{num_tracks}</p>
                <p class="metric-label">🏁 Tracks Driven</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            trust_level = driver_stats.get('trust_level', 'N/A')
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.5rem;">{trust_level}</p>
                <p class="metric-label">🛡️ Trust Level</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            bad_reports = driver_stats.get('bad_reports', 0)
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{bad_reports}</p>
                <p class="metric-label">⚠️ Bad Reports</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Elenco migliori tempi per pista
        st.markdown("---")
        st.subheader("🏁 Best Times by Track")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            st.caption("🟢 Official Session • ⚪ Unofficial Session • 🏆 Track Record")
        
        self.show_driver_best_times(driver_data['driver_id'])
    
    def show_driver_best_times(self, driver_id: int):
        """Mostra tutti i migliori tempi del pilota per ogni pista"""
        
        best_times_df = self.get_driver_best_times(driver_id)
        
        if best_times_df.empty:
            st.warning("⚠️ No best times data available for this driver")
            return
        
        # Prepara display data
        display_df = best_times_df.copy()
        
        # Formatta tempo con eventuale indicatore record
        display_df['Best Time'] = display_df.apply(
            lambda row: f"{self.format_lap_time(row['best_lap'])} 🏆" if pd.notna(row['best_lap']) and row.get('is_record', False) else (self.format_lap_time(row['best_lap']) if pd.notna(row['best_lap']) else "N/A"),
            axis=1
        )
        
        # Ordina per data del miglior tempo (decrescente)
        display_df = display_df.sort_values('session_date', ascending=False)
        
        # Formatta data
        display_df['Date'] = display_df['session_date'].apply(
            lambda x: self.format_session_date(x) if pd.notna(x) else "N/A"
        )
        
        # Formatta tipo sessione con indicatore ufficiale
        display_df['Session'] = display_df.apply(
            lambda row: self.format_session_type_with_official_indicator(
                row['session_type'], row['competition_id']
            ) if pd.notna(row['session_type']) else "N/A", axis=1
        )
        
        # Nome pista senza indicatore record (ora è nel tempo)
        display_df['Track'] = display_df['track_name']
        
        # Seleziona colonne finali
        columns_to_show = ['Track', 'Best Time', 'valid_laps', 'Session', 'Date']
        column_names = {
            'Track': 'Track',
            'Best Time': 'Best Time',
            'valid_laps': 'Valid Laps',
            'Session': 'Session Type',
            'Date': 'Date'
        }
        
        final_display = display_df[columns_to_show].copy()
        final_display.columns = [column_names[col] for col in columns_to_show]
        
        st.dataframe(
            final_display,
            width='stretch',
            hide_index=True,
            height=400
        )
        
        # Info aggiuntive
        total_tracks = len(display_df)
        records_held = len(display_df[display_df.get('is_record', False) == True])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"🏁 **{total_tracks}** tracks driven with recorded times")
        
        with col2:
            st.success(f"🏆 **{records_held}** track records currently held")
    

def main():
    """Funzione principale dell'applicazione"""
    try:
        # Inizializza dashboard
        dashboard = ACCWebDashboard()
        
        # Sidebar per navigazione
        st.sidebar.title("🏁 Navigation")

        # Info versione per admin (solo in locale)
        if not dashboard.is_github_deployment:
            st.sidebar.markdown("---")
            st.sidebar.markdown("**🔧 Development Mode**")
            st.sidebar.markdown(f"DB: `{os.path.basename(dashboard.db_path)}`")

        # Menu principale
        page = st.sidebar.selectbox(
            "Select page:",
            [
                "🏠 Homepage",
                "⏱️ Time Attack",
                "🏁 Race Results",
                "🏆 Standings",
                "📅 All Sessions",
                "⚡ Best Laps",
                "👥 Drivers",
                "📈 Statistics"
            ]
        )

        # Routing pagine
        if page == "🏠 Homepage":
            dashboard.show_homepage()

        elif page == "⏱️ Time Attack":
            dashboard.show_time_attack_report()

        elif page == "🏁 Race Results":
            dashboard.show_race_results()

        elif page == "🏆 Standings":
            dashboard.show_leagues_report()

        elif page == "📅 All Sessions":
            dashboard.show_sessions_report()

        elif page == "⚡ Best Laps":
            dashboard.show_best_laps_report()

        elif page == "👥 Drivers":
            dashboard.show_drivers_report()

        elif page == "📈 Statistics":
            st.header("📈 Statistics")
            st.info("🚧 Section under development - will be implemented soon")
        
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            <p>🏁 {dashboard.config['community']['name']}</p>
            <p>{dashboard.config['community'].get('description', 'ACC Server Dashboard')}</p>
            {f'<p>🌐 Cloud Deployment</p>' if dashboard.is_github_deployment else '<p>🏠 Sviluppo Locale</p>'}
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error("❌ **Errore Critico nell'Applicazione**")
        st.error(f"Dettagli: {str(e)}")
        
        # Informazioni di debug solo in locale
        if not os.getenv('STREAMLIT_SHARING'):
            st.code(f"Traceback: {e}", language="text")
        
        st.markdown("""
        ### 🔧 Possibili Soluzioni:
        1. Verifica che il database sia presente e valido
        2. Controlla il file di configurazione
        3. Ricarica la pagina
        4. Contatta l'amministratore se il problema persiste
        """)


if __name__ == "__main__":
    main()

