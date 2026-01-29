"""
Internationalization (i18n) System.
Multi-language support for global expansion.
"""
from typing import Dict, Optional
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    PORTUGUESE = "pt"
    JAPANESE = "ja"
    KOREAN = "ko"
    CHINESE_SIMPLIFIED = "zh-CN"
    HINDI = "hi"


# Translation dictionaries
TRANSLATIONS = {
    "en": {
        # Common
        "welcome": "Welcome to Video Creator!",
        "create_video": "Create Video",
        "my_videos": "My Videos",
        "settings": "Settings",
        "logout": "Logout",
        
        # Dashboard
        "dashboard": "Dashboard",
        "total_videos": "Total Videos",
        "total_views": "Total Views",
        "engagement_rate": "Engagement Rate",
        "growth": "Growth",
        
        # Video creation
        "video_title": "Video Title",
        "video_description": "Description",
        "select_template": "Select Template",
        "upload_media": "Upload Media",
        "publish": "Publish",
        "save_draft": "Save Draft",
        
        # Messages
        "video_created": "Video created successfully!",
        "video_published": "Video published to {platform}!",
        "error_occurred": "An error occurred. Please try again.",
        "videos_created_count": "You've created {count} videos",
        
        # Subscription
        "upgrade_to_pro": "Upgrade to Pro",
        "subscribe": "Subscribe",
        "cancel_subscription": "Cancel Subscription",
        "billing": "Billing"
    },
    
    "es": {
        # Spanish
        "welcome": "¡Bienvenido a Video Creator!",
        "create_video": "Crear Video",
        "my_videos": "Mis Videos",
        "settings": "Configuración",
        "logout": "Cerrar Sesión",
        
        "dashboard": "Panel de Control",
        "total_videos": "Videos Totales",
        "total_views": "Vistas Totales",
        "engagement_rate": "Tasa de Interacción",
        "growth": "Crecimiento",
        
        "video_title": "Título del Video",
        "video_description": "Descripción",
        "select_template": "Seleccionar Plantilla",
        "upload_media": "Subir Medios",
        "publish": "Publicar",
        "save_draft": "Guardar Borrador",
        
        "video_created": "¡Video creado exitosamente!",
        "video_published": "¡Video publicado en {platform}!",
        "error_occurred": "Ocurrió un error. Por favor, intenta de nuevo.",
        "videos_created_count": "Has creado {count} videos",
        
        "upgrade_to_pro": "Actualizar a Pro",
        "subscribe": "Suscribirse",
        "cancel_subscription": "Cancelar Suscripción",
        "billing": "Facturación"
    },
    
    "fr": {
        # French
        "welcome": "Bienvenue sur Video Creator !",
        "create_video": "Créer une Vidéo",
        "my_videos": "Mes Vidéos",
        "settings": "Paramètres",
        "logout": "Déconnexion",
        
        "dashboard": "Tableau de Bord",
        "total_videos": "Vidéos Totales",
        "total_views": "Vues Totales",
        "engagement_rate": "Taux d'Engagement",
        "growth": "Croissance",
        
        "video_title": "Titre de la Vidéo",
        "video_description": "Description",
        "select_template": "Sélectionner un Modèle",
        "upload_media": "Télécharger des Médias",
        "publish": "Publier",
        "save_draft": "Enregistrer le Brouillon",
        
        "video_created": "Vidéo créée avec succès !",
        "video_published": "Vidéo publiée sur {platform} !",
        "error_occurred": "Une erreur s'est produite. Veuillez réessayer.",
        "videos_created_count": "Vous avez créé {count} vidéos",
        
        "upgrade_to_pro": "Passer à Pro",
        "subscribe": "S'abonner",
        "cancel_subscription": "Annuler l'Abonnement",
        "billing": "Facturation"
    },
    
    "de": {
        # German
        "welcome": "Willkommen bei Video Creator!",
        "create_video": "Video Erstellen",
        "my_videos": "Meine Videos",
        "settings": "Einstellungen",
        "logout": "Abmelden",
        
        "dashboard": "Dashboard",
        "total_videos": "Gesamte Videos",
        "total_views": "Gesamte Aufrufe",
        "engagement_rate": "Engagement-Rate",
        "growth": "Wachstum",
        
        "video_title": "Video-Titel",
        "video_description": "Beschreibung",
        "select_template": "Vorlage Auswählen",
        "upload_media": "Medien Hochladen",
        "publish": "Veröffentlichen",
        "save_draft": "Entwurf Speichern",
        
        "video_created": "Video erfolgreich erstellt!",
        "video_published": "Video auf {platform} veröffentlicht!",
        "error_occurred": "Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.",
        "videos_created_count": "Sie haben {count} Videos erstellt",
        
        "upgrade_to_pro": "Auf Pro upgraden",
        "subscribe": "Abonnieren",
        "cancel_subscription": "Abonnement Kündigen",
        "billing": "Abrechnung"
    },
    
    "pt": {
        # Portuguese
        "welcome": "Bem-vindo ao Video Creator!",
        "create_video": "Criar Vídeo",
        "my_videos": "Meus Vídeos",
        "settings": "Configurações",
        "logout": "Sair",
        
        "dashboard": "Painel",
        "total_videos": "Total de Vídeos",
        "total_views": "Total de Visualizações",
        "engagement_rate": "Taxa de Engajamento",
        "growth": "Crescimento",
        
        "video_title": "Título do Vídeo",
        "video_description": "Descrição",
        "select_template": "Selecionar Modelo",
        "upload_media": "Carregar Mídia",
        "publish": "Publicar",
        "save_draft": "Salvar Rascunho",
        
        "video_created": "Vídeo criado com sucesso!",
        "video_published": "Vídeo publicado em {platform}!",
        "error_occurred": "Ocorreu um erro. Por favor, tente novamente.",
        "videos_created_count": "Você criou {count} vídeos",
        
        "upgrade_to_pro": "Atualizar para Pro",
        "subscribe": "Inscrever-se",
        "cancel_subscription": "Cancelar Assinatura",
        "billing": "Faturamento"
    },
    
    "ja": {
        # Japanese
        "welcome": "Video Creatorへようこそ！",
        "create_video": "動画を作成",
        "my_videos": "マイ動画",
        "settings": "設定",
        "logout": "ログアウト",
        
        "dashboard": "ダッシュボード",
        "total_videos": "総動画数",
        "total_views": "総視聴回数",
        "engagement_rate": "エンゲージメント率",
        "growth": "成長",
        
        "video_title": "動画タイトル",
        "video_description": "説明",
        "select_template": "テンプレートを選択",
        "upload_media": "メディアをアップロード",
        "publish": "公開",
        "save_draft": "下書きを保存",
        
        "video_created": "動画が正常に作成されました！",
        "video_published": "{platform}に動画を公開しました！",
        "error_occurred": "エラーが発生しました。もう一度お試しください。",
        "videos_created_count": "{count}本の動画を作成しました",
        
        "upgrade_to_pro": "Proにアップグレード",
        "subscribe": "購読",
        "cancel_subscription": "サブスクリプションをキャンセル",
        "billing": "請求"
    },
    
    "ko": {
        # Korean
        "welcome": "Video Creator에 오신 것을 환영합니다!",
        "create_video": "비디오 만들기",
        "my_videos": "내 비디오",
        "settings": "설정",
        "logout": "로그아웃",
        
        "dashboard": "대시보드",
        "total_videos": "총 비디오",
        "total_views": "총 조회수",
        "engagement_rate": "참여율",
        "growth": "성장",
        
        "video_title": "비디오 제목",
        "video_description": "설명",
        "select_template": "템플릿 선택",
        "upload_media": "미디어 업로드",
        "publish": "게시",
        "save_draft": "초안 저장",
        
        "video_created": "비디오가 성공적으로 생성되었습니다!",
        "video_published": "{platform}에 비디오가 게시되었습니다!",
        "error_occurred": "오류가 발생했습니다. 다시 시도해 주세요.",
        "videos_created_count": "{count}개의 비디오를 만들었습니다",
        
        "upgrade_to_pro": "Pro로 업그레이드",
        "subscribe": "구독",
        "cancel_subscription": "구독 취소",
        "billing": "청구"
    },
    
    "zh-CN": {
        # Chinese (Simplified)
        "welcome": "欢迎来到 Video Creator！",
        "create_video": "创建视频",
        "my_videos": "我的视频",
        "settings": "设置",
        "logout": "登出",
        
        "dashboard": "仪表板",
        "total_videos": "总视频数",
        "total_views": "总观看次数",
        "engagement_rate": "互动率",
        "growth": "增长",
        
        "video_title": "视频标题",
        "video_description": "描述",
        "select_template": "选择模板",
        "upload_media": "上传媒体",
        "publish": "发布",
        "save_draft": "保存草稿",
        
        "video_created": "视频创建成功！",
        "video_published": "视频已发布到 {platform}！",
        "error_occurred": "发生错误，请重试。",
        "videos_created_count": "您已创建 {count} 个视频",
        
        "upgrade_to_pro": "升级到 Pro",
        "subscribe": "订阅",
        "cancel_subscription": "取消订阅",
        "billing": "账单"
    },
    
    "hi": {
        # Hindi
        "welcome": "Video Creator में आपका स्वागत है!",
        "create_video": "वीडियो बनाएं",
        "my_videos": "मेरे वीडियो",
        "settings": "सेटिंग्स",
        "logout": "लॉग आउट",
        
        "dashboard": "डैशबोर्ड",
        "total_videos": "कुल वीडियो",
        "total_views": "कुल दृश्य",
        "engagement_rate": "एंगेजमेंट दर",
        "growth": "वृद्धि",
        
        "video_title": "वीडियो शीर्षक",
        "video_description": "विवरण",
        "select_template": "टेम्पलेट चुनें",
        "upload_media": "मीडिया अपलोड करें",
        "publish": "प्रकाशित करें",
        "save_draft": "ड्राफ्ट सहेजें",
        
        "video_created": "वीडियो सफलतापूर्वक बनाया गया!",
        "video_published": "{platform} पर वीडियो प्रकाशित हुआ!",
        "error_occurred": "एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
        "videos_created_count": "आपने {count} वीडियो बनाए हैं",
        
        "upgrade_to_pro": "Pro में अपग्रेड करें",
        "subscribe": "सदस्यता लें",
        "cancel_subscription": "सदस्यता रद्द करें",
        "billing": "बिलिंग"
    }
}


