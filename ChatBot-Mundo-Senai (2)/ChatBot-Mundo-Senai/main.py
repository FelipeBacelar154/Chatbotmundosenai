import sys
import os

sys.path.insert(0, os.path.dirname(
    os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import random
import re
import os
import unicodedata  # Adicionado para remover acentos

app = Flask(__name__)
# Permite requisições de qualquer origem (para desenvolvimento)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)  # Necessário para usar session


# --- Função para remover acentos ---
def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')


# --- Definição das Categorias e Respostas ---
categorias = {
    # === CATEGORIA DE ALTA PRIORIDADE: FORA DE ESCOPO / INADEQUADO ===
    "fora_de_escopo": {
        "padroes": [
            r"\b(negros|brancos|asiáticos|mulheres|homens|gays|lésbicas|trans|judeus|muçulmanos|cristãos|pobres|ricos|políticos)\b",
            r"\b(todo|toda|todos|todas) (negro|branca|asiático|mulher|homem|gay|lésbica|trans|judeu|muçulmano|cristão|pobre|rico|político)\b",
            r"qual (o|é o) sentido da vida\b", r"deus existe\b",
            r"\b(odeio|detesto) (negros|brancos|asiáticos|mulheres|homens|gays|lésbicas|trans|judeus|muçulmanos|cristãos)\b",
            r"qual (a|é a) capital d(o|a|os|as)\b",
            r"quem descobriu o brasil\b",
            r"\b(futebol|política|religião|economia)\b"
        ],
        "respostas": [
            "Como terapeuta virtual, meu foco é ajudar você a explorar seus sentimentos e emoções. Não posso comentar sobre generalizações, opiniões sobre grupos ou tópicos fora desse escopo terapêutico. Como você está se sentindo hoje?",
            "Minha função é oferecer apoio emocional individual. Não estou programada para discutir temas polêmicos, política, religião, fazer julgamentos sobre grupos de pessoas ou responder perguntas factuais aleatórias. Podemos focar em como você está se sentindo?",
            "Para manter nosso foco terapêutico, não posso responder a perguntas que envolvam generalizações, temas sensíveis não relacionados diretamente aos seus sentimentos ou fatos gerais. Gostaria de falar sobre como você está se sentindo hoje?"
        ]
    },
    "brincadeira": {
        "padroes": [
            r"\b(caguei|peidei|arrotei|vomitei|me mijei|me mijei todo|me caguei|cocô|xixi|pum|bosta|merda|peido|nojento)\b",
            r"\b(trolar|zoar|besteira|brincadeira|só zuando|só brincando|bobagem|idiota|bunda|penis|vagina|puta|fuder|porra|lixo|xingamento|nojento|cagada|pirada|fodase|fodasse|peito|peitinho|gostosa|gostoso|goxtoso|goxtosa)\b"
        ],
        "respostas": [
            "Este espaço é voltado para apoio emocional. Se quiser conversar sobre algo sério, estou aqui.",
            "Lembre-se que este chat é feito para te ajudar em momentos difíceis. Vamos focar nisso?",
            "Se você estiver passando por algo e quiser conversar de verdade, estou aqui para ajudar.",
            "Sou um espaço de acolhimento. Podemos focar em algo que esteja te incomodando de verdade?"
        ]
    },
    # === CATEGORIA DE ALTA PRIORIDADE: IDEAÇÃO SUICIDA ===
    "ideacao_suicida": {
        "padroes": [
            r"\b(quero morrer|quero me matar|não quero mais viver|nao quero mais viver|não aguento mais|nao aguento mais|pensando em suicídio|pensando em suicidio|acabar com tudo|sumir|desaparecer|morrer|suicidio)\b",
            r"\b(sem sentido|sem proposito|vida não vale a pena|vida nao vale a pena)\b"
        ],
        "respostas": [
            "Sinto muito que você esteja se sentindo assim, com tanta dor. Saiba que você não está sozinho(a) e que sua vida é importante. Estou aqui para ouvir.",
            "Pensamentos suicidas são um sinal de sofrimento extremo, mas não precisam ser o fim. Existem pessoas e recursos que podem te ajudar a encontrar um caminho diferente. Por favor, procure ajuda imediatamente.",
            "**Se você está em perigo imediato, ligue para o CVV (Centro de Valorização da Vida) no número 188 (ligação gratuita) ou para o SAMU (192). Eles estão disponíveis 24h para te ajudar.**",
            "Falar sobre esses sentimentos é um passo corajoso. O que está tornando as coisas tão insuportáveis para você agora?"
        ],
        "conselhos": [
            "**Procure ajuda profissional urgente:** Um psicólogo ou psiquiatra pode te ajudar a lidar com essa dor. Não hesite em buscar um serviço de emergência se necessário.",
            "**Converse com alguém de confiança:** Falar sobre seus sentimentos com um amigo, familiar ou líder religioso pode trazer algum alívio.",
            "**Ligue para o CVV (188):** É um serviço gratuito, sigiloso e disponível 24 horas por dia para apoio emocional.",
            "**Afaste-se de meios letais:** Se você tem planos ou meios para se machucar, tente se afastar deles e procure um local seguro ou a companhia de alguém."
        ]
    },
    # --- Categorias Emocionais (Negativas) ---
    "ansiedade": {
        "padroes": [
            r"\b(ansiedade|ansioso|ansiosa|nervoso|nervosa|preocupado|preocupada|preocupação|pânico|panico|tenso|tensa)\b",
            r"\b(não consigo relaxar|mente acelerada|coração acelerado|coracao acelerado|respiração|respiracao)\b",
            r"\b(estou em pânico|acho que vou morrer|não consigo respirar|meu coração está disparado|tô tremendo|crise de pânico)\b"  # Crise de Pânico
        ],
        "respostas": [
            "A ansiedade pode ser muito desafiadora. Você consegue identificar o que está desencadeando esses sentimentos?",
            "Entendo que a ansiedade pode ser avassaladora. Respire fundo algumas vezes. O que está passando pela sua mente agora?",
            "A sensação de ansiedade é difícil. Você já tentou alguma técnica de respiração ou mindfulness para esses momentos?",
            "É normal sentir ansiedade, mas não precisa enfrentar isso sozinho. Quer compartilhar mais sobre o que está sentindo?",
            "Respira comigo, tudo bem? Você está em segurança agora. Isso vai passar.",  # Crise de Pânico
            "Crises de pânico são assustadoras, mas não são perigosas. Vamos passar por isso juntos."  # Crise de Pânico
        ],
        "conselhos": [
            "Quando a ansiedade surgir, tente a técnica 5-5-5: inspire por 5 segundos, segure por 5 segundos, e expire por 5 segundos.",
            "Escrever seus pensamentos ansiosos pode ajudar a externalizar e diminuir seu poder.",
            "Praticar atenção plena diariamente, mesmo por 5 minutos, pode ajudar a reduzir a ansiedade a longo prazo.",
            "Limitar cafeína e praticar atividade física regularmente pode ajudar a reduzir os sintomas físicos da ansiedade.",
            "Tente se concentrar na sua respiração. Inspire por 4 segundos, segure por 4, e expire por 6.",  # Crise de Pânico
            "Identifique cinco coisas que você vê, quatro que pode tocar, três que pode ouvir — isso ajuda a ancorar na realidade."  # Crise de Pânico
        ]
    },
    "tristeza": {
        "padroes": [
            r"\b(triste|tristeza|deprimido|deprimida|depressão|depressao|melancolia|melancólico|melancólica|desanimado|desanimada)\b",
            r"\b(sem esperança|sem esperanca|vazio|vazia|abandonado|abandonada|chorar|chorando)\b",
            r"\b(não aguento mais|nao aguento mais|cansado disso|cansada disso|sem vontade|não sinto vontade de nada|so quero ficar deitado|nada faz sentido)\b"  # Depressão
        ],
        "respostas": [
            "Sinto muito que você esteja passando por esse momento difícil. Sentir tristeza é parte da experiência humana. Quer falar mais sobre o que está sentindo?",
            "A tristeza pode ser muito pesada. Você tem conseguido fazer pequenas coisas que normalmente te trazem alegria?",
            "É importante reconhecer e validar esses sentimentos. Existe algo específico que desencadeou esse sentimento?",
            "Obrigado por compartilhar. A tristeza pode nos fazer sentir muito sozinhos, mas você não está só. Como posso te apoiar?",
            "Sinto muito que você esteja se sentindo assim. Não é fraqueza sentir isso. Quer me contar mais sobre o que tem vivido?",  # Depressão
            "Você não está sozinho(a). Muitas pessoas passam por isso e conseguem melhorar com ajuda."  # Depressão
        ],
        "conselhos": [
            "Mesmo nos dias mais difíceis, tente uma pequena atividade que costumava lhe trazer alegria.",
            "Estabelecer uma rotina diária, mesmo simples, pode ajudar a criar estrutura.",
            "Permita-se sentir suas emoções sem julgamento. A tristeza é uma resposta natural.",
            "Conectar-se com outras pessoas, mesmo sem vontade, pode ser terapêutico.",
            "Procure manter uma rotina básica, mesmo que difícil: se alimentar, tomar banho, sair um pouco ao sol.",  # Depressão
            "A depressão é uma condição séria, mas tratável. Buscar um psicólogo ou psiquiatra é um passo importante."  # Depressão
        ]
    },
    "raiva": {
        "padroes": [
            r"\b(raiva|irritado|irritada|bravo|brava|furioso|furiosa|ódio|odio|detesto|detesta)\b",
            r"\b(frustrado|frustrada|frustração|frustracao|indignado|indignada|revoltado|revoltada)\b",
            r"\b(não aguento|nao aguento|não suporto|nao suporto|odeio|odeia|quero matar|estou puto|estou puta)\b"
        ],
        "respostas": [
            "Entendo que você está sentindo raiva. É uma emoção natural. Pode me contar mais sobre o que provocou esse sentimento?",
            "A raiva muitas vezes surge quando nos sentimos injustiçados ou desrespeitados. O que aconteceu para você se sentir assim?",
            "É compreensível sentir raiva. Como você costuma lidar com esses sentimentos intensos?",
            "A raiva pode ser avassaladora. Respire fundo. Você consegue identificar o que está por trás dessa raiva?"
        ],
        "conselhos": [
            "Quando sentir raiva intensa, tente a técnica do \"tempo fora\": afaste-se da situação por alguns minutos e respire.",
            "Expresse a raiva de forma construtiva, usando frases na primeira pessoa como \"Eu me sinto frustrado quando...\".",
            "A atividade física pode ser uma excelente válvula de escape para a raiva.",
            "Escrever sobre seus sentimentos de raiva pode ajudar a processá-los e identificar gatilhos."
        ]
    },
    "autoestima_corporal": {
        "padroes": [
            r"\b(gordo|gorda|peso|corpo|feio|feia|me acho|não gosto de mim|nao gosto de mim|meu corpo|minha aparência|minha aparencia)\b",
            r"\b(inseguro|insegura) com (meu|minha) aparência\b",
            r"\b(vergonha) d(o|a) (meu|minha) corpo\b",
            r"\b(transtorno alimentar|anorexia|bulimia|não consigo comer|vomito depois de comer|medo de engordar)\b"
        ],
        "respostas": [
            "Entendo que a forma como nos vemos pode impactar muito nossos sentimentos. Quer falar mais sobre como se sente em relação à sua imagem corporal?",
            "Obrigado por compartilhar. A relação com nosso corpo pode ser complexa. Como esses pensamentos afetam seu dia a dia?",
            "É importante explorar esses sentimentos sobre sua imagem. Existe alguma situação específica que intensifica essa percepção?",
            "Sua percepção sobre si mesmo é muito importante. Vamos conversar um pouco mais sobre esses sentimentos?",
            "Sinto muito que esteja passando por isso. Seu corpo merece cuidado. Quer conversar mais sobre como tem se sentido com seu corpo?",  # T.A.
            "Isso que você está sentindo é sério e merece atenção. Você não está sozinho(a). Muitas pessoas se recuperam com ajuda."  # T.A.
        ],
        "conselhos": [
            "Tente focar nas funcionalidades do seu corpo, não apenas na aparência. Praticar gratidão pelo que ele permite fazer pode ajudar.",
            "Desafie pensamentos negativos sobre sua aparência. Pergunte-se: \"Isso é realmente verdade? Qual seria uma forma mais gentil de pensar sobre mim?\"",
            "Limite a exposição a conteúdos (redes sociais) que promovem padrões de beleza irreais ou te fazem sentir inadequado(a).",
            "Lembre-se que seu valor vai muito além da aparência. Cultive seus talentos, hobbies e relacionamentos.",
            "Evite seguir perfis que reforcem padrões irreais. Busque inspirações que promovam saúde e bem-estar real.",  # T.A.
            "Falar com um nutricionista ou psicólogo especializado em transtornos alimentares pode te ajudar a cuidar da sua saúde de forma acolhedora."  # T.A.
        ]
    },
    "autoestima": {
        "padroes": [
            r"\b(não sou bom|nao sou bom|não sou boa|nao sou boa|não sou suficiente|nao sou suficiente)\b",
            r"\b(me odeio|odeio a mim|não me amo|nao me amo|sou um fracasso|inútil|inutil|incompetente|incapaz|sem valor|não valho|nao valho|não mereço|nao mereco)\b",
            r"\b(medo do que vão pensar|me sinto julgado|tenho vergonha de ser eu|sou muito inseguro|fico me comparando|não consigo me soltar perto dos outros)\b",  # Medo de julgamento
            r"\b(só erro na vida|não sirvo pra nada|todo mundo consegue menos eu|me sinto um inútil|não sou bom o bastante)\b"  # Sensação de fracasso
        ],
        "respostas": [
            "Sinto muito que esteja se sentindo assim. Todos nós temos valor. O que te leva a ter esses pensamentos sobre si?",
            "Esses pensamentos negativos podem ser dolorosos. Você consegue lembrar de qualidades ou momentos que contradizem essa visão?",
            "Nossa autoestima flutua. Se um amigo estivesse na sua situação, o que você diria a ele?",
            "Esses pensamentos não definem quem você é. Como você acha que começou a desenvolver essa visão sobre si?",
            "Sentir medo do julgamento é comum. Quer conversar sobre isso?",  # Medo de julgamento
            "Sinto que você está se cobrando muito. Você não é um fracasso. Quer conversar sobre isso?"  # Sensação de fracasso
        ],
        "conselhos": [
            "Mantenha um diário de gratidão e realizações, anotando 3 coisas que você fez bem ou pelas quais é grato a cada dia.",
            "Pratique falar consigo mesmo com a mesma gentileza que ofereceria a um amigo querido.",
            "Desafie pensamentos autocríticos: \"Qual a evidência real para isso?\" e \"Existe uma perspectiva mais equilibrada?\"",
            "Estabeleça pequenas metas alcançáveis e celebre cada sucesso. Isso constrói confiança.",
            "Observe com quem você se sente mais livre. Estar com pessoas acolhedoras ajuda.",  # Medo de julgamento
            "Relembre suas pequenas conquistas. Fracasso não define quem você é, é parte do caminho."  # Sensação de fracasso
        ]
    },
    "solidao": {
        "padroes": [
            r"\b(sozinho|sozinha|solitário|solitária|solidao|solidão|ninguém gosta de mim|ninguem gosta de mim|sem amigos|me sinto isolado|isolada|isolado|excluido)\b"
        ],
        "respostas": [
            "A solidão pode ser um sentimento pesado. Você tem se sentido assim há muito tempo?",
            "Entendo que se sentir sozinho(a) é difícil. Quer falar sobre o que pode estar contribuindo para isso?",
            "Lembre-se que você não está realmente sozinho(a) nessa sensação. Muitas pessoas passam por isso. Como posso te apoiar?"
        ],
        "conselhos": [
            "Tente se conectar com pessoas que compartilham seus interesses (grupos online, atividades locais).",
            "Um pequeno gesto, como iniciar uma conversa, pode abrir portas para novas conexões.",
            "Invista tempo em atividades que você gosta. Isso pode atrair pessoas com interesses semelhantes.",
            "Se a solidão persistir e causar sofrimento, conversar com um terapeuta pode ajudar a explorar as causas."
        ]
    },
    "confusao": {
        "padroes": [
            r"\b(confuso|confusa|perdido|perdida|não sei o que fazer|nao sei o que fazer|indeciso|indecisa|em dúvida|em duvida|sem rumo)\b",
            r"\b(não sei o que fazer|estou dividido entre duas escolhas|tenho medo de escolher errado|qual é o caminho certo?|toda decisão parece errada)\b"  # Decisões difíceis
        ],
        "respostas": [
            "Sentir-se confuso(a) é normal, especialmente em momentos de transição. O que está passando pela sua mente que causa essa sensação?",
            "A confusão pode ser paralisante. Vamos tentar organizar os pensamentos. Quais são as opções ou caminhos que você vê?",
            "É compreensível sentir-se perdido(a). Quais são os valores ou objetivos mais importantes para você neste momento?",
            "Tomar decisões pode ser difícil. Quais são os prós e contras de cada opção que você está considerando?"  # Decisões difíceis
        ],
        "conselhos": [
            "Escreva seus pensamentos e sentimentos. Colocar no papel pode trazer clareza.",
            "Converse com alguém de confiança sobre sua confusão. Uma perspectiva externa pode ajudar.",
            "Faça uma lista de prós e contras para cada opção que está considerando.",
            "Dê um tempo para a mente descansar. Às vezes, a clareza surge após uma pausa.",
            "Pense nos seus valores fundamentais. Qual opção se alinha mais com o que é importante para você?"  # Decisões difíceis
        ]
    },
    "medo": {
        "padroes": [
            r"\b(medo|receio|apreensivo|apreensiva|assustado|assustada|pavor|temor)\b",
            r"\b(fobia|pânico|pavor) de\b"
        ],
        "respostas": [
            "O medo é uma resposta natural ao perigo percebido. O que está te causando medo neste momento?",
            "Sentir medo pode ser paralisante. Você consegue identificar a origem desse medo?",
            "É normal sentir medo. Como você costuma lidar com essa sensação?"
        ],
        "conselhos": [
            "Respire fundo e lentamente. A respiração profunda pode acalmar o sistema nervoso.",
            "Desafie o pensamento catastrófico: \"Qual a probabilidade real disso acontecer?\" e \"Como eu poderia lidar se acontecesse?\"",
            "Exponha-se gradualmente ao que te causa medo, em pequenas doses controladas, se for seguro.",
            "Converse sobre seus medos com alguém de confiança ou um profissional."
        ]
    },
    "culpa": {
        "padroes": [
            r"\b(culpa|culpado|culpada|remorso|arrependido|arrependida)\b",
            r"\b(eu deveria ter feito|eu não deveria ter feito|se eu tivesse feito diferente)\b"
        ],
        "respostas": [
            "A culpa pode ser um fardo pesado. O que aconteceu para você se sentir assim?",
            "Sentir culpa indica que você tem um senso de responsabilidade. Quer falar mais sobre a situação?",
            "O arrependimento faz parte da vida. O que você aprendeu com essa experiência?"
        ],
        "conselhos": [
            "Reconheça o erro, se houve um, e peça desculpas se for apropriado e possível.",
            "Perdoe a si mesmo(a). Todos cometemos erros. O importante é aprender com eles.",
            "Foque no que você pode fazer agora para reparar a situação ou agir diferente no futuro.",
            "Diferencie culpa produtiva (que leva à mudança) de culpa ruminativa (que só causa sofrimento)."
        ]
    },
    "estresse": {
        "padroes": [
            r"\b(estresse|estressado|estressada|sobrecarregado|sobrecarregada|pressão|pressao|exausto|exausta|esgotado|esgotada)\b"
        ],
        "respostas": [
            "O estresse é uma resposta comum às demandas da vida. O que está contribuindo para seu estresse agora?",
            "Sentir-se sobrecarregado(a) é desgastante. Você tem conseguido tempo para cuidar de si?",
            "A pressão pode ser intensa. Quais são as principais fontes dessa pressão no momento?"
        ],
        "conselhos": [
            "Priorize suas tarefas e aprenda a dizer \"não\" para compromissos excessivos.",
            "Reserve tempo diário para atividades relaxantes, como ler, ouvir música ou tomar um banho quente.",
            "Pratique exercícios físicos regularmente. É uma ótima forma de liberar a tensão.",
            "Garanta uma boa noite de sono. O descanso é fundamental para lidar com o estresse."
        ]
    },
    # --- Categorias Emocionais (Positivas) ---
    "alegria": {
        "padroes": [
            r"\b(feliz|alegre|contente|satisfeito|satisfeita|animado|animada|ótimo|otimo|bem|maravilhoso|maravilhosa|incrível|incrivel)\b"
        ],
        "respostas": [
            "Que ótimo saber que você está se sentindo feliz! O que te trouxe essa alegria?",
            "Fico feliz por você! É maravilhoso sentir-se assim. Quer compartilhar mais sobre esse momento?",
            "Alegria é contagiante! O que está tornando seu dia especial?"
        ],
        "conselhos": [
            "Saboreie o momento! Permita-se sentir plenamente essa alegria.",
            "Compartilhe sua alegria com outras pessoas. Isso pode amplificar o sentimento.",
            "Anote o que te trouxe felicidade. Isso pode te ajudar a cultivar mais momentos assim.",
            "Expresse gratidão pelas coisas boas que estão acontecendo."
        ]
    },
    "gratidao": {
        "padroes": [
            r"\b(grato|grata|gratidão|gratidao|agradecido|agradecida|obrigado|obrigada)\b por (algo|tudo|vida)\b"
        ],
        "respostas": [
            "A gratidão é um sentimento poderoso. Pelo que você se sente grato(a) hoje?",
            "Que bom que você está cultivando a gratidão! Compartilhar isso pode inspirar outros.",
            "É maravilhoso reconhecer as coisas boas da vida. O que te inspira essa gratidão?"
        ],
        "conselhos": [
            "Mantenha um diário de gratidão, anotando algumas coisas pelas quais você é grato(a) todos os dias.",
            "Expresse sua gratidão às pessoas importantes em sua vida.",
            "Pratique a atenção plena para notar as pequenas coisas boas do dia a dia.",
            "Reflita sobre os desafios que você superou. Isso também pode gerar gratidão pela sua força."
        ]
    },
    "esperanca": {
        "padroes": [
            r"\b(esperança|esperancoso|esperancosa|confiante|otimista)\b",
            r"\b(acredito que vai melhorar|tenho fé|as coisas vão dar certo)\b"
        ],
        "respostas": [
            "A esperança nos impulsiona. O que te dá esperança neste momento?",
            "É muito bom ter esperança! Quais são suas expectativas positivas para o futuro?",
            "Manter a esperança é fundamental. Como você nutre esse sentimento?"
        ],
        "conselhos": [
            "Cerque-se de pessoas e histórias positivas que reforcem sua esperança.",
            "Defina pequenas metas alcançáveis que te aproximem dos seus objetivos.",
            "Lembre-se de momentos difíceis que você já superou. Sua resiliência é uma fonte de esperança.",
            "Foque no que você pode controlar e aja em direção ao que deseja."
        ]
    },
    "amor": {
        "padroes": [
            r"\b(amo|adoro|apaixonado|apaixonada|carinho|afeto)\b (por|pelo|pela) (alguém|alguem|meu|minha)\b",
            r"\b(relacionamento|namorado|namorada|marido|esposa|parceiro|parceira)\b"
        ],
        "respostas": [
            "O amor é um sentimento lindo e complexo. Como você está vivenciando o amor agora?",
            "Falar sobre amor e relacionamentos é importante. O que você gostaria de compartilhar sobre isso?",
            "Que bom sentir esse carinho! Como esse sentimento se manifesta em sua vida?"
        ],
        "conselhos": [
            "Comunique seus sentimentos e necessidades de forma aberta e honesta no relacionamento.",
            "Dedique tempo de qualidade para nutrir seus relacionamentos importantes.",
            "Pratique a empatia, tentando compreender a perspectiva do outro.",
            "Lembre-se de cuidar também do amor próprio. É a base para relacionamentos saudáveis."
        ]
    },
    # --- Categorias Gerais / Funcionais ---
    "saudacao": {
        "padroes":
        [r"\b(oi|olá|ola|bom dia|boa tarde|boa noite|ei|e aí|eae)\b"],
        "respostas": [
            "Olá! Como você está se sentindo hoje?",
            "Oi! Em que posso te ajudar a refletir sobre seus sentimentos?",
            "Olá! Estou aqui para te ouvir. Como posso te apoiar agora?"
        ]
    },
    "despedida": {
        "padroes": [
            r"\b(tchau|adeus|até mais|ate mais|até logo|ate logo|vou indo|preciso ir)\b"
        ],
        "respostas": [
            "Tudo bem. Lembre-se que estou aqui se precisar conversar novamente. Cuide-se!",
            "Entendido. Espero que nossa conversa tenha sido útil. Até a próxima!",
            "Ok. Se cuida e não hesite em voltar se precisar de apoio."
        ]
    },
    "agradecimento": {
        "padroes": [
            r"\b(obrigado|obrigada|valeu|agradeço|agradeco|grato|grata|gosto muito de voce|seu lindo|sua linda)\b"
        ],
        "respostas": [
            "De nada! Estou aqui para ajudar no que for possível.",
            "Fico feliz em poder ajudar!",
            "Disponha! Se precisar de mais alguma coisa, é só dizer."
        ]
    },
    "afirmacao": {
        "padroes":
        [r"\b(sim|claro|com certeza|ok|entendi|entendo|concordo|uhum|aham)\b"],
        "respostas": ["Entendido.", "Ok.", "Compreendo."]
    },
    "negacao": {
        "padroes": [r"\b(não|nao|nunca|jamais|de jeito nenhum|negativo)\b"],
        "respostas": ["Entendido.", "Ok, compreendo.", "Certo."]
    },
    "duvida_sobre_bot": {
        "padroes": [
            r"quem é você|quem e voce|o que você faz|o que voce faz|você é real|voce e real|é um robô|e um robo|como você funciona|como voce funciona"
        ],
        "respostas": [
            "Eu sou um chatbot terapêutico, projetado para te ouvir, oferecer apoio emocional e ajudar a refletir sobre seus sentimentos. Não sou um terapeuta humano, mas posso ser um espaço seguro para você se expressar.",
            "Minha função é conversar com você sobre suas emoções e pensamentos, oferecendo um espaço de acolhimento. Eu uso padrões de linguagem para entender as categorias de sentimentos e oferecer respostas e conselhos gerais. Lembre-se que não substituo um profissional de saúde mental.",
            "Sou uma inteligência artificial criada para simular uma conversa terapêutica. Meu objetivo é te ajudar a explorar seus sentimentos e oferecer apoio, mas não tenho consciência ou emoções próprias."
        ]
    },
    # --- Categoria Padrão (Fallback) ---
    "padrao": {
        "padroes":
        [],  # Sem padrões específicos, será usado se nenhuma outra categoria for detectada
        "respostas": [
            "Hmm, interessante. Como você se sente em relação a isso?",
            "Entendo. Você gostaria de explorar mais esse sentimento?",
            "Obrigado por compartilhar. Pode me contar um pouco mais sobre o que está pensando?",
            "Isso parece importante. Como essa situação te afeta?",
            "Compreendo. E como você está lidando com isso?"
        ]
    }
}

# Lista de categorias de alta prioridade para verificar primeiro
high_priority_categories = ["fora_de_escopo", "brincadeira", "ideacao_suicida"]


# --- Função de Detecção de Categoria ---
def detectar_categoria(mensagem):
    mensagem_normalizada = remover_acentos(mensagem.lower())

    # 1. Verifica categorias de alta prioridade
    for categoria_nome in high_priority_categories:
        categoria_info = categorias[categoria_nome]
        for padrao in categoria_info["padroes"]:
            if re.search(padrao, mensagem_normalizada, re.IGNORECASE):
                resposta = random.choice(categoria_info["respostas"])
                # Adiciona conselhos se existirem para ideação suicida
                if categoria_nome == "ideacao_suicida" and "conselhos" in categoria_info:
                    resposta += "\n\n" + random.choice(
                        categoria_info["conselhos"])
                return categoria_nome, resposta

    # 2. Verifica outras categorias
    melhor_categoria = "padrao"
    max_palavras_chave = 0

    for categoria_nome, categoria_info in categorias.items():
        if categoria_nome in high_priority_categories or categoria_nome == "padrao":
            continue  # Já verificadas ou é o fallback

        palavras_chave_encontradas = 0
        for padrao in categoria_info["padroes"]:
            if re.search(padrao, mensagem_normalizada, re.IGNORECASE):
                # Conta palavras-chave básicas (uma aproximação simples)
                palavras_chave_padrao = re.findall(r'\b(\w+)\b', padrao)
                for palavra in palavras_chave_padrao:
                    if palavra in mensagem_normalizada.split():
                        palavras_chave_encontradas += 1

        if palavras_chave_encontradas > max_palavras_chave:
            max_palavras_chave = palavras_chave_encontradas
            melhor_categoria = categoria_nome

    # Se encontrou uma categoria não prioritária com correspondência
    if melhor_categoria != "padrao":
        categoria_info = categorias[melhor_categoria]
        resposta = random.choice(categoria_info["respostas"])
        # Adiciona conselhos se existirem
        if "conselhos" in categoria_info:
            resposta += "\n\n" + random.choice(categoria_info["conselhos"])
        return melhor_categoria, resposta

    # 3. Se nenhuma categoria foi detectada, usa a padrão
    return "padrao", random.choice(categorias["padrao"]["respostas"])


# --- Rotas da API Flask ---
@app.route("/")
def index():
    # Verifica se a pasta 'templates' e o 'index.html' existem
    template_folder = os.path.join(os.path.dirname(__file__), "templates")
    index_html_path = os.path.join(template_folder, "index.html")

    if not os.path.exists(template_folder):
        os.makedirs(template_folder)
        print("Pasta 'templates' criada.")  # Corrigido

    if not os.path.exists(index_html_path):
        print(
            "Arquivo 'templates/index.html' não encontrado. Criando um básico..."
        )  # Corrigido
        # Cria um conteúdo HTML básico se o arquivo não existir
        html_content = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Terapêutico</title>
    <style>
        body {
            font-family: sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: #f4f4f4;
        }
        #chat-container {
            width: 90%;
            max-width: 500px;
            height: 80vh;
            max-height: 600px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        h1 {
            text-align: center;
            padding: 15px;
            margin: 0;
            background-color: #5a9;
            color: white;
            font-size: 1.2em;
        }
        #chatbox {
            flex-grow: 1;
            padding: 15px;
            overflow-y: auto;
            border-top: 1px solid #eee;
            border-bottom: 1px solid #eee;
            display: flex;
            flex-direction: column;
        }
        .message-container {
            display: flex;
            margin-bottom: 10px;
            max-width: 80%;
        }
        .message-container.user {
            align-self: flex-end;
            justify-content: flex-end;
        }
        .message-container.bot {
            align-self: flex-start;
            justify-content: flex-start;
        }
        .message {
            padding: 10px 15px;
            border-radius: 18px;
            word-wrap: break-word;
            line-height: 1.4;
        }
        .message-container.user .message {
            background-color: #dcf8c6;
            color: #333;
            border-bottom-right-radius: 4px;
        }
        .message-container.bot .message {
            background-color: #eee;
            color: #333;
            border-bottom-left-radius: 4px;
        }
        #input-area {
            display: flex;
            padding: 10px;
            background-color: #f0f0f0;
        }
        #msg {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 20px;
            margin-right: 10px;
            outline: none;
        }
        #send-button {
            padding: 10px 20px;
            background-color: #5a9;
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        #send-button:hover {
            background-color: #488;
        }
        /* Estilização da barra de rolagem */
        #chatbox::-webkit-scrollbar {
            width: 8px;
        }
        #chatbox::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        #chatbox::-webkit-scrollbar-thumb {
            background: #ccc;
            border-radius: 10px;
        }
        #chatbox::-webkit-scrollbar-thumb:hover {
            background: #aaa;
        }
    </style>
