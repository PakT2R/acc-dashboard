# CLAUDE.md - ACC Dashboard

## Project Overview

**ACC Dashboard** is a Streamlit-based web dashboard for the TFL3 (TIER Friends League GT3 - ITA) racing community. It provides data visualization and management for Assetto Corsa Competizione (ACC) racing league statistics, standings, and race results.

**Author:** PakT2R
**Community:** TFL3 - TIER Friends League GT3 (ITA)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run dashboard_acc.py
```

## Project Structure

```
acc-dashboard/
├── dashboard_acc.py          # Main application (single-file architecture)
├── acc_config_d.json         # Configuration (community info, database path)
├── acc_stats.db              # SQLite database with all racing data
├── requirements.txt          # Python dependencies
├── tfl3_regolamento.html     # Official league rulebook (Italian)
├── banner.jpg                # Community banner image
└── CLAUDE.md                 # This file
```

**Note:** This is a single-file application. All application logic is contained in `dashboard_acc.py`.

## Technology Stack

- **Framework:** Streamlit >= 1.28.0
- **Language:** Python 3
- **Database:** SQLite3
- **Data Processing:** Pandas >= 2.0.0
- **Visualization:** Plotly >= 5.18.0
- **HTTP:** requests >= 2.31.0

## Architecture

### Main Class: `ACCWebDashboard`

The entire application is encapsulated in a single class with ~55 methods organized into categories:

1. **Core Methods** - Configuration, database access, initialization
2. **Data Retrieval** - SQL queries returning DataFrames
3. **Formatting** - Time/date formatting utilities
4. **Page Display** - UI components for each dashboard page
5. **Chart Generation** - Plotly visualizations
6. **UI Helpers** - Reusable components

### Application Pages

| Page | Method | Description |
|------|--------|-------------|
| Homepage | `show_homepage()` | Community info, stats summary, rulebook |
| Time Attack | `show_time_attack_report()` | Time attack competition results |
| Race Results | `show_race_results()` | Competition results and session details |
| Standings | `show_leagues_report()` | Championship and league standings |
| All Sessions | `show_sessions_report()` | Session history and participation |
| Best Laps | `show_best_laps_report()` | Track leaderboards and lap records |
| Drivers | `show_drivers_report()` | Driver profiles and statistics |
| Statistics | `show_statistics()` | (Under development) |

## Database Schema

The SQLite database (`acc_stats.db`) contains 18 tables:

### Core Tables
- **drivers** - Driver profiles (333 records)
- **sessions** - Racing sessions (121 records)
- **session_results** - Results per driver per session (888 records)
- **laps** - Individual lap data (3,954 records)

### Competition Structure
- **leagues** - Overall league/season
- **championships** - Multi-tier championships
- **competitions** - Individual race events/rounds

### Standings
- **league_standings** - League-wide points
- **championship_standings** - Championship points
- **competition_standings** - Per-competition standings

### Supporting Tables
- **car_models** - Vehicle database
- **penalties** - Race penalties
- **manual_penalties** - Administrative penalties
- **points_systems** - Point calculation rules
- **time_attack_results** - Time attack scores
- **bad_driver_reports** - Behavior reports
- **synced_files** - Data sync tracking

## Key Conventions

### Code Style
- **Language:** Code comments and UI text in Italian (community language)
- **Single-file architecture:** All code in `dashboard_acc.py`
- **Class-based design:** One main class `ACCWebDashboard`
- **SQL queries:** Always use parameterized queries via `safe_sql_query()`

### Time Formatting
- Lap times stored as milliseconds in database
- Display format: `MM:SS.sss` (e.g., `1:45.123`)
- Use `format_lap_time()` for conversion

### Session Types
- `R` = Gara (Race)
- `Q` = Qualifiche (Qualifying)
- `FP` = Prove Libere (Free Practice)

### Database Access Pattern
```python
# Always use safe_sql_query for database operations
df = self.safe_sql_query("""
    SELECT column FROM table WHERE id = ?
""", (param_value,))
```

### Error Handling
- Graceful fallbacks for missing data/files
- `safe_sql_query()` returns empty DataFrame on error
- Configuration fallback system for different deployments

## Development Guidelines

### Adding New Pages
1. Create a new `show_<page_name>()` method in `ACCWebDashboard`
2. Add navigation entry in `main()` function's sidebar menu
3. Add routing case in the page selection logic

### Adding New Data Queries
1. Create method following pattern: `get_<data_type>()`
2. Use `safe_sql_query()` for database access
3. Return pandas DataFrame
4. Handle empty results gracefully

### Modifying UI Components
- Custom CSS is injected via `inject_custom_css()`
- Mobile breakpoints at 768px
- Use Streamlit columns for layout
- Plotly for interactive charts

## Deployment

### Supported Platforms
- Streamlit Cloud
- Heroku
- Railway
- Render
- Vercel
- Netlify
- GitHub Actions

### Environment Detection
The app auto-detects deployment environment via `detect_github_deployment()` and adjusts configuration paths accordingly.

### Configuration
- Local: Uses `acc_config_d.json` directly
- Cloud: Supports environment variable overrides

## Testing

No automated testing framework is currently implemented. Testing is done manually.

## Common Tasks

### Update Database
Database updates are typically automated via sync scripts (see commit history pattern).

### Modify Point System
Points systems are stored in `points_systems` table. Modify via SQL or create new entries for new seasons.

### Add New Driver
Drivers are auto-populated from session results data during sync operations.

## Notes for AI Assistants

1. **Single-file architecture** - All changes go in `dashboard_acc.py`
2. **Italian language** - UI text and some comments are in Italian
3. **SQL safety** - Always use parameterized queries
4. **Streamlit patterns** - Follow existing method patterns for UI components
5. **No tests** - Be extra careful with changes; test manually
6. **Database is live data** - Don't modify database directly without understanding impact
7. **Configuration fallbacks** - Consider both local and cloud deployment scenarios
