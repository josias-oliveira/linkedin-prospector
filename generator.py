import random
from scraper import LinkedInProfile


SHORT_TEMPLATES = [
    "Olá {first_name}, acompanho o trabalho da {company} e gostaria de conectar. Seria ótimo trocar ideias!",
    "Oi {first_name}! Vi seu perfil como {title} na {company} e queria te adicionar à minha rede.",
    "Olá {first_name}, admiro o que a {company} vem fazendo. Podemos nos conectar?",
    "Oi {first_name}! Sua trajetória como {title} me chamou atenção. Gostaria de conversar!",
]

LONG_TEMPLATES = [
    """\
Olá {first_name}, tudo bem?

Vi seu perfil e fiquei impressionado com sua trajetória como {title} na {company}.

Entro em contato porque acredito que podemos ter uma conversa interessante sobre {topic}. Tenho trabalhado com empresas similares e vejo bastante sinergia entre o que fazemos.

Seria possível reservar 20 minutos para uma conversa rápida? Sem compromisso, só para nos conhecermos melhor.

Abraço,
""",
    """\
Oi {first_name}!

Pesquisei sobre a {company} e fiquei muito curioso sobre como vocês estão abordando os desafios de {topic}.

Tenho trabalhado com líderes como você e acredito que posso trazer algumas perspectivas que talvez sejam úteis. Também adoraria entender mais sobre o que vocês estão construindo.

Topas um bate-papo rápido de 15-20 minutos essa semana?

Abraço,
""",
    """\
Olá {first_name}, espero que esteja bem!

Como {title} da {company}, você deve lidar diariamente com decisões importantes sobre {topic}.

Queria compartilhar algo que tem ajudado outros líderes no mesmo contexto e ver se faz sentido para vocês também.

Podemos conversar brevemente? Fica à vontade para sugerir um horário.

Abraço,
""",
]

TOPICS_BY_TITLE = {
    "ceo": "crescimento e estratégia de negócios",
    "founder": "construção de produto e escala",
    "cto": "tecnologia e inovação",
    "coo": "operações e eficiência",
    "diretor": "gestão e resultados",
    "dono": "gestão do negócio",
    "presidente": "liderança e visão estratégica",
}


def _first_name(full_name: str) -> str:
    import re
    # Remove grau de conexão (• 2nd, · 3rd+, etc) e caracteres estranhos
    clean = re.sub(r'[•·]\s*(1st|2nd|3rd\+?|\d+)', '', full_name)
    clean = re.sub(r'[•·]', '', clean).strip()
    first = clean.split()[0] if clean else ""
    return first if first else "você"


def _topic(title: str) -> str:
    title_lower = title.lower()
    for key, topic in TOPICS_BY_TITLE.items():
        if key in title_lower:
            return topic
    return "inovação e crescimento"


def generate_message(profile: LinkedInProfile, context: str = "", tone: str = "direto") -> dict:
    first_name = _first_name(profile.name)
    company = profile.company or "sua empresa"
    title = profile.title or "líder"
    topic = _topic(profile.title)

    short = random.choice(SHORT_TEMPLATES).format(
        first_name=first_name,
        company=company,
        title=title,
    )

    long = random.choice(LONG_TEMPLATES).format(
        first_name=first_name,
        company=company,
        title=title,
        topic=topic,
    )

    return {
        "short_message": short,
        "long_message": long,
    }
