from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
import time
from app.models.mcc import MCCCode, MCCTranslation
from app.schemas.category import DefaultCategoryOut
from app.utils.logger import get_logger

# Supported languages
SUPPORTED_LANGUAGES = {"ru", "uk", "en"}
DEFAULT_LANGUAGE = "en"

class DefaultCategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)

    def get_default_categories(self, language: Optional[str] = None) -> List[DefaultCategoryOut]:
        """Get all default MCC categories with optional translations
        
        Args:
            language: Language code ('ru', 'uk', 'en'). If None or 'en', returns English names.
                     If unsupported language provided, defaults to English.
        """
        start_time = time.time()
        
        try:
            # Validate and normalize language
            if language and language not in SUPPORTED_LANGUAGES:
                self.logger.warning(
                    f"Unsupported language '{language}' requested, falling back to English",
                    category="business",
                    operation="unsupported_language_fallback",
                    requested_language=language,
                    supported_languages=list(SUPPORTED_LANGUAGES)
                )
                language = DEFAULT_LANGUAGE
            
            # If no language specified or 'en', use English names (no translation needed)
            if not language or language == DEFAULT_LANGUAGE:
                language = None
            
            self.logger.info(
                f"Retrieving default categories",
                category="business",
                operation="default_categories_list_start",
                language=language
            )
            
            # Query default MCC codes
            query = self.db.query(MCCCode).filter(MCCCode.is_default == True)
            
            if language:
                # Join with translations for the specified language
                query = query.outerjoin(
                    MCCTranslation, 
                    and_(
                        MCCCode.mcc_code == MCCTranslation.mcc_code,
                        MCCTranslation.lang == language
                    )
                )
            
            mcc_codes = query.all()
            
            # Build response objects
            result = []
            self.logger.info(f"Processing {len(mcc_codes)} MCC codes with language: {language}")
            for mcc_code in mcc_codes:
                # Find translation if language is specified
                translation = None
                if language:
                    if language == "en":
                        # For English, use the original name as translation
                        translation = mcc_code.name
                    else:
                        # For other languages, try to find translation
                        translation_obj = next(
                            (t for t in mcc_code.translations if t.lang == language), 
                            None
                        )
                        self.logger.info(
                            f"Translation object: {translation_obj}",
                            category="business",
                            operation="translation_object",
                            language=language,
                            mcc_code=mcc_code.mcc_code,
                        )
                        if translation_obj:
                            translation = translation_obj.text
                
                result.append(DefaultCategoryOut(
                    mcc_code=mcc_code.mcc_code,
                    name=mcc_code.name,
                    translation=translation,
                    is_default=mcc_code.is_default
                ))
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info(
                f"Default categories retrieved successfully",
                category="business",
                operation="default_categories_list_success",
                language=language,
                count=len(result),
                duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.error(
                f"Error getting default categories: {str(e)}",
                category="business",
                operation="default_categories_list_failed",
                language=language,
                duration_ms=duration_ms
            )
            raise Exception("Failed to retrieve default categories")

    def get_all_mcc_codes(self, language: Optional[str] = None) -> List[DefaultCategoryOut]:
        """Get all MCC codes with optional translations
        
        Args:
            language: Language code ('ru', 'uk', 'en'). If None or 'en', returns English names.
                     If unsupported language provided, defaults to English.
        """
        start_time = time.time()
        
        try:
            # Validate and normalize language
            if language and language not in SUPPORTED_LANGUAGES:
                self.logger.warning(
                    f"Unsupported language '{language}' requested, falling back to English",
                    category="business",
                    operation="unsupported_language_fallback",
                    requested_language=language,
                    supported_languages=list(SUPPORTED_LANGUAGES)
                )
                language = DEFAULT_LANGUAGE
            
            self.logger.info(
                f"Retrieving all MCC codes",
                category="business",
                operation="all_mcc_codes_list_start",
                language=language
            )
            
            # Query all MCC codes
            query = self.db.query(MCCCode)
            
            if language:
                # Join with translations for the specified language
                query = query.outerjoin(
                    MCCTranslation, 
                    and_(
                        MCCCode.mcc_code == MCCTranslation.mcc_code,
                        MCCTranslation.lang == language
                    )
                )
            
            mcc_codes = query.all()
            
            # Build response objects
            result = []
            self.logger.info(f"Processing {len(mcc_codes)} MCC codes with language: {language}")
            for mcc_code in mcc_codes:
                # Find translation if language is specified
                translation = None
                if language:
                    if language == "en":
                        # For English, use the original name as translation
                        translation = mcc_code.name
                    else:
                        # For other languages, try to find translation
                        translation_obj = next(
                            (t for t in mcc_code.translations if t.lang == language), 
                            None
                        )
                        if translation_obj:
                            translation = translation_obj.text
                
                result.append(DefaultCategoryOut(
                    mcc_code=mcc_code.mcc_code,
                    name=mcc_code.name,
                    translation=translation,
                    is_default=mcc_code.is_default
                ))
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info(
                f"All MCC codes retrieved successfully",
                category="business",
                operation="all_mcc_codes_list_success",
                language=language,
                count=len(result),
                duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.error(
                f"Error getting all MCC codes: {str(e)}",
                category="business",
                operation="all_mcc_codes_list_failed",
                language=language,
                duration_ms=duration_ms
            )
            raise Exception("Failed to retrieve all MCC codes")
