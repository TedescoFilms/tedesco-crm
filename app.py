import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
import time
import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="TedescoFilms CRM", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")

# --- CSS: ESTETICA AVANZATA (MENU A BOTTONI) ---
st.markdown("""
<style>
    /* 1. SFONDO BLU GRADIENTE */
    .stApp {
        background: linear-gradient(to right, #141e30, #243b55) !important; /* Blu più profondo e cinematografico */
        color: white !important;
    }

    /* 2. MENU DI NAVIGAZIONE (TRASFORMAZIONE RADIO IN TABS) */
    /* Nasconde i pallini brutti */
    div[data-testid="stRadio"] > label > div:first-child {
        display: none;
    }
    
    /* Contenitore del menu */
    div[data-testid="stRadio"] {
        background-color: transparent;
        border: none;
    }
    
    /* Gruppo orizzontale */
    div[role="radiogroup"] {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }

    /* STILE DEI BOTTONI DEL MENU (Le scritte) */
    div[data-testid="stRadio"] label {
        background-color: rgba(255, 255, 255, 0.05); /* Sfondo leggero */
        padding: 10px 20px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        font-weight: 500;
        color: #ccc !important;
        min-width: 110px; /* Larghezza minima per uniformità */
        justify-content: center;
    }

    /* Effetto Hover (Passaggio del mouse) */
    div[data-testid="stRadio"] label:hover {
        background-color: rgba(255, 255, 255, 0.15);
        border-color: white;
        color: white !important;
        transform: translateY(-2px); /* Si alza leggermente */
    }

    /* BOTTONE ATTIVO (Quello selezionato) - Usa selettore avanzato */
    div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, #e50914, #b20710) !important; /* Rosso Netflix */
        color: white !important;
        border: 1px solid #ff4b4b !important;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4); /* Alone rosso */
        transform: scale(1.05);
    }

    /* 3. INPUT E CASELLE (Migliorati) */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #0a0a0a !important; 
        color: #e0e0e0 !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    /* Focus sugli input */
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #e50914 !important;
        box-shadow: 0 0 5px rgba(229, 9, 20, 0.5);
    }
    
    /* 4. TABELLE E CARD PROGETTO */
    div[data-testid="stDataFrame"], .project-card {
        background: rgba(0, 0, 0, 0.4) !important;
        backdrop-filter: blur(10px); /* Effetto vetro sfocato */
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 5. TESTI E TITOLI */
    h1, h2, h3 { 
        font-family: 'Helvetica Neue', sans-serif; 
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* 6. EXPANDER (Migliorato) */
    .streamlit-expanderHeader {
        background-color: #1a1a1a !important;
        color: white !important;
        border-radius: 6px;
        border: 1px solid #333;
    }
    
    /* 7. BOTTONI D'AZIONE (Salva, Crea) */
    .stButton button {
        background: linear-gradient(to bottom, #e50914, #c90812) !important;
        color: white !important;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        transition: transform 0.1s;
    }
    .stButton button:active {
        transform: scale(0.98);
    }
    
    /* NASCONDI MENU STREAMLIT IN ALTO A DESTRA */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    section[data-testid="stSidebar"] { display: none; }
    
</style>
""", unsafe_allow_html=True)

