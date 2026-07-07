/**
 * Translation Abstraction Layer
 * Handles translation between English and Kannada.
 */

const translationCache = new Map<string, string>();

/**
 * Detects if the given text contains Kannada characters.
 * Kannada Unicode range: \u0C80-\u0CFF
 */
export const detectKannada = (text: string): boolean => {
  return /[\u0C80-\u0CFF]/.test(text);
};

export const translateText = async (text: string, sourceLang: 'en' | 'kn' | 'auto', targetLang: 'en' | 'kn'): Promise<string> => {
  if (!text || text.trim() === '') return text;
  
  const actualSource = sourceLang === 'auto' 
    ? (detectKannada(text) ? 'kn' : 'en')
    : sourceLang;
    
  if (actualSource === targetLang) return text;

  // Intercept natural AI responses
  if (targetLang === 'kn') {
    if (text.match(/Retrieved \d+ record\(s\) matching request/i)) {
      const match = text.match(/\d+/);
      return `ಈ ಹುಡುಕಾಟಕ್ಕೆ ಹೊಂದುವ ${match ? match[0] : ''} ದಾಖಲೆಗಳು ಲಭ್ಯವಿವೆ.`;
    }
    if (text === 'Actionable intelligence retrieved successfully.') {
      return 'ಯಶಸ್ವಿಯಾಗಿ ಕಾರ್ಯಾಚರಣೆಯ ಗುಪ್ತಚರ ಮಾಹಿತಿಯನ್ನು ಪಡೆಯಲಾಗಿದೆ.';
    }
    if (text.match(/Total aggregate count: \d+/i)) {
      const match = text.match(/\d+/);
      return `ಒಟ್ಟು ಒಟ್ಟುಗೂಡಿದ ಸಂಖ್ಯೆ: ${match ? match[0] : ''}`;
    }
    if (text.match(/Prediction for .*?: \d+ cases expected\. Risk: .*?\. Confidence: \d+%\./i)) {
      const parts = text.match(/Prediction for (.*?): (\d+) cases expected\. Risk: (.*?)\. Confidence: (\d+)%\./i);
      if (parts) {
         const [, month, cases, risk, conf] = parts;
         let knRisk = risk === 'HIGH' ? 'ಹೆಚ್ಚು' : risk === 'MEDIUM' ? 'ಮಧ್ಯಮ' : risk === 'LOW' ? 'ಕಡಿಮೆ' : risk;
         return `${month} ತಿಂಗಳಿನ ಮುನ್ಸೂಚನೆ: ಸುಮಾರು ${cases} ಪ್ರಕರಣಗಳು ದಾಖಲಾಗುವ ಸಾಧ್ಯತೆ ಇದೆ. ಅಪಾಯ ಮಟ್ಟ: ${knRisk}. ವಿಶ್ವಾಸ ಮಟ್ಟ: ${conf}%.`;
      }
    }
  }
  
  const cacheKey = `${actualSource}-${targetLang}:${text}`;
  if (translationCache.has(cacheKey)) {
    return translationCache.get(cacheKey)!;
  }

  // Masking mechanism for Entities (e.g. KSP-1001, FIR-402, 17.8%)
  const entityRegex = /\b(?:[A-Z]+-\d+|\d+(?:\.\d+)?%?)\b/g;
  const entities: string[] = [];
  let maskedText = text.replace(entityRegex, (match) => {
    const placeholder = `__E${entities.length}__`;
    entities.push(match);
    return placeholder;
  });

  try {
    const langpair = `${actualSource}|${targetLang}`;
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(maskedText)}&langpair=${langpair}`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    if (data && data.responseData && data.responseData.translatedText) {
      let translated = data.responseData.translatedText;
      
      if (translated.includes('MYMEMORY WARNING')) {
         throw new Error('Translation limit exceeded.');
      }
      
      // Unmask entities
      entities.forEach((ent, idx) => {
        translated = translated.replace(new RegExp(`__E${idx}__`, 'g'), ent);
      });

      translationCache.set(cacheKey, translated);
      return translated;
    }
  } catch (error) {
    console.error("Translation error:", error);
    throw new Error('Unable to translate the query. Please try again.');
  }
  
  throw new Error('Unable to translate the query. Please try again.');
};

export const translateToKannada = (text: string): Promise<string> => {
  return translateText(text, 'en', 'kn');
};

export const translateToEnglish = (text: string): Promise<string> => {
  return translateText(text, 'kn', 'en');
};
