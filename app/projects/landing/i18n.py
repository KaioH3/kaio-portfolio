"""
Internationalization for Landing Page
PT-BR only (Brazilian audience)
"""

# Todas as strings em português brasileiro
TRANSLATIONS = {
    # === HERO SECTION ===
    "hero_headline": "Transforme Sua Paixão por Unhas em um Negócio Lucrativo",
    "hero_subheadline": "Aprenda técnicas profissionais de unha gel e fature até R$ 3.000/mês trabalhando em casa",
    "hero_cta": "Quero Começar Agora →",

    # === PROBLEMA ===
    "problem_title": "Você Está Cansada de...",
    "problem_1": "Trabalhar muito e ganhar pouco?",
    "problem_2": "Depender de um chefe para ter renda?",
    "problem_3": "Não ter tempo para sua família?",
    "problem_4": "Ver suas contas acumulando sem solução?",

    # === SOLUÇÃO ===
    "solution_title": "A Solução Está Aqui",
    "solution_subtitle": "Curso completo de Unha Gel com certificado reconhecido",
    "module_1_title": "Módulo 1: Fundamentos",
    "module_1_desc": "Anatomia das unhas, tipos de produtos, higienização e segurança",
    "module_2_title": "Módulo 2: Técnicas Básicas",
    "module_2_desc": "Preparação, aplicação de gel, alongamento e modelagem",
    "module_3_title": "Módulo 3: Design Avançado",
    "module_3_desc": "Decorações, nail art, francesinha, ombré e muito mais",
    "module_4_title": "Módulo 4: Negócio Lucrativo",
    "module_4_desc": "Como precificar, atrair clientes, marketing digital e gestão",

    # === PROVA SOCIAL ===
    "social_proof_title": "Alunas que Já Transformaram Suas Vidas",
    "testimonial_1_name": "Maria Silva",
    "testimonial_1_text": "\"Em 3 meses já estava faturando R$ 2.500/mês! O curso mudou minha vida.\"",
    "testimonial_2_name": "Ana Costa",
    "testimonial_2_text": "\"Consegui largar meu emprego e agora trabalho de casa. Melhor decisão!\"",
    "testimonial_3_name": "Juliana Santos",
    "testimonial_3_text": "\"As técnicas são muito bem explicadas. Até quem nunca fez unha consegue!\"",

    # === TRANSFORMAÇÃO ===
    "transformation_title": "Imagine Você...",
    "transformation_1": "Trabalhando de casa, no seu horário",
    "transformation_2": "Faturando R$ 3.000+ por mês",
    "transformation_3": "Com mais tempo para sua família",
    "transformation_4": "Sendo sua própria chefe",
    "transformation_5": "Reconhecida como profissional de qualidade",

    # === COMO FUNCIONA ===
    "how_it_works_title": "Como Funciona",
    "step_1_title": "1. Inscreva-se Agora",
    "step_1_desc": "Clique no botão e garanta sua vaga com desconto especial",
    "step_2_title": "2. Acesso Imediato",
    "step_2_desc": "Receba login e senha por email em até 5 minutos",
    "step_3_title": "3. Comece Hoje Mesmo",
    "step_3_desc": "Assista as aulas, pratique e tire dúvidas no grupo VIP",

    # === BÔNUS ===
    "bonus_title": "Bônus Exclusivos",
    "bonus_1_title": "Kit de Materiais (PDF)",
    "bonus_1_value": "Valor: R$ 47",
    "bonus_1_desc": "Lista completa de fornecedores confiáveis com desconto",
    "bonus_2_title": "Grupo VIP WhatsApp",
    "bonus_2_value": "Valor: R$ 97",
    "bonus_2_desc": "Suporte direto com a professora e networking com outras alunas",
    "bonus_3_title": "Certificado Profissional",
    "bonus_3_value": "Valor: R$ 67",
    "bonus_3_desc": "Certificado reconhecido para comprovar sua qualificação",

    # === GARANTIA ===
    "guarantee_title": "Garantia Incondicional de 7 Dias",
    "guarantee_text": "Se você não gostar do curso por qualquer motivo, devolvemos 100% do seu dinheiro. Sem perguntas, sem burocracia.",
    "guarantee_badge": "Risco Zero",

    # === URGÊNCIA ===
    "urgency_title": "Atenção: Oferta Especial por Tempo Limitado",
    "urgency_timer_text": "Esta oferta expira em:",
    "urgency_spots_text": "Restam apenas 7 vagas com desconto!",

    # === PREÇO ===
    "price_title": "Investimento",
    "price_before": "De",
    "price_strikethrough": "R$ 297,00",
    "price_after": "Por apenas",
    "price_highlight": "R$ 197,00",
    "price_installments": "ou 12x de R$ 19,63",
    "price_cta": "Sim! Quero Garantir Minha Vaga Agora →",

    # === FAQ ===
    "faq_title": "Perguntas Frequentes",
    "faq_1_q": "Preciso ter experiência prévia?",
    "faq_1_a": "Não! O curso é para iniciantes. Começamos do zero.",
    "faq_2_q": "Quanto tempo dura o curso?",
    "faq_2_a": "São 40 horas de conteúdo. Você estuda no seu ritmo, com acesso vitalício.",
    "faq_3_q": "Preciso comprar materiais caros?",
    "faq_3_a": "Não! No bônus temos lista de fornecedores com kits a partir de R$ 150.",
    "faq_4_q": "O certificado é reconhecido?",
    "faq_4_a": "Sim! Certificado profissional válido em todo Brasil.",
    "faq_5_q": "E se eu não gostar?",
    "faq_5_a": "Garantia de 7 dias. Devolvemos 100% do valor, sem perguntas.",
    "faq_6_q": "Quando recebo o acesso?",
    "faq_6_a": "Imediatamente! Em até 5 minutos após o pagamento aprovado.",
    "faq_7_q": "Posso parcelar?",
    "faq_7_a": "Sim! Até 12x no cartão de crédito.",
    "faq_8_q": "Tem suporte?",
    "faq_8_a": "Sim! Grupo VIP no WhatsApp com a professora e outras alunas.",

    # === FOOTER ===
    "footer_disclaimer": "Este produto não garante a obtenção de resultados. Qualquer referência ao desempenho de uma estratégia não deve ser interpretada como garantia de resultados.",
    "footer_privacy": "Política de Privacidade",
    "footer_terms": "Termos de Uso",
    "footer_contact": "Contato",
}

def t(key: str) -> str:
    """Get translation by key"""
    return TRANSLATIONS.get(key, key)
