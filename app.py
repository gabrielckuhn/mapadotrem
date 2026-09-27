"""
MapaDoTrem — rotas no Metrô/CPTM de São Paulo
Rede baseada no "Mapa do Transporte Metropolitano" (julho/2026).
Rodar localmente:  streamlit run app.py
"""

import heapq
import streamlit as st

# ---------------------------------------------------------------------------
# 1. REDE
# ---------------------------------------------------------------------------
# Cada linha: nome, cor, cor do texto sobre a cor, operadora, minutos médios
# entre estações e a lista de estações NA ORDEM (a 1ª e a última são os
# terminais que dão nome aos sentidos).

LINHAS = {
    "1": dict(nome="Azul", cor="#0455A1", txt="#FFFFFF", op="Metrô", min=2, est=[
        "Tucuruvi", "Parada Inglesa", "Jardim São Paulo-Ayrton Senna", "Santana",
        "Carandiru", "Portuguesa-Tietê", "Armênia", "Tiradentes", "Luz", "São Bento",
        "Sé", "Japão-Liberdade", "São Joaquim", "Vergueiro", "Paraíso", "Ana Rosa",
        "Vila Mariana", "Santa Cruz", "Praça da Árvore", "Saúde", "São Judas",
        "Conceição", "Jabaquara"]),
    "2": dict(nome="Verde", cor="#007E5E", txt="#FFFFFF", op="Metrô", min=2, est=[
        "Vila Madalena", "Sumaré", "Clínicas", "Consolação", "Trianon-Masp",
        "Brigadeiro", "Paraíso", "Ana Rosa", "Chácara Klabin", "Santos-Imigrantes",
        "Alto do Ipiranga", "Sacomã", "Tamanduateí", "Vila Prudente"]),
    "3": dict(nome="Vermelha", cor="#EE372F", txt="#FFFFFF", op="Metrô", min=2, est=[
        "Palmeiras-Barra Funda", "Marechal Deodoro", "Santa Cecília", "República",
        "Anhangabaú", "Sé", "Pedro II", "Brás", "Bresser-Mooca", "Belém", "Tatuapé",
        "Carrão-Assaí Atacadista", "Penha-Lojas Besni", "Vila Matilde",
        "Guilhermina-Esperança", "Patriarca-Vila Ré", "Artur Alvim",
        "Corinthians-Itaquera"]),
    "4": dict(nome="Amarela", cor="#FFD400", txt="#1C2430", op="Motiva", min=2, est=[
        "Luz", "República", "Higienópolis-Mackenzie", "Paulista", "Oscar Freire",
        "Fradique Coutinho", "Faria Lima", "Pinheiros", "Butantã",
        "São Paulo-Morumbi", "Vila Sônia"]),
    "5": dict(nome="Lilás", cor="#9B3894", txt="#FFFFFF", op="Motiva", min=2, est=[
        "Capão Redondo", "Campo Limpo", "Vila das Belezas", "Giovanni Gronchi",
        "Santo Amaro", "Largo Treze", "Adolfo Pinheiro", "Alto da Boa Vista",
        "Borba Gato", "Brooklin", "Campo Belo", "Eucaliptos", "Moema",
        "AACD-Servidor", "Hospital São Paulo", "Santa Cruz", "Chácara Klabin"]),
    "6": dict(nome="Laranja", cor="#F68B1F", txt="#1C2430", op="Linha Uni", min=2, est=[
        "João Paulo I", "Freguesia do Ó", "Santa Marina", "Água Branca",
        "SESC-Pompeia", "Perdizes"]),
    "7": dict(nome="Rubi", cor="#A8105F", txt="#FFFFFF", op="TIC Trens", min=4, est=[
        "Jundiaí", "Várzea Paulista", "Campo Limpo Paulista", "Botujuru",
        "Francisco Morato", "Baltazar Fidélis", "Franco da Rocha", "Caieiras",
        "Perus", "Vila Aurora", "Jaraguá", "Vila Clarice", "Pirituba", "Piqueri",
        "Lapa", "Água Branca", "Palmeiras-Barra Funda"]),
    "8": dict(nome="Diamante", cor="#8A9390", txt="#FFFFFF", op="Motiva", min=3, est=[
        "Amador Bueno", "Santa Rita", "Itapevi", "Engenheiro Cardoso",
        "Sagrado Coração", "Jandira", "Jardim Silveira", "Jardim Belval", "Barueri",
        "Antônio João", "Santa Terezinha", "Carapicuíba", "General Miguel Costa",
        "Quitaúna", "Comandante Sampaio", "Osasco", "Presidente Altino",
        "Imperatriz Leopoldina", "Domingos de Moraes", "Lapa",
        "Palmeiras-Barra Funda", "Júlio Prestes"]),
    "9": dict(nome="Esmeralda", cor="#00A88E", txt="#FFFFFF", op="Motiva", min=3, est=[
        "Osasco", "Presidente Altino", "Ceasa", "Villa Lobos-Jaguaré",
        "Cidade Universitária", "Pinheiros", "Hebraica-Rebouças", "Cidade Jardim",
        "Vila Olímpia", "Berrini", "Morumbi", "Granja Julieta", "João Dias",
        "Santo Amaro", "Socorro", "Jurubatuba", "Autódromo", "Primavera-Interlagos",
        "Grajaú", "Mendes-Vila Natal", "Varginha"]),
    "10": dict(nome="Turquesa", cor="#008B9E", txt="#FFFFFF", op="CPTM", min=3, est=[
        "Brás", "Juventus-Mooca", "Ipiranga", "Tamanduateí", "São Caetano do Sul",
        "Utinga", "Prefeito Saladino", "Santo André", "Capuava", "Mauá",
        "Guapituba", "Ribeirão Pires", "Rio Grande da Serra"]),
    "11": dict(nome="Coral", cor="#F04E23", txt="#FFFFFF", op="Trivia", min=3, est=[
        "Palmeiras-Barra Funda", "Luz", "Brás", "Tatuapé", "Corinthians-Itaquera",
        "Dom Bosco", "José Bonifácio", "Guaianases", "Antonio Gianetti Neto",
        "Ferraz de Vasconcelos", "Poá", "Calmon Viana", "Suzano", "Jundiapeba",
        "Braz Cubas", "Mogi das Cruzes", "Estudantes"]),
    "12": dict(nome="Safira", cor="#133C8B", txt="#FFFFFF", op="Trivia", min=3, est=[
        "Brás", "Tatuapé", "Engenheiro Goulart", "USP Leste", "Comendador Ermelino",
        "São Miguel Paulista", "Jardim Helena-Vila Mara", "Itaim Paulista",
        "Jardim Romano", "Engenheiro Manoel Feio", "Itaquaquecetuba", "Aracaré",
        "Calmon Viana"]),
    "13": dict(nome="Jade", cor="#00B352", txt="#FFFFFF", op="Trivia", min=4, est=[
        "Engenheiro Goulart", "Guarulhos-Cecap", "Aeroporto-Guarulhos"]),
    "15": dict(nome="Prata", cor="#9AA3A8", txt="#1C2430", op="Metrô", min=2, est=[
        "Vila Prudente", "Oratório", "São Lucas", "Camilo Haddad", "Vila Tolstói",
        "Vila União", "Jardim Planalto", "Sapopemba", "Fazenda da Juta",
        "São Mateus", "Jardim Colonial"]),
    "17": dict(nome="Ouro", cor="#B8913A", txt="#1C2430", op="Metrô", min=2, est=[
        "Morumbi", "Chucri Zaidan", "Vila Cordeiro", "Campo Belo",
        "Vereador José Diniz", "Brooklin Paulista", "Aeroporto de Congonhas",
        "Washington Luís"]),
}

