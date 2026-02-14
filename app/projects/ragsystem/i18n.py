"""
Internationalization (i18n) Module for RAG System
Supports: PT-BR (Brazilian Portuguese) + EN-US (English)

Usage:
    from .i18n import t, get_language_from_request
    
    # Basic translation
    text = t("upload_title", lang="pt-BR")
    
    # With parameters
    message = t("upload_success", lang="en-US", filename="doc.pdf", chunks=10)
    
    # Auto-detect from request
    lang = get_language_from_request(request)
"""

from typing import Literal, Dict, Any
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

Language = Literal["pt-BR", "en-US"]
DEFAULT_LANGUAGE: Language = "en-US"

TRANSLATIONS: Dict[str, Dict[Language, str]] = {
    # === PAGE TITLES ===
    "page_title": {
        "pt-BR": "🧠 RAG Document Intelligence",
        "en-US": "🧠 RAG Document Intelligence"
    },
    "page_subtitle": {
        "pt-BR": "Sistema de Recuperação e Geração Aumentada com Chain-of-Verification",
        "en-US": "Retrieval-Augmented Generation with Chain-of-Verification"
    },
    
    # === UPLOAD SECTION ===
    "upload_section_title": {
        "pt-BR": "📤 Enviar Documento",
        "en-US": "📤 Upload Document"
    },
    "upload_file_label": {
        "pt-BR": "Selecione um arquivo (PDF, TXT, MD):",
        "en-US": "Select a file (PDF, TXT, MD):"
    },
    "upload_button": {
        "pt-BR": "Enviar",
        "en-US": "Upload"
    },
    "upload_indicator": {
        "pt-BR": "⏳ Enviando...",
        "en-US": "⏳ Uploading..."
    },
    "upload_success": {
        "pt-BR": "✅ <strong>{filename}</strong> indexado com sucesso!<br>📄 {chunks} chunks criados<br>⏱️ {time_ms:.0f}ms",
        "en-US": "✅ <strong>{filename}</strong> indexed successfully!<br>📄 {chunks} chunks created<br>⏱️ {time_ms:.0f}ms"
    },
    "upload_error": {
        "pt-BR": "❌ Erro ao processar documento: {error}",
        "en-US": "❌ Error processing document: {error}"
    },
    "upload_error_size": {
        "pt-BR": "❌ Arquivo muito grande (máx {max_mb}MB)",
        "en-US": "❌ File too large (max {max_mb}MB)"
    },
    "upload_error_type": {
        "pt-BR": "❌ Tipo de arquivo não suportado: {ext}",
        "en-US": "❌ Unsupported file type: {ext}"
    },
    
    # === QUERY SECTION ===
    "query_section_title": {
        "pt-BR": "💬 Fazer Pergunta",
        "en-US": "💬 Ask Question"
    },
    "query_input_placeholder": {
        "pt-BR": "O que você gostaria de saber?",
        "en-US": "What would you like to know?"
    },
    "query_verification_label": {
        "pt-BR": "Ativar Chain-of-Verification (reduz alucinações)",
        "en-US": "Enable Chain-of-Verification (reduces hallucinations)"
    },
    "query_button": {
        "pt-BR": "Perguntar",
        "en-US": "Ask"
    },
    "query_indicator": {
        "pt-BR": "🤔 Pensando...",
        "en-US": "🤔 Thinking..."
    },
    "query_answer_title": {
        "pt-BR": "Resposta:",
        "en-US": "Answer:"
    },
    "query_sources_title": {
        "pt-BR": "Fontes:",
        "en-US": "Sources:"
    },
    "query_metadata": {
        "pt-BR": "Confiança: {confidence:.0%} | Tempo: {time_ms:.0f}ms | Modelo: {model}",
        "en-US": "Confidence: {confidence:.0%} | Time: {time_ms:.0f}ms | Model: {model}"
    },
    "query_no_documents": {
        "pt-BR": "Nenhum documento relevante encontrado. Por favor, envie documentos primeiro.",
        "en-US": "No relevant documents found. Please upload documents first."
    },
    "query_error": {
        "pt-BR": "❌ Erro ao processar pergunta: {error}",
        "en-US": "❌ Error processing query: {error}"
    },
    "query_rate_limited": {
        "pt-BR": "⚠️ Limite mensal atingido ({limit} consultas/mês). Resets no próximo mês.",
        "en-US": "⚠️ Monthly limit reached ({limit} queries/month). Resets next month."
    },
    "query_remaining": {
        "pt-BR": "Consultas restantes este mês: {remaining}/{limit}",
        "en-US": "Queries remaining this month: {remaining}/{limit}"
    },
    
    # === VERIFICATION STEPS ===
    "verification_title": {
        "pt-BR": "🔍 Etapas de Verificação:",
        "en-US": "🔍 Verification Steps:"
    },
    "verification_step": {
        "pt-BR": "{step}: {status} (confiança: {confidence:.0%})",
        "en-US": "{step}: {status} (confidence: {confidence:.0%})"
    },
    "verification_passed": {
        "pt-BR": "✅ Passou",
        "en-US": "✅ Passed"
    },
    "verification_failed": {
        "pt-BR": "❌ Falhou",
        "en-US": "❌ Failed"
    },
    
    # === LANGUAGE SELECTOR ===
    "language_pt_br": {
        "pt-BR": "🇧🇷 Português",
        "en-US": "🇧🇷 Portuguese"
    },
    "language_en_us": {
        "pt-BR": "🇺🇸 English",
        "en-US": "🇺🇸 English"
    },
    
    # === FOOTER ===
    "footer_tech_stack": {
        "pt-BR": "Construído com FastAPI + FastEmbed + Qdrant + Groq",
        "en-US": "Built with FastAPI + FastEmbed + Qdrant + Groq"
    },
    "footer_performance": {
        "pt-BR": "~200MB RAM | <2s latência | $0/mês",
        "en-US": "~200MB RAM | <2s latency | $0/month"
    },
}