</head>
<body>
    <div id="chat-container">
        <h1>Chat Terapêutico</h1>
        <div id="chatbox"></div>
        <div id="input-area">
            <input type="text" id="msg" placeholder="Digite sua mensagem..." autocomplete="off">
            <button id="send-button" onclick="sendMessage()">Enviar</button>
        </div>
    </div>

    <script>
        const chatbox = document.getElementById('chatbox');
        const msgInput = document.getElementById('msg');

        function sendMessage() {
            const message = msgInput.value.trim();
            if (!message) return;

            displayMessage(message, 'user');
            msgInput.value = '';
            msgInput.focus();

            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ mensagem: message })
            })
            .then(response => {
                if (!response.ok) {
                    // Tenta ler a mensagem de erro do JSON, se houver
                    return response.json().then(errData => {
                        throw new Error(errData.resposta || `HTTP error! status: ${response.status}`);
                    }).catch(() => {
                         throw new Error(`HTTP error! status: ${response.status}`); // Caso não seja JSON
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.resposta) {
                    displayMessage(data.resposta, 'bot');
                } else {
                    displayMessage('Desculpe, não recebi uma resposta válida.', 'bot');
                }
            })
            .catch(error => {
                console.error('Erro ao enviar/receber mensagem:', error);
                displayMessage(`Desculpe, ocorreu um erro: ${error.message}. Tente novamente.`, 'bot');
            });
        }

        function displayMessage(text, sender) {
            const messageContainer = document.createElement('div');
            messageContainer.classList.add('message-container', sender);

            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.textContent = text;

            messageContainer.appendChild(messageDiv);
            chatbox.appendChild(messageContainer);

            chatbox.scrollTop = chatbox.scrollHeight;
        }

        msgInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Opcional: Mensagem inicial do bot ao carregar
        // window.onload = () => {
        //     displayMessage("Olá! Como posso te ajudar hoje?", 'bot');
        // };

    </script>
</body>
</html>
"""
        with open(index_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(
            "Arquivo 'templates/index.html' criado com sucesso.")  # Corrigido

    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    dados = request.get_json()
    mensagem = dados.get("mensagem", "")
    if not mensagem:
        return jsonify({
            "categoria": "erro",
            "resposta": "Mensagem vazia recebida."
        }), 400

    categoria, resposta = detectar_categoria(mensagem)
    return jsonify({"categoria": categoria, "resposta": resposta})


# --- Execução do App ---
if __name__ == "__main__":
    # Verifica e cria o arquivo index.html se não existir (repetido, mas garante)
    template_folder = os.path.join(os.path.dirname(__file__), "templates")
    index_html_path = os.path.join(template_folder, "index.html")
    if not os.path.exists(template_folder):
        os.makedirs(template_folder)
        print("Pasta 'templates' criada.")  # Corrigido
    if not os.path.exists(index_html_path):
        print(
            "Arquivo 'templates/index.html' não encontrado. Criando um básico..."
        )  # Corrigido
        html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Terapêutico</title>
    <style>
        body {
            font-family: sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: #f4f4f4;
        }
        #chat-container {
            width: 90%;
            max-width: 500px;
            height: 80vh;
            max-height: 600px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        h1 {
            text-align: center;
            padding: 15px;
            margin: 0;
            background-color: #5a9;
            color: white;
            font-size: 1.2em;
        }
        #chatbox {
            flex-grow: 1;
            padding: 15px;
            overflow-y: auto;
            border-top: 1px solid #eee;
            border-bottom: 1px solid #eee;
            display: flex;
            flex-direction: column;
        }
        .message-container {
            display: flex;
            margin-bottom: 10px;
            max-width: 80%;
        }
        .message-container.user {
            align-self: flex-end;
            justify-content: flex-end;
        }
        .message-container.bot {
            align-self: flex-start;
            justify-content: flex-start;
        }
        .message {
            padding: 10px 15px;
            border-radius: 18px;
            word-wrap: break-word;
            line-height: 1.4;
        }
        .message-container.user .message {
            background-color: #dcf8c6;
            color: #333;
            border-bottom-right-radius: 4px;
        }
        .message-container.bot .message {
            background-color: #eee;
            color: #333;
            border-bottom-left-radius: 4px;
        }
        #input-area {
            display: flex;
            padding: 10px;
            background-color: #f0f0f0;
        }
        #msg {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 20px;
            margin-right: 10px;
            outline: none;
        }
        #send-button {
            padding: 10px 20px;
            background-color: #5a9;
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        #send-button:hover {
            background-color: #488;
        }
        /* Estilização da barra de rolagem */
        #chatbox::-webkit-scrollbar {
            width: 8px;
        }
        #chatbox::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        #chatbox::-webkit-scrollbar-thumb {
            background: #ccc;
            border-radius: 10px;
        }
        #chatbox::-webkit-scrollbar-thumb:hover {
            background: #aaa;
        }
    </style>
</head>
<body>
    <div id="chat-container">
        <h1>Chat Terapêutico</h1>
        <div id="chatbox"></div>
        <div id="input-area">
            <input type="text" id="msg" placeholder="Digite sua mensagem..." autocomplete="off">
            <button id="send-button" onclick="sendMessage()">Enviar</button>
        </div>
    </div>

    <script>
        const chatbox = document.getElementById('chatbox');
        const msgInput = document.getElementById('msg');

        function sendMessage() {
            const message = msgInput.value.trim();
            if (!message) return;

            displayMessage(message, 'user');
            msgInput.value = '';
            msgInput.focus();

            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ mensagem: message })
            })
            .then(response => {
                if (!response.ok) {
                    // Tenta ler a mensagem de erro do JSON, se houver
                    return response.json().then(errData => {
                        throw new Error(errData.resposta || `HTTP error! status: ${response.status}`);
                    }).catch(() => {
                         throw new Error(`HTTP error! status: ${response.status}`); // Caso não seja JSON
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.resposta) {
                    displayMessage(data.resposta, 'bot');
                } else {
                    displayMessage('Desculpe, não recebi uma resposta válida.', 'bot');
                }
            })
            .catch(error => {
                console.error('Erro ao enviar/receber mensagem:', error);
                displayMessage(`Desculpe, ocorreu um erro: ${error.message}. Tente novamente.`, 'bot');
            });
        }

        function displayMessage(text, sender) {
            const messageContainer = document.createElement('div');
            messageContainer.classList.add('message-container', sender);

            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.textContent = text;

            messageContainer.appendChild(messageDiv);
            chatbox.appendChild(messageContainer);

            chatbox.scrollTop = chatbox.scrollHeight;
        }

        msgInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Opcional: Mensagem inicial do bot ao carregar
        // window.onload = () => {
        //     displayMessage("Olá! Como posso te ajudar hoje?", 'bot');
        // };

    </script>
</body>
</html>
"""
        with open(index_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(
            "Arquivo 'templates/index.html' criado com sucesso.")  # Corrigido

    # Executa o servidor Flask
    print("Iniciando o servidor Flask...")
    print("Acesse o chat em http://localhost:5000 (ou o IP da máquina)")
    # Use debug=True apenas para desenvolvimento, False para produção
    app.run(host="0.0.0.0", port=5000, debug=False)
