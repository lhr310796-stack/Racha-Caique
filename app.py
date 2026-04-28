import streamlit as st
import pandas as pd
import os
import time
import base64
from io import BytesIO
from datetime import date, timedelta
from PIL import Image, ImageOps

# 1. CONFIGURAÇÃO E ESTILO "ARENA LARANJA"
st.set_page_config(page_title="Gestão - Racha", layout="wide")

URL_FUNDO = "https://img.freepik.com/vetores-gratis/fundo-do-campo-de-futebol-de-estilo-gradiente_23-2148995842.jpg?semt=ais_hybrid&w=740&q=80"

st.markdown(f"""
    <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("{URL_FUNDO}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            z-index: 0;
        }}

        [data-testid="stVerticalBlock"] {{ position: relative; z-index: 1; }}

        label[data-testid="stWidgetLabel"] p {{ color: white !important; font-size: 16px !important; font-weight: bold; }}
        div[data-baseweb="radio"] label p {{ color: white !important; font-weight: bold !important; }}
        
        div[data-baseweb="select"] span {{ color: black !important; font-weight: bold !important; }}
        div[data-baseweb="select"] div {{ color: black !important; }}
        
        .stTextInput input {{ background-color: white !important; color: black !important; font-weight: bold !important; }}

        html, body, [class*="st-"] {{ font-size: 14px !important; color: #ffffff !important; }}
        h1, h2, h3 {{ color: #ffffff !important; text-shadow: 2px 2px 4px #000; }}
        
        div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {{
            background-color: rgba(0, 0, 0, 0.85) !important;
            border: 1px solid #25D366 !important;
            border-radius: 15px;
            padding: 20px;
        }}

        iframe {{ background-color: transparent !important; border: none !important; }}
    </style>
""", unsafe_allow_html=True)

# 2. VARIÁVEIS E FUNÇÕES
DATABASE = "atletas.csv"
HISTORICO_TIMES = "historico_times.csv"
RESULTADOS_DB = "resultados.csv"
PASTA_FOTOS = "fotos"

if not os.path.exists(PASTA_FOTOS): os.makedirs(PASTA_FOTOS)

def carregar_dados():
    if os.path.exists(DATABASE): return pd.read_csv(DATABASE)
    return pd.DataFrame(columns=["Nome", "Tipo", "Estrelas", "Posicao"])

def salvar_csv(df, nome): df.to_csv(nome, index=False)

def carregar_historico():
    if os.path.exists(HISTORICO_TIMES): return pd.read_csv(HISTORICO_TIMES)
    return pd.DataFrame(columns=["Data", "TimeA", "TimeB"])