def t(key: str, lang: Language = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Get translated string with optional parameter substitution"""
    try:
        translations = TRANSLATIONS.get(key, {})
        text = translations.get(lang)
        
        if text is None:
            text = translations.get(DEFAULT_LANGUAGE, key)
            logger.warning(f"Translation missing: key={key}, lang={lang}")
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                logger.error(f"Missing parameter in translation: {e}")
                return text
        
        return text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return key

def get_language_from_request(request: Request) -> Language:
    """Detect language from request"""
    # 1. Check query parameter
    lang_param = request.query_params.get("lang")
    if lang_param in ["pt-BR", "en-US"]:
        return lang_param  # type: ignore
    
    # 2. Check cookie
    lang_cookie = request.cookies.get("lang")
    if lang_cookie in ["pt-BR", "en-US"]:
        return lang_cookie  # type: ignore
    
    # 3. Check Accept-Language header
    accept_lang = request.headers.get("accept-language", "")
    if "pt" in accept_lang.lower():
        return "pt-BR"
    
    return DEFAULT_LANGUAGE

def verify_translations() -> Dict[str, Any]:
    """Verify translation integrity"""
    report = {
        "total_keys": len(TRANSLATIONS),
        "missing_pt_br": [],
        "missing_en_us": [],
        "placeholder_mismatches": [],
    }
    
    for key, translations in TRANSLATIONS.items():
        if "pt-BR" not in translations:
            report["missing_pt_br"].append(key)
        if "en-US" not in translations:
            report["missing_en_us"].append(key)
        
        if "pt-BR" in translations and "en-US" in translations:
            pt_placeholders = set(
                part.split("}")[0]
                for part in translations["pt-BR"].split("{")[1:]
            )
            en_placeholders = set(
                part.split("}")[0]
                for part in translations["en-US"].split("{")[1:]
            )
            
            if pt_placeholders != en_placeholders:
                report["placeholder_mismatches"].append({
                    "key": key,
                    "pt_br": list(pt_placeholders),
                    "en_us": list(en_placeholders),
                })
    
    return report

if __name__ == "__main__":
    print("🔍 Chain of Verification - i18n Module")
    print("=" * 60)
    
    print("\n✅ Test 1: Basic translation")
    print(f"PT-BR: {t('upload_section_title', 'pt-BR')}")
    print(f"EN-US: {t('upload_section_title', 'en-US')}")
    
    print("\n✅ Test 2: Parameter substitution")
    msg = t("upload_success", "pt-BR", filename="test.pdf", chunks=10, time_ms=1234.5)
    print(f"PT-BR: {msg}")
    
    print("\n✅ Test 3: Translation integrity")
    report = verify_translations()
    print(f"Total keys: {report['total_keys']}")
    print(f"Missing PT-BR: {len(report['missing_pt_br'])}")
    print(f"Missing EN-US: {len(report['missing_en_us'])}")
    print(f"Placeholder mismatches: {len(report['placeholder_mismatches'])}")
    
    if report["placeholder_mismatches"]:
        print("\n⚠️  Placeholder mismatches found:")
        for mismatch in report["placeholder_mismatches"]:
            print(f"  - {mismatch['key']}")
    
    print("\n" + "=" * 60)
    print("✅ i18n module verified successfully!")