class I18nService:
    """Handle internationalization and localization."""
    
    def __init__(self):
        self.translations = TRANSLATIONS
        self.default_language = Language.ENGLISH.value
    
    def translate(
        self,
        key: str,
        language: str = "en",
        params: Optional[Dict] = None
    ) -> str:
        """
        Get translation for key.
        
        Args:
            key: Translation key
            language: Target language code
            params: Optional parameters for interpolation
            
        Returns:
            Translated string
        """
        # Get language dictionary (fallback to English)
        lang_dict = self.translations.get(language, self.translations[self.default_language])
        
        # Get translation (fallback to key if not found)
        translation = lang_dict.get(key, key)
        
        # Interpolate parameters
        if params:
            try:
                translation = translation.format(**params)
            except KeyError as e:
                logger.warning(f"Missing parameter in translation: {e}")
        
        return translation
    
    def t(self, key: str, language: str = "en", **params) -> str:
        """Shorthand for translate."""
        return self.translate(key, language, params if params else None)
    
    def get_supported_languages(self) -> List[Dict]:
        """Get list of supported languages."""
        return [
            {
                "code": lang.value,
                "name": self._get_language_name(lang.value),
                "native_name": self._get_native_name(lang.value)
            }
            for lang in Language
        ]
    
    def _get_language_name(self, code: str) -> str:
        """Get English name of language."""
        names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "pt": "Portuguese",
            "ja": "Japanese",
            "ko": "Korean",
            "zh-CN": "Chinese (Simplified)",
            "hi": "Hindi"
        }
        return names.get(code, code)
    
    def _get_native_name(self, code: str) -> str:
        """Get native name of language."""
        names = {
            "en": "English",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "pt": "Português",
            "ja": "日本語",
            "ko": "한국어",
            "zh-CN": "简体中文",
            "hi": "हिन्दी"
        }
        return names.get(code, code)
    
    def detect_language(self, accept_language_header: str) -> str:
        """
        Detect preferred language from Accept-Language header.
        
        Args:
            accept_language_header: HTTP Accept-Language header
            
        Returns:
            Detected language code
        """
        # Parse Accept-Language header
        # Format: "en-US,en;q=0.9,es;q=0.8"
        
        if not accept_language_header:
            return self.default_language
        
        # Extract language codes
        languages = []
        for lang_part in accept_language_header.split(','):
            parts = lang_part.strip().split(';')
            lang_code = parts[0].split('-')[0]  # Get base language
            
            # Get quality value (default 1.0)
            quality = 1.0
            if len(parts) > 1 and parts[1].startswith('q='):
                try:
                    quality = float(parts[1][2:])
                except ValueError:
                    quality = 1.0
            
            languages.append((lang_code, quality))
        
        # Sort by quality
        languages.sort(key=lambda x: x[1], reverse=True)
        
        # Find first supported language
        for lang_code, _ in languages:
            if lang_code in [l.value for l in Language]:
                return lang_code
        
        return self.default_language


