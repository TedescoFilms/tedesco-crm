import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
import time
import datetime
import urllib.parse
from io import BytesIO

# ---------------------------
# UTILITY: FORMATTAZIONE DATA (ITALIANA)
# ---------------------------
def fmt_date(d):
    """Converte date da YYYY-MM-DD a DD-MM-YYYY per la visualizzazione"""
    if not d: return "-"
    try:
        if isinstance(d, str):
            if "-" in d and len(d.split("-")[0]) == 4: # Formato YYYY-MM-DD
                return datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%d-%m-%Y")
        elif isinstance(d, datetime.date):
            return d.strftime("%d-%m-%Y")
        return str(d)
    except:
        return str(d)

# ---------------------------
# CONFIGURAZIONE
# ---------------------------
st.set_page_config(
    page_title="TedescoFilms Gestionale",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------
# CSS V8.0 (INTOCCABILE)
# ---------------------------
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%) !important; color: white !important; }
    h1, h2, h3, h4, h5, h6, p, label, span, li, .stMarkdown, div, caption { color: #ffffff !important; }
    h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.5px !important; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea { background-color: rgba(0, 0, 0, 0.4) !important; color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 8px !important; backdrop-filter: blur(10px) !important; }
    div[data-baseweb="input"] { background-color: rgba(0, 0, 0, 0.4) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    div[data-baseweb="select"] > div { background-color: rgba(0, 0, 0, 0.4) !important; color: white !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    div[role="listbox"], ul[role="listbox"] { background-color: #000000 !important; }
    li[role="option"] { background-color: transparent !important; color: white !important; }
    li[role="option"]:hover { background-color: #b20710 !important; }
    .project-card, div[data-testid="stDataFrame"], div[data-testid="stForm"] { background: linear-gradient(135deg, rgba(17, 17, 17, 0.95) 0%, rgba(30, 30, 30, 0.95) 100%) !important; color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 16px !important; padding: 20px !important; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important; }
    .stButton button { background: linear-gradient(135deg, #b20710 0%, #d32f2f 100%) !important; color: white !important; border: none !important; border-radius: 10px !important; padding: 10px 20px !important; font-weight: 600 !important; width: 100% !important; }
    .stButton button:hover { background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%) !important; transform: translateY(-2px); }
    [data-testid="stMetricValue"] { font-weight: 700 !important; }
    div[data-testid="stRadio"] > label > div:first-child { display: none !important; }
    div[data-testid="stRadio"] label { background: rgba(0, 0, 0, 0.3) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: #ddd !important; padding: 10px 18px !important; border-radius: 10px !important; transition: all 0.3s ease !important; }
    div[data-testid="stRadio"] label:has(input:checked) { background: linear-gradient(135deg, #b20710 0%, #d32f2f 100%) !important; color: white !important; border-color: #ff4b4b !important; font-weight: 600 !important; }
    section[data-testid="stSidebar"] { display: none; }
    svg { fill: white !important; }
</style>
""", unsafe_allow_html=True)


# ---------------------------
# DATABASE
# ---------------------------
def get_connection(): return sqlite3.connect("tedesco_films.db", check_same_thread=False)

def init_db():
    conn = get_connection(); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS clienti (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_azienda TEXT, nome_cognome TEXT, telefono TEXT, email TEXT, cf_piva TEXT, indirizzo TEXT, cap TEXT, citta TEXT, sdi TEXT, pec TEXT, tag_categoria TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS progetti (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, nome_progetto TEXT, prezzo REAL, fee_commerciale REAL, stato TEXT, anno INTEGER, categoria_progetto TEXT, data_set DATE)")
    c.execute("CREATE TABLE IF NOT EXISTS spese_progetto (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, voce_spesa TEXT, costo REAL, categoria TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS dettagli_produzione (project_id INTEGER PRIMARY KEY, note_regia TEXT, organizzazione TEXT, lista_attrezzatura TEXT, regia_video TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS fornitori (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_cognome TEXT, categoria TEXT, telefono TEXT, paese TEXT, costo_servizio REAL, citta TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS utenti (username TEXT PRIMARY KEY, password TEXT, ruolo TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS calendario (id INTEGER PRIMARY KEY AUTOINCREMENT, titolo TEXT, data DATE, ora TIME, tipo TEXT, note TEXT, telefono TEXT, email TEXT)")
    try: c.execute("INSERT INTO utenti (username, password, ruolo) VALUES ('admin', 'admin123', 'admin')")
    except: pass
    conn.commit(); conn.close()
init_db()


# ---------------------------
# LOGIN
# ---------------------------
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False; st.session_state["role"] = None
if not st.session_state["logged_in"]:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><h2 style='text-align:center;'>🔐 LOGIN</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.form_submit_button("ENTRA"):
                conn = get_connection(); res = pd.read_sql_query("SELECT * FROM utenti WHERE username=? AND password=?", conn, params=(u, p)); conn.close()
                if not res.empty: st.session_state["logged_in"] = True; st.session_state["username"] = u; st.session_state["role"] = res.iloc[0]["ruolo"]; st.rerun()
                else: st.error("No.")
    st.stop()


# ---------------------------
# HEADER
# ---------------------------
c1, c2 = st.columns([1, 4])
with c1:
    cd = os.path.dirname(os.path.abspath(__file__)); lp = os.path.join(cd, "logo1.png")
    if os.path.exists(lp):
        with open(lp, "rb") as f: enc = base64.b64encode(f.read()).decode()
        st.markdown(f"""<div style="display:flex;justify-content:center;"><img src="data:image/png;base64,{enc}" style="width:100%;max-width:160px;border-radius:8px;"></div>""", unsafe_allow_html=True)
    else: st.markdown("### 🎬 STUDIO")

with c2:
    st.write(""); menu = ["PROGETTI", "CLIENTI", "CALENDARIO"] if st.session_state["role"] == "europastudio" else ["DASHBOARD", "PROGETTI", "CLIENTI", "FORNITORI", "CALENDARIO"]
    sel = st.radio("NAV", menu, horizontal=True, label_visibility="collapsed", key="nav")
with st.sidebar:
    if st.button("LOGOUT"): st.session_state["logged_in"] = False; st.rerun()


# ---------------------------
# DASHBOARD
# ---------------------------
if sel == "DASHBOARD":
    st.markdown("### 📊 Dashboard")
    if st.session_state["role"] == "admin":
        conn = get_connection(); p = pd.read_sql_query("SELECT * FROM progetti", conn); s = pd.read_sql_query("SELECT SUM(costo) as t FROM spese_progetto", conn).iloc[0]["t"] or 0
        if not p.empty:
            p["prezzo"] = p["prezzo"].fillna(0); p["fee_commerciale"] = p["fee_commerciale"].fillna(0)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("FATTURATO", f"€ {p['prezzo'].sum():,.0f}"); c2.metric("FEE", f"€ {p['fee_commerciale'].sum():,.0f}"); c3.metric("SPESE", f"€ {s:,.0f}"); c4.metric("UTILE", f"€ {(p['prezzo'].sum() - p['fee_commerciale'].sum() - s):,.0f}")
        st.markdown("---")
        with st.expander("👮 Gestione Utenti"):
            c1, c2 = st.columns(2)
            with c1:
                with st.form("nu"):
                    un = st.text_input("Username"); pw = st.text_input("Password"); rl = st.selectbox("Ruolo", ["admin", "staff", "europastudio"])
                    if st.form_submit_button("Crea"): conn.execute("INSERT INTO utenti VALUES (?,?,?)", (un, pw, rl)); conn.commit(); st.success("Ok")
            with c2: st.dataframe(pd.read_sql_query("SELECT username, ruolo FROM utenti", conn), hide_index=True)
        conn.close()
    else: st.info("Area riservata.")


# ---------------------------
# PROGETTI (AGGIORNATA: PDF SCHEDA TECNICA)
# ---------------------------
elif sel == "PROGETTI":
    conn = get_connection()
    c_sx, c_dx = st.columns([1, 2])

    with c_sx:
        st.markdown("#### 📂 Archivio")
        
        # FILTRO CATEGORIA
        cats = ["TUTTI", "EUROPA STUDIO", "VIDEO MUSICALI", "WEDDING", "COMMERCIALE", "ALTRO"]
        if st.session_state["role"] == "europastudio":
            f_cat = "EUROPA STUDIO"
        else:
            f_cat = st.selectbox("📂 Filtra Categoria", cats)
        
        sq = st.text_input("🔍 Cerca...", key="search")

        if st.session_state["role"] in ["admin", "europastudio"]:
            with st.expander("➕ NUOVO"):
                clis = pd.read_sql_query("SELECT * FROM clienti", conn)
                if st.session_state["role"] == "europastudio": clis = clis[clis["tag_categoria"] == "EUROPA STUDIO"]
                if not clis.empty:
                    clis["d"] = clis.apply(lambda x: x["nome_azienda"] or x["nome_cognome"], axis=1)
                    cs = st.selectbox("Cliente", clis["d"]); pn = st.text_input("Nome Progetto"); 
                    ds = st.date_input("Data Set", format="DD/MM/YYYY") # DATA ITA
                    pp = st.number_input("Budget", step=100.0); fee = st.number_input("Fee", step=50.0)
                    if st.session_state["role"] == "europastudio": cat = "EUROPA STUDIO"
                    else: cat = st.selectbox("Cat", ["EUROPA STUDIO", "VIDEO MUSICALI", "WEDDING", "COMMERCIALE", "ALTRO"])
                    yr = st.number_input("Anno", value=2026)
                    
                    if st.button("Salva"):
                        cid = int(clis[clis["d"] == cs].iloc[0]["id"])
                        cur = conn.cursor()
                        cur.execute("INSERT INTO progetti (cliente_id, nome_progetto, prezzo, fee_commerciale, stato, anno, categoria_progetto, data_set) VALUES (?,?,?,?,'Preventivo',?,?,?)", (cid, pn, pp, fee, yr, cat, ds))
                        conn.commit()
                        st.session_state['selected_pid'] = cur.lastrowid 
                        st.rerun()

        # COSTRUZIONE QUERY
        bq = "SELECT * FROM progetti WHERE 1=1"
        if st.session_state["role"] == "europastudio":
            bq += " AND categoria_progetto='EUROPA STUDIO'"
        elif f_cat != "TUTTI":
            bq += f" AND categoria_progetto='{f_cat}'"
        
        if sq: 
            bq += f" AND nome_progetto LIKE '%{sq}%'"
        
        projs = pd.read_sql_query(bq + " ORDER BY id DESC", conn)
        
        # LOGICA SELEZIONE
        if not projs.empty:
            st.markdown("---")
            opts = {row['id']: row['nome_progetto'] for _, row in projs.iterrows()}
            all_ids = list(opts.keys())

            current_selection = st.session_state.get('selected_pid', all_ids[0])
            if current_selection not in all_ids: current_selection = all_ids[0]

            def update_selection():
                st.session_state['selected_pid'] = st.session_state['project_radio']

            st.radio(
                "Lista:", 
                all_ids, 
                format_func=lambda x: opts[x], 
                index=all_ids.index(current_selection),
                key="project_radio",
                on_change=update_selection
            )
            pid = st.session_state.get('selected_pid', all_ids[0])
        else:
            pid = None
            st.caption("Nessun progetto trovato.")

    with c_dx:
        # TRUCCO CONTENITORE VUOTO
        details_container = st.empty()
        
        if pid:
            with details_container.container():
                pr = pd.read_sql_query("SELECT * FROM progetti WHERE id=?", conn, params=(pid,)).iloc[0]
                sp_tot = pd.read_sql_query("SELECT SUM(costo) as t FROM spese_progetto WHERE project_id=?", conn, params=(pid,)).iloc[0]["t"] or 0
                
                # DATA ITA IN VISUALIZZAZIONE
                data_ita = fmt_date(pr['data_set'])

                st.markdown(f"""
                <div class="project-card">
                    <h2 style='margin:0;color:white;'>🎬 {pr['nome_progetto']}</h2>
                    <p style='color:#ccc;margin:0;'>{pr['categoria_progetto']} | {pr['anno']} | Set: {data_ita}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.session_state["role"] in ["admin", "europastudio"]:
                    c1, c2, c3, c4 = st.columns(4)
                    curr = pr["stato"] or "Preventivo"; poss = ["Preventivo", "Produzione", "Consegnato", "Pagato"]
                    
                    ns = c1.selectbox("Stato", poss, index=poss.index(curr) if curr in poss else 0, key=f"state_box_{pid}")
                    if ns != curr: conn.execute("UPDATE progetti SET stato=? WHERE id=?", (ns, pid)); conn.commit(); st.rerun()

                    c2.metric("Budget", f"€ {pr['prezzo']:,.0f}")
                    c3.metric("Fee", f"€ {pr['fee_commerciale']:,.0f}")
                    c4.metric("Utile", f"€ {(pr['prezzo'] - pr['fee_commerciale'] - sp_tot):,.0f}")
                    
                    tabs = st.tabs(["💰 COSTI", "📝 NOTE", "🎬 ODG", "🎥 REGIA", "🎥 RENT", "🛠 EQUIP", "💳 PAGAMENTI", "📄 PDF"])
                    t_c, t_n, t_o, t_regia, t_r, t_e, t_pay, t_p = tabs
                    
                    with t_c:
                        c_i, c_o = st.columns(2)
                        with c_i:
                            st.markdown("##### Aggiungi Spesa")
                            with st.form(f"form_costs_{pid}"):
                                v = st.text_input("Voce", key=f"inp_voce_{pid}"); c_sp = st.number_input("€", step=10.0, min_value=0.0, key=f"inp_cost_{pid}"); k = st.selectbox("Tipo", ["Noleggio", "Crew", "Logistica", "Altro"], key=f"inp_type_{pid}")
                                if st.form_submit_button("💾 Aggiungi"): conn.execute("INSERT INTO spese_progetto (project_id, voce_spesa, costo, categoria) VALUES (?,?,?,?)", (pid, v, c_sp, k)); conn.commit(); st.rerun()
                        with c_o:
                            st.markdown("##### Riepilogo")
                            sp = pd.read_sql_query("SELECT * FROM spese_progetto WHERE project_id=?", conn, params=(pid,))
                            if not sp.empty:
                                st.dataframe(sp[["voce_spesa", "costo"]], hide_index=True, use_container_width=True)
                                st.markdown(f"**Totale:** :red[€ {sp_tot:,.2f}]")
                                with st.expander("🗑️"):
                                    d_m = {f"{r['voce_spesa']} (€{r['costo']})": r['id'] for _, r in sp.iterrows()}
                                    sd = st.selectbox("Elimina", list(d_m.keys()), key=f"del_box_{pid}")
                                    if st.button("Conferma", key=f"btn_del_{pid}"): conn.execute("DELETE FROM spese_progetto WHERE id=?", (d_m[sd],)); conn.execute("DELETE FROM spese_progetto WHERE id=?", (d_m[sd],)); conn.commit(); st.rerun()
                else:
                    tabs = st.tabs(["📝 NOTE", "🎬 ODG", "🎥 RENT", "🛠 EQUIP", "⛔ COSTI", "📄 PDF"]); t_n, t_o, t_r, t_e, t_c, t_p = tabs; t_c.error("No access")
                
                dett = pd.read_sql_query("SELECT * FROM dettagli_produzione WHERE project_id=?", conn, params=(pid,))
                if dett.empty: conn.execute("INSERT INTO dettagli_produzione (project_id, note_regia, organizzazione, lista_attrezzatura, regia_video) VALUES (?, '', '', '', '')", (pid,)); conn.commit(); dett = pd.read_sql_query("SELECT * FROM dettagli_produzione WHERE project_id=?", conn, params=(pid,))
                row = dett.iloc[0]

                with t_n:
                    nt = st.text_area("Note Generali", value=row['note_regia'], height=300, key=f"txt_note_{pid}")
                    if st.button("Salva Note", key=f"btn_note_{pid}"): conn.execute("UPDATE dettagli_produzione SET note_regia=? WHERE project_id=?", (nt, pid)); conn.commit(); st.toast("Saved")
                with t_o:
                    odg = st.text_area("ODG", value=row['organizzazione'], height=300, key=f"txt_odg_{pid}")
                    if st.button("Salva ODG", key=f"btn_odg_{pid}"): conn.execute("UPDATE dettagli_produzione SET organizzazione=? WHERE project_id=?", (odg, pid)); conn.commit(); st.toast("Saved")
                with t_regia:
                    rv = st.text_area("Note Regia Video", value=row['regia_video'] if row['regia_video'] else "", height=300, key=f"txt_rv_{pid}")
                    if st.button("Salva Regia", key=f"btn_rv_{pid}"): conn.execute("UPDATE dettagli_produzione SET regia_video=? WHERE project_id=?", (rv, pid)); conn.commit(); st.toast("Saved")
                with t_r:
                    rent_df = pd.read_sql_query("SELECT voce_spesa, costo FROM spese_progetto WHERE project_id=? AND categoria='Noleggio'", conn, params=(pid,))
                    st.metric("Totale Noleggio", f"€ {rent_df['costo'].sum():,.0f}"); st.dataframe(rent_df, hide_index=True, use_container_width=True)
                with t_e:
                    eq = st.text_area("Equip", value=row['lista_attrezzatura'], height=400, key=f"txt_eq_{pid}")
                    if st.button("Salva Equip", key=f"btn_eq_{pid}"): conn.execute("UPDATE dettagli_produzione SET lista_attrezzatura=? WHERE project_id=?", (eq, pid)); conn.commit(); st.toast("Saved")
                
                if st.session_state["role"] in ["admin", "europastudio"]:
                    # SEZIONE PAGAMENTI (RICEVUTA)
                    with t_pay:
                        st.subheader("Gestione Incasso")
                        met = st.radio("Metodo", ["Bonifico Bancario", "PayPal", "Contanti"], horizontal=True, key=f"pay_m_{pid}")
                        iban = "IBAN: IT46U0364601600526618874285\nIntestato a: Guglielmo Tedesco\nBanca: N26 Bank"
                        ppl = "PayPal:\nNome: Guglielmo Tedesco\nNumero: 3272916929\nLink: paypal.me/freddo081"
                        st.markdown("---")
                        if met == "Bonifico Bancario": st.info("🏦 BONIFICO"); st.code(iban)
                        elif met == "PayPal": st.info("🅿️ PAYPAL"); st.code(ppl)
                        else: st.info("💵 CONTANTI")
                        st.markdown("---")
                        if st.button("📄 SCARICA RICEVUTA", key=f"btn_pdf_rec_{pid}"):
                            try:
                                from reportlab.lib.pagesizes import A4
                                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
                                from reportlab.lib.styles import getSampleStyleSheet
                                from reportlab.lib import colors
                                from reportlab.lib.units import cm
                                bf = BytesIO()
                                doc = SimpleDocTemplate(bf, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                                story = []
                                sty = getSampleStyleSheet()
                                if os.path.exists(lp):
                                    im = RLImage(lp, width=4*cm, height=1.5*cm)
                                    im.hAlign = 'LEFT'
                                    story.append(im)
                                    story.append(Spacer(1, 10))
                                story.append(Paragraph("<b>TEDESCO FILMS</b> - RICEVUTA", sty['Heading1']))
                                story.append(Spacer(1, 20))
                                # CLIENTE
                                cid = pr['cliente_id']
                                d_c = "<b>Cliente:</b><br/>Non specificato"
                                d_p = f"<b>Progetto:</b><br/>{pr['nome_progetto']}<br/>Data: {data_ita}"
                                if cid and cid > 0:
                                    cr_list = pd.read_sql_query("SELECT * FROM clienti WHERE id=?", conn, params=(cid,))
                                    if not cr_list.empty:
                                        cr = cr_list.iloc[0]
                                        nom_azienda = cr['nome_azienda'] if cr['nome_azienda'] else cr['nome_cognome']
                                        indirizzo = cr['indirizzo'] if cr['indirizzo'] else ""
                                        citta_cl = cr['citta'] if cr['citta'] else ""
                                        piva = cr['cf_piva'] if cr['cf_piva'] else ""
                                        d_c = f"<b>Cliente:</b><br/>{nom_azienda}<br/>{indirizzo} - {citta_cl}<br/>{piva}"
                                
                                t_h = Table([[Paragraph(d_c, sty['Normal']), Paragraph(d_p, sty['Normal'])]], colWidths=[10*cm, 8*cm])
                                t_h.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
                                story.append(t_h)
                                story.append(Spacer(1, 20))
                                # TABELLA IMPORTI (CLEAN)
                                dt = [
                                    ["DESCRIZIONE", "IMPORTO"],
                                    [f"Servizio: {pr['nome_progetto']}", f"€ {pr['prezzo']:,.2f}"],
                                    ["", ""],
                                    ["TOTALE", f"€ {pr['prezzo']:,.2f}"]
                                ]
                                t = Table(dt, colWidths=[12*cm, 4*cm])
                                t.setStyle(TableStyle([
                                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2c3e50")),
                                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), # Header Bold
                                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                                    ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Totale Bold
                                    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#ecf0f1")),
                                    ('TEXTCOLOR', (0,-1), (-1,-1), colors.black),
                                ]))
                                story.append(t)
                                story.append(Spacer(1, 20))
                                crd = iban if met == "Bonifico Bancario" else (ppl if met == "PayPal" else "Contanti")
                                story.append(Paragraph("<b>COORDINATE PAGAMENTO:</b>", sty['Heading4']))
                                story.append(Paragraph(crd.replace('\n', '<br/>'), sty['Normal']))
                                doc.build(story)
                                bf.seek(0)
                                st.download_button(
                                    "Download Ricevuta PDF",
                                    data=bf.getvalue(),
                                    file_name=f"Ricevuta_{pr['nome_progetto'].replace(' ', '_')}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_rec_{pid}"
                                )
                                st.success("✅ PDF generato!")
                            except Exception as e:
                                st.error(f"❌ Errore PDF: {str(e)}")

                    # SEZIONE SCHEDA TECNICA (RIPRISTINATA)
                    with t_p:
                        st.markdown("#### 📄 Scheda Progetto (Call Sheet)")
                        if st.button("SCARICA SCHEDA TECNICA", key=f"btn_cs_{pid}"):
                            try:
                                from reportlab.lib.pagesizes import A4
                                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
                                from reportlab.lib.styles import getSampleStyleSheet
                                from reportlab.lib import colors
                                from reportlab.lib.units import cm
                                bf = BytesIO()
                                doc = SimpleDocTemplate(bf, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                                story = []
                                sty = getSampleStyleSheet()
                                
                                # Header
                                if os.path.exists(lp):
                                    im = RLImage(lp, width=4*cm, height=1.5*cm)
                                    im.hAlign = 'LEFT'
                                    story.append(im)
                                    story.append(Spacer(1, 10))
                                
                                story.append(Paragraph(f"<b>SCHEDA PROGETTO: {pr['nome_progetto']}</b>", sty['Heading1']))
                                story.append(Paragraph(f"Data Set: {data_ita} | Categoria: {pr['categoria_progetto']}", sty['Normal']))
                                story.append(Spacer(1, 20))
                                
                                # ODG
                                story.append(Paragraph("<b>ORDINE DEL GIORNO (ODG)</b>", sty['Heading3']))
                                odg_txt = row['organizzazione'] if row['organizzazione'] else "Nessun dettaglio inserito."
                                story.append(Paragraph(odg_txt.replace('\n', '<br/>'), sty['Normal']))
                                story.append(Spacer(1, 20))

                                # NOTE REGIA
                                story.append(Paragraph("<b>NOTE DI REGIA / GENERALI</b>", sty['Heading3']))
                                note_txt = row['note_regia'] if row['note_regia'] else "-"
                                story.append(Paragraph(note_txt.replace('\n', '<br/>'), sty['Normal']))
                                story.append(Spacer(1, 20))

                                # EQUIPMENT
                                story.append(Paragraph("<b>LISTA ATTREZZATURA</b>", sty['Heading3']))
                                eq_txt = row['lista_attrezzatura'] if row['lista_attrezzatura'] else "-"
                                story.append(Paragraph(eq_txt.replace('\n', '<br/>'), sty['Normal']))
                                
                                doc.build(story)
                                bf.seek(0)
                                st.download_button(
                                    "Download Scheda Tecnica",
                                    data=bf.getvalue(),
                                    file_name=f"Scheda_{pr['nome_progetto'].replace(' ', '_')}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_cs_{pid}"
                                )
                                st.success("✅ Scheda generata!")
                            except Exception as e:
                                st.error(f"❌ Errore PDF: {str(e)}")

                if st.session_state["role"] == "admin":
                    st.markdown("---")
                    with st.expander("🗑️ DELETE PROJECT"):
                        if st.button("CONFIRM DELETE", key=f"del_{pid}"):
                            conn.execute("DELETE FROM progetti WHERE id=?", (pid,)); conn.execute("DELETE FROM spese_progetto WHERE project_id=?", (pid,)); conn.execute("DELETE FROM dettagli_produzione WHERE project_id=?", (pid,)); conn.commit(); st.rerun()
    conn.close()


# ---------------------------
# CLIENTI
# ---------------------------
elif sel == "CLIENTI":
    conn = get_connection(); st.markdown("### 👥 Clienti")
    t1, t2 = st.tabs(["LISTA", "NUOVO"])

    with t1:
        q = "SELECT * FROM clienti WHERE tag_categoria='EUROPA STUDIO'" if st.session_state["role"] == "europastudio" else "SELECT * FROM clienti"
        dfc = pd.read_sql_query(q, conn); sq = st.text_input("🔍 Cerca...", key="sc")
        if not dfc.empty:
            if sq: dfc = dfc[dfc["nome_azienda"].str.contains(sq, case=False, na=False) | dfc["nome_cognome"].str.contains(sq, case=False, na=False)]
            
            for _, r in dfc.iterrows():
                # Visualizzazione rapida
                display_name = r['nome_azienda'] if r['nome_azienda'] else r['nome_cognome']
                
                with st.expander(f"🏢 {display_name}"):
                    # FORM DI MODIFICA
                    with st.form(key=f"edit_cli_{r['id']}"):
                        st.caption(f"ID: {r['id']}")
                        c1, c2 = st.columns(2)
                        with c1:
                            e_az = st.text_input("Ragione Sociale", value=r['nome_azienda'] if r['nome_azienda'] else "")
                            e_ref = st.text_input("Referente", value=r['nome_cognome'] if r['nome_cognome'] else "")
                            e_piva = st.text_input("P.IVA / C.F.", value=r['cf_piva'] if r['cf_piva'] else "")
                            e_sdi = st.text_input("Codice SDI", value=r['sdi'] if r['sdi'] else "")
                            e_pec = st.text_input("PEC", value=r['pec'] if r['pec'] else "")
                        with c2:
                            e_ind = st.text_input("Indirizzo", value=r['indirizzo'] if r['indirizzo'] else "")
                            e_cap = st.text_input("CAP", value=r['cap'] if r['cap'] else "")
                            e_cit = st.text_input("Città", value=r['citta'] if r['citta'] else "")
                            e_tel = st.text_input("Telefono", value=r['telefono'] if r['telefono'] else "")
                            e_em = st.text_input("Email", value=r['email'] if r['email'] else "")
                        
                        col_save, col_del = st.columns([1, 0.2])
                        with col_save:
                            if st.form_submit_button("💾 Salva Modifiche"):
                                conn.execute("""
                                    UPDATE clienti SET 
                                    nome_azienda=?, nome_cognome=?, telefono=?, email=?, 
                                    cf_piva=?, indirizzo=?, cap=?, citta=?, sdi=?, pec=?
                                    WHERE id=?""", 
                                    (e_az, e_ref, e_tel, e_em, e_piva, e_ind, e_cap, e_cit, e_sdi, e_pec, r['id']))
                                conn.commit()
                                st.success("Salvato!")
                                time.sleep(0.5)
                                st.rerun()
                        
                        if st.session_state["role"] == "admin":
                            with col_del:
                                if st.form_submit_button("🗑️ Elimina"):
                                    conn.execute("DELETE FROM clienti WHERE id=?", (r["id"],))
                                    conn.commit()
                                    st.warning("Eliminato.")
                                    time.sleep(0.5)
                                    st.rerun()

        else: st.info("Vuoto")

    with t2:
        st.markdown("#### Anagrafica Cliente")
        with st.form("nc"):
            c1, c2 = st.columns(2)
            with c1:
                na = st.text_input("Ragione Sociale / Azienda")
                nc = st.text_input("Nome Referente")
                piva = st.text_input("P.IVA / C.F.")
                sdi = st.text_input("Codice SDI")
                pec = st.text_input("PEC")
            with c2:
                ind = st.text_input("Indirizzo (Via/Piazza)")
                cap = st.text_input("CAP")
                citta_new = st.text_input("Città")
                tel = st.text_input("Telefono")
                em = st.text_input("Email")
            
            cat = "EUROPA STUDIO" if st.session_state["role"] == "europastudio" else st.selectbox("Categoria", ["TedescoFilms", "EUROPA STUDIO"])
            
            if st.form_submit_button("💾 Salva Nuovo Cliente"):
                conn.execute("""
                    INSERT INTO clienti 
                    (nome_azienda, nome_cognome, telefono, email, cf_piva, indirizzo, cap, citta, sdi, pec, tag_categoria) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", 
                    (na, nc, tel, em, piva, ind, cap, citta_new, sdi, pec, cat))
                conn.commit()
                st.success("Cliente aggiunto con successo!")
                time.sleep(1)
                st.rerun()
    conn.close()


# ---------------------------
# FORNITORI
# ---------------------------
elif sel == "FORNITORI":
    conn = get_connection(); st.markdown("### 🤝 Fornitori")
    t1, t2 = st.tabs(["LISTA", "NUOVO"])
    with t1:
        df = pd.read_sql_query("SELECT * FROM fornitori ORDER BY nome_cognome", conn)
        sq = st.text_input("🔍 Cerca (es: 'Drone Salerno')", key="sf")
        
        if not df.empty:
            # LOGICA RICERCA MULTI-PAROLA
            if sq:
                tokens = sq.lower().split()
                mask = pd.Series([True] * len(df))
                for t in tokens:
                    # Per ogni parola, controlla se esiste in nome, categoria o città
                    m = (
                        df["nome_cognome"].str.contains(t, case=False, na=False) |
                        df["categoria"].str.contains(t, case=False, na=False) |
                        df["citta"].str.contains(t, case=False, na=False)
                    )
                    mask = mask & m
                df = df[mask]
            
            if not df.empty:
                for _, row in df.iterrows():
                    citt_disp = row['citta'] if row['citta'] else "-"
                    with st.expander(f"👤 {row['nome_cognome']} ({row['categoria']} - {citt_disp})"):
                        # FORM DI MODIFICA
                        with st.form(f"edit_supplier_{row['id']}"):
                            c_a, c_b = st.columns(2)
                            with c_a:
                                new_nome = st.text_input("Nome", value=row['nome_cognome'])
                                new_cat = st.selectbox("Categoria", ["Videomaker", "Fotografo", "Drone", "Rent", "Altro"], index=["Videomaker", "Fotografo", "Drone", "Rent", "Altro"].index(row['categoria']) if row['categoria'] in ["Videomaker", "Fotografo", "Drone", "Rent", "Altro"] else 0)
                                new_citta = st.text_input("Città", value=row['citta'] if row['citta'] else "")
                            with c_b:
                                new_tel = st.text_input("Telefono", value=row['telefono'] if row['telefono'] else "")
                                new_costo = st.number_input("Costo Servizio (€)", value=float(row['costo_servizio']) if row['costo_servizio'] else 0.0, step=50.0)
                            
                            col_save, col_del = st.columns([1, 0.2])
                            with col_save:
                                if st.form_submit_button("💾 Salva Modifiche"):
                                    conn.execute("UPDATE fornitori SET nome_cognome=?, categoria=?, citta=?, telefono=?, costo_servizio=? WHERE id=?", 
                                                 (new_nome, new_cat, new_citta, new_tel, new_costo, row['id']))
                                    conn.commit()
                                    st.success("Salvato!")
                                    time.sleep(0.5)
                                    st.rerun()
                            
                            if st.session_state["role"] == "admin":
                                with col_del:
                                    if st.form_submit_button("🗑️ Elimina"):
                                        conn.execute("DELETE FROM fornitori WHERE id=?", (row['id'],))
                                        conn.commit()
                                        st.warning("Eliminato.")
                                        time.sleep(0.5)
                                        st.rerun()
            else:
                st.info("Nessun fornitore trovato con questi criteri.")
        else: st.info("Database fornitori vuoto.")
    with t2:
        with st.form("nf"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nome"); c = c1.selectbox("Categoria", ["Videomaker", "Fotografo", "Drone", "Rent", "Altro"]); citta = c1.text_input("Città")
            t = c2.text_input("Tel"); cs = c2.number_input("Costo Servizio", step=50.0)
            if st.form_submit_button("Salva"): conn.execute("INSERT INTO fornitori (nome_cognome, categoria, telefono, citta, costo_servizio) VALUES (?,?,?,?,?)", (n, c, t, citta, cs)); conn.commit(); st.success("Ok"); st.rerun()
    conn.close()


# ---------------------------
# CALENDARIO (VERSIONE FINAL)
# ---------------------------
elif sel == "CALENDARIO":
    st.markdown("### 📅 Calendario & Agenda")
    conn = get_connection()
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.markdown("#### ➕ Nuovo Appuntamento")
        with st.form("nev"):
            tit = st.text_input("Titolo / Cliente")
            dat = st.date_input("Data", format="DD/MM/YYYY") # DATA ITA
            ora = st.time_input("Ora")
            tip = st.selectbox("Tipo", ["Shooting", "Sopralluogo", "Riunione", "Consegna", "Colloquio"])
            tel = st.text_input("Telefono (per WhatsApp)")
            em = st.text_input("Email")
            not_ = st.text_area("Note Tecniche")
            
            if st.form_submit_button("📅 Aggiungi in Agenda"):
                conn.execute("INSERT INTO calendario (titolo, data, ora, tipo, note, telefono, email) VALUES (?,?,?,?,?,?,?)", (tit, dat, ora.strftime("%H:%M"), tip, not_, tel, em))
                conn.commit()
                st.success("Aggiunto!"); time.sleep(0.5); st.rerun()
        st.markdown("---")
        st.markdown("""<a href="https://calendar.google.com/calendar/u/0/r" target="_blank"><button style="background:#4285F4;color:white;padding:10px;border:none;border-radius:5px;width:100%;font-weight:bold;">🌍 GOOGLE CALENDAR</button></a>""", unsafe_allow_html=True)

    with c2:
        st.markdown("#### 🗓 Ordine del Giorno")
        filtro = st.radio("Mostra:", ["Futuri", "Tutti"], horizontal=True)
        q_cal = "SELECT * FROM calendario"; q_cal += " WHERE data >= DATE('now')" if filtro == "Futuri" else ""
        q_cal += " ORDER BY data, ora"
        ev = pd.read_sql_query(q_cal, conn)
        
        if not ev.empty:
            for _, r in ev.iterrows():
                data_ita = fmt_date(r['data'])
                icon = "🎥" if r['tipo'] == "Shooting" else "🕵️" if r['tipo'] == "Sopralluogo" else "🗣️" if r['tipo'] == "Colloquio" else "🤝"
                
                with st.expander(f"{icon} {data_ita} | {r['ora']} - {r['titolo']}"):
                    with st.container():
                        c_a, c_b = st.columns(2)
                        with c_a: new_tit = st.text_input("Titolo", value=r['titolo'], key=f"t_{r['id']}"); new_tel = st.text_input("Telefono", value=r['telefono'] if r['telefono'] else "", key=f"tel_{r['id']}")
                        
                        possibili_tipi = ["Shooting", "Sopralluogo", "Riunione", "Consegna", "Colloquio"]
                        idx_tipo = possibili_tipi.index(r['tipo']) if r['tipo'] in possibili_tipi else 0
                        
                        with c_b: new_tip = st.selectbox("Tipo", possibili_tipi, index=idx_tipo, key=f"tip_{r['id']}"); new_email = st.text_input("Email", value=r['email'] if r['email'] else "", key=f"em_{r['id']}")
                        new_note = st.text_area("Note Tecniche", value=r['note'], key=f"n_{r['id']}")
                        
                        col_wa, col_memo, col_mail, col_save, col_del = st.columns([1, 1, 1, 1, 0.5])
                        clean_num = new_tel.replace(" ", "").replace("-", "").replace("+", "") if new_tel else ""
                        
                        with col_wa:
                            if clean_num: st.markdown(f"""<a href="https://wa.me/{clean_num}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:8px 12px; border-radius:5px; width:100%;">💬 Chat</button></a>""", unsafe_allow_html=True)
                            else: st.caption("No Tel")
                        
                        with col_memo:
                            if clean_num:
                                txt_msg = f"Gentile {r['titolo']},\nle ricordiamo l'appuntamento confermato per il giorno {data_ita} alle ore {r['ora']}.\n\nCordiali saluti,\nTedesco Films"
                                enc_msg = urllib.parse.quote(txt_msg)
                                st.markdown(f"""<a href="https://wa.me/{clean_num}?text={enc_msg}" target="_blank"><button style="background-color:#F39C12; color:white; border:none; padding:8px 12px; border-radius:5px; width:100%;">🔔 Memo</button></a>""", unsafe_allow_html=True)
                            else: st.caption("-")

                        with col_mail:
                            if new_email: st.markdown(f"""<a href="mailto:{new_email}" target="_blank"><button style="background-color:#0072C6; color:white; border:none; padding:8px 12px; border-radius:5px; width:100%;">📧 Email</button></a>""", unsafe_allow_html=True)
                            else: st.caption("No Mail")

                        with col_save:
                            if st.button("💾 Salva", key=f"sv_{r['id']}"): conn.execute("UPDATE calendario SET titolo=?, tipo=?, note=?, telefono=?, email=? WHERE id=?", (new_tit, new_tip, new_note, new_tel, new_email, r['id'])); conn.commit(); st.success("Ok"); time.sleep(0.5); st.rerun()
                        with col_del:
                            if st.button("❌", key=f"del_{r['id']}"): conn.execute("DELETE FROM calendario WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        else: st.info("Nessun appuntamento in agenda.")
    conn.close()
