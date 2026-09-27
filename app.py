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
    "4": dict(nome="Amarela", cor="#FFD400", txt="#1F1D1A", op="Motiva", min=2, est=[
        "Luz", "República", "Higienópolis-Mackenzie", "Paulista", "Oscar Freire",
        "Fradique Coutinho", "Faria Lima", "Pinheiros", "Butantã",
        "São Paulo-Morumbi", "Vila Sônia"]),
    "5": dict(nome="Lilás", cor="#9B3894", txt="#FFFFFF", op="Motiva", min=2, est=[
        "Capão Redondo", "Campo Limpo", "Vila das Belezas", "Giovanni Gronchi",
        "Santo Amaro", "Largo Treze", "Adolfo Pinheiro", "Alto da Boa Vista",
        "Borba Gato", "Brooklin", "Campo Belo", "Eucaliptos", "Moema",
        "AACD-Servidor", "Hospital São Paulo", "Santa Cruz", "Chácara Klabin"]),
    "6": dict(nome="Laranja", cor="#F68B1F", txt="#1F1D1A", op="Linha Uni", min=2, est=[
        "João Paulo I", "Freguesia do Ó", "Santa Marina", "Água Branca",
        "SESC-Pompeia", "Perdizes"]),
    "7": dict(nome="Rubi", cor="#A8105F", txt="#FFFFFF", op="TIC Trens", min=4, est=[
        "Jundiaí", "Várzea Paulista", "Campo Limpo Paulista", "Botujuru",
        "Francisco Morato", "Baltazar Fidélis", "Franco da Rocha", "Caieiras",
        "Perus", "Vila Aurora", "Jaraguá", "Vila Clarice", "Pirituba", "Piqueri",
        "Lapa", "Água Branca", "Palmeiras-Barra Funda", "Luz"]),
    "8": dict(nome="Diamante", cor="#8A9390", txt="#1F1D1A", op="Motiva", min=3, est=[
        "Amador Bueno", "Ambuitá", "Santa Rita", "Itapevi", "Engenheiro Cardoso",
        "Sagrado Coração", "Jandira", "Jardim Silveira", "Jardim Belval", "Barueri",
        "Antônio João", "Santa Terezinha", "Carapicuíba", "General Miguel Costa",
        "Quitaúna", "Comandante Sampaio", "Osasco", "Presidente Altino",
        "Imperatriz Leopoldina", "Domingos de Moraes", "Lapa",
        "Palmeiras-Barra Funda", "Júlio Prestes"]),
    "9": dict(nome="Esmeralda", cor="#00A88E", txt="#1F1D1A", op="Motiva", min=3, est=[
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
    "13": dict(nome="Jade", cor="#00B352", txt="#1F1D1A", op="Trivia", min=4, est=[
        "Engenheiro Goulart", "Guarulhos-Cecap", "Aeroporto-Guarulhos"]),
    "15": dict(nome="Prata", cor="#9AA3A8", txt="#1F1D1A", op="Metrô", min=2, est=[
        "Vila Prudente", "Oratório", "São Lucas", "Camilo Haddad", "Vila Tolstói",
        "Vila União", "Jardim Planalto", "Sapopemba", "Fazenda da Juta",
        "São Mateus", "Jardim Colonial"]),
    "17": dict(nome="Ouro", cor="#B8913A", txt="#1F1D1A", op="Metrô", min=2, est=[
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
    return f"Linha {lid}-{LINHAS[lid]['nome']}"


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
# 4. INTERFACE — "Concreto Paulista"
# ---------------------------------------------------------------------------
# Concreto aparente como chão, lajes mais claras para os controles, tinta quente
# para tudo que é comando. As cores das linhas são os únicos planos saturados.

_RUIDO = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
          "width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' "
          "baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix "
          "values='0 0 0 0 .12 0 0 0 0 .11 0 0 0 0 .1 0 0 0 .16 0'/%3E%3C/filter%3E%3Crect "
          "width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&display=swap');

:root{
  --chao:#D3CEC5;      /* concreto aparente */
  --laje:#E8E4DD;      /* laje moldada, mais clara */
  --laje-2:#DEDAD2;    /* laje em sombra */
  --tinta:#1F1D1A;     /* tinta quente: texto e comandos */
  --tinta-2:#57524A;   /* texto secundário */
  --forma:#BDB7AC;     /* marcas das tábuas de fôrma */
  --ruido:__RUIDO__;
  --cond:'Archivo', 'Archivo Narrow', 'Arial Narrow', sans-serif;
  --ease:cubic-bezier(.16,1,.3,1);
}

/* ---- Base e superfícies do navegador ---- */
html, body, .stApp, .stApp p, .stApp label, .stApp input, .stApp button, .stApp li,
.stApp summary, .stApp [role="option"], .stApp [data-testid="stMarkdownContainer"] *{
  font-family:'Archivo', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp{
  background-color:var(--chao);
  background-image:var(--ruido),
    repeating-linear-gradient(180deg, transparent 0 47px, rgba(31,29,26,.045) 47px 48px);
  color:var(--tinta);
}
::selection{ background:var(--tinta); color:var(--laje); }
*{ caret-color:var(--tinta); scrollbar-color:var(--forma) transparent; }
a{ color:var(--tinta); text-underline-offset:.2em; text-decoration-thickness:1.5px; }
:focus-visible{ outline:2px solid var(--tinta) !important; outline-offset:2px; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"]{ display:none !important; }
[data-testid="stHeader"]{ background:transparent; height:0; }
.block-container{ max-width:660px; padding:0 1rem 5rem !important; }
[data-testid="stVerticalBlock"]{ gap:.75rem; }

/* ---- Viga ---- */
.viga{
  position:relative; width:100vw; margin-left:calc(50% - 50vw);
  background-color:#C8C2B8;
  background-image:
    radial-gradient(circle, rgba(31,29,26,.26) 0 3.5px, transparent 4px),
    var(--ruido),
    linear-gradient(180deg, rgba(255,255,255,.18), rgba(31,29,26,.06));
  background-size:64px 40px, auto, auto;
  background-position:32px 20px, 0 0, 0 0;
  box-shadow:0 10px 18px -14px rgba(31,29,26,.55);
  border-bottom:3px solid var(--tinta);
  margin-bottom:.4rem;
}
.viga-dentro{ max-width:660px; margin:0 auto; padding:2.6rem 1rem 1.4rem; }
.viga h1{
  font-family:var(--cond); font-stretch:62%; font-weight:900; font-size:4.2rem;
  line-height:.86; letter-spacing:-.01em; margin:0; padding:0; color:var(--tinta);
  text-transform:none;
}
.viga p{ margin:.7rem 0 0; max-width:34ch; font-size:1.02rem; line-height:1.45; color:#3A362F; }

/* ---- Lajes (containers dos blocos) ---- */
.st-key-laje_o, .st-key-laje_d{
  position:relative; z-index:1;
  background-color:var(--laje);
  background-image:var(--ruido);
  border-radius:3px; padding:1rem 1rem 1.1rem;
  box-shadow:0 12px 22px -16px rgba(31,29,26,.6);
  gap:.6rem;
}
.titulo-laje{
  display:flex; align-items:baseline; justify-content:space-between; gap:1rem;
  font-family:var(--cond); font-stretch:62%; font-weight:900; font-size:1.9rem;
  line-height:1; color:var(--tinta); margin:0 0 1.15rem;
}
.titulo-laje span{ font-family:'Archivo', sans-serif; font-stretch:100%; font-weight:500;
  font-size:.86rem; color:var(--tinta-2); }

/* Rótulos dos widgets */
.stApp label, .stApp [data-testid="stWidgetLabel"] p{
  color:var(--tinta-2) !important; font-size:.84rem !important; font-weight:600 !important; }

/* Seletores e campos: moldados, cantos quase retos */
.stApp [data-testid="stSelectbox"] [role="group"], .stApp [data-testid="stTextInput"] div:has(> input){
  background:#F4F1EC !important; border:1.5px solid var(--forma) !important;
  border-radius:3px !important; min-height:2.9rem; color:var(--tinta) !important;
  transition:border-color .18s var(--ease), box-shadow .18s var(--ease);
}
.stApp [data-testid="stSelectbox"] [role="group"]:hover, .stApp [data-testid="stTextInput"] div:has(> input):hover{
  border-color:var(--tinta-2) !important; }
.stApp [data-testid="stSelectbox"] [role="group"]:focus-within, .stApp [data-testid="stTextInput"] div:has(> input):focus-within{
  border-color:var(--tinta) !important; box-shadow:0 0 0 1px var(--tinta) !important; }
.stApp [data-testid="stSelectbox"] input, .stApp input{ color:var(--tinta) !important;
  -webkit-text-fill-color:var(--tinta); font-weight:500; font-size:1rem !important; }
.stApp input::placeholder{ color:#7A746A !important; -webkit-text-fill-color:#7A746A; }
[role="listbox"]{ background:#F4F1EC !important; }
[role="listbox"] [role="option"]{ color:var(--tinta) !important; }
[role="listbox"] [role="option"][aria-selected="true"], [role="listbox"] [role="option"]:hover,
[role="listbox"] [role="option"][data-focused="true"]{ background:var(--laje-2) !important; }
.stApp [data-testid="stSelectbox"] button svg{ fill:var(--tinta); }

/* Controle segmentado (modo de entrada e preferência) */
.st-key-o_modo, .st-key-d_modo, .st-key-pref{ width:100% !important; }
.stApp [data-testid="stButtonGroup"], .stApp [data-testid="stButtonGroup"] [role="radiogroup"]{
  width:100% !important; max-width:none !important; }
.stApp [data-testid="stButtonGroup"] > div{ width:100%; display:flex; gap:0;
  border:1.5px solid var(--tinta); border-radius:3px; overflow:hidden; }
.stApp [data-testid="stButtonGroup"] button{
  flex:1 1 0; min-width:0; border:0 !important; border-radius:0 !important; min-height:2.6rem;
  background:transparent !important; color:var(--tinta) !important; font-weight:600;
  box-shadow:none !important; transition:background .18s var(--ease), color .18s var(--ease);
}
.stApp [data-testid="stButtonGroup"] button + button{ border-left:1.5px solid var(--tinta) !important; }
.stApp [data-testid="stButtonGroup"] button:hover{ background:rgba(31,29,26,.07) !important; }
.stApp [data-testid="stButtonGroup"] button[data-selected="true"]{
  background:var(--tinta) !important; color:var(--laje) !important; }
.stApp [data-testid="stButtonGroup"] button[data-selected="true"] p{ color:var(--laje) !important; }
.stApp [data-testid="stButtonGroup"] button p{ font-size:.95rem; font-weight:600; white-space:nowrap;
  overflow:visible; text-overflow:clip; }
.stApp [data-testid="stButtonGroup"] button *{ max-width:none; overflow:visible; }

/* Botões comuns */
.stApp .stButton > button, .stApp [data-testid="stFormSubmitButton"] > button{
  background:var(--tinta); color:var(--laje); border:0; border-radius:3px; min-height:2.9rem;
  font-weight:700; box-shadow:0 6px 12px -8px rgba(31,29,26,.8);
  transition:transform .15s var(--ease), background .15s var(--ease);
}
.stApp .stButton > button p, .stApp [data-testid="stFormSubmitButton"] > button p{ color:var(--laje); font-weight:700; }
.stApp .stButton > button:hover, .stApp [data-testid="stFormSubmitButton"] > button:hover{
  background:#34302A; color:var(--laje); border:0; }
.stApp .stButton > button:active{ transform:translateY(1px); }

/* Linhas que não devem empilhar no celular */
.st-key-linha_geo [data-testid="stHorizontalBlock"], .stApp [data-testid="stForm"] [data-testid="stHorizontalBlock"]{
  flex-wrap:nowrap !important; gap:.6rem; }
.st-key-linha_geo [data-testid="stColumn"], .stApp [data-testid="stForm"] [data-testid="stColumn"]{
  min-width:0 !important; width:auto !important; }
.st-key-linha_geo [data-testid="stColumn"]:first-child{ flex:0 0 52px !important; }
.st-key-linha_geo [data-testid="stColumn"]:last-child{ flex:1 1 auto !important; }
.stApp [data-testid="stForm"] [data-testid="stColumn"]:first-child{ flex:1 1 auto !important; }
.stApp [data-testid="stForm"] [data-testid="stColumn"]:last-child{ flex:0 0 6.5rem !important; }
.st-key-linha_geo .dica{ margin:0; }

/* ---- Pilar entre as lajes ---- */
.st-key-pilar [data-testid="stHorizontalBlock"]{ flex-wrap:nowrap !important; align-items:center; gap:.9rem; }
.st-key-pilar [data-testid="stColumn"]{ min-width:0 !important; width:auto !important; flex:1 1 auto !important; }
.st-key-pilar [data-testid="stColumn"]:first-child{ flex:0 0 auto !important; }
.st-key-pilar{ margin:-.75rem 0; position:relative; z-index:0; }
.st-key-trocar button{
  background:transparent !important; color:var(--tinta) !important; box-shadow:none !important;
  border:1.5px dashed var(--tinta-2) !important; min-height:2.5rem !important; width:100%;
}
.st-key-trocar button p{ color:var(--tinta) !important; font-weight:600 !important; }
.st-key-trocar button:hover{ background:rgba(31,29,26,.06) !important; border-style:solid !important; }
.pilar{ position:relative; width:16px; height:5.2rem; margin-left:1.35rem;
  background:#BDB7AC; background-image:var(--ruido); }
.pilar .fill{ position:absolute; inset:0; display:flex; flex-direction:column;
  animation:concretar .7s var(--ease) both; }
.pilar .fill i{ display:block; }
@keyframes concretar{ from{ clip-path:inset(0 0 100% 0); } to{ clip-path:inset(0 0 0 0); } }

/* ---- Resultado ---- */
.veredito{ margin:1.4rem 0 .2rem; }
.veredito h2{ font-family:var(--cond); font-stretch:62%; font-weight:900; font-size:3rem;
  line-height:.92; margin:0; padding:0; color:var(--tinta); font-variant-numeric:tabular-nums; }
.veredito p{ margin:.45rem 0 0; font-size:1.02rem; color:#3A362F; line-height:1.4; }
.sequencia{ display:flex; flex-wrap:wrap; align-items:center; gap:.4rem; margin:.9rem 0 1rem; }
.sequencia svg{ width:18px; height:18px; stroke:var(--tinta-2); }
.pilarete{ display:inline-flex; align-items:center; gap:.45rem; border-radius:2px;
  padding:.28rem .7rem .28rem .3rem; font-family:var(--cond); font-stretch:75%;
  font-weight:800; font-size:1.2rem; line-height:1; white-space:nowrap; }
.pilarete .num{ display:inline-flex; align-items:center; justify-content:center; width:1.55rem;
  height:1.55rem; border-radius:50%; background:#F4F1EC; color:var(--tinta);
  font-stretch:62%; font-weight:900; font-size:1.05rem; }
.pilarete.pe{ background:transparent; border:1.5px dashed var(--tinta-2); color:var(--tinta);
  padding:.26rem .6rem; gap:.3rem; }
.pilarete.pe svg{ width:17px; height:17px; stroke:var(--tinta); }

.rota{ background-color:var(--laje); background-image:var(--ruido); border-radius:3px;
  padding:1.2rem 1rem .5rem; box-shadow:0 12px 22px -16px rgba(31,29,26,.6); color:var(--tinta); }
.passo{ position:relative; padding:0 0 1.35rem 2.5rem; }
.passo::before{ content:""; position:absolute; left:.72rem; top:.4rem; bottom:-.4rem; width:10px;
  background:var(--c, var(--forma)); }
.passo.fim::before{ display:none; }
.passo.caminhada::before{ width:4px; left:.92rem;
  background:radial-gradient(circle, var(--tinta-2) 0 2px, transparent 2.5px) center top/4px 9px repeat-y; }
.passo .no{ position:absolute; left:.37rem; top:.08rem; width:1.35rem; height:1.35rem; border-radius:50%;
  background:#F4F1EC; border:3px solid var(--tinta); box-sizing:border-box; }
.passo.chegada .no{ background:var(--tinta); }
.passo h4{ margin:0 0 .25rem; padding:0; font-size:1.1rem; font-weight:700; line-height:1.3; color:var(--tinta); }
.passo p{ margin:.2rem 0; font-size:.98rem; line-height:1.5; color:#3A362F; max-width:60ch; }
.passo a{ display:inline-flex; align-items:center; gap:.35rem; font-weight:600; margin-top:.15rem; }
.passo a svg{ width:15px; height:15px; stroke:currentColor; }
.sentido{ display:inline-flex; align-items:baseline; gap:.45rem; margin:.45rem 0 .35rem; padding:.55rem .9rem .6rem;
  border-radius:2px; background:var(--c); color:var(--t); min-width:62%;
  box-shadow:0 8px 16px -10px rgba(31,29,26,.7); }
.sentido span{ font-family:var(--cond); font-stretch:62%; font-weight:500; font-size:1.55rem; line-height:.95; color:var(--t); }
.sentido b{ font-family:var(--cond); font-stretch:62%; font-weight:900; font-size:2.1rem; line-height:.95; color:var(--t); }
.confira{ display:flex; gap:.5rem; align-items:flex-start; background:rgba(31,29,26,.06);
  border-radius:3px; padding:.55rem .7rem; margin:.4rem 0 .1rem; font-size:.93rem; line-height:1.45; color:#3A362F; }
.confira svg{ flex:0 0 18px; width:18px; height:18px; stroke:var(--tinta); margin-top:.1rem; }
details{ margin:.4rem 0 .1rem; }
details summary{ cursor:pointer; color:var(--tinta); font-size:.93rem; font-weight:600;
  text-decoration:underline; text-underline-offset:.22em; text-decoration-color:var(--forma); }
details[open] summary{ text-decoration-color:var(--tinta); }
details ol{ margin:.5rem 0 0 1.2rem; padding:0; font-size:.95rem; color:#3A362F; }
details li{ margin:.12rem 0; }
details li::marker{ color:var(--tinta-2); font-variant-numeric:tabular-nums; }

/* Ponto escolhido */
.ponto{ display:flex; gap:.6rem; align-items:flex-start; background:#F4F1EC; border-radius:3px;
  padding:.65rem .75rem; font-size:.93rem; line-height:1.4; color:var(--tinta); }
.ponto svg{ flex:0 0 20px; width:20px; height:20px; stroke:var(--tinta); margin-top:.05rem; }
.ponto b{ display:block; font-weight:700; }
.ponto small{ color:var(--tinta-2); font-size:.86rem; }

/* Notas */
.nota{ display:flex; gap:.6rem; align-items:flex-start; border-radius:3px; padding:.75rem .85rem;
  font-size:.96rem; line-height:1.45; background:var(--laje); color:var(--tinta);
  box-shadow:0 10px 18px -14px rgba(31,29,26,.6); margin:.4rem 0; }
.nota svg{ flex:0 0 20px; width:20px; height:20px; stroke:var(--tinta); margin-top:.05rem; }
.nota.forte{ background:var(--tinta); color:var(--laje); }
.nota.forte svg{ stroke:var(--laje); }
.nota.forte a{ color:var(--laje); }
.dica{ font-size:.86rem; color:var(--tinta-2); margin:-.2rem 0 0; }

/* Expander do mapa e iframes */
.stApp [data-testid="stExpander"] details{ background:var(--laje); border:0; border-radius:3px;
  box-shadow:0 12px 22px -16px rgba(31,29,26,.6); }
.stApp [data-testid="stExpander"] summary{ text-decoration:none; font-weight:700; }
.stApp [data-testid="stExpander"] summary p{ font-weight:700; color:var(--tinta); }
.stApp iframe{ border-radius:2px; }

.rodape{ color:var(--tinta-2); font-size:.84rem; line-height:1.5; margin-top:1.2rem; max-width:60ch; }

@media (min-width:640px){
  .viga h1{ font-size:5.6rem; }
  .veredito h2{ font-size:3.6rem; }
  .viga-dentro{ padding-top:3.4rem; }
}
@media (max-width:380px){
  .viga h1{ font-size:3.5rem; }
  .veredito h2{ font-size:2.5rem; }
  .sentido b{ font-size:1.8rem; }
}
@media (prefers-reduced-motion:reduce){
  .pilar .fill{ animation:none; }
  *{ transition:none !important; }
}
</style>
""".replace("__RUIDO__", _RUIDO)


# Ícones (traço único, 24x24, estilo Lucide)
def icone(nome: str) -> str:
    caminhos = {
        "pe": '<path d="M4 16v-2.38C4 11.5 2.97 10.5 3 8c.03-2.72 1.49-6 4.5-6C9.37 2 10 3.8 10 5.5c0 3.11-2 5.66-2 8.68V16a2 2 0 1 1-4 0Z"/><path d="M20 20v-2.38c0-2.12 1.03-3.12 1-5.62-.03-2.72-1.49-6-4.5-6C14.63 6 14 7.8 14 9.5c0 3.11 2 5.66 2 8.68V20a2 2 0 1 0 4 0Z"/><path d="M16 17h4"/><path d="M4 13h4"/>',
        "pino": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
        "ok": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
        "alerta": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
        "seta": '<path d="m9 18 6-6-6-6"/>',
        "externo": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
        "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    }
    return ('<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{caminhos[nome]}</svg>')


def nota(texto: str, tipo: str = "info", forte: bool = False):
    classe = "nota forte" if forte else "nota"
    st.markdown(f'<div class="{classe}">{icone(tipo)}<div>{texto}</div></div>',
                unsafe_allow_html=True)


def pilarete(lid: str) -> str:
    d = LINHAS[lid]
    return (f'<span class="pilarete" style="background:{d["cor"]};color:{d["txt"]}">'
            f'<span class="num">{lid}</span>{d["nome"]}</span>')


def _plural(n, um, varios):
    return f"{n} {um if n == 1 else varios}"


def link_pe(url: str) -> str:
    return f'<a href="{url}" target="_blank" rel="noopener">Abrir caminho a pé {icone("externo")}</a>'


def passo_caminhada(titulo, texto, link):
    return (f'<div class="passo caminhada"><span class="no"></span><h4>{titulo}</h4>'
            f'<p>{texto}</p>{link_pe(link)}</div>')


def html_rota(rota, p_origem, p_destino) -> str:
    trechos = rota["trechos"]
    n_bald = max(len(trechos) - 1, 0)
    pe_total = rota["pe_ini"][0] + rota["pe_fim"][0]

    partes = ["sem baldeação" if n_bald == 0 else f"com {_plural(n_bald, 'baldeação', 'baldeações')}"]
    if pe_total:
        partes.append(f"{pe_total} min a pé")
    sub = f"{', '.join(partes)}. Tempo estimado, sem contar a espera pelo trem."
    h = [f'<div class="veredito"><h2>Cerca de {rota["minutos"]} min</h2><p>{sub[0].upper() + sub[1:]}</p></div>']

    selos = [pilarete(t["linha"]) for t in trechos]
    pe = f'<span class="pilarete pe">{icone("pe")}a pé</span>'
    if p_origem:
        selos.insert(0, pe)
    if p_destino:
        selos.append(pe)
    h.append(f'<div class="sequencia">{icone("seta").join(selos)}</div><div class="rota">')

    if p_origem:
        lid0, s0 = rota["no_ini"]
        mins, m = rota["pe_ini"]
        h.append(passo_caminhada(
            f"Caminhe até a estação {s0}",
            f"Cerca de {mins} min a pé (≈{round(m / 50) * 50:.0f} m em linha reta) "
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
        h.append(f'<p>Vá para a plataforma da <b>{rotulo(lid)}</b> com esta placa:</p>')
        h.append(f'<div class="sentido"><span>Sentido</span><b>{sent}</b></div>')
        h.append(f'<div class="confira">{icone("ok")}<span>A próxima parada precisa ser '
                 f'<b>{est[1]}</b>. Se for outra, desça e troque para a plataforma oposta.</span></div></div>')

        h.append(f'<div class="passo" style="{c}"><span class="no"></span>')
        if paradas == 1:
            h.append(f'<h4>Viaje 1 parada</h4><p>Desça já na próxima estação, <b>{des}</b>.</p>')
        else:
            h.append(f'<h4>Viaje {paradas} paradas</h4>'
                     f'<p>Fique no trem até <b>{des}</b>.</p>')
            lista = "".join(f"<li>{s}</li>" for s in est[1:])
            h.append(f'<details><summary>Ver as {paradas} estações</summary><ol>{lista}</ol></details>')
        h.append('</div>')

        if i < len(trechos) - 1:
            nxt = trechos[i + 1]
            nl, ne = nxt["linha"], nxt["est"][0]
            h.append(f'<div class="passo caminhada"><span class="no"></span>'
                     f'<h4>Desça em {des} e troque de linha</h4>')
            if ne == des:
                h.append(f'<p>Dentro da estação, siga as placas <b>{rotulo(nl)}</b> até a plataforma.</p>')
            else:
                h.append(f'<p>Siga as placas <b>{rotulo(nl)}</b> até a estação <b>{ne}</b>.</p>')
            if nxt.get("dica_entrada"):
                h.append(f'<div class="confira">{icone("alerta")}<span>{nxt["dica_entrada"]}</span></div>')
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
            f"De {sf} até {p_destino['rotulo']}: cerca de {mins} min a pé.",
            link_a_pe(coord(lidf, sf), (p_destino["lat"], p_destino["lon"]))))
        h.append('<div class="passo chegada fim"><span class="no"></span><h4>Você chegou.</h4></div>')

    h.append('</div>')
    return "".join(h)


def html_pilar(rota) -> str:
    """Pilar entre as lajes: vazio sem rota; concretado nas cores das linhas com rota."""
    if not rota or not rota["trechos"]:
        return '<div class="pilar" aria-hidden="true"></div>'
    fatias = []
    if rota["pe_ini"][0]:
        fatias.append(("#8C867B", max(rota["pe_ini"][0] / 3, 1)))
    for t in rota["trechos"]:
        fatias.append((LINHAS[t["linha"]]["cor"], len(t["est"]) - 1))
    if rota["pe_fim"][0]:
        fatias.append(("#8C867B", max(rota["pe_fim"][0] / 3, 1)))
    blocos = "".join(f'<i style="background:{c};flex:{p}"></i>' for c, p in fatias)
    return f'<div class="pilar" aria-hidden="true"><div class="fill">{blocos}</div></div>'


def mapa_da_rota(rota, p_origem, p_destino):
    pontos = []
    m = folium.Map(tiles="OpenStreetMap", control_scale=True)
    for t in rota["trechos"]:
        cor = LINHAS[t["linha"]]["cor"]
        linha = [coord(t["linha"], s) for s in t["est"]]
        pontos += linha
        folium.PolyLine(linha, color="#1F1D1A", weight=11, opacity=.85).add_to(m)
        folium.PolyLine(linha, color=cor, weight=7, opacity=1).add_to(m)
        for s, xy in zip(t["est"], linha):
            folium.CircleMarker(xy, radius=5, color="#1F1D1A", fill=True, fill_color="#F4F1EC",
                                fill_opacity=1, weight=2.5, tooltip=s).add_to(m)
    for p, no in ((p_origem, rota["no_ini"]), (p_destino, rota["no_fim"])):
        if p:
            a, b = (p["lat"], p["lon"]), coord(*no)
            pontos += [a, b]
            folium.PolyLine([a, b], color="#1F1D1A", weight=3, dash_array="2 8").add_to(m)
            folium.CircleMarker(a, radius=8, color="#1F1D1A", fill=True, fill_color="#1F1D1A",
                                fill_opacity=1, tooltip=p["rotulo"]).add_to(m)
    if pontos:
        m.fit_bounds([[min(x for x, _ in pontos), min(y for _, y in pontos)],
                      [max(x for x, _ in pontos), max(y for _, y in pontos)]], padding=(24, 24))
    return m


# --- Lajes de Partida / Destino ---------------------------------------------
MODOS = ["Estação", "Endereço", "Mapa"]
NAO_TROCAR = ("mapa", "clk", "geo")  # estado de componentes, fica em cada laje


def trocar():
    s = st.session_state
    antigos = {k: s[k] for k in list(s.keys())
               if isinstance(k, str) and k[:2] in ("o_", "d_") and not k.endswith(NAO_TROCAR)}
    sufixos = {k[2:] for k in antigos}
    for suf in sufixos:
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
    r = s[f"{p}_res"][s[f"{p}_escolha"]]
    definir_ponto(p, r["lat"], r["lon"], r["rotulo"])


def mostrar_ponto(p):
    ponto = st.session_state.get(f"{p}_ponto")
    if not ponto:
        return
    prox = estacoes_proximas((ponto["lat"], ponto["lon"]), 2)
    vistos, itens = set(), []
    for (_, s), (mins, _) in sorted(prox.items(), key=lambda x: x[1][1]):
        if s not in vistos:
            vistos.add(s)
            itens.append(f"{s}, {mins} min a pé")
    st.markdown(f'<div class="ponto">{icone("pino")}<div><b>{ponto["rotulo"]}</b>'
                f'<small>Mais perto: {"; ".join(itens)}</small></div></div>',
                unsafe_allow_html=True)


def laje(p: str, titulo: str, ajuda: str):
    s = st.session_state
    with st.container(key=f"laje_{p}"):
        st.markdown(f'<div class="titulo-laje">{titulo}<span>{ajuda}</span></div>',
                    unsafe_allow_html=True)
        modo = st.segmented_control("Como informar", MODOS, key=f"{p}_modo",
                                    label_visibility="collapsed") or "Estação"

        if modo == "Estação":
            c1, c2 = st.columns([1, 1.35])
            with c1:
                lid = st.selectbox("Linha", list(LINHAS), format_func=rotulo, key=f"{p}_linha")
            with c2:
                est = st.selectbox("Estação", LINHAS[lid]["est"], key=f"{p}_est_{lid}")
            return ("estacao", est)

        if modo == "Endereço":
            if p == "o":
                with st.container(key="linha_geo"):
                    c1, c2 = st.columns([1, 6], vertical_alignment="center")
                    with c1:
                        loc = streamlit_geolocation()
                    with c2:
                        st.markdown('<p class="dica">Toque no alvo para usar onde você está agora.</p>',
                                    unsafe_allow_html=True)
                if loc and loc.get("latitude"):
                    atual = (round(loc["latitude"], 6), round(loc["longitude"], 6))
                    if s.get("o_geo") != atual:
                        s["o_geo"] = atual
                        definir_ponto(p, *atual, "Sua localização atual")
            with st.form(f"{p}_form", border=False):
                c1, c2 = st.columns([3, 1.1], vertical_alignment="bottom")
                with c1:
                    texto = st.text_input("Endereço ou lugar", key=f"{p}_txt",
                                          placeholder="Ex.: Av. Paulista, 1578")
                with c2:
                    buscar = st.form_submit_button("Buscar", use_container_width=True)
            if buscar and texto.strip():
                try:
                    with st.spinner("Procurando o endereço…"):
                        res = geocodificar(texto.strip())
                except Exception:
                    res = None
                    nota("A busca de endereços não respondeu. Tente de novo em alguns segundos.", "alerta")
                if res is not None:
                    s[f"{p}_res"] = res
                    s[f"{p}_escolha"] = 0
                    if res:
                        definir_ponto(p, res[0]["lat"], res[0]["lon"], res[0]["rotulo"])
                    else:
                        nota("Nenhum endereço encontrado na Grande São Paulo. "
                             "Acrescente o número, o bairro ou a cidade.", "alerta")
            res = s.get(f"{p}_res") or []
            if len(res) > 1:
                st.selectbox("Não é esse? Escolha o certo", range(len(res)),
                             format_func=lambda i: res[i]["rotulo"], key=f"{p}_escolha",
                             on_change=ao_escolher_resultado, args=(p,))

        if modo == "Mapa":
            st.markdown('<p class="dica">Toque no mapa para marcar o ponto. As bolinhas '
                        'coloridas são estações.</p>', unsafe_allow_html=True)
            ponto = s.get(f"{p}_ponto")
            centro = (ponto["lat"], ponto["lon"]) if ponto else CENTRO_SP
            m = folium.Map(location=centro, zoom_start=15 if ponto else 12,
                           tiles="OpenStreetMap", control_scale=True)
            for lid, d in LINHAS.items():
                for est in d["est"]:
                    folium.CircleMarker(coord(lid, est), radius=4, color=d["cor"], fill=True,
                                        fill_color="#F4F1EC", fill_opacity=1, weight=3,
                                        tooltip=f"{est} ({rotulo(lid)})").add_to(m)
            if ponto:
                folium.CircleMarker(centro, radius=9, color="#1F1D1A", fill=True,
                                    fill_color="#1F1D1A", fill_opacity=1,
                                    tooltip=ponto["rotulo"]).add_to(m)
            out = st_folium(m, key=f"{p}_mapa", height=300, use_container_width=True,
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
        s.o_modo, s.d_modo, s.pref = "Estação", "Estação", "Mais rápida"
        s.o_linha, s["o_est_4"] = "4", "Oscar Freire"
        s.d_linha, s["d_est_1"] = "1", "Vergueiro"

    st.markdown(
        '<header class="viga"><div class="viga-dentro"><h1>MapaDoTrem</h1>'
        '<p>Diga de onde sai e aonde vai. Mostramos em qual trem entrar, em que sentido '
        'e onde trocar de linha.</p></div></header>', unsafe_allow_html=True)

    sel_o = laje("o", "Partida", "de onde você sai")
    with st.container(key="pilar"):
        c1, c2 = st.columns([1, 6], vertical_alignment="center")
        with c1:
            vaga_pilar = st.empty()
        with c2:
            st.button("Inverter partida e destino", key="trocar", on_click=trocar,
                      icon=":material/swap_vert:", use_container_width=True)
    sel_d = laje("d", "Destino", "aonde você vai")

    st.segmented_control("Preferência", ["Mais rápida", "Menos baldeações"], key="pref",
                         label_visibility="collapsed")
    pref = s.get("pref") or "Mais rápida"

    rota = None
    try:
        if not sel_o or not sel_d:
            nota("Falta informar a partida ou o destino. Escolha uma estação, busque um "
                 "endereço ou toque no mapa.", "info")
            return
        if sel_o[0] == sel_d[0] == "estacao" and sel_o[1] == sel_d[1]:
            nota("Partida e destino são a mesma estação. Troque a estação de destino.", "info")
            return

        fontes, p_o = extremos(sel_o)
        alvos, p_d = extremos(sel_d)
        rota = buscar_rota(fontes, alvos, 3 if pref == "Mais rápida" else 60)
        if rota is None:
            nota("Não há ligação entre esses pontos na rede atual.", "alerta")
            return

        a = (p_o["lat"], p_o["lon"]) if p_o else coord(*next(iter(fontes)))
        b = (p_d["lat"], p_d["lon"]) if p_d else coord(*next(iter(alvos)))
        direto = minutos_a_pe(distancia_m(a, b))
        if not rota["trechos"] or direto <= rota["minutos"]:
            nota(f"Ir a pé leva cerca de {direto} min, tão rápido quanto o trem. "
                 f'<a href="{link_a_pe(a, b)}" target="_blank" rel="noopener">Abrir caminho a pé</a>',
                 "pe", forte=True)
            if not rota["trechos"]:
                return

        maior_pe = max(rota["pe_ini"][0], rota["pe_fim"][0])
        if maior_pe > 30:
            nota(f"Um dos pontos fica a cerca de {maior_pe} min a pé da estação mais próxima. "
                 "Vale combinar com ônibus ou carro por aplicativo.", "alerta")

        st.markdown(html_rota(rota, p_o, p_d), unsafe_allow_html=True)
        with st.expander("Ver o trajeto no mapa", icon=":material/map:"):
            st_folium(mapa_da_rota(rota, p_o, p_d), key="mapa_rota", height=380,
                      use_container_width=True, returned_objects=[])

        st.markdown(
            '<p class="rodape">Tempos aproximados. Caminhadas estimadas pela distância. '
            'Rede conforme o mapa oficial de julho de 2026; horários, obras e integrações '
            'tarifadas podem mudar, então confira no site da operadora antes de sair. '
            'Endereços: © colaboradores do OpenStreetMap.</p>', unsafe_allow_html=True)
    finally:
        vaga_pilar.markdown(html_pilar(rota), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
