import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
import time
import datetime
from io import BytesIO

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="TedescoFilms Gestionale", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")

# --- CSS V7.2: FIX COLORI SCRITTE + STILE GENERALE ---
st.markdown("""
<style>
    /* 1. SFONDO GENERALE */
    .stApp {
        background: linear-gradient(to right, #0f2027, #203a43, #2c5364) !important;
        color: white !important;
    }
    
    /* 2. TESTI SEMPRE BIANCHI */
    h1, h2, h3, h4, h5, h6, p, label, span, li, .stMarkdown, div, caption {
        color: #ffffff !important;
    }
    
    /* 3. INPUT TEXT, NUMERI E TEXTAREA */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 1px solid #555 !important;
    }
    
    /* 4. DATE & TIME INPUT */
    div[data-baseweb="input"] {
        background-color: #000000 !important;
        border: 1px solid #555 !important;
    }
    div[data-testid="stDateInput"] input, div[data-testid="stTimeInput"] input {
        color: #ffffff !important;
        background-color: #000000 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #000000 !important;
        color: white !important;
        border: 1px solid #555 !important;
    }
    div[role="listbox"] ul {
        background-color: #000000 !important;
    }
    li[role="option"] {
        background-color: #000000 !important;
        color: white !important;
    }
    li[role="option"]:hover {
        background-color: #333333 !important;
    }
    div[data-baseweb="select"] span {
        color: white !important;
    }

    /* 5. BOX INFO E CODE (FIX SCRITTE BIANCHE SU SFONDO NERO) */
    div[data-testid="stAlert"] {
        background-color: #111111 !important;
        color: white !important;
        border: 1px solid #444 !important;
    }
    /* Il blocco di codice ora è NERO con scritte BIANCHE (no verde) */
    code {
        background-color: #000000 !important;
        color: #ffffff !important; 
        border: 1px solid #333;
        font-family: monospace;
    }
    div[data-testid="stCodeBlock"] {
        background-color: #000000 !important;
    }

    /* 6. RADIO BUTTONS */
    div[data-testid="stRadio"] > label > div:first-child { display: none !important; }
    div[data-testid="stRadio"] { background: transparent !important; }
    div[data-testid="stRadio"] label {
        background-color: rgba(0,0,0,0.5);
        border: 1px solid #444;
        color: #ddd !important;
        padding: 8px 15px;
        border-radius: 8px;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: #b20710 !important;
        color: white !important;
        border-color: #ff4b4b !important;
        font-weight: bold;
    }

    /* 7. CARD E TABELLE */
    .project-card, div[data-testid="stDataFrame"], div[data-testid="stForm"] {
        background: #111111 !important;
        border: 1px solid #444;
        border-radius: 10px;
        padding: 15px;
    }
    
    /* 8. BOTTONI */
    .stButton button {
        background: #b20710 !important;
        color: white !important;
        border: none;
    }

    section[data-testid="stSidebar"] { display: none; }
    svg { fill: white !important; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE ---
def get_connection(): return sqlite3.connect('tedesco_films.db')
def init_db():
    conn = get_connection(); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS clienti (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_azienda TEXT, nome_cognome TEXT, telefono TEXT, email TEXT, cf_piva TEXT, indirizzo TEXT, cap TEXT, citta TEXT, sdi TEXT, pec TEXT, tag_categoria TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS progetti (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, nome_progetto TEXT, prezzo REAL, fee_commerciale REAL, stato TEXT, anno INTEGER, categoria_progetto TEXT, data_set DATE)")
    c.execute("CREATE TABLE IF NOT EXISTS spese_progetto (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, voce_spesa TEXT, costo REAL, categoria TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS dettagli_produzione (project_id INTEGER PRIMARY KEY, note_regia TEXT, organizzazione TEXT, lista_attrezzatura TEXT)")
    try: c.execute("ALTER TABLE dettagli_produzione ADD COLUMN regia_video TEXT"); conn.commit()
    except: pass
    c.execute("CREATE TABLE IF NOT EXISTS fornitori (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_cognome TEXT, categoria TEXT, telefono TEXT, paese TEXT, costo_servizio REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS utenti (username TEXT PRIMARY KEY, password TEXT, ruolo TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS calendario (id INTEGER PRIMARY KEY AUTOINCREMENT, titolo TEXT, data DATE, ora TIME, tipo TEXT, note TEXT)")
    try: c.execute("INSERT INTO utenti (username, password, ruolo) VALUES ('admin', 'admin123', 'admin')")
    except: pass
    conn.commit(); conn.close()

init_db()

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state['logged_in']=False; st.session_state['role']=None

if not st.session_state['logged_in']:
    c1,c2,c3=st.columns([1,2,1])
    with c2:
        st.markdown("<br><h2 style='text-align:center;'>🔐 LOGIN</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u=st.text_input("User"); p=st.text_input("Pass", type="password")
            if st.form_submit_button("ENTRA"):
                conn=get_connection(); res=pd.read_sql_query("SELECT * FROM utenti WHERE username=? AND password=?", conn, params=(u,p)); conn.close()
                if not res.empty: st.session_state['logged_in']=True; st.session_state['username']=u; st.session_state['role']=res.iloc[0]['ruolo']; st.rerun()
                else: st.error("No.")
    st.stop()

# --- HEADER ---
c1, c2 = st.columns([1, 4])
with c1:
    cd=os.path.dirname(os.path.abspath(__file__)); lp=os.path.join(cd, "logo1.png")
    if os.path.exists(lp):
        with open(lp, "rb") as f: enc=base64.b64encode(f.read()).decode()
        st.markdown(f"""<div style="display:flex;justify-content:center;"><img src="data:image/jpeg;base64,{enc}" style="width:100%;max-width:160px;border-radius:8px;"></div>""", unsafe_allow_html=True)
    else: st.markdown("### 🎬 STUDIO")

with c2:
    st.write("") 
    menu = ["PROGETTI", "CLIENTI", "CALENDARIO"] if st.session_state['role']=='europastudio' else ["DASHBOARD", "PROGETTI", "CLIENTI", "FORNITORI", "CALENDARIO"]
    sel = st.radio("NAV", menu, horizontal=True, label_visibility="collapsed")

with st.sidebar:
    if st.button("LOGOUT"): st.session_state['logged_in']=False; st.rerun()

# --- DASHBOARD ---
if sel == "DASHBOARD":
    st.markdown(f"### 📊 Dashboard")
    if st.session_state['role']=='admin':
        conn=get_connection()
        p=pd.read_sql_query("SELECT * FROM progetti", conn); s=pd.read_sql_query("SELECT SUM(costo) as t FROM spese_progetto", conn).iloc[0]['t'] or 0
        if not p.empty:
            p['prezzo']=p['prezzo'].fillna(0); p['fee_commerciale']=p['fee_commerciale'].fillna(0)
            c1,c2,c3,c4=st.columns(4)
            c1.metric("FATTURATO", f"€ {p['prezzo'].sum():,.0f}")
            c2.metric("FEE", f"€ {p['fee_commerciale'].sum():,.0f}")
            c3.metric("SPESE", f"€ {s:,.0f}")
            c4.metric("UTILE", f"€ {(p['prezzo'].sum()-p['fee_commerciale'].sum()-s):,.0f}")
        
        st.markdown("---")
        with st.expander("👮 Gestione Utenti"):
            c1,c2=st.columns(2)
            with c1:
                st.markdown("##### Nuovo Utente")
                with st.form("nu"):
                    un=st.text_input("Username"); pw=st.text_input("Password"); rl=st.selectbox("Ruolo", ["admin", "staff", "europastudio"])
                    if st.form_submit_button("Crea"):
                        try: conn.execute("INSERT INTO utenti VALUES (?,?,?)", (un,pw,rl)); conn.commit(); st.success("Ok")
                        except: st.error("Errore")
            with c2:
                st.markdown("##### Utenti Attivi")
                st.dataframe(pd.read_sql_query("SELECT username, ruolo FROM utenti", conn), hide_index=True)
        conn.close()
    else: st.info("Area riservata.")

# --- PROGETTI ---
elif sel == "PROGETTI":
    conn=get_connection()
    c_sx, c_dx = st.columns([1, 2])
    with c_sx:
        st.markdown("#### 📂 Archivio")
        sq = st.text_input("🔍 Cerca...", key="pq")
        
        if st.session_state['role'] in ['admin', 'europastudio']:
            with st.expander("➕ NUOVO"):
                clis = pd.read_sql_query("SELECT * FROM clienti", conn)
                if st.session_state['role']=='europastudio': clis=clis[clis['tag_categoria']=='EUROPA STUDIO']
                if not clis.empty:
                    clis['d']=clis.apply(lambda x: x['nome_azienda'] or x['nome_cognome'], axis=1)
                    cs=st.selectbox("Cliente", clis['d'])
                    pn=st.text_input("Nome Progetto"); ds=st.date_input("Data Set")
                    pp=st.number_input("Budget", step=100.0); fee=st.number_input("Fee", step=50.0)
                    if st.session_state['role']=='europastudio': cat="EUROPA STUDIO"; st.info("Cat: EUROPA STUDIO")
                    else: cat=st.selectbox("Cat", ["EUROPA STUDIO", "VIDEO MUSICALI", "WEDDING", "COMMERCIALE", "ALTRO"])
                    yr=st.number_input("Anno", value=2026)
                    if st.button("Salva"):
                        cid=clis[clis['d']==cs].iloc[0]['id']
                        conn.execute("INSERT INTO progetti (cliente_id, nome_progetto, prezzo, fee_commerciale, stato, anno, categoria_progetto, data_set) VALUES (?,?,?,?,'Preventivo',?,?,?)", (int(cid),pn,pp,fee,yr,cat,ds)); conn.commit(); st.rerun()
        
        bq="SELECT * FROM progetti"; bq+=" WHERE categoria_progetto='EUROPA STUDIO'" if st.session_state['role']=='europastudio' else ""
        if sq:
            bq+= f" {'AND' if 'WHERE' in bq else 'WHERE'} nome_progetto LIKE '%{sq}%'"
            projs=pd.read_sql_query(bq+" ORDER BY id DESC", conn)
        else:
            dfa=pd.read_sql_query(bq+" ORDER BY id DESC", conn)
            if not dfa.empty:
                dfa['anno']=dfa['anno'].fillna(2026).astype(int); dfa['categoria_progetto']=dfa['categoria_progetto'].fillna("ALTRO")
                sa=st.selectbox("Anno", sorted(dfa['anno'].unique(), reverse=True))
                # Pulizia categorie
                raw_cats = dfa[dfa['anno']==sa]['categoria_progetto'].unique()
                clean_cats = [c for c in raw_cats if c and str(c).strip() != '']
                cats = sorted(clean_cats)
                sc=st.radio("Filtra Cat:", ["TUTTI"]+cats, horizontal=True)
                projs=dfa[dfa['anno']==sa] if sc=="TUTTI" else dfa[(dfa['anno']==sa)&(dfa['categoria_progetto']==sc)]
            else: projs=pd.DataFrame()
        
        pid=None
        if not projs.empty:
            opts={f"{r['nome_progetto']}": r['id'] for _,r in projs.iterrows()}
            st.markdown("---")
            sel_l=st.radio("Lista:", list(opts.keys()), label_visibility="collapsed")
            pid=opts[sel_l]
        else: st.caption("Nessun progetto.")

    with c_dx:
        if pid:
            pr=pd.read_sql_query("SELECT * FROM progetti WHERE id=?", conn, params=(pid,)).iloc[0]
            st.markdown(f"""<div class="project-card"><h2 style='margin:0;color:white;'>🎬 {pr['nome_progetto']}</h2><p style='color:#ccc;margin:0;'>{pr['categoria_progetto']} | {pr['anno']} | Set: {pr['data_set']}</p></div>""", unsafe_allow_html=True)
            
            if st.session_state['role'] in ['admin', 'europastudio']:
                c1,c2,c3,c4=st.columns(4)
                curr=pr['stato'] or "Preventivo"; poss=["Preventivo","Produzione","Consegnato","Pagato"]
                ns=c1.selectbox("Stato", poss, index=poss.index(curr) if curr in poss else 0, key=f"s_{pid}")
                if ns!=curr: conn.execute("UPDATE progetti SET stato=? WHERE id=?", (ns,pid)); conn.commit(); st.rerun()
                
                sp_tot=pd.read_sql_query("SELECT SUM(costo) as t FROM spese_progetto WHERE project_id=?", conn, params=(pid,)).iloc[0]['t'] or 0
                c2.metric("Budget", f"€ {pr['prezzo']:,.0f}"); c3.metric("Fee", f"€ {pr['fee_commerciale']:,.0f}"); c4.metric("Utile", f"€ {(pr['prezzo']-pr['fee_commerciale']-sp_tot):,.0f}")
                
                tabs=st.tabs(["💰 COSTI", "📝 NOTE", "🎬 ODG", "🎥 REGIA", "🎥 RENT", "🛠 EQUIP", "💳 PAGAMENTI", "📄 PDF"])
                t_c,t_n,t_o,t_regia,t_r,t_e,t_pay,t_p = tabs
                
                with t_c:
                    c_i,c_o=st.columns(2)
                    with c_i:
                        with st.form(f"fc_{pid}"):
                            v=st.text_input("Voce"); c=st.number_input("€", step=10.0); k=st.selectbox("Tipo", ["Noleggio","Crew","Logistica","Altro"])
                            if st.form_submit_button("Add"): conn.execute("INSERT INTO spese_progetto (project_id, voce_spesa, costo, categoria) VALUES (?,?,?,?)", (pid,v,c,k)); conn.commit(); st.rerun()
                    with c_o:
                        sp=pd.read_sql_query("SELECT * FROM spese_progetto WHERE project_id=?", conn, params=(pid,))
                        if not sp.empty: st.dataframe(sp[['voce_spesa','costo']], hide_index=True)
            else:
                tabs=st.tabs(["📝 NOTE", "🎬 ODG", "🎥 RENT", "🛠 EQUIP", "⛔ COSTI", "📄 PDF"])
                t_n,t_o,t_r,t_e,t_c,t_p=tabs; t_c.error("No access")
            
            dett=pd.read_sql_query("SELECT * FROM dettagli_produzione WHERE project_id=?", conn, params=(pid,))
            if dett.empty: conn.execute("INSERT INTO dettagli_produzione (project_id, note_regia, organizzazione, lista_attrezzatura, regia_video) VALUES (?, '', '', '', '')", (pid,)); conn.commit(); dett=pd.read_sql_query("SELECT * FROM dettagli_produzione WHERE project_id=?", conn, params=(pid,))
            row=dett.iloc[0]

            with t_n:
                nt=st.text_area("Note Generali", value=row['note_regia'], height=300, key=f"nt_{pid}")
                if st.button("Salva Note", key=f"bnt_{pid}"): conn.execute("UPDATE dettagli_produzione SET note_regia=? WHERE project_id=?", (nt,pid)); conn.commit(); st.toast("Saved")
            with t_o:
                odg=st.text_area("ODG", value=row['organizzazione'], height=300, key=f"odg_{pid}")
                if st.button("Salva ODG", key=f"bodg_{pid}"): conn.execute("UPDATE dettagli_produzione SET organizzazione=? WHERE project_id=?", (odg,pid)); conn.commit(); st.toast("Saved")
            
            with t_regia:
                rv=st.text_area("Note Regia Video", value=row['regia_video'] if row['regia_video'] else "", height=300, key=f"rv_{pid}")
                if st.button("Salva Regia", key=f"brv_{pid}"): conn.execute("UPDATE dettagli_produzione SET regia_video=? WHERE project_id=?", (rv,pid)); conn.commit(); st.toast("Saved")

            with t_r: 
                rent_df = pd.read_sql_query("SELECT voce_spesa, costo FROM spese_progetto WHERE project_id=? AND categoria='Noleggio'", conn, params=(pid,))
                tot_rent = rent_df['costo'].sum() if not rent_df.empty else 0
                st.metric("Totale Rental", f"€ {tot_rent:,.0f}")
                st.dataframe(rent_df, hide_index=True, use_container_width=True)
                
            with t_e:
                eq=st.text_area("Equip", value=row['lista_attrezzatura'], height=400, key=f"eq_{pid}")
                if st.button("Salva Equip", key=f"beq_{pid}"): conn.execute("UPDATE dettagli_produzione SET lista_attrezzatura=? WHERE project_id=?", (eq,pid)); conn.commit(); st.toast("Saved")

            with t_pay:
                st.subheader("Gestione Incasso")
                metodo = st.radio("Metodo di Pagamento", ["Bonifico Bancario", "PayPal", "Contanti"], horizontal=True)
                
                # DATI BANCARI E PAYPAL UFFICIALI
                iban_info = """IBAN: IT46U0364601600526618874285
Intestato a: Guglielmo Tedesco
Banca: N26 Bank"""
                
                paypal_info = """Nome: Guglielmo Tedesco
Numero: 3272916929
Link: paypal.me/freddo081"""

                st.markdown("---")
                if metodo == "Bonifico Bancario":
                    st.info("🏦 **DATI PER BONIFICO**")
                    st.code(iban_info, language="text")
                elif metodo == "PayPal":
                    st.info("🅿️ **PAYPAL**")
                    st.code(paypal_info, language="text")
                elif metodo == "Contanti":
                    st.info("💵 **CONTANTI**")
                    st.write("Pagamento diretto in sede o sul set.")

                st.markdown("---")
                if st.button("📄 SCARICA RICEVUTA PAGAMENTO (PRO)", key=f"rec_{pid}"):
                    try:
                        from reportlab.lib.pagesizes import A4; from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage; from reportlab.lib.styles import getSampleStyleSheet; from reportlab.lib import colors; from reportlab.lib.units import cm
                        bf=BytesIO(); doc=SimpleDocTemplate(bf, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                        s=[]; sty=getSampleStyleSheet()
                        
                        # INTESTAZIONE CON LOGO
                        if os.path.exists(lp):
                            im = RLImage(lp, width=4*cm, height=1.5*cm); im.hAlign = 'LEFT'
                            s.append(im); s.append(Spacer(1, 10))
                        
                        # Titolo
                        s.append(Paragraph("<b>TEDESCO FILMS</b> - RICEVUTA DI PAGAMENTO", sty['Heading1']))
                        s.append(Spacer(1, 20))
                        
                        # Dati Progetto e Cliente (Box affiancati)
                        # Recupero dati cliente
                        cli_row = pd.read_sql_query("SELECT * FROM clienti WHERE id=?", conn, params=(pr['cliente_id'],)).iloc[0]
                        
                        dati_cli = f"<b>Spett.le Cliente:</b><br/>{cli_row['nome_azienda'] or cli_row['nome_cognome']}<br/>{cli_row['indirizzo']}<br/>{cli_row['citta']} - {cli_row['cf_piva']}"
                        dati_pro = f"<b>Riferimento Progetto:</b><br/>{pr['nome_progetto']}<br/>Data Set: {pr['data_set']}<br/>Anno: {pr['anno']}"
                        
                        data_intest = [[Paragraph(dati_cli, sty['Normal']), Paragraph(dati_pro, sty['Normal'])]]
                        t_int = Table(data_intest, colWidths=[10*cm, 8*cm])
                        t_int.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
                        s.append(t_int)
                        s.append(Spacer(1, 30))
                        
                        # Tabella Importi
                        s.append(Paragraph(f"<b>Metodo Selezionato:</b> {metodo}", sty['Normal']))
                        s.append(Spacer(1, 10))
                        
                        data = [
                            ["DESCRIZIONE SERVIZIO", "IMPORTO"],
                            [f"Saldo produzione video: {pr['nome_progetto']}", f"€ {pr['prezzo']:,.2f}"],
                            ["", ""],
                            ["<b>TOTALE DA PAGARE</b>", f"<b>€ {pr['prezzo']:,.2f}</b>"]
                        ]
                        t = Table(data, colWidths=[12*cm, 4*cm])
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), '#2c3e50'), # Colore scuro intestazione
                            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0,0), (-1,0), 12),
                            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Totale grassetto
                            ('BACKGROUND', (0,-1), (-1,-1), '#ecf0f1') # Grigio chiaro totale
                        ]))
                        s.append(t)
                        s.append(Spacer(1, 40))
                        
                        # Footer con coordinate pagamento
                        s.append(Paragraph("<b>COORDINATE PER IL PAGAMENTO</b>", sty['Heading4']))
                        if metodo == "Bonifico Bancario":
                            pay_txt = iban_info.replace('\n', '<br/>')
                        elif metodo == "PayPal":
                            pay_txt = paypal_info.replace('\n', '<br/>')
                        else:
                            pay_txt = "Pagamento in contanti"
                            
                        s.append(Paragraph(pay_txt, sty['Normal']))
                        s.append(Spacer(1, 20))
                        s.append(Paragraph("<i>Grazie per la collaborazione.</i>", sty['Normal']))
                        
                        doc.build(s); bf.seek(0)
                        st.download_button("Download Ricevuta PDF", data=bf.getvalue(), file_name=f"Ricevuta_{pr['nome_progetto']}.pdf", mime="application/pdf")
                    except Exception as e: st.error(f"Errore PDF: {e}")

            with t_p:
                if st.button("⬇️ PDF SCHEDA TECNICA", key=f"pdf_{pid}"):
                    try:
                        from reportlab.lib.pagesizes import A4; from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table; from reportlab.lib.styles import getSampleStyleSheet; from io import BytesIO
                        bf=BytesIO(); doc=SimpleDocTemplate(bf, pagesize=A4); s=[]; sty=getSampleStyleSheet()
                        s.append(Paragraph(f"🎬 {pr['nome_progetto']}", sty['Heading1'])); s.append(Paragraph(f"Set: {pr['data_set']}", sty['Normal'])); s.append(Spacer(1,12))
                        if row['note_regia']: s.append(Paragraph("<b>Note</b>", sty['Heading2'])); s.append(Paragraph(row['note_regia'], sty['Normal']))
                        if row['regia_video']: s.append(Paragraph("<b>Regia Video</b>", sty['Heading2'])); s.append(Paragraph(row['regia_video'], sty['Normal']))
                        if row['organizzazione']: s.append(Paragraph("<b>ODG</b>", sty['Heading2'])); s.append(Paragraph(row['organizzazione'], sty['Normal']))
                        rent=pd.read_sql_query("SELECT voce_spesa FROM spese_progetto WHERE project_id=? AND categoria='Noleggio'", conn, params=(pid,))
                        if not rent.empty: s.append(Paragraph("<b>Rent</b>", sty['Heading2'])); s.append(Table([['Item']]+rent.values.tolist()))
                        if row['lista_attrezzatura']: s.append(Paragraph("<b>Equip</b>", sty['Heading2'])); s.append(Paragraph(row['lista_attrezzatura'], sty['Normal']))
                        doc.build(s); bf.seek(0); st.download_button("Scarica", data=bf.getvalue(), file_name=f"{pr['nome_progetto']}.pdf", mime="application/pdf")
                    except: st.error("No reportlab")
            
            if st.session_state['role']=='admin':
                st.markdown("---")
                with st.expander("🗑️ DELETE"):
                    if st.button("CONFIRM", key=f"del_{pid}"): conn.execute("DELETE FROM progetti WHERE id=?", (pid,)); conn.execute("DELETE FROM spese_progetto WHERE project_id=?", (pid,)); conn.execute("DELETE FROM dettagli_produzione WHERE project_id=?", (pid,)); conn.commit(); st.rerun()
    conn.close()

# --- CLIENTI ---
elif sel == "CLIENTI":
    conn=get_connection(); st.markdown("### 👥 Clienti")
    t1,t2=st.tabs(["LISTA", "NUOVO"])
    with t1:
        q="SELECT * FROM clienti WHERE tag_categoria='EUROPA STUDIO'" if st.session_state['role']=='europastudio' else "SELECT * FROM clienti"
        dfc=pd.read_sql_query(q, conn)
        sq=st.text_input("🔍 Cerca...", key="sc")
        if not dfc.empty:
            if sq: dfc=dfc[dfc['nome_azienda'].str.contains(sq, case=False, na=False) | dfc['nome_cognome'].str.contains(sq, case=False, na=False)]
            for _,r in dfc.iterrows():
                tag=f" [{r['tag_categoria']}]" if r['tag_categoria'] else ""
                with st.expander(f"🏢 {r['nome_azienda']} - {r['nome_cognome']}{tag}"):
                    c1,c2,c3=st.columns(3)
                    with c1: st.write(f"📍 {r['indirizzo']} {r['citta']}"); st.write(f"💳 {r['cf_piva']}")
                    with c2: st.write(f"📞 {r['telefono']}"); st.write(f"📧 {r['email']}")
                    with c3: 
                        if st.session_state['role']=='admin': 
                            if st.button("🗑️", key=f"dc_{r['id']}"): conn.execute("DELETE FROM clienti WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        else: st.info("Vuoto")
    with t2:
        with st.form("nc"):
            c1,c2=st.columns(2)
            na=c1.text_input("Azienda"); nc=c1.text_input("Ref"); cf=c1.text_input("CF/IVA")
            cat="EUROPA STUDIO" if st.session_state['role']=='europastudio' else c1.selectbox("Cat", ["TedescoFilms","EUROPA STUDIO","Altro"])
            ind=c2.text_input("Indirizzo"); cit=c2.text_input("Città"); tel=c2.text_input("Tel"); em=c2.text_input("Email")
            if st.form_submit_button("Salva"): conn.execute("INSERT INTO clienti (nome_azienda,nome_cognome,cf_piva,indirizzo,citta,telefono,email,tag_categoria) VALUES (?,?,?,?,?,?,?,?)", (na,nc,cf,ind,cit,tel,em,cat)); conn.commit(); st.success("Ok"); st.rerun()
    conn.close()

# --- FORNITORI ---
elif sel == "FORNITORI":
    conn=get_connection(); st.markdown("### 🤝 Fornitori"); c1,c2=st.columns([2,1])
    with c1:
        st.markdown("#### Lista")
        df=pd.read_sql_query("SELECT * FROM fornitori", conn)
        sq=st.text_input("🔍 Cerca...", key="sf")
        if not df.empty:
            if sq: df=df[df['nome_cognome'].str.contains(sq, case=False, na=False)]
            df['Costo']=df['costo_servizio'].apply(lambda x: f"€ {x:,.0f}" if pd.notnull(x) else "-")
            st.dataframe(df[['nome_cognome','categoria','telefono','Costo']], hide_index=True, use_container_width=True)
            if st.session_state['role']=='admin':
                with st.expander("🗑️"):
                    dn=st.selectbox("Chi?", df['nome_cognome'].unique())
                    if st.button("Elimina"): conn.execute("DELETE FROM fornitori WHERE nome_cognome=?", (dn,)); conn.commit(); st.rerun()
    with c2:
        st.markdown("#### Nuovo")
        with st.form("nf"):
            n=st.text_input("Nome"); c=st.selectbox("Cat", ["Videomaker","Fotografo","Drone","Rent","Altro"]); t=st.text_input("Tel"); cs=st.number_input("€", step=50.0)
            if st.form_submit_button("Salva"): conn.execute("INSERT INTO fornitori (nome_cognome,categoria,telefono,costo_servizio) VALUES (?,?,?,?)", (n,c,t,cs)); conn.commit(); st.rerun()
    conn.close()

# --- CALENDARIO ---
elif sel == "CALENDARIO":
    st.markdown("### 📅 Calendario")
    conn=get_connection(); c1,c2=st.columns([1,2])
    with c1:
        st.markdown("#### 🔗 Google Calendar")
        st.markdown("""
        <a href="https://calendar.google.com/calendar/u/0/r" target="_blank">
            <button style="background:#4285F4;color:white;padding:10px;border:none;border-radius:5px;width:100%;font-weight:bold;">
                🌍 APRI GOOGLE CALENDAR
            </button>
        </a>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### ➕ Nota Rapida")
        with st.form("nev"):
            tit=st.text_input("Titolo"); dat=st.date_input("Data"); ora=st.time_input("Ora")
            tip=st.selectbox("Tipo", ["Shooting","Sopralluogo","Riunione"]); not_=st.text_area("Note")
            if st.form_submit_button("Aggiungi"): conn.execute("INSERT INTO calendario (titolo,data,ora,tipo,note) VALUES (?,?,?,?,?)", (tit,dat,ora.strftime("%H:%M"),tip,not_)); conn.commit(); st.rerun()
    
    with c2:
        st.markdown("#### 🗓 Agenda Interna")
        pr=pd.read_sql_query("SELECT nome_progetto, data_set FROM progetti WHERE data_set IS NOT NULL AND data_set >= DATE('now') ORDER BY data_set", conn)
        ev=pd.read_sql_query("SELECT * FROM calendario WHERE data >= DATE('now') ORDER BY data", conn)
        
        if not pr.empty:
            st.caption("🎬 SHOOTING PREVISTI")
            for _,r in pr.iterrows(): st.info(f"🎥 {r['data_set']} | **{r['nome_progetto']}**")
        
        if not ev.empty:
            st.caption("📌 APPUNTAMENTI")
            for _,r in ev.iterrows():
                with st.expander(f"📅 {r['data']} {r['ora']} - {r['titolo']}"):
                    st.write(r['note'])
                    if st.button("X", key=f"dx_{r['id']}"): conn.execute("DELETE FROM calendario WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
    conn.close()