# --- DATABASE E INIT ---
def get_connection(): return sqlite3.connect('tedesco_films.db')

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Tabelle esistenti
    c.execute("CREATE TABLE IF NOT EXISTS clienti (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_azienda TEXT, nome_cognome TEXT, telefono TEXT, email TEXT, tipo TEXT, cf_piva TEXT, indirizzo TEXT, pec TEXT, sdi TEXT, note TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS progetti (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, nome_progetto TEXT, prezzo REAL, fee_commerciale REAL, stato TEXT, data_creazione DATE, anno INTEGER, categoria_progetto TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS spese_progetto (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, voce_spesa TEXT, costo REAL, categoria TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS dettagli_produzione (project_id INTEGER PRIMARY KEY, note_regia TEXT, organizzazione TEXT, lista_attrezzatura TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS fornitori (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_cognome TEXT, categoria TEXT, paese TEXT, telefono TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS utenti (username TEXT PRIMARY KEY, password TEXT, ruolo TEXT)")
    
       # Creazione Admin di default (Password presa dai Secrets)
    try:
        # Prendo user e pass dalla cassaforte segreta
        safe_user = st.secrets["admin_user"]
        safe_pass = st.secrets["admin_password"]
        c.execute("INSERT INTO utenti (username, password, ruolo) VALUES (?, ?, 'admin')", (safe_user, safe_pass))
    except: pass 

    
    # Migrazioni colonne se mancano
    try: c.execute("ALTER TABLE progetti ADD COLUMN fee_commerciale REAL"); 
    except: pass
    try: c.execute("ALTER TABLE clienti ADD COLUMN tag_categoria TEXT"); 
    except: pass
    try: c.execute("ALTER TABLE fornitori ADD COLUMN costo_servizio REAL"); 
    except: pass
    try: c.execute("ALTER TABLE clienti ADD COLUMN cap TEXT"); 
    except: pass
    try: c.execute("ALTER TABLE clienti ADD COLUMN citta TEXT"); 
    except: pass
    
    conn.commit()
    conn.close()

init_db()

# --- FUNZIONI AUTH ---
def login(user, pw):
    conn = get_connection()
    u = pd.read_sql_query("SELECT * FROM utenti WHERE username=? AND password=?", conn, params=(user, pw))
    conn.close()
    if not u.empty:
        return u.iloc[0]['ruolo']
    return None

# --- LOGICA LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['role'] = None

if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br><br><h2 style='text-align:center;'>🔐 TEDESCO FILMS LOGIN</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            usr = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            sub = st.form_submit_button("ACCEDI")
            if sub:
                role = login(usr, pwd)
                if role:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = usr
                    st.session_state['role'] = role
                    st.rerun()
                else:
                    st.error("Credenziali errate")
    st.stop() 

# --- APP PRINCIPALE (SOLO SE LOGGATO) ---

# --- HEADER CON LOGO (SENZA SFONDO BIANCO) ---
c_head_1, c_head_2 = st.columns([1, 4])

