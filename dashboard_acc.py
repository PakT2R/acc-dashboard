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
from datetime import datetime
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, List, Tuple

# Configurazione pagina
st.set_page_config(
    page_title="ACC Server Dashboard",
    page_icon="ðŸ",
    layout="wide",
    initial_sidebar_state="expanded"
)

class ACCWebDashboard:
    """Classe principale per il dashboard web ACC"""
    
    def __init__(self):
        """Inizializza il dashboard con gestione ambiente"""
        self.config = self.load_config()
        self.db_path = self.get_database_path()
        
        # Verifica esistenza database
        if not self.check_database():
            self.show_database_error()
            st.stop()
        
        # CSS personalizzato
        self.inject_custom_css()
    
    def get_database_path(self) -> str:
        """Ottiene il percorso del database considerando l'ambiente"""
        # PrioritÃ : variabile d'ambiente > config file > default
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
					
					# ?? IMPOSTA IL FLAG BASANDOSI SUL FILE CARICATO
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
        """Verifica esistenza e validitÃ  del database"""
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
        st.error("âŒ **Database non disponibile**")
        
        if self.is_github_deployment:
            st.markdown("""
            ### ðŸ”„ Database in aggiornamento
            
            Il database potrebbe essere in fase di aggiornamento. 
            Riprova tra qualche minuto.
            
            **Per gli amministratori:**
            - Verifica che il file `acc_stats.db` sia presente nel repository
            - Controlla che il file non sia danneggiato
            - Assicurati che contenga le tabelle necessarie
            """)
        else:
            st.markdown(f"""
            ### ðŸš€ Setup Locale
            
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
                ðŸ  Locale
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
                    st.warning(f"âš ï¸ Errore nella query {key}: {e}")
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
            st.error(f"âŒ Errore nel recupero statistiche: {e}")
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
            st.error(f"âŒ Errore nella query: {e}")
            return pd.DataFrame()
    
    def show_homepage(self):
        """Mostra la homepage con statistiche generali"""
        # Indicatore ambiente (solo locale)
        self.show_environment_indicator()
        
        # Header principale
        community_name = self.config['community']['name']
        st.markdown(f"""
        <div class="main-header">
            <h1>ðŸ {community_name}</h1>
            <h3>ACC Server Dashboard</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Info deployment per admin (solo in locale)
        if not self.is_github_deployment:
            with st.expander("â„¹ï¸ Info Sistema", expanded=False):
                st.write(f"**Database:** `{self.db_path}`")
                st.write(f"**Configurazione:** Caricata")
                st.write(f"**Ambiente:** Sviluppo Locale")
        
        # Ottieni statistiche
        stats = self.get_database_stats()
        
        if not any(stats.values()):
            st.warning("âš ï¸ Nessun dato disponibile nel database")
            return
        
        # PRIMA RIGA - Layout a colonne per le metriche
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['total_drivers']}</p>
                <p class="metric-label">ðŸ‘¥ Piloti Registrati</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['total_sessions']}</p>
                <p class="metric-label">ðŸŽ® Sessioni Totali</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['total_laps']:,}</p>
                <p class="metric-label">ðŸ”„ Giri Totali</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Calcola media giri per sessione
            avg_laps = round(stats['total_laps'] / stats['total_sessions'], 1) if stats['total_sessions'] > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{avg_laps}</p>
                <p class="metric-label">ðŸ“Š Media Giri/Sessione</p>
            </div>
            """, unsafe_allow_html=True)
        
        # SECONDA RIGA di metriche
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['total_championships']}</p>
                <p class="metric-label">ðŸ† Campionati Conclusi</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{stats['completed_competitions']}</p>
                <p class="metric-label">ðŸ Competizioni Campionati</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            championship_sessions = stats.get('championship_sessions', 0)
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{championship_sessions}</p>
                <p class="metric-label">ðŸŽ¯ Sessioni Campionati</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Ultima sessione
            if stats['last_session']:
                try:
                    last_date = datetime.fromisoformat(stats['last_session'].replace('Z', '+00:00'))
                    days_ago = (datetime.now() - last_date).days
                    if days_ago == 0:
                        last_text = "Oggi"
                    elif days_ago == 1:
                        last_text = "Ieri"
                    else:
                        last_text = f"{days_ago} giorni fa"
                except:
                    last_text = "N/A"
            else:
                last_text = "N/A"
            
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value" style="font-size: 1.8rem;">{last_text}</p>
                <p class="metric-label">ðŸ“… Ultima Sessione Campionati</p>
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
                st.subheader("ðŸ“Š Sessioni per Settimana")
                
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
                    # Formatta le date per una migliore leggibilitÃ 
                    df_sessions['week_label'] = pd.to_datetime(df_sessions['week_start']).dt.strftime('%d/%m')
                    
                    fig_sessions = px.bar(
                        df_sessions, 
                        x='week_label', 
                        y='sessions',
                        title="Sessioni per Settimana (Ultime 12)",
                        color='sessions',
                        color_continuous_scale='blues'
                    )
                    fig_sessions.update_xaxes(title="Settimana (LunedÃ¬)")
                    fig_sessions.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_sessions, use_container_width=True)
                else:
                    st.info("Nessun dato disponibile per il grafico sessioni")
            
            with col2:
                st.subheader("ðŸ‘¥ Piloti PiÃ¹ Attivi")
                
                # Query per piloti piÃ¹ attivi
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
                        title="Top 10 Piloti per AttivitÃ ",
                        color='sessions',
                        color_continuous_scale='greens'
                    )
                    fig_active.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_active, use_container_width=True)
                else:
                    st.info("Nessun dato disponibile per il grafico attivitÃ ")
            
            conn.close()
            
        except Exception as e:
            st.error(f"âŒ Errore nel caricamento grafici: {e}")
    
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
                    CASE WHEN start_date IS NULL THEN 1 ELSE 0 END,
                    start_date DESC,
                    championship_id DESC
            """)
            
            championships = cursor.fetchall()
            conn.close()
            
            return championships
            
        except Exception as e:
            st.error(f"âŒ Errore nel recupero campionati: {e}")
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
                    CASE WHEN date_start IS NULL THEN 1 ELSE 0 END,
                    date_start DESC,
                    round_number DESC
            """, (championship_id,))
            
            competitions = cursor.fetchall()
            conn.close()
            
            return competitions
            
        except Exception as e:
            st.error(f"âŒ Errore nel recupero competizioni: {e}")
            return []
    
    def get_competition_results(self, competition_id: int) -> pd.DataFrame:
        """Ottiene risultati competizione"""
        query = """
            SELECT 
                cr.race_position as position,
                d.last_name as driver,
                cr.qualifying_position,
                cr.race_points,
                cr.pole_points,
                cr.fastest_lap_points,
                cr.total_points,
                cr.best_lap_time,
                cr.total_laps,
                cr.is_classified
            FROM competition_results cr
            JOIN drivers d ON cr.driver_id = d.driver_id
            WHERE cr.competition_id = ?
            ORDER BY 
                CASE WHEN cr.race_position IS NULL THEN 1 ELSE 0 END,
                cr.race_position
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
            st.error(f"âŒ Errore nel recupero sessioni: {e}")
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
            st.error(f"âŒ Errore nel recupero competizioni 4Fun: {e}")
            return []
    
    def show_4fun_report(self):
        """Mostra il report competizioni 4Fun"""
        st.header("ðŸŽ® Report Official 4Fun")
        
        # Ottieni lista competizioni 4Fun
        competitions = self.get_4fun_competitions_list()
        
        if not competitions:
            st.warning("âŒ Nessuna competizione 4Fun trovata nel database")
            st.info("""
            **Le competizioni 4Fun sono:**
            - Competizioni con `competition_id` valorizzato
            - Competizioni con `championship_id` NULL (non appartengono a campionati)
            """)
            return
        
        # Prepara opzioni per selectbox
        competition_options = []
        competition_map = {}
        
        for comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed in competitions:
            # Formato display
            round_str = f"R{round_num} - " if round_num else ""
            status_str = " âœ…" if is_completed else " ðŸ”„"
            
            if date_start:
                date_str = f" - {date_start[:10]}"
            else:
                date_str = ""
            
            display_name = f"{round_str}{name} - {track}{date_str}{status_str}"
            
            competition_options.append(display_name)
            competition_map[display_name] = comp_id
        
        # Selectbox competizione (default: prima = piÃ¹ recente)
        selected_competition = st.selectbox(
            "ðŸŽ® Seleziona Competizione 4Fun:",
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
                    <h2>ðŸŽ® {round_str}{name}</h2>
                    <p>ðŸ“ {track} | ðŸ“‹ {weekend_format}</p>
                    {f'<p>ðŸ“… {date_start} - {date_end}</p>' if date_start and date_end else f'<p>ðŸ“… {date_start}</p>' if date_start else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Usa gli stessi metodi delle competizioni di campionato
                self.show_4fun_competition_details(selected_comp_info, competition_id)
    
    def show_4fun_competition_details(self, competition_info: Tuple, competition_id: int):
        """Mostra dettagli competizione 4Fun (usa gli stessi metodi delle competizioni di campionato)"""
        comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed = competition_info
        
        # Risultati competizione (stesso metodo)
        st.subheader("ðŸ† Classifica 4Fun")
        results_df = self.get_competition_results(competition_id)
        
        if not results_df.empty:
            # Formatta risultati per visualizzazione (stesso codice)
            results_display = results_df.copy()
            
            # Aggiungi medaglie
            results_display['Pos'] = results_display['position'].apply(
                lambda x: "ðŸ¥‡" if x == 1 else "ðŸ¥ˆ" if x == 2 else "ðŸ¥‰" if x == 3 else str(int(x)) if pd.notna(x) else "NC"
            )
            
            # Formatta tempi giro
            results_display['Miglior Giro'] = results_display['best_lap_time'].apply(
                lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
            )
            
            # Seleziona e rinomina colonne
            columns_to_show = [
                'Pos', 'driver', 'qualifying_position', 'race_points', 
                'pole_points', 'fastest_lap_points', 'total_points', 'Miglior Giro'
            ]
            
            column_names = {
                'Pos': 'Pos',
                'driver': 'Pilota',
                'qualifying_position': 'Pos Quali',
                'race_points': 'Punti Gara',
                'pole_points': 'Punti Pole',
                'fastest_lap_points': 'Punti GL',
                'total_points': 'Tot Punti',
                'Miglior Giro': 'Miglior Giro'
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
            st.warning("âš ï¸ Risultati competizione 4Fun non ancora calcolati")
        
        # Sessioni della competizione (stesso metodo)
        st.markdown("---")
        st.subheader("ðŸŽ® Sessioni della Competizione 4Fun")
        
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
                    <strong>ðŸ {session_type}</strong> - {date_str} | ðŸ‘¥ {total_drivers} piloti
                    {f'| âš¡ Best: {self.format_lap_time(best_lap_overall)}' if best_lap_overall else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Risultati sessione (stesso metodo)
                session_results_df = self.get_session_results(session_id)
                
                if not session_results_df.empty:
                    # Formatta risultati sessione
                    session_display = session_results_df.copy()
                    
                    # Aggiungi medaglie per primi 3
                    session_display['Pos'] = session_display['position'].apply(
                        lambda x: "ðŸ¥‡" if x == 1 else "ðŸ¥ˆ" if x == 2 else "ðŸ¥‰" if x == 3 else str(int(x)) if pd.notna(x) else "NC"
                    )
                    
                    # Formatta tempo giro
                    session_display['Miglior Giro'] = session_display['best_lap'].apply(
                        lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
                    )
                    
                    # Formatta tempo totale
                    session_display['Tempo Totale'] = session_display['total_time'].apply(
                        lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
                    )
                    
                    # Seleziona colonne da mostrare
                    columns_to_show = ['Pos', 'race_number', 'driver', 'lap_count', 'Miglior Giro', 'Tempo Totale']
                    column_names = {
                        'Pos': 'Pos',
                        'race_number': 'Num#',
                        'driver': 'Pilota',
                        'lap_count': 'Giri',
                        'Miglior Giro': 'Miglior Giro',
                        'Tempo Totale': 'Tempo Totale'
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
                    st.warning(f"âš ï¸ Nessun risultato trovato per {session_type}")
                
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.warning("âŒ Nessuna sessione trovata per questa competizione 4Fun")
    
    def show_4fun_charts(self, results_df: pd.DataFrame):
        """Mostra grafici specifici per competizioni 4Fun"""
        if results_df.empty:
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("ðŸ“Š Distribuzione Punti 4Fun")
            
            # Grafico punti totali (solo chi ha punti > 0)
            points_data = results_df[results_df['total_points'] > 0].copy()
            if not points_data.empty:
                # Ordina per visualizzazione orizzontale
                points_data = points_data.sort_values('total_points', ascending=True)
                
                fig_points = px.bar(
                    points_data,
                    x='total_points',
                    y='driver',
                    orientation='h',
                    title="Punti Totali per Pilota",
                    color='total_points',
                    color_continuous_scale='viridis'
                )
                fig_points.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_points, use_container_width=True)
            else:
                st.info("Nessun punto assegnato ancora")
        
        with col2:
            st.subheader("âš¡ Performance Qualifiche vs Gara")
            
            # Scatter plot qualifiche vs gara (solo piloti classificati)
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
                    title="Posizione Qualifica vs Posizione Gara",
                    labels={
                        'qualifying_position': 'Posizione Qualifica',
                        'position': 'Posizione Gara'
                    }
                )
                
                # Aggiungi linea di riferimento (stesso piazzamento)
                max_pos = max(scatter_data['qualifying_position'].max(), scatter_data['position'].max())
                fig_scatter.add_shape(
                    type="line",
                    x0=1, y0=1, x1=max_pos, y1=max_pos,
                    line=dict(color="red", width=2, dash="dash"),
                )
                
                fig_scatter.update_layout(height=400)
                fig_scatter.update_yaxes(autorange="reversed")  # Posizione 1 in alto
                fig_scatter.update_xaxes(autorange="reversed")  # Posizione 1 a sinistra
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Dati insufficienti per il grafico performance")

    def show_championships_report(self):
        """Mostra il report campionati"""
        st.header("ðŸ† Report Campionati")
        
        # Ottieni lista campionati
        championships = self.get_championships_list()
        
        if not championships:
            st.warning("âŒ Nessun campionato trovato nel database")
            return
        
        # Prepara opzioni per selectbox
        championship_options = []
        championship_map = {}
        
        for champ_id, name, season, start_date, end_date, is_completed, description in championships:
            # Formato display
            season_str = f" ({season})" if season else ""
            status_str = " âœ…" if is_completed else " ðŸ”„"
            
            if start_date:
                date_str = f" - {start_date[:10]}"
            else:
                date_str = ""
            
            display_name = f"{name}{season_str}{date_str}{status_str}"
            
            championship_options.append(display_name)
            championship_map[display_name] = champ_id
        
        # Selectbox campionato
        selected_championship = st.selectbox(
            "ðŸ† Seleziona Campionato:",
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
                    <h2>ðŸ† {name}{season_info}</h2>
                """
                
                if description:
                    header_html += f"<p>{description}</p>"
                
                if start_date and end_date:
                    header_html += f"<p>ðŸ“… {start_date} - {end_date}</p>"
                
                header_html += "</div>"
                
                st.markdown(header_html, unsafe_allow_html=True)
                
                # Classifica campionato
                st.subheader("ðŸ“Š Classifica Campionato")
                standings_df = self.get_championship_standings(championship_id)
                
                if not standings_df.empty:
                    # Formatta classifica per visualizzazione
                    standings_display = standings_df.copy()
                    
                    # Aggiungi medaglie per primi 3
                    standings_display['Pos'] = standings_display['position'].apply(
                        lambda x: "ðŸ¥‡" if x == 1 else "ðŸ¥ˆ" if x == 2 else "ðŸ¥‰" if x == 3 else str(x)
                    )
                    
                    # Seleziona colonne da mostrare
                    columns_to_show = [
                        'Pos', 'driver', 'total_points', 'competitions_participated', 
                        'wins', 'podiums', 'poles', 'fastest_laps'
                    ]
                    
                    # Rinomina colonne
                    column_names = {
                        'Pos': 'Pos',
                        'driver': 'Pilota',
                        'total_points': 'Punti',
                        'competitions_participated': 'Gare',
                        'wins': 'Vittorie',
                        'podiums': 'Podi',
                        'poles': 'Pole',
                        'fastest_laps': 'Giri Veloci'
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
                                title="Vittorie per Pilota nel Campionato",
                                color='wins',
                                color_continuous_scale='reds'
                            )
                            fig_wins.update_layout(height=400, showlegend=False)
                            st.plotly_chart(fig_wins, use_container_width=True)
                        else:
                            st.info("Nessuna vittoria registrata ancora")
                    
                    with col2:
                        # Grafico distribuzione podi
                        podiums_data = standings_df[standings_df['podiums'] > 0]
                        if not podiums_data.empty:
                            fig_podiums = px.pie(
                                podiums_data,
                                names='driver',
                                values='podiums',
                                title="Distribuzione Podi"
                            )
                            fig_podiums.update_layout(height=400)
                            st.plotly_chart(fig_podiums, use_container_width=True)
                        else:
                            st.info("Nessun podio registrato ancora")
                
                else:
                    st.warning("âš ï¸ Classifica campionato non ancora calcolata")
                
                # Selezione competizione
                st.markdown("---")
                self.show_competition_selection(championship_id)
    
    def show_competition_selection(self, championship_id: int):
        """Mostra selezione e dettagli competizione"""
        st.subheader("ðŸ Competizioni del Campionato")
        
        # Ottieni competizioni
        competitions = self.get_championship_competitions(championship_id)
        
        if not competitions:
            st.warning("âŒ Nessuna competizione trovata per questo campionato")
            return
        
        # Prepara opzioni per selectbox
        competition_options = ["Seleziona una competizione..."]
        competition_map = {}
        
        for comp_id, name, track, round_num, date_start, date_end, weekend_format, is_completed in competitions:
            # Formato display
            round_str = f"R{round_num} - " if round_num else ""
            status_str = " âœ…" if is_completed else " ðŸ”„"
            date_str = f" ({date_start[:10]})" if date_start else ""
            
            display_name = f"{round_str}{name} - {track}{date_str}{status_str}"
            
            competition_options.append(display_name)
            competition_map[display_name] = comp_id
        
        # Selectbox competizione
        selected_competition = st.selectbox(
            "ðŸ Seleziona Competizione:",
            options=competition_options,
            index=0,
            key="competition_select"
        )
        
        if selected_competition and selected_competition != "Seleziona una competizione...":
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
            <h3>ðŸ {round_str}{name}</h3>
            <p>ðŸ“ {track} | ðŸ“‹ {weekend_format} | ðŸ“… {date_start}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Risultati competizione
        st.subheader("ðŸ† Classifica Competizione")
        results_df = self.get_competition_results(competition_id)
        
        if not results_df.empty:
            # Formatta risultati per visualizzazione
            results_display = results_df.copy()
            
            # Aggiungi medaglie
            results_display['Pos'] = results_display['position'].apply(
                lambda x: "ðŸ¥‡" if x == 1 else "ðŸ¥ˆ" if x == 2 else "ðŸ¥‰" if x == 3 else str(int(x)) if pd.notna(x) else "NC"
            )
            
            # Formatta tempi giro
            results_display['Miglior Giro'] = results_display['best_lap_time'].apply(
                lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
            )
            
            # Seleziona e rinomina colonne
            columns_to_show = [
                'Pos', 'driver', 'qualifying_position', 'race_points', 
                'pole_points', 'fastest_lap_points', 'total_points', 'Miglior Giro'
            ]
            
            column_names = {
                'Pos': 'Pos',
                'driver': 'Pilota',
                'qualifying_position': 'Pos Quali',
                'race_points': 'Punti Gara',
                'pole_points': 'Punti Pole',
                'fastest_lap_points': 'Punti GL',
                'total_points': 'Tot Punti',
                'Miglior Giro': 'Miglior Giro'
            }
            
            results_display = results_display[columns_to_show]
            results_display.columns = [column_names[col] for col in columns_to_show]
            
            st.dataframe(
                results_display,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("âš ï¸ Risultati competizione non ancora calcolati")
        
        # Sessioni della competizione
        st.markdown("---")
        st.subheader("ðŸŽ® Sessioni della Competizione")
        
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
                    <strong>ðŸ {session_type}</strong> - {date_str} | ðŸ‘¥ {total_drivers} piloti
                    {f'| âš¡ Best: {self.format_lap_time(best_lap_overall)}' if best_lap_overall else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Risultati sessione
                session_results_df = self.get_session_results(session_id)
                
                if not session_results_df.empty:
                    # Formatta risultati sessione
                    session_display = session_results_df.copy()
                    
                    # Aggiungi medaglie per primi 3
                    session_display['Pos'] = session_display['position'].apply(
                        lambda x: "ðŸ¥‡" if x == 1 else "ðŸ¥ˆ" if x == 2 else "ðŸ¥‰" if x == 3 else str(int(x)) if pd.notna(x) else "NC"
                    )
                    
                    # Formatta tempo giro
                    session_display['Miglior Giro'] = session_display['best_lap'].apply(
                        lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
                    )
                    
                    # Formatta tempo totale
                    session_display['Tempo Totale'] = session_display['total_time'].apply(
                        lambda x: self.format_lap_time(x) if pd.notna(x) else "N/A"
                    )
                    
                    # Seleziona colonne da mostrare
                    columns_to_show = ['Pos', 'race_number', 'driver', 'lap_count', 'Miglior Giro', 'Tempo Totale']
                    column_names = {
                        'Pos': 'Pos',
                        'race_number': 'Num#',
                        'driver': 'Pilota',
                        'lap_count': 'Giri',
                        'Miglior Giro': 'Miglior Giro',
                        'Tempo Totale': 'Tempo Totale'
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
                    st.warning(f"âš ï¸ Nessun risultato trovato per {session_type}")
                
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.warning("âŒ Nessuna sessione trovata per questa competizione")


def main():
    """Funzione principale dell'applicazione"""
    try:
        # Inizializza dashboard
        dashboard = ACCWebDashboard()
        
        # Sidebar per navigazione
        st.sidebar.title("ðŸ Navigazione")
        
        # Info versione per admin (solo in locale)
        if not dashboard.is_github_deployment:
            st.sidebar.markdown("---")
            st.sidebar.markdown("**ðŸ”§ ModalitÃ  Sviluppo**")
            st.sidebar.markdown(f"DB: `{os.path.basename(dashboard.db_path)}`")
        
        # Menu principale
        page = st.sidebar.selectbox(
            "Seleziona pagina:",
            [
                "ðŸ  Homepage",
                "ðŸ† Report Campionati",
                "ðŸŽ® Report Official 4Fun",
                "ðŸ Report Piste",
                "ðŸ‘¤ Report Piloti",
                "ðŸ“Š Statistiche Avanzate"
            ]
        )
        
        # Routing pagine
        if page == "ðŸ  Homepage":
            dashboard.show_homepage()
        
        elif page == "ðŸ† Report Campionati":
            dashboard.show_championships_report()
        
        elif page == "ðŸŽ® Report Official 4Fun":
            dashboard.show_4fun_report()
        
        elif page == "ðŸ Report Piste":
            st.header("ðŸ Report Piste")
            st.info("ðŸš§ Sezione in sviluppo - sarÃ  implementata prossimamente")
        
        elif page == "ðŸ‘¤ Report Piloti":
            st.header("ðŸ‘¤ Report Piloti")
            st.info("ðŸš§ Sezione in sviluppo - sarÃ  implementata prossimamente")
        
        elif page == "ðŸ“Š Statistiche Avanzate":
            st.header("ðŸ“Š Statistiche Avanzate")
            st.info("ðŸš§ Sezione in sviluppo - sarÃ  implementata prossimamente")
        
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            <p>ðŸ ACC Server Dashboard</p>
            <p>Community: {dashboard.config['community']['name']}</p>
            {f'<p>ðŸŒ Cloud Deployment</p>' if dashboard.is_github_deployment else '<p>ðŸ  Sviluppo Locale</p>'}
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error("âŒ **Errore Critico nell'Applicazione**")
        st.error(f"Dettagli: {str(e)}")
        
        # Informazioni di debug solo in locale
        if not os.getenv('STREAMLIT_SHARING'):
            st.code(f"Traceback: {e}", language="text")
        
        st.markdown("""
        ### ðŸ”§ Possibili Soluzioni:
        1. Verifica che il database sia presente e valido
        2. Controlla il file di configurazione
        3. Ricarica la pagina
        4. Contatta l'amministratore se il problema persiste
        """)


if __name__ == "__main__":
    main()