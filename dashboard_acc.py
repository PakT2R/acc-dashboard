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
from datetime import datetime, timedelta, date
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, List, Tuple

# Configurazione pagina
st.set_page_config(
    page_title="ACC Server Dashboard",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

class ACCWebDashboard:
    """Classe principale per il dashboard web ACC"""
    
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
                "name": os.getenv('ACC_COMMUNITY_NAME', "[E?]nigma Overdrive"),
                "description": os.getenv('ACC_COMMUNITY_DESC', "ACC Racing Community")
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
            background: linear-gradient(90deg, #d4af37, #ffd700);
            color: #333;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            margin: 1rem 0;
        }
        
        .competition-header {
            background: linear-gradient(90deg, #ff6b35, #ff8c42);
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
    
    def show_environment_indicator(self):
        """Mostra indicatore ambiente (solo in sviluppo locale)"""
        if not self.is_github_deployment:
            st.markdown("""
            <div class="environment-indicator local-badge">
                🏠 Locale
            </div>
            """, unsafe_allow_html=True)
    
    def get_database_stats(self) -> Dict:
        """Ottiene statistiche generali dal database con gestione errori migliorata"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Statistiche base con fallback
            stats = {}
            
            # Query sicure con gestione errori
            safe_queries = {
                'total_drivers': 'SELECT COUNT(*) FROM drivers',
                'total_sessions': 'SELECT COUNT(*) FROM sessions',
                'total_championships': 'SELECT COUNT(*) FROM championships WHERE is_completed = 1',
                'completed_competitions': '''SELECT COUNT(*) FROM competitions 
                                           WHERE is_completed = 1 AND championship_id is not null''',
                'total_laps': 'SELECT COUNT(*) FROM laps',
                'championship_sessions': '''SELECT COUNT(*) FROM sessions s 
                                          WHERE s.competition_id IS NOT NULL AND EXISTS
                                          (SELECT 1 FROM competitions c 
                                           WHERE c.competition_id = s.competition_id 
                                           AND c.championship_id IS NOT NULL)''',
            }
            
            for key, query in safe_queries.items():
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    stats[key] = result[0] if result else 0
                except Exception as e:
                    st.warning(f"⚠️ Error in query {key}: {e}")
                    stats[key] = 0
            
            # Ultima sessione
            try:
                cursor.execute('''SELECT MAX(session_date) FROM sessions s 
                                WHERE s.competition_id IS NOT NULL AND EXISTS
                                (SELECT 1 FROM competitions c 
                                 WHERE c.competition_id = s.competition_id 
                                 AND c.championship_id IS NOT NULL)''')
                stats['last_session'] = cursor.fetchone()[0]
            except Exception:
                stats['last_session'] = None
            
            conn.close()
            return stats
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero statistiche: {e}")
            # Ritorna statistiche vuote invece di crashare
            return {
                'total_drivers': 0,
                'total_sessions': 0,
                'total_championships': 0,
                'completed_competitions': 0,
                'total_laps': 0,
                'championship_sessions': 0,
                'last_session': None
            }
    
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
        
        # PRIMA RIGA - Layout a colonne per le metriche
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['total_drivers']}</p>
                <p class="metric-label">👥 Registered Drivers</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['total_sessions']}</p>
                <p class="metric-label">🎮 Total Sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['total_laps']:,}</p>
                <p class="metric-label">🔄 Total Laps</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Calcola media giri per sessione
            avg_laps = round(stats['total_laps'] / stats['total_sessions'], 1) if stats['total_sessions'] > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{avg_laps}</p>
                <p class="metric-label">📊 Average Laps/Session</p>
            </div>
            """, unsafe_allow_html=True)
        
        # SECONDA RIGA di metriche
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['total_championships']}</p>
                <p class="metric-label">🏆 Completed Championships</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['completed_competitions']}</p>
                <p class="metric-label">🏁 Championship Competitions</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            championship_sessions = stats.get('championship_sessions', 0)
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{championship_sessions}</p>
                <p class="metric-label">🎯 Championship Sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Ultima sessione
            if stats['last_session']:
                try:
                    last_date = datetime.fromisoformat(stats['last_session'].replace('Z', '+00:00'))
                    days_ago = (datetime.now() - last_date).days
                    if days_ago == 0:
                        last_text = "Today"
                    elif days_ago == 1:
                        last_text = "Yesterday"
                    else:
                        last_text = f"{days_ago} days ago"
                except:
                    last_text = "N/A"
            else:
                last_text = "N/A"
            
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.8rem;">{last_text}</p>
                <p class="metric-label">📅 Last Championship Session</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Grafici statistiche
        st.markdown("---")
        self.show_homepage_charts()
    
    def show_homepage_charts(self):
        """Mostra grafici nella homepage con gestione errori migliorata"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Sessions per Week")
                
                # Query per sessioni per settimana
                query_sessions = """
                SELECT 
                    date(session_date, 'weekday 0', '-6 days') as week_start,
                    COUNT(*) as sessions
                FROM sessions 
                WHERE session_date IS NOT NULL
                GROUP BY date(session_date, 'weekday 0', '-6 days')
                ORDER BY week_start ASC
                LIMIT 12
                """
                
                df_sessions = self.safe_sql_query(query_sessions)
                
                if not df_sessions.empty:
                    # Formatta le date per una migliore leggibilità
                    df_sessions['week_label'] = pd.to_datetime(df_sessions['week_start']).dt.strftime('%d/%m')
                    
                    fig_sessions = px.bar(
                        df_sessions, 
                        x='week_label', 
                        y='sessions',
                        title="Sessioni per Settimana (Ultime 12)",
                        color='sessions',
                        color_continuous_scale='blues'
                    )
                    fig_sessions.update_xaxes(title="Week (Monday)")
                    fig_sessions.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_sessions, use_container_width=True)
                else:
                    st.info("No data available for sessions chart")
            
            with col2:
                st.subheader("👥 Most Active Drivers")
                
                # Query per piloti più attivi
                query_active = """
                SELECT 
                    d.last_name as driver,
                    d.total_sessions as sessions
                FROM drivers d
                WHERE d.total_sessions > 0
                ORDER BY d.total_sessions DESC
                LIMIT 10
                """
                
                df_active = self.safe_sql_query(query_active)
                
                if not df_active.empty:
                    # Ordina per visualizzazione orizzontale
                    df_active = df_active.sort_values('sessions', ascending=True)
                    
                    fig_active = px.bar(
                        df_active, 
                        x='sessions', 
                        y='driver',
                        orientation='h',
                        title="Top 10 Drivers by Activity",
                        color='sessions',
                        color_continuous_scale='greens'
                    )
                    fig_active.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_active, use_container_width=True)
                else:
                    st.info("No data available for activity chart")
            
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Errore nel caricamento grafici: {e}")
    
    # [Tutte le altre funzioni rimangono identiche]
    def get_championships_list(self) -> List[Tuple]:
        """Ottiene lista campionati ordinati per data di inizio discendente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    championship_id, 
                    name, 
                    season, 
                    start_date, 
                    end_date,
                    is_completed,
                    description
                FROM championships 
                ORDER BY 
                    is_completed ASC,
                    CASE WHEN end_date IS NULL THEN 1 ELSE 0 END,
                    end_date DESC,
                    championship_id DESC
            """)
            
            championships = cursor.fetchall()
            conn.close()
            
            return championships
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero campionati: {e}")
            return []
    
    def get_championship_standings(self, championship_id: int) -> pd.DataFrame:
        """Ottiene classifica campionato"""
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
                cs.points_dropped,
                cs.average_position,
                cs.best_position,
                cs.consistency_rating
            FROM championship_standings cs
            JOIN drivers d ON cs.driver_id = d.driver_id
            WHERE cs.championship_id = ?
            ORDER BY cs.position
        """
        
        return self.safe_sql_query(query, [championship_id])
    
    def get_championship_competitions(self, championship_id: int) -> List[Tuple]:
        """Ottiene lista competizioni del campionato"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    competition_id,
                    name,
                    track_name,
                    round_number,
                    date_start,
                    date_end,
                    weekend_format,
                    is_completed
                FROM competitions
                WHERE championship_id = ?
                ORDER BY 
                    is_completed DESC,
                    CASE WHEN date_start IS NULL THEN 1 ELSE 0 END,
                    CASE WHEN is_completed = 1 THEN date_start END DESC,
                    CASE WHEN is_completed = 0 THEN date_start END ASC,
                    round_number DESC
            """, (championship_id,))
            
            competitions = cursor.fetchall()
            conn.close()
            
            return competitions
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero competizioni: {e}")
            return []
    
    def get_competition_results(self, competition_id: int) -> pd.DataFrame:
        """Ottiene risultati competizione - AGGIORNATO per nuova struttura"""
        query = """
            SELECT 
                d.last_name as driver,
                cr.race_points,
                cr.pole_points,
                cr.fastest_lap_points,
                cr.bonus_points,
                cr.penalty_points,
                cr.total_points,
                -- Posizione in qualifica (dalle session results)
                (SELECT csr.position 
                 FROM competition_session_results csr 
                 WHERE csr.competition_id = cr.competition_id 
                 AND csr.driver_id = cr.driver_id 
                 AND csr.session_type LIKE '%Q%' 
                 ORDER BY csr.session_type DESC 
                 LIMIT 1) as qualifying_position,
                -- Posizione in gara (dalle session results)
                (SELECT csr.position 
                 FROM competition_session_results csr 
                 WHERE csr.competition_id = cr.competition_id 
                 AND csr.driver_id = cr.driver_id 
                 AND csr.session_type LIKE '%R%' 
                 ORDER BY csr.session_type DESC 
                 LIMIT 1) as position
            FROM competition_results cr
            JOIN drivers d ON cr.driver_id = d.driver_id
            WHERE cr.competition_id = ?
            ORDER BY cr.total_points DESC, cr.race_points DESC
        """
        
        return self.safe_sql_query(query, [competition_id])
    
    def get_competition_sessions(self, competition_id: int) -> List[Tuple]:
        """Ottiene sessioni della competizione"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    session_id,
                    session_type,
                    session_date,
                    session_order,
                    total_drivers,
                    best_lap_overall
                FROM sessions
                WHERE competition_id = ?
                ORDER BY session_order, session_date
            """, (competition_id,))
            
            sessions = cursor.fetchall()
            conn.close()
            
            return sessions
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero sessioni: {e}")
            return []
    
    def get_session_results(self, session_id: str) -> pd.DataFrame:
        """Ottiene risultati sessione"""
        query = """
            SELECT 
                sr.position,
                sr.race_number,
                d.last_name as driver,
                sr.lap_count,
                sr.best_lap,
                sr.total_time,
                sr.is_spectator
            FROM session_results sr
            JOIN drivers d ON sr.driver_id = d.driver_id
            WHERE sr.session_id = ?
            ORDER BY 
                CASE WHEN sr.position IS NULL THEN 1 ELSE 0 END,
                sr.position
        """
        
        return self.safe_sql_query(query, [session_id])
    
    def get_4fun_competitions_list(self) -> List[Tuple]:
        """Ottiene lista competizioni 4Fun (championship_id IS NULL)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    competition_id,
                    name,
                    track_name,
                    round_number,
                    date_start,
                    date_end,
                    weekend_format,
                    is_completed
                FROM competitions
                WHERE championship_id IS NULL 
                AND competition_id IS NOT NULL
                ORDER BY 
                    CASE WHEN date_start IS NULL THEN 1 ELSE 0 END,
                    date_start DESC,
                    competition_id DESC
            """)
            
            competitions = cursor.fetchall()
            conn.close()
            
            return competitions
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero competizioni 4Fun: {e}")
            return []
    
    def show_4fun_report(self):
        """Mostra il report competizioni 4Fun"""
        st.header("🎮 Report Official 4Fun")
        
        # Ottieni lista competizioni 4Fun
        competitions = self.get_4fun_competitions_list()
        
        if not competitions:
            st.warning("❌ No 4Fun competitions found in database")
            st.info("""
            **4Fun competitions are:**
            - Competitions with `competition_id` valued
            - Competitions with `championship_id` NULL (not belonging to championships)
            """)
            return
        
        # Prepara opzioni per selectbox
        competition_options = []
        competition_map = {}
        
        for comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed in competitions:
            # Formato display
            round_str = f"R{round_num} - " if round_num else ""
            status_str = " ✅" if is_completed else " 🔄"
            
            if date_start:
                date_str = f" - {date_start[:10]}"
            else:
                date_str = ""
            
            display_name = f"{round_str}{name} - {track}{date_str}{status_str}"
            
            competition_options.append(display_name)
            competition_map[display_name] = comp_id
        
        # Selectbox competizione (default: prima = più recente)
        selected_competition = st.selectbox(
            "🎮 Select 4Fun Competition:",
            options=competition_options,
            index=0,
            key="4fun_competition_select"
        )
        
        if selected_competition:
            competition_id = competition_map[selected_competition]
            
            # Trova info competizione selezionata
            selected_comp_info = next(
                (c for c in competitions if c[0] == competition_id), 
                None
            )
            
            if selected_comp_info:
                comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed = selected_comp_info
                
                # Header competizione 4Fun
                round_str = f"Round {round_num} - " if round_num else ""
                st.markdown(f"""
                <div class="competition-header" style="background: linear-gradient(90deg, #28a745, #20c997);">
                    <h2>🎮 {round_str}{name}</h2>
                    <p>📍 {track} | 📋 {weekend_format}</p>
                    {f'<p>📅 {date_start} - {date_end}</p>' if date_start and date_end else f'<p>📅 {date_start}</p>' if date_start else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Usa gli stessi metodi delle competizioni di campionato
                self.show_4fun_competition_details(selected_comp_info, competition_id)
    
    def show_4fun_competition_details(self, competition_info: Tuple, competition_id: int):
        """Mostra dettagli competizione 4Fun (usa gli stessi metodi delle competizioni di campionato)"""
        comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed = competition_info
        
        # Risultati competizione (stesso metodo)
        st.subheader("🏆 4Fun Leaderboard")
        results_df = self.get_competition_results(competition_id)
        
        if not results_df.empty:
            # Formatta risultati per visualizzazione - AGGIORNATO
            results_display = results_df.copy()
            
            # Aggiungi posizione basata sull'ordine (già ordinato per punti nella query)
            results_display['Pos'] = range(1, len(results_display) + 1)
            results_display['Pos'] = results_display['Pos'].apply(
                lambda x: "🥇" if x == 1 else "🥈" if x == 2 else "🥉" if x == 3 else str(x)
            )
            
            # Seleziona e rinomina colonne - SOLO CAMPI RICHIESTI
            columns_to_show = [
                'Pos', 'driver', 'race_points', 'pole_points', 
                'fastest_lap_points', 'bonus_points', 'penalty_points', 'total_points'
            ]
            
            column_names = {
                'Pos': 'Pos',
                'driver': 'Driver',
                'race_points': 'Race Points',
                'pole_points': 'Pole Points',
                'fastest_lap_points': 'Fast Lap Points',
                'bonus_points': 'Bonus Points',
                'penalty_points': 'Penalty Points',
                'total_points': 'Total Points'
            }
            
            results_display = results_display[columns_to_show]
            results_display.columns = [column_names[col] for col in columns_to_show]
            
            st.dataframe(
                results_display,
                use_container_width=True,
                hide_index=True
            )
            
            # Grafici specifici per 4Fun
            self.show_4fun_charts(results_df)
            
        else:
            st.warning("⚠️ 4Fun competition results not yet calculated")
        
        # Sessioni della competizione (stesso metodo)
        st.markdown("---")
        st.subheader("🎮 4Fun Competition Sessions")
        
        sessions = self.get_competition_sessions(competition_id)
        
        if sessions:
            for session_id, session_type, session_date, session_order, total_drivers, best_lap_overall in sessions:
                # Format data
                try:
                    date_obj = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%d/%m/%Y %H:%M')
                except:
                    date_str = session_date[:16] if session_date else 'N/A'
                
                # Header sessione
                st.markdown(f"""
                <div class="session-header">
                    <strong>🏁 {session_type}</strong> - {date_str} | 👥 {total_drivers} drivers
                    {f'| ⚡ Best: {self.format_lap_time(best_lap_overall)}' if best_lap_overall else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Risultati sessione (stesso metodo)
                session_results_df = self.get_session_results(session_id)
                
                if not session_results_df.empty:
                    # Formatta risultati sessione
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
                    
                    # Mostra tutti i risultati senza limitazioni
                    st.dataframe(
                        session_display,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning(f"⚠️ No results found for {session_type}")
                
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.warning("❌ No sessions found for this 4Fun competition")
    
    def show_4fun_charts(self, results_df: pd.DataFrame):
        """Shows specific charts for 4Fun competitions"""
        if results_df.empty:
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 4Fun Points Distribution")
            
            # Total points chart (only drivers with points > 0)
            points_data = results_df[results_df['total_points'] > 0].copy()
            if not points_data.empty:
                # Sort for horizontal display
                points_data = points_data.sort_values('total_points', ascending=True)
                
                fig_points = px.bar(
                    points_data,
                    x='total_points',
                    y='driver',
                    orientation='h',
                    title="Total Points per Driver",
                    color='total_points',
                    color_continuous_scale='viridis'
                )
                fig_points.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_points, use_container_width=True)
            else:
                st.info("No points assigned yet")
        
        with col2:
            st.subheader("⚡ Qualifying vs Race Performance")
            
            # Scatter plot qualifying vs race (only classified drivers)
            scatter_data = results_df[
                (pd.notna(results_df['qualifying_position'])) & 
                (pd.notna(results_df['position'])) &
                (results_df['position'] > 0)
            ].copy()
            
            if len(scatter_data) > 1:
                fig_scatter = px.scatter(
                    scatter_data,
                    x='qualifying_position',
                    y='position',
                    hover_data=['driver', 'total_points'],
                    title="Qualifying Position vs Race Position",
                    labels={
                        'qualifying_position': 'Qualifying Position',
                        'position': 'Race Position'
                    }
                )
                
                # Add reference line (same position)
                max_pos = max(scatter_data['qualifying_position'].max(), scatter_data['position'].max())
                fig_scatter.add_shape(
                    type="line",
                    x0=1, y0=1, x1=max_pos, y1=max_pos,
                    line=dict(color="red", width=2, dash="dash"),
                )
                
                fig_scatter.update_layout(height=400)
                fig_scatter.update_yaxes(autorange="reversed")  # Position 1 at top
                fig_scatter.update_xaxes(autorange="reversed")  # Position 1 at left
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Insufficient data for performance chart")

    def show_championships_report(self):
        """Mostra il report campionati"""
        st.header("🏆 Championships Report")
        
        # Ottieni lista campionati
        championships = self.get_championships_list()
        
        if not championships:
            st.warning("❌ No championships found in database")
            return
        
        # Prepara opzioni per selectbox
        championship_options = []
        championship_map = {}
        
        for champ_id, name, season, start_date, end_date, is_completed, description in championships:
            # Formato display
            season_str = f" ({season})" if season else ""
            status_str = " ✅" if is_completed else " 🔄"
            
            if start_date:
                date_str = f" - {start_date[:10]}"
            else:
                date_str = ""
            
            display_name = f"{name}{season_str}{date_str}{status_str}"
            
            championship_options.append(display_name)
            championship_map[display_name] = champ_id
        
        # Selectbox campionato
        selected_championship = st.selectbox(
            "🏆 Select Championship:",
            options=championship_options,
            index=0,
            key="championship_select"
        )
        
        if selected_championship:
            championship_id = championship_map[selected_championship]
            
            # Trova info campionato selezionato
            selected_champ_info = next(
                (c for c in championships if c[0] == championship_id), 
                None
            )
            
            if selected_champ_info:
                champ_id, name, season, start_date, end_date, is_completed, description = selected_champ_info
                
                # Header campionato
                season_info = f" - Stagione {season}" if season else ""
                
                # Costruisci l'HTML completo
                header_html = f"""
                <div class="championship-header">
                    <h2>🏆 {name}{season_info}</h2>
                """
                
                if description:
                    header_html += f"<p>{description}</p>"
                
                if start_date and end_date:
                    header_html += f"<p>📅 {start_date} - {end_date}</p>"
                
                header_html += "</div>"
                
                st.markdown(header_html, unsafe_allow_html=True)
                
                # Classifica campionato
                st.subheader("📊 Championship Leaderboard")
                standings_df = self.get_championship_standings(championship_id)
                
                if not standings_df.empty:
                    # Formatta classifica per visualizzazione
                    standings_display = standings_df.copy()
                    
                    # Aggiungi medaglie per primi 3
                    standings_display['Pos'] = standings_display['position'].apply(
                        lambda x: "🥇" if x == 1 else "🥈" if x == 2 else "🥉" if x == 3 else str(x)
                    )
                    
                    # Seleziona colonne da mostrare
                    columns_to_show = [
                        'Pos', 'driver', 'total_points', 'competitions_participated', 
                        'wins', 'podiums', 'poles', 'fastest_laps'
                    ]
                    
                    # Rinomina colonne
                    column_names = {
                        'Pos': 'Pos',
                        'driver': 'Driver',
                        'total_points': 'Points',
                        'competitions_participated': 'Competitions',
                        'wins': 'Wins',
                        'podiums': 'Podiums',
                        'poles': 'Poles',
                        'fastest_laps': 'Fast Laps'
                    }
                    
                    standings_display = standings_display[columns_to_show]
                    standings_display.columns = [column_names[col] for col in columns_to_show]
                    
                    # Mostra tabella senza indice e con altezza fissa
                    st.dataframe(
                        standings_display,
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
                    
                    # Grafici classifica
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Grafico vittorie in campionato
                        wins_data = standings_df[standings_df['wins'] > 0]
                        if not wins_data.empty:
                            # Ordina per numero di vittorie (crescente per il grafico)
                            wins_data = wins_data.sort_values('wins', ascending=True)
                            
                            fig_wins = px.bar(
                                wins_data,
                                x='wins',
                                y='driver',
                                orientation='h',
                                title="Wins by Driver in Championship",
                                color='wins',
                                color_continuous_scale='reds'
                            )
                            fig_wins.update_layout(height=400, showlegend=False)
                            st.plotly_chart(fig_wins, use_container_width=True)
                        else:
                            st.info("No wins recorded yet")
                    
                    with col2:
                        # Grafico distribuzione podi
                        podiums_data = standings_df[standings_df['podiums'] > 0]
                        if not podiums_data.empty:
                            fig_podiums = px.pie(
                                podiums_data,
                                names='driver',
                                values='podiums',
                                title="Podium Distribution"
                            )
                            fig_podiums.update_layout(height=400)
                            st.plotly_chart(fig_podiums, use_container_width=True)
                        else:
                            st.info("No podium recorded yet")
                
                else:
                    st.warning("⚠️ Championship leaderboard not yet calculated")
                
                # Selezione competizione
                st.markdown("---")
                self.show_competition_selection(championship_id)
    
    def show_competition_selection(self, championship_id: int):
        """Mostra selezione e dettagli competizione"""
        st.subheader("🏁 Championship Competitions")
        
        # Ottieni competizioni
        competitions = self.get_championship_competitions(championship_id)
        
        if not competitions:
            st.warning("❌ No competitions found for this championship")
            return
        
        # Prepara opzioni per selectbox
        competition_options = ["Select a competition..."]
        competition_map = {}
        
        for comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed in competitions:
            # Formato display
            round_str = f"R{round_num} - " if round_num else ""
            status_str = " ✅" if is_completed else " 🔄"
            date_str = f" ({date_start[:10]})" if date_start else ""
            
            display_name = f"{round_str}{name} - {track}{date_str}{status_str}"
            
            competition_options.append(display_name)
            competition_map[display_name] = comp_id
        
        # Selectbox competizione
        selected_competition = st.selectbox(
            "🏁 Select Competition:",
            options=competition_options,
            index=0,
            key="competition_select"
        )
        
        if selected_competition and selected_competition != "Select a competition...":
            competition_id = competition_map[selected_competition]
            
            # Trova info competizione selezionata
            selected_comp_info = next(
                (c for c in competitions if c[0] == competition_id), 
                None
            )
            
            if selected_comp_info:
                self.show_competition_details(selected_comp_info, competition_id)
    
    def show_competition_details(self, competition_info: Tuple, competition_id: int):
        """Mostra dettagli competizione"""
        comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed = competition_info
        
        # Header competizione
        round_str = f"Round {round_num} - " if round_num else ""
        st.markdown(f"""
        <div class="competition-header">
            <h3>🏁 {round_str}{name}</h3>
            <p>📍 {track} | 📋 {weekend_format} | 📅 {date_start}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Risultati competizione
        st.subheader("🏆 Competition Leaderboard")
        results_df = self.get_competition_results(competition_id)
        
        if not results_df.empty:
            # Formatta risultati per visualizzazione - AGGIORNATO
            results_display = results_df.copy()
            
            # Aggiungi posizione basata sull'ordine (già ordinato per punti nella query)
            results_display['Pos'] = range(1, len(results_display) + 1)
            results_display['Pos'] = results_display['Pos'].apply(
                lambda x: "🥇" if x == 1 else "🥈" if x == 2 else "🥉" if x == 3 else str(x)
            )
            
            # Seleziona e rinomina colonne - SOLO CAMPI RICHIESTI
            columns_to_show = [
                'Pos', 'driver', 'race_points', 'pole_points', 
                'fastest_lap_points', 'bonus_points', 'penalty_points', 'total_points'
            ]
            
            column_names = {
                'Pos': 'Pos',
                'driver': 'Driver',
                'race_points': 'Race Points',
                'pole_points': 'Pole Points',
                'fastest_lap_points': 'Fast Lap Points',
                'bonus_points': 'Bonus Points',
                'penalty_points': 'Penalty Points',
                'total_points': 'Total Points'
            }
            
            results_display = results_display[columns_to_show]
            results_display.columns = [column_names[col] for col in columns_to_show]
            
            st.dataframe(
                results_display,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("⚠️ Competition results not yet calculated")
        
        # Sessioni della competizione
        st.markdown("---")
        st.subheader("🎮 Competition Sessions")
        
        sessions = self.get_competition_sessions(competition_id)
        
        if sessions:
            for session_id, session_type, session_date, session_order, total_drivers, best_lap_overall in sessions:
                # Format data
                try:
                    date_obj = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%d/%m/%Y %H:%M')
                except:
                    date_str = session_date[:16] if session_date else 'N/A'
                
                # Header sessione
                st.markdown(f"""
                <div class="session-header">
                    <strong>🏁 {session_type}</strong> - {date_str} | 👥 {total_drivers} drivers
                    {f'| ⚡ Best: {self.format_lap_time(best_lap_overall)}' if best_lap_overall else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Risultati sessione
                session_results_df = self.get_session_results(session_id)
                
                if not session_results_df.empty:
                    # Formatta risultati sessione
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
                    
                    # Mostra tutti i risultati senza limitazioni
                    st.dataframe(
                        session_display,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning(f"⚠️ No results found for {session_type}")
                
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.warning("❌ No sessions found for this competition")
            
    def show_sessions_report(self):
        """Mostra il report Sessions con filtri e statistiche"""
        st.header("🎮 Sessions Report")
        
        # Calcola date di default (ultima settimana)
        today = datetime.now().date()
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
        
        # STATISTICHE PRINCIPALI
        self.show_sessions_main_stats(sessions_stats)
        
        # SELEZIONE SESSIONE (STILE BEST LAP REPORT)
        st.markdown("---")
        
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
            
            # Status ufficiale/non ufficiale
            status = "🏆" if pd.notna(row['competition_id']) else "❌"
            
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
            self.show_sessions_summary_table(sessions_list)
            
        elif selected_session_option in session_map:
            # Mostra dettagli della sessione specifica
            selected_session_id = session_map[selected_session_option]
            st.markdown("---")
            self.show_session_details(selected_session_id)
    
    def show_sessions_summary_table(self, sessions_list: pd.DataFrame):
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
        
        # Status ufficiale/non ufficiale
        display_df['Status'] = display_df['competition_id'].apply(
            lambda x: "🏆 Official" if pd.notna(x) else "❌ Unofficial"
        )
        
        # Data formattata con ora
        display_df['Date & Time'] = display_df['session_date'].apply(
            lambda x: self.format_session_datetime(x) if pd.notna(x) else "N/A"
        )
        
        # Winner info formattata
        display_df['Winner'] = display_df['winner_name'].fillna("N/A")
        
        # Winner time formattata
        display_df['Winner Time'] = display_df['winner_time'].apply(
            lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
        )
        
        # Seleziona colonne finali per display
        columns_to_show = ['Session', 'Type', 'Status', 'track_name', 'Date & Time', 'total_drivers', 'Winner', 'Winner Time']
        column_names = {
            'Session': 'Session',
            'Type': 'Type',
            'Status': 'Status',
            'track_name': 'Track',
            'Date & Time': 'Date & Time',
            'total_drivers': 'Drivers',
            'Winner': 'Winner',
            'Winner Time': 'Winner Time'
        }
        
        final_display = display_df[columns_to_show].copy()
        final_display.columns = [column_names[col] for col in columns_to_show]
        
        # Mostra tabella completa
        st.dataframe(
            final_display,
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        # Info riassuntive
        total_sessions = len(final_display)
        official_count = len(display_df[pd.notna(display_df['competition_id'])])
        unofficial_count = total_sessions - official_count
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"📊 **{total_sessions}** total sessions in period")
        
        with col2:
            st.success(f"🏆 **{official_count}** official sessions")
        
        with col3:
            st.warning(f"❌ **{unofficial_count}** unofficial sessions")

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
    
    def show_sessions_main_stats(self, stats: Dict):
        """Mostra statistiche principali delle sessioni"""
        # Prima riga di metriche
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['total_sessions']}</p>
                <p class="metric-label">🎮 Total Sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['unique_drivers']}</p>
                <p class="metric-label">👥 Unique Drivers</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['official_sessions']}</p>
                <p class="metric-label">🏆 Official Sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['non_official_sessions']}</p>
                <p class="metric-label">❌ Unofficial Sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Seconda riga di metriche
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.5rem;">{stats['most_used_track']}</p>
                <p class="metric-label">🏁 Most Used Track</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['most_used_count']}</p>
                <p class="metric-label">📊 Sessions on Track</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Ultima sessione - circuito
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.5rem;">{stats['last_session_track']}</p>
                <p class="metric-label">📍 Last Session Track</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Ultima sessione - data e ora
            if stats['last_session_date']:
                try:
                    last_date = datetime.fromisoformat(stats['last_session_date'].replace('Z', '+00:00'))
                    date_str = last_date.strftime('%d/%m %H:%M')
                except:
                    date_str = stats['last_session_date'][:16] if stats['last_session_date'] else "N/A"
            else:
                date_str = "N/A"
            
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.3rem;">{date_str}</p>
                <p class="metric-label">📅 Last Session Date</p>
            </div>
            """, unsafe_allow_html=True)
    
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
                -- Winner info (posizione 1)
                winner.driver_name as winner_name,
                winner.total_time as winner_time,
                winner.best_lap as winner_best_lap,
                -- Competition info se disponibile
                c.name as competition_name,
                c.round_number
            FROM sessions s
            LEFT JOIN (
                SELECT 
                    sr.session_id,
                    d.last_name as driver_name,
                    sr.total_time,
                    sr.best_lap
                FROM session_results sr
                JOIN drivers d ON sr.driver_id = d.driver_id
                WHERE sr.position = 1
            ) winner ON s.session_id = winner.session_id
            LEFT JOIN competitions c ON s.competition_id = c.competition_id
            WHERE DATE(s.session_date) >= ? AND DATE(s.session_date) < ?
            ORDER BY s.session_date DESC
        '''
        
        return self.safe_sql_query(query, [date_from_str, date_to_str])
    
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
                use_container_width=True,
                hide_index=True
            )
            
            # Grafici se ci sono abbastanza dati
            if len(session_results_df) > 3:
                self.show_session_charts(session_results_df, session_type)
                
        else:
            st.warning(f"⚠️ No results found for this session")
    
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
                
                st.plotly_chart(fig_gap, use_container_width=True)
                
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
                st.plotly_chart(fig_laps, use_container_width=True)
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
            
            st.plotly_chart(fig_hist, use_container_width=True)
    
    def format_session_datetime(self, session_date: str) -> str:
        """Formatta data e ora sessione per visualizzazione"""
        try:
            date_obj = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
            return date_obj.strftime('%d/%m/%Y %H:%M')
        except:
            return session_date[:16] if session_date else 'N/A'

    def show_best_laps_report(self):
        """Mostra il report Best Laps per pista"""
        st.header("🏁 Report Best Laps")
        
        # Ottieni lista piste
        tracks = self.get_tracks_list()
        
        if not tracks:
            st.warning("❌ No tracks found in database")
            return
        
        # Layout a due colonne per i filtri
        col1, col2 = st.columns(2)
        
        with col1:
            # Selectbox pista con riepilogo generale come prima opzione
            track_options = ["📊 General Summary"] + tracks
            selected_track = st.selectbox(
                "🏁 Select Track:",
                options=track_options,
                index=0,  # Riepilogo generale selezionato di default
                key="track_select"
            )
        
        with col2:
            # Radio button per tipo statistiche
            stats_type = st.radio(
                "📊 Statistics Type:",
                options=["All Sessions", "Official Competitions Only"],
                index=0,
                key="stats_type_select"
            )
        
        # Mostra contenuto basato sulla selezione
        official_only = (stats_type == "Official Competitions Only")
        
        if selected_track == "📊 General Summary":
            # Mostra riepilogo generale di tutte le piste
            st.markdown("---")
            st.subheader("🏁 Track Records Summary")
            self.show_all_tracks_summary(official_only)
            
        elif selected_track in tracks:
            # Mostra dettagli della pista specifica
            st.markdown("---")
            self.show_track_details(selected_track, official_only)
    
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
    
    def show_all_tracks_summary(self, official_only: bool = False):
        """Mostra riepilogo record per tutte le piste"""
        
        summary_df = self.get_all_tracks_summary(official_only)
        
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
        # Formatta tipo sessione
        summary_display['Tipo'] = summary_display['session_type'].apply(
            lambda x: self.format_session_type(x) if pd.notna(x) else "N/A"
        )
        
        # Seleziona colonne finali
        columns_to_show = ['Pista', 'Record', 'driver_name', 'Data', 'Tipo']
        column_names = {
            'Pista': 'Track',
            'Record': 'Record',
            'driver_name': 'Driver',
            'Data': 'Date',
            'Tipo': 'Session Type'
        }
        
        final_display = summary_display[columns_to_show].copy()
        final_display.columns = [column_names[col] for col in columns_to_show]
        
        st.dataframe(
            final_display,
            use_container_width=True,
            hide_index=True,
            height=400
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
    
    def get_all_tracks_summary(self, official_only: bool = False) -> pd.DataFrame:
        """Ottiene riepilogo record per tutte le piste"""
        
        # Costruisci query con filtro ufficiali se richiesto
        official_filter = " AND s.competition_id IS NOT NULL" if official_only else ""
        
        query = f'''
            WITH track_records AS (
                SELECT 
                    s.track_name,
                    MIN(l.lap_time) as best_lap
                FROM laps l
                JOIN sessions s ON l.session_id = s.session_id
                WHERE l.is_valid_for_best = 1 AND l.lap_time > 0{official_filter}
                GROUP BY s.track_name
            )
            SELECT 
                tr.track_name,
                tr.best_lap,
                d.last_name as driver_name,
                s.session_date,
                s.session_type
            FROM track_records tr
            JOIN laps l ON tr.best_lap = l.lap_time
            JOIN sessions s ON l.session_id = s.session_id AND s.track_name = tr.track_name
            JOIN drivers d ON l.driver_id = d.driver_id
            WHERE l.is_valid_for_best = 1{official_filter}
            GROUP BY tr.track_name
            ORDER BY tr.best_lap ASC
        '''
        
        return self.safe_sql_query(query)
    
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
        """Mostra dettagli completi per la pista selezionata"""
        
        # Header pista con indicatore tipo statistiche
        stats_indicator = "🏆 Official Competitions Only" if official_only else "📊 All Sessions"
        
        st.markdown(f"""
        <div class="championship-header">
            <h2>🏁 {track_name}</h2>
            <p>{stats_indicator}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Ottieni statistiche generali
        track_stats = self.get_track_statistics(track_name, official_only)
        
        if not any(track_stats.values()):
            st.warning("⚠️ No data available for this track with selected filters")
            return
        
        # Prima riga: Statistiche generali
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{track_stats['total_sessions']}</p>
                <p class="metric-label">🎮 Total Sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{track_stats['unique_drivers']}</p>
                <p class="metric-label">👥 Piloti Unici</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{track_stats['total_laps']:,}</p>
                <p class="metric-label">🔄 Giri Validi</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            best_time_str = self.format_lap_time(track_stats['best_time']) if track_stats['best_time'] else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.8rem;">{best_time_str}</p>
                <p class="metric-label">⚡ Record Assoluto</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Seconda riga: Info record e media
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            record_holder = track_stats.get('record_holder', 'N/A')
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.5rem;">{record_holder}</p>
                <p class="metric-label">🏆 Detentore Record</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_time_str = self.format_lap_time(track_stats['avg_time']) if track_stats['avg_time'] else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.8rem;">{avg_time_str}</p>
                <p class="metric-label">📈 Tempo Medio</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Calcola media giri per sessione
            avg_laps = round(track_stats['total_laps'] / track_stats['total_sessions'], 1) if track_stats['total_sessions'] > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{avg_laps}</p>
                <p class="metric-label">📊 Average Laps/Session</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Ultima sessione su questa pista
            last_session = track_stats.get('last_session_date')
            if last_session:
                try:
                    last_date = datetime.fromisoformat(last_session.replace('Z', '+00:00'))
                    days_ago = (datetime.now() - last_date).days
                    if days_ago == 0:
                        last_text = "Today"
                    elif days_ago == 1:
                        last_text = "Yesterday"
                    else:
                        last_text = f"{days_ago} days ago"
                except:
                    last_text = "N/A"
            else:
                last_text = "N/A"
            
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.5rem;">{last_text}</p>
                <p class="metric-label">📅 Ultima Sessione</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Classifica Best Laps
        st.markdown("---")
        st.subheader("🏆 Best Laps Leaderboard by Driver")
        
        leaderboard_df = self.get_track_leaderboard(track_name, official_only)
        
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
            
            # Seleziona colonne finali
            columns_to_show = ['Pos', 'driver_name', 'Best Time', 'Gap', 'total_laps', 'Record Date', 'session_type']
            column_names = {
                'Pos': 'Pos',
                'driver_name': 'Pilota',
                'Best Time': 'Best Time',
                'Gap': 'Gap',
                'total_laps': 'Total Laps',
                'Record Date': 'Record Date',
                'session_type': 'Session Type'
            }
            
            final_display = leaderboard_display[columns_to_show].copy()
            final_display.columns = [column_names[col] for col in columns_to_show]
            
            # Mostra tabella con evidenziazione primi 3
            st.dataframe(
                final_display,
                use_container_width=True,
                hide_index=True,
                height=500
            )
            
            # Analisi gap per i top 10
            if len(leaderboard_display) > 1:
                st.subheader("⏱️ Top 10 Gap Analysis")
                
                top_10 = leaderboard_display.head(10)
                gap_analysis = []
                
                for idx, row in top_10.iterrows():
                    if idx == 0:  # Leader
                        gap_analysis.append(f"🥇 **{row['driver_name']}**: {row['Best Time']} (Leader)")
                    else:
                        gap_analysis.append(f"   {row['Pos']}. **{row['driver_name']}**: {row['Best Time']} ({row['Gap']})")
                
                for line in gap_analysis:
                    st.markdown(line)
        
        else:
            st.warning("⚠️ No data available for leaderboard")
        
        # Grafici
        st.markdown("---")
        self.show_track_charts(track_name, official_only, leaderboard_df)

    def show_track_details(self, track_name: str, official_only: bool = False):
        """Mostra dettagli completi per la pista selezionata"""
        
        # Header pista con indicatore tipo statistiche
        stats_indicator = "🏆 Official Competitions Only" if official_only else "📊 All Sessions"
        
        st.markdown(f"""
        <div class="championship-header">
            <h2>🏁 {track_name}</h2>
            <p>{stats_indicator}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Ottieni statistiche generali
        track_stats = self.get_track_statistics(track_name, official_only)
        
        if not any(track_stats.values()):
            st.warning("⚠️ No data available for this track with selected filters")
            return
        
        # Prima riga: Statistiche generali
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{track_stats['total_sessions']}</p>
                <p class="metric-label">🎮 Total Sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{track_stats['unique_drivers']}</p>
                <p class="metric-label">👥 Piloti Unici</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{track_stats['total_laps']:,}</p>
                <p class="metric-label">🔄 Giri Validi</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            best_time_str = self.format_lap_time(track_stats['best_time']) if track_stats['best_time'] else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.8rem;">{best_time_str}</p>
                <p class="metric-label">⚡ Record Assoluto</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Seconda riga: Info record e media
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            record_holder = track_stats.get('record_holder', 'N/A')
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.5rem;">{record_holder}</p>
                <p class="metric-label">🏆 Detentore Record</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_time_str = self.format_lap_time(track_stats['avg_time']) if track_stats['avg_time'] else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.8rem;">{avg_time_str}</p>
                <p class="metric-label">📈 Tempo Medio</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Calcola media giri per sessione
            avg_laps = round(track_stats['total_laps'] / track_stats['total_sessions'], 1) if track_stats['total_sessions'] > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{avg_laps}</p>
                <p class="metric-label">📊 Average Laps/Session</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Ultima sessione su questa pista
            last_session = track_stats.get('last_session_date')
            if last_session:
                try:
                    last_date = datetime.fromisoformat(last_session.replace('Z', '+00:00'))
                    days_ago = (datetime.now() - last_date).days
                    if days_ago == 0:
                        last_text = "Today"
                    elif days_ago == 1:
                        last_text = "Yesterday"
                    else:
                        last_text = f"{days_ago} days ago"
                except:
                    last_text = "N/A"
            else:
                last_text = "N/A"
            
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.5rem;">{last_text}</p>
                <p class="metric-label">📅 Ultima Sessione</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Classifica Best Laps
        st.markdown("---")
        st.subheader("🏆 Best Laps Leaderboard by Driver")
        
        leaderboard_df = self.get_track_leaderboard(track_name, official_only)
        
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
            
            # Seleziona colonne finali
            columns_to_show = ['Pos', 'driver_name', 'Best Time', 'Gap', 'total_laps', 'Record Date', 'session_type']
            column_names = {
                'Pos': 'Pos',
                'driver_name': 'Pilota',
                'Best Time': 'Best Time',
                'Gap': 'Gap',
                'total_laps': 'Total Laps',
                'Record Date': 'Record Date',
                'session_type': 'Session Type'
            }
            
            final_display = leaderboard_display[columns_to_show].copy()
            final_display.columns = [column_names[col] for col in columns_to_show]
            
            # Mostra tabella con evidenziazione primi 3
            st.dataframe(
                final_display,
                use_container_width=True,
                hide_index=True,
                height=500
            )
            
            # Analisi gap per i top 10
            if len(leaderboard_display) > 1:
                st.subheader("⏱️ Top 10 Gap Analysis")
                
                top_10 = leaderboard_display.head(10)
                gap_analysis = []
                
                for idx, row in top_10.iterrows():
                    if idx == 0:  # Leader
                        gap_analysis.append(f"🥇 **{row['driver_name']}**: {row['Best Time']} (Leader)")
                    else:
                        gap_analysis.append(f"   {row['Pos']}. **{row['driver_name']}**: {row['Best Time']} ({row['Gap']})")
                
                for line in gap_analysis:
                    st.markdown(line)
        
        else:
            st.warning("⚠️ No data available for leaderboard")
        
        # Grafici
        st.markdown("---")
        self.show_track_charts(track_name, official_only, leaderboard_df)    

    def get_track_statistics(self, track_name: str, official_only: bool = False) -> Dict:
        """Ottiene statistiche generali per la pista"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Costruisci query base con filtro ufficiali se richiesto
            official_filter = " AND s.competition_id IS NOT NULL" if official_only else ""
            
            # Statistiche generali
            query = f'''
                SELECT 
                    COUNT(DISTINCT s.session_id) as total_sessions,
                    COUNT(DISTINCT l.driver_id) as unique_drivers,
                    COUNT(l.id) as total_laps,
                    MIN(l.lap_time) as best_time,
                    AVG(CAST(l.lap_time AS REAL)) as avg_time,
                    MAX(s.session_date) as last_session_date
                FROM sessions s
                LEFT JOIN laps l ON s.session_id = l.session_id
                WHERE s.track_name = ? AND l.is_valid_for_best = 1 AND l.lap_time > 0{official_filter}
            '''
            
            cursor.execute(query, (track_name,))
            result = cursor.fetchone()
            
            if result:
                sessions, drivers, laps, best, avg, last_session = result
                
                # Chi detiene il record
                record_query = f'''
                    SELECT d.last_name 
                    FROM laps l
                    JOIN drivers d ON l.driver_id = d.driver_id
                    JOIN sessions s ON l.session_id = s.session_id
                    WHERE s.track_name = ? AND l.lap_time = ? AND l.is_valid_for_best = 1{official_filter}
                    LIMIT 1
                '''
                
                cursor.execute(record_query, (track_name, best))
                record_result = cursor.fetchone()
                record_holder = record_result[0] if record_result else "N/A"
                
                stats = {
                    'total_sessions': sessions or 0,
                    'unique_drivers': drivers or 0,
                    'total_laps': laps or 0,
                    'best_time': best,
                    'avg_time': int(avg) if avg else None,
                    'record_holder': record_holder,
                    'last_session_date': last_session
                }
            else:
                stats = {
                    'total_sessions': 0,
                    'unique_drivers': 0,
                    'total_laps': 0,
                    'best_time': None,
                    'avg_time': None,
                    'record_holder': 'N/A',
                    'last_session_date': None
                }
            
            conn.close()
            return stats
            
        except Exception as e:
            st.error(f"❌ Errore nel recupero statistiche pista: {e}")
            return {}
    
    def get_track_leaderboard(self, track_name: str, official_only: bool = False) -> pd.DataFrame:
        """Ottiene classifica best laps per pista"""
        
        # Costruisci query con filtro ufficiali se richiesto
        official_filter = " AND s.competition_id IS NOT NULL" if official_only else ""
        
        query = f'''
            SELECT 
                d.last_name as driver_name,
                d.short_name,
                MIN(l.lap_time) as best_lap,
                COUNT(l.id) as total_laps,
                s.session_date,
                s.session_type
            FROM laps l
            JOIN drivers d ON l.driver_id = d.driver_id
            JOIN sessions s ON l.session_id = s.session_id
            WHERE s.track_name = ? AND l.is_valid_for_best = 1 AND l.lap_time > 0{official_filter}
            GROUP BY l.driver_id
            ORDER BY best_lap ASC
            LIMIT 50
        '''
        
        return self.safe_sql_query(query, [track_name])
    
    def show_track_charts(self, track_name: str, official_only: bool, leaderboard_df: pd.DataFrame):
        """Mostra grafici per la pista"""
        if leaderboard_df.empty:
            st.info("No data available for charts")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Top 20 Times Distribution")
            
            # Grafico distribuzione tempi dei primi 20
            top_20 = leaderboard_df.head(20).copy()
            if not top_20.empty:
                # Converti tempi in secondi per il grafico
                top_20['tempo_secondi'] = top_20['best_lap'] / 1000
                top_20 = top_20.sort_values('tempo_secondi', ascending=True)
                
                fig_times = px.bar(
                    top_20,
                    x='driver_name',
                    y='tempo_secondi',
                    title="Tempi Best Lap (Top 20)",
                    color='tempo_secondi',
                    color_continuous_scale='viridis'
                )
                fig_times.update_xaxes(tickangle=45)
                fig_times.update_layout(height=400, showlegend=False)
                fig_times.update_yaxes(title="Tempo (secondi)")
                st.plotly_chart(fig_times, use_container_width=True)
            else:
                st.info("Insufficient data for distribution chart")
        
        with col2:
            st.subheader("🔄 Activity per Driver")
            
            # Grafico giri totali per pilota (top 15 più attivi)
            activity_data = leaderboard_df.nlargest(15, 'total_laps').copy()
            if not activity_data.empty:
                activity_data = activity_data.sort_values('total_laps', ascending=True)
                
                fig_activity = px.bar(
                    activity_data,
                    x='total_laps',
                    y='driver_name',
                    orientation='h',
                    title="Giri Totali per Pilota (Top 15)",
                    color='total_laps',
                    color_continuous_scale='greens'
                )
                fig_activity.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_activity, use_container_width=True)
            else:
                st.info("Insufficient data for activity chart")
        
        # Grafico evoluzione record nel tempo (se abbastanza dati)
        if len(leaderboard_df) > 5:
            st.subheader("📈 Performance Evolution")
            
            # Ottieni dati storici per grafico evoluzione
            evolution_data = self.get_track_evolution_data(track_name, official_only)
            
            if not evolution_data.empty and len(evolution_data) > 1:
                fig_evolution = px.line(
                    evolution_data,
                    x='session_date',
                    y='tempo_secondi',
                    title=f"Evoluzione Record su {track_name}",
                    hover_data=['driver_name', 'session_type']
                )
                fig_evolution.update_layout(height=400)
                fig_evolution.update_yaxes(title="Tempo Record (secondi)")
                fig_evolution.update_xaxes(title="Data")
                st.plotly_chart(fig_evolution, use_container_width=True)
            else:
                st.info("Insufficient data for evolution chart")
    
    def get_track_evolution_data(self, track_name: str, official_only: bool = False) -> pd.DataFrame:
        """Ottiene dati evoluzione record nel tempo"""
        
        official_filter = " AND s.competition_id IS NOT NULL" if official_only else ""
        
        query = f'''
            SELECT 
                s.session_date,
                d.last_name as driver_name,
                s.session_type,
                MIN(l.lap_time) as best_lap_session
            FROM laps l
            JOIN drivers d ON l.driver_id = d.driver_id
            JOIN sessions s ON l.session_id = s.session_id
            WHERE s.track_name = ? AND l.is_valid_for_best = 1 AND l.lap_time > 0{official_filter}
            GROUP BY s.session_id
            ORDER BY s.session_date ASC
        '''
        
        df = self.safe_sql_query(query, [track_name])
        
        if not df.empty:
            # Calcola record progressivo
            df['tempo_secondi'] = df['best_lap_session'] / 1000
            df['record_progressivo'] = df['best_lap_session'].cummin()
            df['tempo_secondi'] = df['record_progressivo'] / 1000
            
            # Filtra solo i miglioramenti del record
            df = df[df['best_lap_session'] == df['record_progressivo']].copy()
        
        return df
    
    def format_time_duration(self, milliseconds: int) -> str:
        """Formatta durata in millisecondi per gap"""
        if not milliseconds or milliseconds <= 0:
            return "0.000"
        
        if milliseconds < 1000:
            return f"0.{milliseconds:03d}"
        else:
            seconds = milliseconds / 1000
            return f"{seconds:.3f}"
    
    def format_session_date(self, session_date: str) -> str:
        """Formatta data sessione per visualizzazione"""
        try:
            date_obj = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
            return date_obj.strftime('%d/%m/%Y')
        except:
            return session_date[:10] if session_date else 'N/A'

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
                        <h3 style="margin: 0.5rem 0 0 0; font-size: 1.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">ACC Server Dashboard</h3>
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
                        social_buttons.append(f'<a href="{simgrid_url}" target="_blank" style="text-decoration: none; margin: 0 1rem;"><button style="background: linear-gradient(90deg, #ff6b35, #ff8c42); color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 25px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">🏆 SimGrid Community</button></a>')
                    
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
                st.markdown(f"""
                <div class="main-header">
                    <h1>🏁 {community_name}</h1>
                    <h3>ACC Server Dashboard</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Link social (solo se configurati)
                social_config = self.config.get('social', {})
                discord_url = social_config.get('discord')
                simgrid_url = social_config.get('simgrid')
                
                if discord_url or simgrid_url:
                    social_buttons = []
                    
                    if simgrid_url:
                        social_buttons.append(f'<a href="{simgrid_url}" target="_blank" style="text-decoration: none; margin: 0 1rem;"><button style="background: linear-gradient(90deg, #ff6b35, #ff8c42); color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 25px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">🏆 SimGrid Community</button></a>')
                    
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
                "🏆 Championships Report",
                "🎮 Official 4Fun Report",
                "🏁 Best Lap Report",
                "🎮 Sessions Report",
                "👤 Drivers Report",
                "📊 Advanced Statistics"
            ]
        )
        
        # Routing pagine
        if page == "🏠 Homepage":
            dashboard.show_homepage()
        
        elif page == "🏆 Championships Report":
            dashboard.show_championships_report()
        
        elif page == "🎮 Official 4Fun Report":
            dashboard.show_4fun_report()
        
        elif page == "🏁 Best Lap Report":
            dashboard.show_best_laps_report()

        elif page == "🎮 Sessions Report":
            dashboard.show_sessions_report()

        elif page == "👤 Drivers Report":
            st.header("👤 Drivers Report")
            st.info("🚧 Section under development - will be implemented soon")
        
        elif page == "📊 Advanced Statistics":
            st.header("📊 Advanced Statistics")
            st.info("🚧 Section under development - will be implemented soon")
        
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            <p>🏁 ACC Server Dashboard</p>
            <p>Community: {dashboard.config['community']['name']}</p>
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