with c_head_1:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(current_dir, "logo1.png")
    
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            # Ho tolto il div con sfondo bianco, ora l'immagine è libera
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: center;">
                    <img src="data:image/jpeg;base64,{encoded}" style="width: 100%; max-width: 180px; border-radius: 10px;">
                </div>
                """, 
                unsafe_allow_html=True
            )
        except:
            st.error("Errore lettura logo")
    else:
        st.markdown("### 🎬 TEDESCO FILMS")

with c_head_2:
    st.write("")
    if st.session_state['role'] == 'europastudio':
        menu_items = ["PROGETTI", "CLIENTI"]
    else:
        menu_items = ["DASHBOARD", "PROGETTI", "CLIENTI", "FORNITORI"]
    
    selected = st.radio("MENU", menu_items, horizontal=True)



# Logout button
with st.sidebar:
    st.write(f"Utente: {st.session_state['username']} ({st.session_state['role']})")
    if st.button("LOGOUT"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- PAGINE ---

# 1. DASHBOARD
if selected == "DASHBOARD":
    st.markdown(f"### 📊 Benvenuto, {st.session_state['username']}")
    
    # SEZIONE ADMIN
    if st.session_state['role'] == 'admin':
        conn = get_connection()
        
        # KPI ECONOMICI
        df_p = pd.read_sql_query("SELECT * FROM progetti", conn)
        spese_tot = pd.read_sql_query("SELECT SUM(costo) as tot FROM spese_progetto", conn).iloc[0]['tot'] or 0
        
        if not df_p.empty:
            df_p['prezzo'] = df_p['prezzo'].fillna(0)
            df_p['fee_commerciale'] = df_p['fee_commerciale'].fillna(0)
            lordo = df_p['prezzo'].sum()
            fee = df_p['fee_commerciale'].sum()
            netto = lordo - fee - spese_tot
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("FATTURATO", f"€ {lordo:,.0f}")
            c2.metric("COMMISSIONI", f"€ {fee:,.0f}")
            c3.metric("COSTI VIVI", f"€ {spese_tot:,.0f}")
            c4.metric("UTILE NETTO", f"€ {netto:,.0f}")
        
        st.markdown("---")
        
        # GESTIONE UTENTI
        with st.expander("👮 GESTIONE UTENTI"):
            c_u1, c_u2 = st.columns(2)
            with c_u1:
                st.markdown("##### Aggiungi Utente")
                with st.form("new_user"):
                    nu = st.text_input("Nuovo Username")
                    np = st.text_input("Nuova Password")
                    nr = st.selectbox("Ruolo", ["admin", "staff", "europastudio"])
                    if st.form_submit_button("Crea Utente"):
                        try:
                            conn.execute("INSERT INTO utenti (username, password, ruolo) VALUES (?,?,?)", (nu, np, nr))
                            conn.commit()
                            st.success(f"Utente {nu} creato con ruolo {nr}!")
                        except:
                            st.error("Utente già esistente.")
            with c_u2:
                st.markdown("##### Utenti Attivi")
                users = pd.read_sql_query("SELECT username, ruolo FROM utenti", conn)
                st.dataframe(users, hide_index=True)
        
        conn.close()
    else:
        st.info("👋 Ciao! Vai nella sezione PROGETTI per le note tecniche.")

# 2. PROGETTI
# --- SEZIONE PROGETTI AGGIORNATA (EUROPA STUDIO GESTISCE BUDGET) ---
elif selected == "PROGETTI":
    conn = get_connection()
    col_sx, col_dx = st.columns([1, 2])
    
    # --- COLONNA SINISTRA: ARCHIVIO ---
    with col_sx:
        st.markdown("#### 📂 Archivio")
        
        # CREAZIONE (Admin + EuropaStudio)
        if st.session_state['role'] in ['admin', 'europastudio']:
            with st.expander("➕ CREA NUOVO", expanded=False):
                df_c = pd.read_sql_query("SELECT * FROM clienti", conn)
                if not df_c.empty:
                    # Filtra clienti se Europa Studio
                    if st.session_state['role'] == 'europastudio':
                        df_c = df_c[df_c['tag_categoria'] == 'EUROPA STUDIO']
                    
                    if not df_c.empty:
                        df_c['d'] = df_c.apply(lambda x: x['nome_azienda'] or x['nome_cognome'], axis=1)
                        cs = st.selectbox("Cliente", df_c['d'])
                        np = st.text_input("Nome Progetto")
                        
                        # ORA TUTTI (Admin e EuropaStudio) POSSONO INSERIRE IL BUDGET
                        pp = st.number_input("Budget (€)", step=100.0)
                        fee = st.number_input("Fee (€)", step=50.0)
                        
                        # Categoria: Admin sceglie, Europa Studio è bloccato
                        if st.session_state['role'] == 'europastudio':
                            cat = "EUROPA STUDIO"
                            st.info(f"Categoria fissata: {cat}")
                        else:
                            cat = st.selectbox("Cat", ["EUROPA STUDIO", "VIDEO MUSICALI", "WEDDING", "COMMERCIALE", "ALTRO"])
                        
                        anno = st.number_input("Anno", value=2026)
                        
                        if st.button("Crea"):
                            cid = df_c[df_c['d']==cs].iloc[0]['id']
                            conn.execute("INSERT INTO progetti (cliente_id, nome_progetto, prezzo, fee_commerciale, stato, anno, categoria_progetto) VALUES (?,?,?,?,'Preventivo',?,?)", (int(cid), np, pp, fee, anno, cat))
                            conn.commit()
                            st.rerun()
                    else: st.warning("Nessun cliente disponibile. Creane uno nella sezione Clienti.")
                else: st.warning("Manca Cliente")
        
        # FILTRI
        if st.session_state['role'] == 'europastudio':
            query = "SELECT * FROM progetti WHERE categoria_progetto='EUROPA STUDIO' ORDER BY id DESC"
        else:
            query = "SELECT * FROM progetti ORDER BY id DESC"
            
        df_all = pd.read_sql_query(query, conn)
        pid = None 
        
        if not df_all.empty:
            df_all['anno'] = df_all['anno'].fillna(2026).astype(int)
            df_all['categoria_progetto'] = df_all['categoria_progetto'].fillna("ALTRO")
            
            anni_disp = sorted(df_all['anno'].unique(), reverse=True)
            sa = st.selectbox("📅 Anno", anni_disp)
            
            cats_nel_db = sorted(df_all[df_all['anno']==sa]['categoria_progetto'].unique())
            cats_list = ["TUTTI"] + cats_nel_db
            sc = st.radio("📂 Categoria", cats_list)
            
            if sc == "TUTTI": projs = df_all[df_all['anno']==sa]
            else: projs = df_all[(df_all['anno']==sa) & (df_all['categoria_progetto']==sc)]
            
            opts = {f"{r['nome_progetto']}": r['id'] for _, r in projs.iterrows()}
            if opts:
                st.markdown("---")
                sel_label = st.radio("Seleziona Progetto:", list(opts.keys()), label_visibility="collapsed")
                pid = opts[sel_label]
            else: st.info("Nessun progetto qui.")
        else: st.info("Archivio vuoto.")

    # --- COLONNA DESTRA: DETTAGLIO ---
    with col_dx:
        if pid:
            proj = pd.read_sql_query("SELECT * FROM progetti WHERE id=?", conn, params=(pid,)).iloc[0]
            
            st.markdown(f"""
            <div class="project-card">
                <h2 style='margin:0; color:white;'>🎬 {proj['nome_progetto']}</h2>
                <p style='color:#ccc; margin:0;'>{proj['categoria_progetto']} | {proj['anno']} | Stato: {proj['stato']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # INFO AMMINISTRATIVA (ADMIN + EUROPA STUDIO ORA VEDONO I SOLDI)
            if st.session_state['role'] in ['admin', 'europastudio']:
                c1, c2, c3, c4 = st.columns(4)
                
                curr = proj['stato'] or "Preventivo"
                poss = ["Preventivo", "Produzione", "Consegnato", "Pagato"]
                idx_st = poss.index(curr) if curr in poss else 0
                ns = c1.selectbox("Stato", poss, index=idx_st, key=f"st_{pid}")
                
                if ns != curr:
                    conn.execute("UPDATE progetti SET stato=? WHERE id=?", (ns, pid))
                    conn.commit()
                    st.rerun()
                
                spese_q = pd.read_sql_query("SELECT SUM(costo) as tot FROM spese_progetto WHERE project_id=?", conn, params=(pid,))
                spese_val = spese_q.iloc[0]['tot'] if not spese_q.empty and spese_q.iloc[0]['tot'] else 0
                utile = (proj['prezzo'] or 0) - (proj['fee_commerciale'] or 0) - spese_val
                
                c2.metric("Budget", f"€ {proj['prezzo']:,.0f}")
                c3.metric("Fee", f"€ {proj['fee_commerciale']:,.0f}")
                c4.metric("UTILE", f"€ {utile:,.0f}")
                
                tabs = st.tabs(["💰 COSTI", "📝 NOTE TECNICHE", "🎬 REGIA/ODG", "🎥 NOLEGGIO", "🛠 EQUIP", "📄 PDF"])
                
                # Definisco i tabs per chi ha i permessi di gestione
                t_costi = tabs[0]
                t_tech, t_odg, t_rent, t_eq, t_pdf = tabs[1], tabs[2], tabs[3], tabs[4], tabs[5]
                
                # GESTIONE COSTI (Abilitata per Admin e Europa Studio)
                with t_costi:
                    c_in, c_out = st.columns(2)
                    with c_in:
                        with st.form(f"sp_{pid}"):
                            v = st.text_input("Voce")
                            c = st.number_input("€", step=10.0)
                            k = st.selectbox("Cat", ["Noleggio", "Crew", "Logistica", "Altro"])
                            if st.form_submit_button("Add"):
                                conn.execute("INSERT INTO spese_progetto (project_id, voce_spesa, costo, categoria) VALUES (?,?,?,?)", (pid, v, c, k))
                                conn.commit()
                                st.rerun()
                    with c_out:
                        sp = pd.read_sql_query("SELECT * FROM spese_progetto WHERE project_id=?", conn, params=(pid,))
                        if not sp.empty: st.dataframe(sp[['voce_spesa', 'costo']], hide_index=True)
            
            else:
                # VISTA STAFF (Senza soldi)
                st.info(f"Stato Progetto: {proj['stato']}")
                tabs = st.tabs(["📝 NOTE TECNICHE", "🎬 REGIA/ODG", "🎥 NOLEGGIO LISTA", "🛠 EQUIP", "⛔ COSTI", "📄 PDF"])
                with tabs[4]: st.error("Accesso Negato")
                t_tech, t_odg, t_rent, t_eq, t_pdf = tabs[0], tabs[1], tabs[2], tabs[3], tabs[5]

            # --- CONTENUTI COMUNI ---
            dett = pd.read_sql_query("SELECT * FROM dettagli_produzione WHERE project_id=?", conn, params=(pid,))
            if dett.empty:
                conn.execute("INSERT INTO dettagli_produzione (project_id, note_regia, organizzazione, lista_attrezzatura) VALUES (?, '', '', '')", (pid,))
                conn.commit()
                dett = pd.read_sql_query("SELECT * FROM dettagli_produzione WHERE project_id=?", conn, params=(pid,))
            row = dett.iloc[0]

            with t_tech:
                nt = st.text_area("Specifiche", value=row['note_regia'], height=300, key=f"nt_{pid}")
                if st.button("Salva Note", key=f"btn_nt_{pid}"):
                    conn.execute("UPDATE dettagli_produzione SET note_regia=? WHERE project_id=?", (nt, pid))
                    conn.commit()
                    st.toast("Salvato")

            with t_odg:
                odg = st.text_area("ODG", value=row['organizzazione'], height=300, key=f"odg_{pid}")
                if st.button("Salva ODG", key=f"btn_odg_{pid}"):
                    conn.execute("UPDATE dettagli_produzione SET organizzazione=? WHERE project_id=?", (odg, pid))
                    conn.commit()
                    st.toast("Salvato")
            
            with t_rent:
                rentals = pd.read_sql_query("SELECT voce_spesa FROM spese_progetto WHERE project_id=? AND categoria='Noleggio'", conn, params=(pid,))
                if not rentals.empty:
                    st.dataframe(rentals, use_container_width=True, hide_index=True)
                else: st.info("Nessun noleggio inserito nei Costi.")

            with t_eq:
                eq = st.text_area("Lista Materiale", value=row['lista_attrezzatura'], height=400, key=f"eq_{pid}")
                if st.button("Salva Equip", key=f"btn_eq_{pid}"):
                    conn.execute("UPDATE dettagli_produzione SET lista_attrezzatura=? WHERE project_id=?", (eq, pid))
                    conn.commit()
                    st.toast("Salvato")
            
            with t_pdf:
                st.markdown("### 📄 Genera PDF Progetto")
                if st.button("⬇️ SCARICA PDF", key=f"pdf_{pid}"):
                    try:
                        from reportlab.lib.pagesizes import A4
                        from reportlab.lib.styles import getSampleStyleSheet
                        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                        from reportlab.lib import colors
                        from io import BytesIO
                        
                        buffer = BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=A4)
                        story = []
                        styles = getSampleStyleSheet()
                        
                        story.append(Paragraph(f"🎬 {proj['nome_progetto']}", styles['Heading1']))
                        story.append(Paragraph(f"Categoria: {proj['categoria_progetto']} | Anno: {proj['anno']}", styles['Normal']))
                        story.append(Spacer(1, 12))
                        
                        if row['note_regia']:
                            story.append(Paragraph("<b>🛠 Note Tecniche</b>", styles['Heading2']))
                            story.append(Paragraph(row['note_regia'].replace('\n', '<br/>'), styles['Normal']))
                            story.append(Spacer(1, 12))
                        
                        if row['organizzazione']:
                            story.append(Paragraph("<b>🎬 Regia & ODG</b>", styles['Heading2']))
                            story.append(Paragraph(row['organizzazione'].replace('\n', '<br/>'), styles['Normal']))
                            story.append(Spacer(1, 12))
                        
                        rentals = pd.read_sql_query("SELECT voce_spesa FROM spese_progetto WHERE project_id=? AND categoria='Noleggio'", conn, params=(pid,))
                        if not rentals.empty:
                            story.append(Paragraph("<b>🎥 Lista Noleggi</b>", styles['Heading2']))
                            rent_data = [['Voce']] + rentals.values.tolist()
                            rent_table = Table(rent_data)
                            rent_table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1, colors.black)]))
                            story.append(rent_table)
                        
                        if row['lista_attrezzatura']:
                            story.append(Paragraph("<b>🛠 Attrezzatura</b>", styles['Heading2']))
                            story.append(Paragraph(row['lista_attrezzatura'].replace('\n', '<br/>'), styles['Normal']))

                        doc.build(story)
                        buffer.seek(0)
                        
                        st.download_button("Download", data=buffer.getvalue(), file_name=f"{proj['nome_progetto']}.pdf", mime="application/pdf")
                    except: st.error("Libreria reportlab mancante.")

            # PULSANTE ELIMINA (Solo Admin - Europa Studio NON può eliminare)
            if st.session_state['role'] == 'admin':
                st.markdown("---")
                with st.expander("🗑️ ZONA PERICOLOSA: Elimina Progetto"):
                    if st.button("CONFERMA ELIMINAZIONE", key=f"del_btn_{pid}"):
                        conn.execute("DELETE FROM progetti WHERE id=?", (pid,))
                        conn.execute("DELETE FROM spese_progetto WHERE project_id=?", (pid,))
                        conn.execute("DELETE FROM dettagli_produzione WHERE project_id=?", (pid,))
                        conn.commit()
                        st.success("Eliminato.")
                        time.sleep(1)
                        st.rerun()

    conn.close()