# Baldeações entre estações de NOMES DIFERENTES (ou com caminhada especial).
# (linha_a, estação_a, linha_b, estação_b, minutos, dica)
CONEXOES_ESPECIAIS = [
    ("4", "Paulista", "2", "Consolação", 7,
     "Paulista (Linha 4) e Consolação (Linha 2) são ligadas por um túnel com "
     "esteiras rolantes. É uma caminhada longa, de uns 5 a 7 minutos."),
]

DICA_LAPA = ("Atenção: as estações Lapa das Linhas 7 e 8 ficam em prédios "
             "separados. É preciso sair e caminhar pela rua até a outra "
             "estação, seguindo a sinalização.")
MIN_BALDEACAO = 4          # tempo médio de uma baldeação comum
PENALIDADE_LAPA = 12       # baldeação na rua, desencorajada


def rotulo(lid: str) -> str:
    return f"Linha {lid} · {LINHAS[lid]['nome']}"


def terminal(lid: str, de: str, para: str) -> str:
    est = LINHAS[lid]["est"]
    return est[-1] if est.index(para) > est.index(de) else est[0]


# ---------------------------------------------------------------------------
# 2. GRAFO + DIJKSTRA
# ---------------------------------------------------------------------------
# Nó = (linha, estação). Arestas de viagem entre vizinhas; arestas de
# baldeação entre nós da mesma estação (ou conexões especiais).