def carregar_resultados():
    if os.path.exists(RESULTADOS_DB) and os.path.getsize(RESULTADOS_DB) > 0:
        df = pd.read_csv(RESULTADOS_DB)
        # Correção: Transformando em data real para o sistema ordenar corretamente
        df['Data_Real'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        return df.sort_values(by="Data_Real", ascending=False).drop(columns=['Data_Real'])
    return pd.DataFrame(columns=["Data", "GolsA", "GolsB"])

def img_to_base64(caminho):
    if os.path.exists(caminho):
        try:
            with Image.open(caminho) as img:
                img.thumbnail((80, 80))
                buf = BytesIO()
                img.save(buf, format="PNG")
                return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
        except: return ""
    return ""

def processar_e_salvar_foto(arquivo_foto, nome_atleta):
    caminho = os.path.join(PASTA_FOTOS, f"{nome_atleta}.png")
    img = Image.open(arquivo_foto)
    img_ajustada = ImageOps.fit(img, (300, 300), Image.Resampling.LANCZOS)
    img_ajustada.save(caminho)

def obter_segundas():
    hoje = date.today()
    dias = (0 - hoje.weekday()) % 7
    prox = hoje + timedelta(days=dias)
    return [(prox + timedelta(weeks=i)).strftime("%d/%m/%Y") for i in range(12)]

# --- INTERFACE ---
st.sidebar.title("🏟️ Arena Racha)
menu = ["Escalação Automática", "Lançar Pontos", "Histórico de Partidas", "Tabela e Pódio", "Ver Atletas", "Cadastrar Atletas", "Gerenciar Elenco"]
escolha = st.sidebar.selectbox("Navegação", menu)

df_at = carregar_dados()

# --- 1. ESCALAÇÃO ---
if escolha == "Escalação Automática":
    st.header("📋 Sorteio Equilibrado")
    segundas = obter_segundas()
    col1, col2 = st.columns([1, 2.5], gap="large")
    
    with col1:
        data_s = st.selectbox("Data do Jogo:", segundas)
        h_check = carregar_historico()
        ja_escalado = data_s in h_check["Data"].values
        if ja_escalado:
            st.warning("🔒 Escalação Oficial Bloqueada.")
            if st.button("🗑️ Excluir para Novo Sorteio"):
                salvar_csv(h_check[h_check["Data"] != data_s], HISTORICO_TIMES)
                st.rerun()
        fixos = df_at[df_at["Tipo"] == "Fixo"]
        faltas = st.multiselect("Ausentes (Fixos):", fixos["Nome"].tolist(), disabled=ja_escalado)
        subs = st.multiselect("Substitutos (Visitantes):", df_at[df_at["Tipo"] == "Visitante"]["Nome"].tolist(), disabled=ja_escalado)
        st.button("🎲 Re-sortear", disabled=ja_escalado)

    with col2:
        if ja_escalado:
            p = h_check[h_check["Data"] == data_s].iloc[0]
            t1_nomes, t2_nomes = str(p["TimeA"]).split(","), str(p["TimeB"]).split(",")
        else:
            confirmados = [n for n in fixos["Nome"].tolist() if n not in faltas] + subs
            df_c = df_at[df_at["Nome"].isin(confirmados)].copy()
            gols = df_c[df_c["Posicao"] == "Goleiro"]
            lins = df_c[df_c["Posicao"] == "Linha"]
            if len(gols) == 2 and len(lins) == 12:
                t1_nomes, t2_nomes = [], []
                soma1, soma2 = 0, 0
                g_sh = gols.sample(frac=1).sort_values("Estrelas", ascending=False)
                t1_nomes.append(g_sh.iloc[0]["Nome"]); soma1 += g_sh.iloc[0]["Estrelas"]
                t2_nomes.append(g_sh.iloc[1]["Nome"]); soma2 += g_sh.iloc[1]["Estrelas"]
                l_sh = lins.sample(frac=1).sort_values("Estrelas", ascending=False)
                for _, player in l_sh.iterrows():
                    if soma1 <= soma2:
                        t1_nomes.append(player["Nome"]); soma1 += player["Estrelas"]
                    else:
                        t2_nomes.append(player["Nome"]); soma2 += player["Estrelas"]
                st.success(f"⚖️ Paridade Técnica: Time A ({soma1}⭐) vs Time B ({soma2}⭐)")
            else:
                # Correção: Mensagem detalhada para entender por que não formou 14
                st.info(f"Escalação inválida. Selecionados: {len(gols)} Goleiros e {len(lins)} de Linha. Necessário: Exatamente 2 Goleiros e 12 de Linha.")
                st.stop()

        c1, c2 = st.columns(2)
        for names, col, lbl in [(t1_nomes, c1, "Time A"), (t2_nomes, c2, "Time B")]:
            with col:
                with st.container(border=True):
                    st.subheader(lbl)
                    for n in names:
                        pos = df_at[df_at["Nome"] == n]["Posicao"].values[0]
                        st.write(f"{'🧤' if pos == 'Goleiro' else '⚽'} {n}")
        
        if not ja_escalado:
            if st.button("💾 Salvar Escalação Oficial", use_container_width=True, type="primary"):
                salvar_csv(pd.concat([h_check, pd.DataFrame({"Data":[data_s],"TimeA":[",".join(t1_nomes)],"TimeB":[",".join(t2_nomes)]})]), HISTORICO_TIMES)
                st.rerun()

# --- 2. LANÇAR PONTOS ---
elif escolha == "Lançar Pontos":
    st.header("📝 Resultado do Jogo")
    h = carregar_historico()
    if h.empty: st.warning("Salve uma escalação primeiro!")
    else:
        dt = st.selectbox("Selecione a Data:", h["Data"].unique())
        res_check = carregar_resultados()
        ja_tem = dt in res_check["Data"].values
        if ja_tem:
            st.error(f"🔒 Placar oficializado.")
            p = res_check[res_check["Data"] == dt].iloc[0]
            vA, vB = str(p["GolsA"]), str(p["GolsB"])
            if st.button("🗑️ Excluir Resultado"):
                salvar_csv(res_check[res_check["Data"] != dt], RESULTADOS_DB)
                st.rerun()
        else: vA, vB = "0", "0"

        cA, cX, cB = st.columns([2, 1, 2])
        with cA: gA = st.text_input("Gols Time A:", value=vA, disabled=ja_tem)
        with cX: st.markdown("<h1 style='text-align:center; margin-top:30px;'>X</h1>", unsafe_allow_html=True)
        with cB: gB = st.text_input("Gols Time B:", value=vB, disabled=ja_tem)
        if not ja_tem:
            if st.button("🏆 Gravar Placar Final", type="primary", use_container_width=True):
                salvar_csv(pd.concat([res_check, pd.DataFrame({"Data":[dt],"GolsA":[int(gA)],"GolsB":[int(gB)]})]), RESULTADOS_DB)
                st.success("Placar Oficializado!"); time.sleep(1); st.rerun()

# --- 3. NOVA ABA: HISTÓRICO DE PARTIDAS ---
elif escolha == "Histórico de Partidas":
    st.header("📜 Histórico de Confrontos")
    res = carregar_resultados()
    hist = carregar_historico()
    
    if res.empty:
        st.info("Nenhuma partida finalizada ainda.")
    else:
        for _, r in res.iterrows():
            data_jogo = r["Data"]
            match_hist = hist[hist["Data"] == data_jogo]
            
            if not match_hist.empty:
                with st.container(border=True):
                    st.markdown(f"### 🗓️ Partida de {data_jogo}")
                    c1, cPlacar, c2 = st.columns([2, 1.5, 2])
                    
                    with cPlacar:
                        st.markdown(f"<h1 style='text-align:center; color:gold;'>{r['GolsA']} x {r['GolsB']}</h1>", unsafe_allow_html=True)
                    
                    with c1:
                        st.write("**🛡️ Time A**")
                        for n in str(match_hist.iloc[0]["TimeA"]).split(","):
                            st.write(f"- {n}")
                    
                    with c2:
                        st.write("**🛡️ Time B**")
                        for n in str(match_hist.iloc[0]["TimeB"]).split(","):
                            st.write(f"- {n}")
                st.write("") 

# --- 4. TABELA E PÓDIO ---
elif escolha == "Tabela e Pódio":
    st.header("🏆 Classificação")
    res, hist = carregar_resultados(), carregar_historico()
    if res.empty: st.info("Sem jogos registrados.")
    else:
        def calcular_rank(ate_dt=None):
            rk = {n: 0 for n in df_at["Nome"].tolist()}
            rf = res.copy()
            if ate_dt is not None:
                # Correção: Transformando a data da partida para calcular quem subiu ou desceu corretamente
                rf['Data_Temp'] = pd.to_datetime(rf['Data'], format='%d/%m/%Y')
                dt_limit = pd.to_datetime(ate_dt, format='%d/%m/%Y')
                rf = rf[rf['Data_Temp'] < dt_limit]
                
            for _, r in rf.iterrows():
                m = hist[hist["Data"] == r["Data"]]
                if not m.empty:
                    tA, tB = str(m.iloc[0]["TimeA"]).split(","), str(m.iloc[0]["TimeB"]).split(",")
                    if r["GolsA"] > r["GolsB"]:
                        for p in tA: rk[p] = rk.get(p, 0) + 3
                    elif r["GolsB"] > r["GolsA"]:
                        for p in tB: rk[p] = rk.get(p, 0) + 3
                    else:
                        for p in tA+tB: rk[p] = rk.get(p, 0) + 1
            return pd.DataFrame(list(rk.items()), columns=["Atleta", "Pts"]).sort_values(by=["Pts", "Atleta"], ascending=[False, True]).reset_index(drop=True)

        df_at_rk = calcular_rank()
        datas = res["Data"].tolist()
        
        # Correção: Buscando o ranking da rodada atual e anterior
        df_ant = calcular_rank(ate_dt=datas[0]) if len(datas) > 1 else df_at_rk.copy()

        if len(df_at_rk) >= 3 and df_at_rk.iloc[0]["Pts"] > 0:
            b1 = img_to_base64(f"{PASTA_FOTOS}/{df_at_rk.iloc[0]['Atleta']}.png")
            b2 = img_to_base64(f"{PASTA_FOTOS}/{df_at_rk.iloc[1]['Atleta']}.png")
            b3 = img_to_base64(f"{PASTA_FOTOS}/{df_at_rk.iloc[2]['Atleta']}.png")
            def t(b): return f'<img src="{b}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid gold;">' if b else '👤'
            st.markdown(f"""<div style="display:flex;justify-content:center;align-items:flex-end;gap:15px;height:240px;padding:20px;">
                <div style="text-align:center;"><small>{df_at_rk.iloc[1]['Atleta']}</small><br><b>{df_at_rk.iloc[1]['Pts']} pts</b><br>{t(b2)}<div style="background:#C0C0C0;height:60px;width:100px;border-radius:5px 5px 0 0;font-size:2rem;font-weight:bold;">2</div></div>
                <div style="text-align:center;"><small>{df_at_rk.iloc[0]['Atleta']}</small><br><b>{df_at_rk.iloc[0]['Pts']} pts</b><br>{t(b1)}<div style="background:#FFD700;height:100px;width:110px;border-radius:5px 5px 0 0;font-size:3rem;font-weight:bold;">1</div></div>
                <div style="text-align:center;"><small>{df_at_rk.iloc[2]['Atleta']}</small><br><b>{df_at_rk.iloc[2]['Pts']} pts</b><br>{t(b3)}<div style="background:#CD7F32;height:40px;width:100px;border-radius:5px 5px 0 0;font-size:1.5rem;font-weight:bold;">3</div></div>
            </div>""", unsafe_allow_html=True)

        txt_zap = f"2026 🏆🔥 *🗓️ {date.today().strftime('%d/%m')}*\n\n🏆\n\n"
        for i, row in df_at_rk.iterrows():
            pos = i + 1
            n, pts = row['Atleta'], row['Pts']
            try:
                p_ant = df_ant[df_ant['Atleta'] == n].index[0] + 1
                seta = "⬆️" if pos < p_ant else ("⬇️" if pos > p_ant else "⏺️")
            except: seta = "⏺️"
            med = "🥇" if pos==1 else ("🥈" if pos==2 else ("🥉" if pos==3 else f"{pos}-"))
            txt_zap += f"{med} ➖ {pts:02}pts- {n} {seta}\n"
        txt_zap += "\nsérie B ⬇️\n🔥🔥🔥🔥🔥🔥🔥🔥"
        
        # Correção: O componente de HTML para clipboard estava dando erro por causa dos frames do Streamlit
        st.markdown("**📋 Copie o ranking abaixo para o WhatsApp:**")
        st.code(txt_zap, language="markdown")
        
        df_show = df_at_rk.copy(); df_show.index = df_show.index + 1
        st.dataframe(df_show, use_container_width=True)

elif escolha == "Ver Atletas":
    st.header("👥 Elenco")
    if not df_at.empty:
        cols = st.columns(5)
        for i, r in df_at.reset_index().iterrows():
            with cols[i % 5]:
                with st.container(border=True):
                    path = f"{PASTA_FOTOS}/{r['Nome']}.png"
                    if os.path.exists(path): st.image(path)
                    else: st.info("👤")
                    st.write(f"**{r['Nome']}**")
                    ico = "🧤" if r['Posicao'] == "Goleiro" else "⚽"
                    st.caption(f"{ico} {r['Posicao']} | {'⭐'*int(r['Estrelas'])}")

elif escolha == "Cadastrar Atletas":
    st.header("📝 Novo Cadastro")
    with st.form("cad", clear_on_submit=True):
        n = st.text_input("Nome:")
        c1, c2 = st.columns(2)
        with c1:
            t = st.radio("Vínculo:", ["Fixo", "Visitante"], horizontal=True)
            p = st.selectbox("Posição:", ["Linha", "Goleiro"])
        with c2:
            e = st.selectbox("Nível:", [1,2,3,4,5], index=2)
        f = st.file_uploader("Foto", type=["png", "jpg"])
        if st.form_submit_button("💾 Salvar Atleta"):
            if n:
                if f: processar_e_salvar_foto(f, n)
                salvar_csv(pd.concat([df_at, pd.DataFrame({"Nome":[n],"Tipo":[t],"Estrelas":[e],"Posicao":[p]})]), DATABASE)
                st.success("Cadastrado!"); st.rerun()

elif escolha == "Gerenciar Elenco":
    st.header("⚙️ Editar Elenco")
    if not df_at.empty:
        sel = st.selectbox("Escolha o Atleta:", df_at["Nome"].tolist())
        d = df_at[df_at["Nome"] == sel].iloc[0]
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            p_at = f"{PASTA_FOTOS}/{sel}.png"
            if os.path.exists(p_at): st.image(p_at)
        with c2:
            nn = st.text_input("Nome:", value=d["Nome"])
            nt = st.radio("Vínculo:", ["Fixo", "Visitante"], index=0 if d["Tipo"]=="Fixo" else 1)
            np = st.selectbox("Posição:", ["Linha", "Goleiro"], index=0 if d["Posicao"]=="Linha" else 1)
            ne = st.selectbox("Nível (Estrelas):", [1,2,3,4,5], index=int(d["Estrelas"])-1)
            nf = st.file_uploader("Trocar Foto", type=["png", "jpg"])
            if st.button("🔄 Atualizar Atleta"):
                if nn != sel and os.path.exists(f"{PASTA_FOTOS}/{sel}.png"): os.rename(f"{PASTA_FOTOS}/{sel}.png", f"{PASTA_FOTOS}/{nn}.png")
                if nf: processar_e_salvar_foto(nf, nn)
                df_at.loc[df_at["Nome"] == sel, ["Nome", "Tipo", "Estrelas", "Posicao"]] = [nn, nt, ne, np]
                salvar_csv(df_at, DATABASE); st.success("Atualizado!"); time.sleep(1); st.rerun()
        with c3:
            if st.button("❌ Excluir Atleta", type="primary"):
                if os.path.exists(f"{PASTA_FOTOS}/{sel}.png"): os.remove(f"{PASTA_FOTOS}/{sel}.png")
                salvar_csv(df_at[df_at["Nome"] != sel], DATABASE); st.rerun()