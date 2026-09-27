"""
MapaDoTrem — rotas no Metrô/CPTM de São Paulo
Rede baseada no "Mapa do Transporte Metropolitano" (julho/2026).
Coordenadas das estações: base oficial do Centro de Estudos da Metrópole
(CEM, 2025). Linhas 6, 17 e a estação Varginha: coordenadas aproximadas.

Busca de endereços: Nominatim (OpenStreetMap), gratuito e sem chave.
Rodar localmente:  streamlit run app.py
"""

import heapq
import math
from urllib.parse import urlencode

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

# Troque pelo seu e-mail: a política do Nominatim pede um contato no User-Agent.
CONTATO = "seu-email@exemplo.com"

# ---------------------------------------------------------------------------
# 1. REDE
# ---------------------------------------------------------------------------
# Cada linha: nome, cor, cor do texto, operadora, minutos médios entre
# estações e a lista de estações NA ORDEM (1ª e última = nomes dos sentidos).

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
        "Lapa", "Água Branca", "Palmeiras-Barra Funda", "Luz"]),
    "8": dict(nome="Diamante", cor="#8A9390", txt="#FFFFFF", op="Motiva", min=3, est=[
        "Amador Bueno", "Ambuitá", "Santa Rita", "Itapevi", "Engenheiro Cardoso",
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
        "Luz", "Brás", "Juventus-Mooca", "Ipiranga", "Tamanduateí", "São Caetano do Sul",
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

# Baldeações entre estações de NOMES DIFERENTES.
# (linha_a, estação_a, linha_b, estação_b, minutos, dica)
CONEXOES_ESPECIAIS = [
    ("4", "Paulista", "2", "Consolação", 7,
     "Paulista (Linha 4) e Consolação (Linha 2) são ligadas por um túnel com "
     "esteiras rolantes. É uma caminhada longa, de uns 5 a 7 minutos."),
]
DICA_LAPA = ("Atenção: as estações Lapa das Linhas 7 e 8 ficam em prédios "
             "separados. É preciso sair e caminhar pela rua até a outra "
             "estação, seguindo a sinalização.")
MIN_BALDEACAO = 4
PENALIDADE_LAPA = 12

# Coordenadas (lat, lon). "Lapa|7" e "Lapa|8" são prédios diferentes.
COORDS = {
    "Tucuruvi": (-23.48023, -46.60332), "Parada Inglesa": (-23.48701, -46.6088),
    "Jardim São Paulo-Ayrton Senna": (-23.49246, -46.61705),
    "Santana": (-23.50263, -46.6247), "Carandiru": (-23.50954, -46.62491),
    "Portuguesa-Tietê": (-23.51626, -46.62511), "Armênia": (-23.52549, -46.62928),
    "Tiradentes": (-23.53098, -46.6321), "Luz": (-23.53689, -46.63367),
    "São Bento": (-23.54427, -46.63399), "Sé": (-23.55018, -46.63287),
    "Japão-Liberdade": (-23.55513, -46.63581), "São Joaquim": (-23.56184, -46.63869),
    "Vergueiro": (-23.56913, -46.63982), "Paraíso": (-23.5758, -46.64076),
    "Ana Rosa": (-23.58118, -46.63838), "Vila Mariana": (-23.58926, -46.6346),
    "Santa Cruz": (-23.59895, -46.63657), "Praça da Árvore": (-23.61057, -46.6379),
    "Saúde": (-23.61839, -46.63911), "São Judas": (-23.62552, -46.64073),
    "Conceição": (-23.63532, -46.64134), "Jabaquara": (-23.64626, -46.64106),
    "Vila Madalena": (-23.54637, -46.69083), "Sumaré": (-23.5511, -46.67729),
    "Clínicas": (-23.55399, -46.67103), "Consolação": (-23.55738, -46.66098),
    "Trianon-Masp": (-23.56312, -46.6544), "Brigadeiro": (-23.5689, -46.64733),
    "Chácara Klabin": (-23.59256, -46.63042),
    "Santos-Imigrantes": (-23.5959, -46.62077),
    "Alto do Ipiranga": (-23.60225, -46.61253), "Sacomã": (-23.6015, -46.60287),
    "Tamanduateí": (-23.59297, -46.58973), "Vila Prudente": (-23.58428, -46.5818),
    "Palmeiras-Barra Funda": (-23.52595, -46.66737),
    "Marechal Deodoro": (-23.53397, -46.65566),
    "Santa Cecília": (-23.54006, -46.64838), "República": (-23.54387, -46.64302),
    "Anhangabaú": (-23.54795, -46.63884), "Pedro II": (-23.54968, -46.62562),
    "Brás": (-23.54781, -46.61568), "Bresser-Mooca": (-23.54643, -46.60736),
    "Belém": (-23.54298, -46.58985), "Tatuapé": (-23.54049, -46.57639),
    "Carrão-Assaí Atacadista": (-23.5379, -46.56412),
    "Penha-Lojas Besni": (-23.53352, -46.5423), "Vila Matilde": (-23.53191, -46.53093),
    "Guilhermina-Esperança": (-23.52942, -46.51673),
    "Patriarca-Vila Ré": (-23.53123, -46.50135), "Artur Alvim": (-23.54037, -46.48456),
    "Corinthians-Itaquera": (-23.54244, -46.4711),
    "Higienópolis-Mackenzie": (-23.54894, -46.65216),
    "Paulista": (-23.55504, -46.66216), "Oscar Freire": (-23.56052, -46.67192),
    "Fradique Coutinho": (-23.56623, -46.68426), "Faria Lima": (-23.56727, -46.6941),
    "Pinheiros": (-23.56739, -46.70161), "Butantã": (-23.57186, -46.70816),
    "São Paulo-Morumbi": (-23.58644, -46.72377), "Vila Sônia": (-23.59338, -46.73458),
    "Capão Redondo": (-23.65927, -46.76799), "Campo Limpo": (-23.64932, -46.75893),
    "Vila das Belezas": (-23.64042, -46.74572),
    "Giovanni Gronchi": (-23.64398, -46.73411), "Santo Amaro": (-23.65575, -46.72089),
    "Largo Treze": (-23.65424, -46.70845), "Adolfo Pinheiro": (-23.65011, -46.7043),
    "Alto da Boa Vista": (-23.64146, -46.69927), "Borba Gato": (-23.63374, -46.69315),
    "Brooklin": (-23.62697, -46.68804), "Campo Belo": (-23.61886, -46.6822),
    "Eucaliptos": (-23.60994, -46.66855), "Moema": (-23.6037, -46.66232),
    "AACD-Servidor": (-23.59764, -46.65228),
    "Hospital São Paulo": (-23.59819, -46.64538), "Água Branca": (-23.5214, -46.68857),
    "Jundiaí": (-23.19538, -46.87203), "Várzea Paulista": (-23.20885, -46.82894),
    "Campo Limpo Paulista": (-23.20664, -46.78549), "Botujuru": (-23.23639, -46.76722),
    "Francisco Morato": (-23.28253, -46.74258),
    "Baltazar Fidélis": (-23.31008, -46.72344),
    "Franco da Rocha": (-23.32965, -46.72624), "Caieiras": (-23.36617, -46.75153),
    "Perus": (-23.40498, -46.75366), "Vila Aurora": (-23.43776, -46.74726),
    "Jaraguá": (-23.45525, -46.73864), "Vila Clarice": (-23.46989, -46.74442),
    "Pirituba": (-23.48847, -46.72613), "Piqueri": (-23.50358, -46.71498),
    "Lapa|7": (-23.51765, -46.70393), "Amador Bueno": (-23.53052, -46.98376),
    "Ambuitá": (-23.53023, -46.97272), "Santa Rita": (-23.54495, -46.94751),
    "Itapevi": (-23.54559, -46.9352), "Engenheiro Cardoso": (-23.53519, -46.92865),
    "Sagrado Coração": (-23.52915, -46.91667), "Jandira": (-23.52775, -46.90237),
    "Jardim Silveira": (-23.5237, -46.89358), "Jardim Belval": (-23.51392, -46.88922),
    "Barueri": (-23.51263, -46.87518), "Antônio João": (-23.51694, -46.85864),
    "Santa Terezinha": (-23.51663, -46.84781), "Carapicuíba": (-23.5185, -46.8354),
    "General Miguel Costa": (-23.52349, -46.81603), "Quitaúna": (-23.52275, -46.80691),
    "Comandante Sampaio": (-23.52568, -46.79599), "Osasco": (-23.52782, -46.77582),
    "Presidente Altino": (-23.53144, -46.76178),
    "Imperatriz Leopoldina": (-23.52342, -46.73724),
    "Domingos de Moraes": (-23.51884, -46.72146), "Lapa|8": (-23.52009, -46.69894),
    "Júlio Prestes": (-23.53317, -46.64059), "Ceasa": (-23.53759, -46.74242),
    "Villa Lobos-Jaguaré": (-23.54587, -46.73315),
    "Cidade Universitária": (-23.55763, -46.71193),
    "Hebraica-Rebouças": (-23.57363, -46.69865),
    "Cidade Jardim": (-23.58552, -46.69112), "Vila Olímpia": (-23.5936, -46.69276),
    "Berrini": (-23.60471, -46.69676), "Morumbi": (-23.62143, -46.70145),
    "Granja Julieta": (-23.62764, -46.71204), "João Dias": (-23.63916, -46.72286),
    "Socorro": (-23.66278, -46.71121), "Jurubatuba": (-23.6774, -46.70227),
    "Autódromo": (-23.7062, -46.68846), "Primavera-Interlagos": (-23.72304, -46.69175),
    "Grajaú": (-23.73635, -46.69688), "Mendes-Vila Natal": (-23.75448, -46.70931),
    "Juventus-Mooca": (-23.55869, -46.60794), "Ipiranga": (-23.58223, -46.5967),
    "São Caetano do Sul": (-23.61003, -46.57007), "Utinga": (-23.6261, -46.54406),
    "Prefeito Saladino": (-23.63832, -46.53671), "Santo André": (-23.65232, -46.52818),
    "Capuava": (-23.65835, -46.49008), "Mauá": (-23.66817, -46.46161),
    "Guapituba": (-23.69217, -46.44867), "Ribeirão Pires": (-23.71363, -46.41477),
    "Rio Grande da Serra": (-23.74331, -46.39186), "Dom Bosco": (-23.54185, -46.44818),
    "José Bonifácio": (-23.53913, -46.4315), "Guaianases": (-23.54234, -46.4155),
    "Antonio Gianetti Neto": (-23.55444, -46.3839),
    "Ferraz de Vasconcelos": (-23.54108, -46.36874), "Poá": (-23.5254, -46.34361),
    "Calmon Viana": (-23.52545, -46.33297), "Suzano": (-23.5341, -46.3079),
    "Jundiapeba": (-23.54271, -46.25802), "Braz Cubas": (-23.53804, -46.231),
    "Mogi das Cruzes": (-23.52123, -46.19725), "Estudantes": (-23.51573, -46.18497),
    "Engenheiro Goulart": (-23.49808, -46.5198), "USP Leste": (-23.48551, -46.50166),
    "Comendador Ermelino": (-23.48515, -46.48229),
    "São Miguel Paulista": (-23.49038, -46.44379),
    "Jardim Helena-Vila Mara": (-23.49269, -46.42154),
    "Itaim Paulista": (-23.494, -46.40187), "Jardim Romano": (-23.48492, -46.38556),
    "Engenheiro Manoel Feio": (-23.47924, -46.36746),
    "Itaquaquecetuba": (-23.48583, -46.34818), "Aracaré": (-23.50059, -46.33902),
    "Guarulhos-Cecap": (-23.44751, -46.49362),
    "Aeroporto-Guarulhos": (-23.43313, -46.4938), "Oratório": (-23.58217, -46.56182),
    "São Lucas": (-23.58892, -46.54466), "Camilo Haddad": (-23.59546, -46.53764),
    "Vila Tolstói": (-23.60085, -46.52725), "Vila União": (-23.60299, -46.51553),
    "Jardim Planalto": (-23.60649, -46.50763), "Sapopemba": (-23.61467, -46.50081),
    "Fazenda da Juta": (-23.61181, -46.48745), "São Mateus": (-23.61213, -46.47677),
    "Jardim Colonial": (-23.59976, -46.46965), "Varginha": (-23.7672, -46.7138),
    "João Paulo I": (-23.4905, -46.6968), "Freguesia do Ó": (-23.4998, -46.6942),
    "Santa Marina": (-23.5118, -46.6872), "SESC-Pompeia": (-23.5258, -46.6838),
    "Perdizes": (-23.5332, -46.6772), "Chucri Zaidan": (-23.6214, -46.6996),
    "Vila Cordeiro": (-23.6226, -46.6914), "Vereador José Diniz": (-23.6245, -46.6765),
    "Brooklin Paulista": (-23.6259, -46.6679),
    "Aeroporto de Congonhas": (-23.6279, -46.6569),
    "Washington Luís": (-23.6372, -46.6588),
}

# Caminhada
VELOCIDADE_M_MIN = 80      # ~4,8 km/h
FATOR_RUAS = 1.3           # ruas não são linha reta
N_ESTACOES_PROXIMAS = 4
PESO_CAMINHADA = 1.6       # na escolha da rota, 1 min a pé "custa" mais que 1 min no trem
CENTRO_SP = (-23.5505, -46.6333)


def rotulo(lid: str) -> str:
    return f"Linha {lid} · {LINHAS[lid]['nome']}"


def terminal(lid: str, de: str, para: str) -> str:
    est = LINHAS[lid]["est"]
    return est[-1] if est.index(para) > est.index(de) else est[0]


def coord(lid: str, s: str):
    return COORDS.get(f"{s}|{lid}") or COORDS[s]


def distancia_m(a, b) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def minutos_a_pe(m: float) -> int:
    return max(1, math.ceil(m * FATOR_RUAS / VELOCIDADE_M_MIN))


def link_a_pe(a, b) -> str:
    q = urlencode({"api": 1, "origin": f"{a[0]},{a[1]}",
                   "destination": f"{b[0]},{b[1]}", "travelmode": "walking"})
    return f"https://www.google.com/maps/dir/?{q}"


# ---------------------------------------------------------------------------
# 2. ENDEREÇOS (Nominatim / OpenStreetMap)
# ---------------------------------------------------------------------------
NOMINATIM = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": f"MapaDoTrem/1.0 ({CONTATO})", "Accept-Language": "pt-BR"}


def _curto(nome: str) -> str:
    partes = [p.strip() for p in nome.split(",")]
    return ", ".join(partes[:3])


def _nominatim(texto: str):
    r = requests.get(f"{NOMINATIM}/search", headers=HEADERS, timeout=10, params={
        "q": texto, "format": "jsonv2", "limit": 5, "countrycodes": "br",
        "viewbox": "-47.30,-23.10,-45.60,-24.10", "bounded": 1})
    r.raise_for_status()
    return [dict(lat=float(x["lat"]), lon=float(x["lon"]),
                 rotulo=_curto(x["display_name"])) for x in r.json()]


def _photon(texto: str):
    """Reserva: Photon (Komoot), também gratuito e baseado no OpenStreetMap."""
    r = requests.get("https://photon.komoot.io/api/", headers=HEADERS, timeout=10, params={
        "q": texto, "limit": 5, "lat": CENTRO_SP[0], "lon": CENTRO_SP[1],
        "bbox": "-47.30,-24.10,-45.60,-23.10"})
    r.raise_for_status()
    saida = []
    for f in r.json().get("features", []):
        pr = f["properties"]
        rua = " ".join(x for x in (pr.get("street"), pr.get("housenumber")) if x)
        partes = [pr.get("name"), rua, pr.get("district"), pr.get("city")]
        rot = ", ".join(dict.fromkeys(x for x in partes if x))
        lon, lat = f["geometry"]["coordinates"]
        saida.append(dict(lat=lat, lon=lon, rotulo=rot or texto))
    return saida


@st.cache_data(ttl=60 * 60 * 24 * 7, show_spinner=False)
def geocodificar(texto: str):
    try:
        res = _nominatim(texto)
        if res:
            return res
    except Exception:
        pass
    return _photon(texto)


@st.cache_data(ttl=60 * 60 * 24 * 7, show_spinner=False)
def endereco_do_ponto(lat: float, lon: float) -> str:
    try:
        r = requests.get(f"{NOMINATIM}/reverse", headers=HEADERS, timeout=10,
                         params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 18})
        r.raise_for_status()
        return _curto(r.json().get("display_name", "")) or "Ponto marcado no mapa"
    except Exception:
        return "Ponto marcado no mapa"


def estacoes_proximas(ponto, n=N_ESTACOES_PROXIMAS):
    """Devolve {(linha, estação): (minutos, metros)} das n estações mais próximas."""
    melhor = {}
    for lid, d in LINHAS.items():
        for s in d["est"]:
            m = distancia_m(ponto, coord(lid, s))
            melhor.setdefault(s, []).append((m, lid))
    nomes = sorted(melhor, key=lambda s: min(x[0] for x in melhor[s]))[:n]
    return {(lid, s): (minutos_a_pe(m), m) for s in nomes for m, lid in melhor[s]}


# ---------------------------------------------------------------------------
# 3. GRAFO + DIJKSTRA
# ---------------------------------------------------------------------------
@st.cache_data
def montar_grafo():
    grafo, por_nome = {}, {}

    def add(a, b, custo, dica=None):
        grafo.setdefault(a, []).append((b, custo, dica, True))

    for lid, d in LINHAS.items():
        est = d["est"]
        for i, s in enumerate(est):
            por_nome.setdefault(s, []).append(lid)
            grafo.setdefault((lid, s), [])
            if i + 1 < len(est):
                grafo[(lid, s)].append(((lid, est[i + 1]), d["min"], None, False))
                grafo.setdefault((lid, est[i + 1]), []).append(((lid, s), d["min"], None, False))

    for s, lids in por_nome.items():
        for a in lids:
            for b in lids:
                if a != b:
                    if s == "Lapa" and {a, b} == {"7", "8"}:
                        add((a, s), (b, s), PENALIDADE_LAPA, DICA_LAPA)
                    else:
                        add((a, s), (b, s), MIN_BALDEACAO)

    for la, sa, lb, sb, m, dica in CONEXOES_ESPECIAIS:
        add((la, sa), (lb, sb), m, dica)
        add((lb, sb), (la, sa), m, dica)
    return grafo, por_nome


def nos_da_estacao(s):
    _, por_nome = montar_grafo()
    return {(lid, s): (0, 0) for lid in por_nome[s]}


def buscar_rota(fontes: dict, alvos: dict, penalidade: int):
    """fontes/alvos: {nó: (minutos a pé, metros)}. Dijkstra multi-origem."""
    grafo, _ = montar_grafo()
    dist, prev, heap = {}, {}, []
    for n, (mins, _) in fontes.items():
        c0 = mins * PESO_CAMINHADA
        dist[n] = (c0, mins)
        heapq.heappush(heap, (c0, mins, n))

    while heap:
        c, t, n = heapq.heappop(heap)
        if (c, t) != dist.get(n):
            continue
        for viz, custo, dica, bald in grafo[n]:
            nc, nt = c + custo + (penalidade if bald else 0), t + custo
            if viz not in dist or (nc, nt) < dist[viz]:
                dist[viz] = (nc, nt)
                prev[viz] = (n, dica)
                heapq.heappush(heap, (nc, nt, viz))

    validos = [a for a in alvos if a in dist]
    if not validos:
        return None
    alvo = min(validos, key=lambda a: (dist[a][0] + alvos[a][0] * PESO_CAMINHADA,
                                       dist[a][1] + alvos[a][0]))

    caminho, dicas, n = [alvo], {}, alvo
    while n in prev:
        p, dica = prev[n]
        if dica:
            dicas[(p, n)] = dica
        caminho.append(p)
        n = p
    caminho.reverse()

    trechos = []
    for i, (lid, s) in enumerate(caminho):
        if not trechos or trechos[-1]["linha"] != lid:
            dica = dicas.get((caminho[i - 1], caminho[i])) if i else None
            trechos.append(dict(linha=lid, est=[s], dica_entrada=dica))
        else:
            trechos[-1]["est"].append(s)
    trechos = [t for t in trechos if len(t["est"]) > 1]

    ini, fim = caminho[0], alvo
    pe_ini, pe_fim = fontes[ini], alvos[alvo]
    return dict(trechos=trechos, no_ini=ini, no_fim=fim,
                pe_ini=pe_ini, pe_fim=pe_fim,
                minutos=dist[alvo][1] + pe_fim[0])


# ---------------------------------------------------------------------------
# 4. INTERFACE
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600;700&display=swap');
:root{ --ink:#1C2430; --muted:#5B6673; --paper:#FFFFFF; --rail:#E4E8EC; --soft:#F3F5F7; }
html, body, [class*="css"], .stApp { font-family:'Barlow', system-ui, sans-serif; }
#MainMenu, footer, header [data-testid="stToolbar"] { visibility:hidden; }
.block-container{ max-width:680px; padding:1.2rem 1rem 4rem; }

.placa{ background:var(--ink); color:#fff; border-radius:14px; overflow:hidden; margin-bottom:1.1rem; }
.placa .faixas{ display:flex; height:8px; }
.placa .faixas span{ flex:1; }
.placa .corpo{ padding:1.1rem 1.2rem 1.2rem; }
.placa h1{ font-family:'Barlow Condensed', sans-serif; font-weight:700; font-size:2.6rem;
  line-height:1; margin:0; padding:0; color:#fff; letter-spacing:.5px; }
.placa p{ margin:.45rem 0 0; color:#C9D1D9; font-size:1rem; line-height:1.4; }

.rotulo-bloco{ font-family:'Barlow Condensed', sans-serif; font-weight:700; font-size:1.25rem;
  color:var(--ink); margin:.6rem 0 .2rem; display:flex; align-items:center; gap:.5rem; }
.pino{ width:14px; height:14px; border-radius:50%; border:3px solid var(--ink); background:#fff; display:inline-block; }
.pino.cheio{ background:var(--ink); }

.ponto{ background:var(--soft); border-radius:12px; padding:.6rem .75rem; margin:.3rem 0 .4rem;
  color:var(--ink); font-size:.93rem; line-height:1.4; }
.ponto b{ display:block; font-size:.98rem; }
.ponto small{ color:var(--muted); }

.resumo{ display:flex; gap:.5rem; margin:1.1rem 0 .9rem; }
.resumo div{ flex:1; background:var(--soft); border-radius:12px; padding:.7rem .5rem; text-align:center; color:var(--ink); }
.resumo b{ display:block; font-family:'Barlow Condensed', sans-serif; font-size:1.7rem; line-height:1; }
.resumo small{ color:var(--muted); font-size:.8rem; }
.sequencia{ display:flex; flex-wrap:wrap; align-items:center; gap:.35rem; margin-bottom:1rem; }
.sequencia .seta{ color:var(--muted); font-weight:700; }
.selo{ display:inline-flex; align-items:center; gap:.35rem; border-radius:999px;
  padding:.18rem .65rem .18rem .2rem; font-weight:600; font-size:.88rem; white-space:nowrap; }
.selo.pe{ background:var(--soft); color:var(--ink); padding:.18rem .65rem; }
.selo .num{ display:inline-flex; align-items:center; justify-content:center; min-width:1.45rem; height:1.45rem;
  border-radius:50%; background:rgba(255,255,255,.92); color:#1C2430;
  font-family:'Barlow Condensed', sans-serif; font-weight:700; font-size:.95rem; }

.rota{ background:var(--paper); border:1px solid var(--rail); border-radius:16px; padding:1rem .9rem .4rem; color:var(--ink); }
.passo{ position:relative; padding:0 0 1.15rem 2.3rem; }
.passo::before{ content:""; position:absolute; left:.62rem; top:.3rem; bottom:-.3rem; width:6px;
  border-radius:3px; background:var(--c, var(--rail)); }
.passo.fim::before{ display:none; }
.passo.caminhada::before{ background:repeating-linear-gradient(var(--muted) 0 5px, transparent 5px 10px);
  width:3px; left:.78rem; }
.passo .no{ position:absolute; left:.2rem; top:.1rem; width:1.4rem; height:1.4rem; border-radius:50%;
  background:#fff; border:4px solid var(--c, var(--ink)); box-sizing:border-box; }
.passo.caminhada .no, .passo.chegada .no{ border-color:var(--ink); }
.passo.chegada .no{ background:var(--ink); }
.passo h4{ margin:0 0 .2rem; padding:0; font-size:1.05rem; font-weight:700; line-height:1.3; color:var(--ink); }
.passo p{ margin:.15rem 0; font-size:.95rem; line-height:1.45; color:#39434F; }
.passo a{ color:#0455A1; font-weight:600; }
.aviso{ background:#FFF6D6; border-radius:10px; padding:.55rem .7rem; margin:.45rem 0 .1rem;
  font-size:.9rem; line-height:1.4; color:#4A3B00; }
.placa-sentido{ display:inline-block; margin:.35rem 0 .2rem; border-radius:8px; padding:.35rem .7rem;
  font-family:'Barlow Condensed', sans-serif; font-weight:700; font-size:1.15rem; background:var(--c); color:var(--t); }
details{ margin:.35rem 0 .1rem; }
details summary{ cursor:pointer; color:var(--muted); font-size:.9rem; font-weight:600; }
details ol{ margin:.4rem 0 0 1.1rem; padding:0; font-size:.92rem; color:#39434F; }
details li{ margin:.1rem 0; }
.rodape{ color:var(--muted); font-size:.82rem; line-height:1.45; margin-top:1rem; }

@media (max-width:480px){
  .placa h1{ font-size:2.2rem; }
  .resumo b{ font-size:1.4rem; }
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


def passo_caminhada(titulo, texto, link, classe="caminhada"):
    return (f'<div class="passo {classe}"><span class="no"></span><h4>{titulo}</h4>'
            f'<p>{texto}</p><p><a href="{link}" target="_blank">Ver o caminho a pé '
            f'no Google Maps</a></p></div>')


def html_rota(rota, p_origem, p_destino) -> str:
    trechos = rota["trechos"]
    n_bald = max(len(trechos) - 1, 0)
    pe_total = rota["pe_ini"][0] + rota["pe_fim"][0]

    h = ['<div class="resumo">',
         f'<div><b>~{rota["minutos"]}</b><small>min no total</small></div>',
         f'<div><b>{pe_total}</b><small>min a pé</small></div>',
         f'<div><b>{n_bald}</b><small>{"baldeação" if n_bald == 1 else "baldeações"}</small></div>',
         '</div><div class="sequencia">']
    selos = [selo(t["linha"]) for t in trechos]
    if p_origem:
        selos.insert(0, '<span class="selo pe">🚶 a pé</span>')
    if p_destino:
        selos.append('<span class="selo pe">🚶 a pé</span>')
    h.append('<span class="seta">›</span>'.join(selos))
    h.append('</div><div class="rota">')

    # Caminhada inicial
    if p_origem:
        lid0, s0 = rota["no_ini"]
        mins, m = rota["pe_ini"]
        h.append(passo_caminhada(
            f"Caminhe até a estação {s0}",
            f"São cerca de {mins} min a pé (≈{round(m / 50) * 50:.0f} m em linha reta) "
            f"a partir de {p_origem['rotulo']}.",
            link_a_pe((p_origem["lat"], p_origem["lon"]), coord(lid0, s0))))

    for i, t in enumerate(trechos):
        lid, est = t["linha"], t["est"]
        d = LINHAS[lid]
        c = f'--c:{d["cor"]};--t:{d["txt"]}'
        emb, des = est[0], est[-1]
        sent = terminal(lid, emb, est[1])
        paradas = len(est) - 1

        titulo = f"Entre na estação {emb}" if i == 0 else f"Embarque na {rotulo(lid)}"
        h.append(f'<div class="passo" style="{c}"><span class="no"></span><h4>{titulo}</h4>')
        h.append(f'<p>Pegue a <b>{rotulo(lid)}</b> na plataforma com a placa:</p>')
        h.append(f'<span class="placa-sentido">Sentido {sent}</span>')
        h.append(f'<p>A próxima estação precisa ser <b>{est[1]}</b>. Se o trem parar em '
                 f'outra, você está no sentido errado: desça e vá para a plataforma oposta.</p></div>')

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

        if i < len(trechos) - 1:
            nxt = trechos[i + 1]
            nl, ne = nxt["linha"], nxt["est"][0]
            h.append(f'<div class="passo caminhada"><span class="no"></span>'
                     f'<h4>Desça em {des} e faça baldeação</h4>')
            if ne == des:
                h.append(f'<p>Dentro da estação {des}, siga as placas '
                         f'<b>“{rotulo(nl)}”</b> até a plataforma dela.</p>')
            else:
                h.append(f'<p>Siga as placas <b>“{rotulo(nl)}”</b> até a estação <b>{ne}</b>.</p>')
            if nxt.get("dica_entrada"):
                h.append(f'<div class="aviso">{nxt["dica_entrada"]}</div>')
            h.append('</div>')
        elif p_destino:
            h.append(f'<div class="passo caminhada"><span class="no"></span>'
                     f'<h4>Desça em {des} e saia da estação</h4></div>')
        else:
            h.append(f'<div class="passo chegada fim"><span class="no"></span>'
                     f'<h4>Desça em {des}. Você chegou.</h4></div>')

    if p_destino:
        lidf, sf = rota["no_fim"]
        mins, m = rota["pe_fim"]
        h.append(passo_caminhada(
            "Caminhe até o destino",
            f"De {sf} até {p_destino['rotulo']} são cerca de {mins} min a pé.",
            link_a_pe(coord(lidf, sf), (p_destino["lat"], p_destino["lon"]))))
        h.append('<div class="passo chegada fim"><span class="no"></span>'
                 '<h4>Você chegou.</h4></div>')

    h.append('</div>')
    return "".join(h)


def mapa_da_rota(rota, p_origem, p_destino):
    pontos = []
    m = folium.Map(tiles="OpenStreetMap", control_scale=True)
    for t in rota["trechos"]:
        cor = LINHAS[t["linha"]]["cor"]
        linha = [coord(t["linha"], s) for s in t["est"]]
        pontos += linha
        folium.PolyLine(linha, color=cor, weight=7, opacity=.9).add_to(m)
        for s, xy in zip(t["est"], linha):
            folium.CircleMarker(xy, radius=5, color=cor, fill=True, fill_color="#fff",
                                fill_opacity=1, weight=3, tooltip=s).add_to(m)
    for p, no in ((p_origem, rota["no_ini"]), (p_destino, rota["no_fim"])):
        if p:
            a, b = (p["lat"], p["lon"]), coord(*no)
            pontos += [a, b]
            folium.PolyLine([a, b], color="#5B6673", weight=3, dash_array="6 8").add_to(m)
            folium.Marker(a, tooltip=p["rotulo"]).add_to(m)
    if pontos:
        m.fit_bounds([[min(x for x, _ in pontos), min(y for _, y in pontos)],
                      [max(x for x, _ in pontos), max(y for _, y in pontos)]], padding=(20, 20))
    return m


# --- Blocos de Partida / Destino -------------------------------------------
MODOS = ["Estação", "Endereço", "Mapa"]
NAO_TROCAR = ("mapa", "clk", "geo")  # estado de componentes, fica em cada bloco


def trocar():
    s = st.session_state
    pares = {}
    for k in list(s.keys()):
        if isinstance(k, str) and k[:2] in ("o_", "d_") and not k.endswith(NAO_TROCAR):
            pares[k[2:]] = True
    antigos = {k: s[k] for k in list(s.keys()) if isinstance(k, str) and k[:2] in ("o_", "d_")}
    for suf in pares:
        o, d = f"o_{suf}", f"d_{suf}"
        if o in antigos:
            s[d] = antigos[o]
        elif d in s:
            del s[d]
        if d in antigos:
            s[o] = antigos[d]
        elif o in s:
            del s[o]


def definir_ponto(p, lat, lon, texto):
    st.session_state[f"{p}_ponto"] = dict(lat=lat, lon=lon, rotulo=texto)


def ao_escolher_resultado(p):
    s = st.session_state
    i = s[f"{p}_escolha"]
    r = s[f"{p}_res"][i]
    definir_ponto(p, r["lat"], r["lon"], r["rotulo"])


def mostrar_ponto(p):
    ponto = st.session_state.get(f"{p}_ponto")
    if not ponto:
        return
    prox = estacoes_proximas((ponto["lat"], ponto["lon"]), 2)
    vistos, itens = set(), []
    for (lid, s), (mins, _) in sorted(prox.items(), key=lambda x: x[1][1]):
        if s not in vistos:
            vistos.add(s)
            itens.append(f"{s} ({mins} min a pé)")
    st.markdown(f'<div class="ponto"><b>📍 {ponto["rotulo"]}</b>'
                f'<small>Mais perto: {" · ".join(itens)}</small></div>',
                unsafe_allow_html=True)


def bloco(p: str, titulo: str, cheio: bool):
    s = st.session_state
    classe = "pino cheio" if cheio else "pino"
    st.markdown(f'<div class="rotulo-bloco"><span class="{classe}"></span>{titulo}</div>',
                unsafe_allow_html=True)
    modo = st.segmented_control("Como informar", MODOS, key=f"{p}_modo",
                                label_visibility="collapsed") or "Estação"

    if modo == "Estação":
        c1, c2 = st.columns([1, 1.4])
        with c1:
            lid = st.selectbox("Linha", list(LINHAS), format_func=rotulo, key=f"{p}_linha")
        with c2:
            est = st.selectbox("Estação", LINHAS[lid]["est"], key=f"{p}_est_{lid}")
        return ("estacao", est)

    if modo == "Endereço":
        if p == "o":
            c1, c2 = st.columns([1, 7], vertical_alignment="center")
            with c1:
                loc = streamlit_geolocation()
            with c2:
                st.caption("Toque no ícone para usar sua localização atual")
            if loc and loc.get("latitude"):
                atual = (round(loc["latitude"], 6), round(loc["longitude"], 6))
                if s.get("o_geo") != atual:
                    s["o_geo"] = atual
                    definir_ponto(p, *atual, "Sua localização atual")
        with st.form(f"{p}_form", border=False):
            c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
            with c1:
                texto = st.text_input("Endereço ou lugar", key=f"{p}_txt",
                                      placeholder="Ex.: Av. Paulista, 1578")
            with c2:
                buscar = st.form_submit_button("Buscar", use_container_width=True)
        if buscar and texto.strip():
            try:
                with st.spinner("Procurando endereço..."):
                    res = geocodificar(texto.strip())
            except Exception:
                res = None
                st.warning("A busca de endereços não respondeu. Tente de novo em alguns segundos.")
            if res is not None:
                s[f"{p}_res"] = res
                s[f"{p}_escolha"] = 0
                if res:
                    definir_ponto(p, res[0]["lat"], res[0]["lon"], res[0]["rotulo"])
                else:
                    st.warning("Nenhum endereço encontrado na Grande São Paulo. "
                               "Inclua o número, o bairro ou a cidade.")
        res = s.get(f"{p}_res") or []
        if len(res) > 1:
            st.selectbox("Não é esse? Escolha o certo:", range(len(res)),
                         format_func=lambda i: res[i]["rotulo"], key=f"{p}_escolha",
                         on_change=ao_escolher_resultado, args=(p,))

    if modo == "Mapa":
        st.caption("Toque no mapa para marcar o ponto.")
        ponto = s.get(f"{p}_ponto")
        centro = (ponto["lat"], ponto["lon"]) if ponto else CENTRO_SP
        m = folium.Map(location=centro, zoom_start=15 if ponto else 12,
                       tiles="OpenStreetMap", control_scale=True)
        for lid, d in LINHAS.items():
            for est in d["est"]:
                folium.CircleMarker(coord(lid, est), radius=4, color=d["cor"], fill=True,
                                    fill_color="#fff", fill_opacity=1, weight=3,
                                    tooltip=f"{est} ({rotulo(lid)})").add_to(m)
        if ponto:
            folium.Marker(centro, tooltip=ponto["rotulo"]).add_to(m)
        out = st_folium(m, key=f"{p}_mapa", height=320, use_container_width=True,
                        returned_objects=["last_clicked"])
        clk = (out or {}).get("last_clicked")
        if clk:
            atual = (round(clk["lat"], 6), round(clk["lng"], 6))
            if s.get(f"{p}_clk") != atual:
                s[f"{p}_clk"] = atual
                definir_ponto(p, *atual, endereco_do_ponto(*atual))
                st.rerun()

    mostrar_ponto(p)
    ponto = s.get(f"{p}_ponto")
    return ("ponto", ponto) if ponto else None


def extremos(sel):
    """Converte a seleção em {nó: (minutos a pé, metros)} e o ponto (se houver)."""
    if sel[0] == "estacao":
        return nos_da_estacao(sel[1]), None
    ponto = sel[1]
    return estacoes_proximas((ponto["lat"], ponto["lon"])), ponto


def main():
    st.set_page_config(page_title="MapaDoTrem", page_icon="🚇", layout="centered",
                       initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)

    s = st.session_state
    if "o_modo" not in s:
        s.o_modo, s.d_modo = "Estação", "Estação"
        s.o_linha, s["o_est_4"] = "4", "Oscar Freire"
        s.d_linha, s["d_est_1"] = "1", "Vergueiro"

    faixas = "".join(f'<span style="background:{d["cor"]}"></span>' for d in LINHAS.values())
    st.markdown(
        f'<div class="placa"><div class="faixas">{faixas}</div><div class="corpo">'
        f'<h1>MapaDoTrem</h1><p>Informe de onde você sai e aonde quer chegar: por '
        f'estação, endereço ou tocando no mapa. Mostramos o sentido de cada trem e '
        f'onde trocar de linha.</p></div></div>', unsafe_allow_html=True)

    sel_o = bloco("o", "Partida", False)
    st.button("⇅  Inverter partida e destino", on_click=trocar, use_container_width=True)
    sel_d = bloco("d", "Destino", True)

    modo = st.radio("Preferência", ["Mais rápida", "Menos baldeações"],
                    horizontal=True, label_visibility="collapsed")

    if not sel_o or not sel_d:
        st.info("Informe a partida e o destino para ver a rota.")
        return
    if sel_o[0] == sel_d[0] == "estacao" and sel_o[1] == sel_d[1]:
        st.info("Partida e destino são a mesma estação. Escolha outra estação de destino.")
        return

    fontes, p_o = extremos(sel_o)
    alvos, p_d = extremos(sel_d)
    rota = buscar_rota(fontes, alvos, 3 if modo == "Mais rápida" else 60)
    if rota is None:
        st.error("Não encontramos ligação entre esses pontos na rede atual.")
        return

    # A pé direto pode ser melhor
    a = (p_o["lat"], p_o["lon"]) if p_o else coord(*next(iter(fontes)))
    b = (p_d["lat"], p_d["lon"]) if p_d else coord(*next(iter(alvos)))
    direto = minutos_a_pe(distancia_m(a, b))
    if not rota["trechos"] or direto <= rota["minutos"]:
        st.success(f"🚶 Ir a pé leva cerca de {direto} min, o que é tão rápido quanto "
                   f"o trem. [Ver caminho a pé]({link_a_pe(a, b)})")
        if not rota["trechos"]:
            return

    maior_pe = max(rota["pe_ini"][0], rota["pe_fim"][0])
    if maior_pe > 30:
        st.warning(f"Um dos pontos fica a ~{maior_pe} min a pé da estação mais próxima. "
                   "Pode valer a pena combinar com ônibus ou carro por aplicativo.")

    st.markdown(html_rota(rota, p_o, p_d), unsafe_allow_html=True)
    with st.expander("Ver trajeto no mapa"):
        st_folium(mapa_da_rota(rota, p_o, p_d), key="mapa_rota", height=380,
                  use_container_width=True, returned_objects=[])

    st.markdown(
        '<p class="rodape">Tempos aproximados, sem contar a espera pelo trem. Caminhadas '
        'estimadas pela distância. Rede conforme o mapa oficial de julho/2026; horários, '
        'obras e integrações tarifadas podem mudar, confira no site da operadora. '
        'Endereços: © colaboradores do OpenStreetMap.</p>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