# Usage examples
"""
from app.services.i18n_service import I18nService

i18n = I18nService()

# Simple translation
welcome_en = i18n.translate("welcome", "en")
# "Welcome to Video Creator!"

welcome_es = i18n.translate("welcome", "es")
# "¡Bienvenido a Video Creator!"

# With parameters
msg = i18n.translate("videos_created_count", "fr", {"count": 10})
# "Vous avez créé 10 vidéos"

# Shorthand
msg = i18n.t("video_published", "de", platform="YouTube")
# "Video auf YouTube veröffentlicht!"

# Detect from header
lang = i18n.detect_language("fr-FR,fr;q=0.9,en;q=0.8")
# "fr"
"""


# FastAPI integration
"""
from fastapi import Request, Depends
from app.services.i18n_service import I18nService

def get_user_language(request: Request) -> str:
    '''Get user's preferred language.'''
    i18n = I18nService()
    
    # Check user preference (from database)
    # user_lang = db.get_user_preference(user_id, "language")
    
    # Fallback to Accept-Language header
    accept_lang = request.headers.get("Accept-Language", "")
    return i18n.detect_language(accept_lang)

@router.get("/")
async def index(lang: str = Depends(get_user_language)):
    i18n = I18nService()
    
    return {
        "message": i18n.t("welcome", lang),
        "cta": i18n.t("create_video", lang)
    }
"""