@st.cache_data
def montar_grafo():
    grafo = {}
    por_nome = {}

    def add(a, b, custo, tipo, dica=None):
        grafo.setdefault(a, []).append((b, custo, tipo, dica))

    for lid, d in LINHAS.items():
        est = d["est"]
        for i, s in enumerate(est):
            por_nome.setdefault(s, []).append(lid)
            grafo.setdefault((lid, s), [])
            if i + 1 < len(est):
                add((lid, s), (lid, est[i + 1]), d["min"], "viagem")
                add((lid, est[i + 1]), (lid, s), d["min"], "viagem")

    for s, lids in por_nome.items():
        for a in lids:
            for b in lids:
                if a == b:
                    continue
                if s == "Lapa" and {a, b} == {"7", "8"}:
                    add((a, s), (b, s), PENALIDADE_LAPA, "baldeacao", DICA_LAPA)
                else:
                    add((a, s), (b, s), MIN_BALDEACAO, "baldeacao")

    for la, sa, lb, sb, m, dica in CONEXOES_ESPECIAIS:
        add((la, sa), (lb, sb), m, "baldeacao", dica)
        add((lb, sb), (la, sa), m, "baldeacao", dica)

    return grafo, por_nome


def buscar_rota(origem: str, destino: str, penalidade_extra: int):
    """Dijkstra. Começa em todas as linhas da estação de origem (a pessoa já
    está lá dentro) e termina em qualquer linha da estação de destino."""
    grafo, por_nome = montar_grafo()
    dist, prev, heap = {}, {}, []
    for lid in por_nome[origem]:
        n = (lid, origem)
        dist[n] = (0, 0)  # (custo de busca, tempo real)
        heapq.heappush(heap, (0, 0, n))

    alvo = None
    while heap:
        c, t, n = heapq.heappop(heap)
        if (c, t) != dist.get(n):
            continue
        if n[1] == destino:
            alvo = n
            break
        for viz, custo, tipo, dica in grafo[n]:
            extra = penalidade_extra if tipo == "baldeacao" else 0
            nc, nt = c + custo + extra, t + custo
            if viz not in dist or (nc, nt) < dist[viz]:
                dist[viz] = (nc, nt)
                prev[viz] = (n, dica)
                heapq.heappush(heap, (nc, nt, viz))

    if alvo is None:
        return None

    caminho, dicas, n = [alvo], {}, alvo
    while n in prev:
        p, dica = prev[n]
        if dica:
            dicas[(p, n)] = dica
        caminho.append(p)
        n = p
    caminho.reverse()

    # Agrupa em trechos contínuos na mesma linha
    trechos = []
    for i, (lid, s) in enumerate(caminho):
        if not trechos or trechos[-1]["linha"] != lid:
            dica = dicas.get((caminho[i - 1], caminho[i])) if i else None
            trechos.append(dict(linha=lid, est=[s], dica_entrada=dica))
        else:
            trechos[-1]["est"].append(s)
    trechos = [t for t in trechos if len(t["est"]) > 1]
    return dict(trechos=trechos, minutos=dist[alvo][1])