# 3. CLIENTI (NUOVA LOGICA CATEGORIE)
elif selected == "CLIENTI":
    conn = get_connection()
    st.markdown("### 👥 Gestione Clienti")
    
    t1, t2 = st.tabs(["LISTA CLIENTI", "AGGIUNGI NUOVO"])
    
    with t1:
        if st.session_state['role'] == 'europastudio':
            query = "SELECT * FROM clienti WHERE tag_categoria='EUROPA STUDIO'"
        else:
            query = "SELECT * FROM clienti"
            
        df_cli = pd.read_sql_query(query, conn)
        
        if not df_cli.empty:
            for idx, row in df_cli.iterrows():
                tag_label = f" [{row['tag_categoria']}]" if row['tag_categoria'] else ""
                with st.expander(f"🏢 {row['nome_azienda']} - {row['nome_cognome']}{tag_label}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write(f"📍 {row['indirizzo']} {row['citta']}")
                        st.write(f"💳 P.IVA: {row['cf_piva']}")
                    with c2:
                        st.write(f"📞 {row['telefono']}")
                        st.write(f"📧 {row['email']}")
                        if row['telefono']:
                            clean = ''.join(filter(str.isdigit, str(row['telefono'])))
                            if not clean.startswith('39') and len(clean)>=9: clean='39'+clean
                            st.markdown(f"<a href='https://web.whatsapp.com/send?phone={clean}' target='_blank'>💬 WhatsApp</a>", unsafe_allow_html=True)
                    with c3:
                        if st.session_state['role'] == 'admin':
                            if st.button("🗑️ ELIMINA", key=f"del_cli_{row['id']}"):
                                conn.execute("DELETE FROM clienti WHERE id=?", (row['id'],))
                                conn.commit()
                                st.warning("Eliminato")
                                time.sleep(1)
                                st.rerun()
        else: st.info("Nessun cliente visibile.")

    with t2:
        st.markdown("#### Inserisci Dati Cliente")
        with st.form("new_client_full"):
            col_a, col_b = st.columns(2)
            with col_a:
                na = st.text_input("Ragione Sociale / Azienda *")
                nc = st.text_input("Nome Referente *")
                
                if st.session_state['role'] == 'europastudio':
                    tag_cat = "EUROPA STUDIO"
                    st.info("Cliente verrà salvato in: EUROPA STUDIO")
                else:
                    tag_cat = st.selectbox("Categoria Cliente", ["TedescoFilms", "EUROPA STUDIO", "Altro"])
                
                cf = st.text_input("P.IVA / CF")
                sdi = st.text_input("SDI")
            with col_b:
                ind = st.text_input("Indirizzo")
                c_cap, c_cit = st.columns(2)
                cap = c_cap.text_input("CAP"); cit = c_cit.text_input("Città")
                tel = st.text_input("Telefono")
                em = st.text_input("Email")
                pec = st.text_input("PEC")

            st.markdown("---")
            if st.form_submit_button("💾 SALVA CLIENTE"):
                if na and nc:
                    query = """INSERT INTO clienti (nome_azienda, nome_cognome, cf_piva, sdi, pec, indirizzo, cap, citta, telefono, email, tag_categoria) VALUES (?,?,?,?,?,?,?,?,?,?,?)"""
                    conn.execute(query, (na, nc, cf, sdi, pec, ind, cap, cit, tel, em, tag_cat))
                    conn.commit()
                    st.success(f"Cliente aggiunto in {tag_cat}!")
                    time.sleep(1)
                    st.rerun()
                else: st.error("Nome Azienda e Referente obbligatori.")
    conn.close()

# 4. FORNITORI
elif selected == "FORNITORI":
    conn = get_connection()
    st.markdown("### 🤝 Gestione Fornitori")
    c_sx, c_dx = st.columns([2, 1])
    
    with c_sx:
        st.markdown("#### 📋 Lista Fornitori")
        df_forn = pd.read_sql_query("SELECT id, nome_cognome, categoria, telefono, costo_servizio FROM fornitori", conn)
        if not df_forn.empty:
            df_forn['Costo'] = df_forn['costo_servizio'].apply(lambda x: f"€ {x:,.0f}" if pd.notnull(x) else "-")
            st.dataframe(df_forn[['nome_cognome', 'categoria', 'telefono', 'Costo']], use_container_width=True, hide_index=True)
            
            if st.session_state['role'] == 'admin':
                st.markdown("---")
                with st.expander("🗑️ Elimina Fornitore"):
                    del_forn_name = st.selectbox("Seleziona chi eliminare", df_forn['nome_cognome'].tolist())
                    if st.button("CONFERMA ELIMINAZIONE"):
                        id_to_del = df_forn[df_forn['nome_cognome'] == del_forn_name].iloc[0]['id']
                        conn.execute("DELETE FROM fornitori WHERE id=?", (int(id_to_del),))
                        conn.commit()
                        st.warning("Eliminato.")
                        time.sleep(1)
                        st.rerun()
        else: st.info("Nessun fornitore.")

    with c_dx:
        st.markdown("#### ➕ Nuovo Fornitore")
        with st.form("new_supplier_form"):
            n = st.text_input("Nome e Cognome *")
            c = st.selectbox("Categoria", ["Videomaker", "Fotografo", "Drone", "Rent", "Assistente", "Altro"])
            t = st.text_input("Telefono")
            p = st.text_input("Città/Paese")
            cs = st.number_input("Costo Giornaliero (€)", step=50.0)
            if st.form_submit_button("AGGIUNGI"):
                if n:
                    conn.execute("INSERT INTO fornitori (nome_cognome, categoria, telefono, paese, costo_servizio) VALUES (?,?,?,?,?)", (n, c, t, p, cs))
                    conn.commit()
                    st.success("Fatto!")
                    time.sleep(1)
                    st.rerun()
                else: st.error("Nome obbligatorio.")
    conn.close()