# ---------------------------------------------------------------------------
# 3. INTERFACE
# ---------------------------------------------------------------------------

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600;700&display=swap');

:root{
  --ink:#1C2430; --muted:#5B6673; --paper:#FFFFFF; --rail:#E4E8EC; --soft:#F3F5F7;
}
html, body, [class*="css"], .stApp { font-family:'Barlow', system-ui, sans-serif; }
#MainMenu, footer, header [data-testid="stToolbar"] { visibility:hidden; }
.block-container{ max-width:680px; padding:1.2rem 1rem 4rem; }

/* Cabeçalho em forma de placa de estação */
.placa{ background:var(--ink); color:#fff; border-radius:14px; overflow:hidden;
  margin-bottom:1.1rem; }
.placa .faixas{ display:flex; height:8px; }
.placa .faixas span{ flex:1; }
.placa .corpo{ padding:1.1rem 1.2rem 1.2rem; }
.placa h1{ font-family:'Barlow Condensed', sans-serif; font-weight:700;
  font-size:2.6rem; line-height:1; margin:0; padding:0; color:#fff; letter-spacing:.5px; }
.placa p{ margin:.45rem 0 0; color:#C9D1D9; font-size:1rem; line-height:1.4; }

.rotulo-bloco{ font-family:'Barlow Condensed', sans-serif; font-weight:700;
  font-size:1.25rem; color:var(--ink); margin:.4rem 0 .1rem; display:flex;
  align-items:center; gap:.5rem; }
.pino{ width:14px; height:14px; border-radius:50%; border:3px solid var(--ink);
  background:#fff; display:inline-block; }
.pino.cheio{ background:var(--ink); }

/* Resumo */
.resumo{ display:flex; gap:.5rem; margin:1.1rem 0 .9rem; }
.resumo div{ flex:1; background:var(--soft); border-radius:12px; padding:.7rem .6rem;
  text-align:center; color:var(--ink); }
.resumo b{ display:block; font-family:'Barlow Condensed', sans-serif; font-size:1.7rem;
  line-height:1; }
.resumo small{ color:var(--muted); font-size:.82rem; }
.sequencia{ display:flex; flex-wrap:wrap; align-items:center; gap:.35rem;
  margin-bottom:1rem; }
.sequencia .seta{ color:var(--muted); font-weight:700; }

.selo{ display:inline-flex; align-items:center; gap:.35rem; border-radius:999px;
  padding:.18rem .65rem .18rem .2rem; font-weight:600; font-size:.88rem; white-space:nowrap; }
.selo .num{ display:inline-flex; align-items:center; justify-content:center;
  min-width:1.45rem; height:1.45rem; border-radius:50%; background:rgba(255,255,255,.92);
  color:#1C2430; font-family:'Barlow Condensed', sans-serif; font-weight:700; font-size:.95rem; }

/* Linha do tempo = diagrama de linha de metrô */
.rota{ background:var(--paper); border:1px solid var(--rail); border-radius:16px;
  padding:1rem .9rem .4rem; color:var(--ink); }
.passo{ position:relative; padding:0 0 1.15rem 2.3rem; }
.passo::before{ content:""; position:absolute; left:.62rem; top:.3rem; bottom:-.3rem;
  width:6px; border-radius:3px; background:var(--c, var(--rail)); }
.passo.fim::before{ display:none; }
.passo.caminhada::before{ background:repeating-linear-gradient(var(--muted) 0 5px, transparent 5px 10px);
  width:3px; left:.78rem; }
.passo .no{ position:absolute; left:.2rem; top:.1rem; width:1.4rem; height:1.4rem;
  border-radius:50%; background:#fff; border:4px solid var(--c, var(--ink)); box-sizing:border-box; }
.passo.caminhada .no, .passo.chegada .no{ border-color:var(--ink); }
.passo.chegada .no{ background:var(--ink); }
.passo h4{ margin:0 0 .2rem; font-size:1.05rem; font-weight:700; line-height:1.3; color:var(--ink); }
.passo p{ margin:.15rem 0; font-size:.95rem; line-height:1.45; color:#39434F; }
.aviso{ background:#FFF6D6; border-radius:10px; padding:.55rem .7rem; margin:.45rem 0 .1rem;
  font-size:.9rem; line-height:1.4; color:#4A3B00; }
.placa-sentido{ display:inline-block; margin:.35rem 0 .2rem; border-radius:8px;
  padding:.35rem .7rem; font-family:'Barlow Condensed', sans-serif; font-weight:700;
  font-size:1.15rem; background:var(--c); color:var(--t); }
details{ margin:.35rem 0 .1rem; }
details summary{ cursor:pointer; color:var(--muted); font-size:.9rem; font-weight:600; }
details ol{ margin:.4rem 0 0 1.1rem; padding:0; font-size:.92rem; color:#39434F; }
details li{ margin:.1rem 0; }

.rodape{ color:var(--muted); font-size:.82rem; line-height:1.45; margin-top:1rem; }

@media (max-width:480px){
  .placa h1{ font-size:2.2rem; }
  .resumo b{ font-size:1.45rem; }
  .passo{ padding-left:2.1rem; }
}
@media (prefers-color-scheme: dark){
  .rotulo-bloco{ color:#E8ECF0; }
  .pino{ border-color:#E8ECF0; background:transparent; }
  .pino.cheio{ background:#E8ECF0; }
  .rodape{ color:#9AA5B1; }
}
</style>
"""


def selo(lid: str) -> str:
    d = LINHAS[lid]
    return (f'<span class="selo" style="background:{d["cor"]};color:{d["txt"]}">'
            f'<span class="num">{lid}</span>{d["nome"]}</span>')


def html_rota(rota, origem, destino) -> str:
    trechos = rota["trechos"]
    n_est = sum(len(t["est"]) - 1 for t in trechos)
    n_bald = len(trechos) - 1

    h = ['<div class="resumo">',
         f'<div><b>~{rota["minutos"]}</b><small>minutos</small></div>',
         f'<div><b>{n_est}</b><small>paradas</small></div>',
         f'<div><b>{n_bald}</b><small>{"baldeação" if n_bald == 1 else "baldeações"}</small></div>',
         '</div><div class="sequencia">']
    h.append('<span class="seta">›</span>'.join(selo(t["linha"]) for t in trechos))
    h.append('</div><div class="rota">')

    for i, t in enumerate(trechos):
        lid, est = t["linha"], t["est"]
        d = LINHAS[lid]
        c = f'--c:{d["cor"]};--t:{d["txt"]}'
        emb, des = est[0], est[-1]
        sent = terminal(lid, emb, est[1])
        paradas = len(est) - 1
        prox = est[1]

        # Embarque
        titulo = (f"Entre na estação {emb}" if i == 0 else f"Embarque na {rotulo(lid)}")
        h.append(f'<div class="passo" style="{c}"><span class="no"></span>')
        h.append(f'<h4>{titulo}</h4>')
        h.append(f'<p>Pegue a <b>{rotulo(lid)}</b> na plataforma com a placa:</p>')
        h.append(f'<span class="placa-sentido">Sentido {sent}</span>')
        h.append(f'<p>A próxima estação precisa ser <b>{prox}</b>. Se o trem parar em '
                 f'outra, você está no sentido errado: desça e vá para a plataforma oposta.</p>')
        h.append('</div>')

        # Viagem
        h.append(f'<div class="passo" style="{c}"><span class="no"></span>')
        if paradas == 1:
            h.append(f'<h4>Viaje 1 parada</h4><p>Desça já na próxima estação, <b>{des}</b>.</p>')
        else:
            h.append(f'<h4>Viaje {paradas} paradas</h4>'
                     f'<p>Fique no trem e não desça antes de <b>{des}</b>.</p>')
            lista = "".join(f"<li>{s}</li>" for s in est[1:])
            h.append(f'<details><summary>Ver as {paradas} estações do trecho</summary>'
                     f'<ol>{lista}</ol></details>')
        h.append('</div>')

        # Desembarque / baldeação
        if i < len(trechos) - 1:
            nxt = trechos[i + 1]
            nl, ne = nxt["linha"], nxt["est"][0]
            h.append(f'<div class="passo caminhada" style="{c}"><span class="no"></span>')
            h.append(f'<h4>Desça em {des} e faça baldeação</h4>')
            if ne == des:
                h.append(f'<p>Dentro da estação {des}, siga as placas '
                         f'<b>“{rotulo(nl)}”</b> até a plataforma dela.</p>')
            else:
                h.append(f'<p>Siga as placas <b>“{rotulo(nl)}”</b> até a estação '
                         f'<b>{ne}</b>.</p>')
            if nxt.get("dica_entrada"):
                h.append(f'<div class="aviso">{nxt["dica_entrada"]}</div>')
            h.append('</div>')
        else:
            h.append('<div class="passo chegada fim"><span class="no"></span>')
            h.append(f'<h4>Desça em {des}. Você chegou.</h4>')
            h.append('</div>')

    h.append('</div>')
    return "".join(h)


def trocar():
    s = st.session_state
    ol, dl = s.o_linha, s.d_linha
    oe, de = s.get(f"o_est_{ol}"), s.get(f"d_est_{dl}")
    s.o_linha, s.d_linha = dl, ol
    s[f"o_est_{dl}"], s[f"d_est_{ol}"] = de, oe


def seletor(prefixo: str, titulo: str, cheio: bool):
    classe = "pino cheio" if cheio else "pino"
    st.markdown(f'<div class="rotulo-bloco"><span class="{classe}"></span>{titulo}</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.4])
    with c1:
        lid = st.selectbox("Linha", list(LINHAS), format_func=rotulo,
                           key=f"{prefixo}_linha")
    with c2:
        est = st.selectbox("Estação", LINHAS[lid]["est"], key=f"{prefixo}_est_{lid}")
    return lid, est


def main():
    st.set_page_config(page_title="MapaDoTrem", page_icon="🚇", layout="centered",
                       initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)

    s = st.session_state
    if "o_linha" not in s:
        s.o_linha, s["o_est_4"] = "4", "Oscar Freire"
        s.d_linha, s["d_est_1"] = "1", "Vergueiro"

    faixas = "".join(f'<span style="background:{d["cor"]}"></span>' for d in LINHAS.values())
    st.markdown(
        f'<div class="placa"><div class="faixas">{faixas}</div><div class="corpo">'
        f'<h1>MapaDoTrem</h1>'
        f'<p>Escolha de onde você sai e aonde quer chegar. Mostramos em qual '
        f'sentido embarcar e onde trocar de linha.</p></div></div>',
        unsafe_allow_html=True)

    _, origem = seletor("o", "Partida", False)
    st.button("⇅  Inverter partida e destino", on_click=trocar, use_container_width=True)
    _, destino = seletor("d", "Destino", True)

    modo = st.radio("Preferência", ["Mais rápida", "Menos baldeações"],
                    horizontal=True, label_visibility="collapsed")

    if origem == destino:
        st.info("Partida e destino são a mesma estação. Escolha outra estação de destino.")
        return

    rota = buscar_rota(origem, destino, 3 if modo == "Mais rápida" else 60)
    if rota is None:
        st.error("Não encontramos ligação entre essas estações na rede atual.")
        return

    st.markdown(html_rota(rota, origem, destino), unsafe_allow_html=True)
    st.markdown(
        '<p class="rodape">Tempos aproximados, sem contar a espera pelo trem. '
        'Rede conforme o mapa oficial de julho/2026. Horários, obras e integrações '
        'tarifadas podem mudar; confira no site da operadora antes de sair.</p>',
        unsafe_allow_html=True)


if __name__ == "__main__":
    main()
