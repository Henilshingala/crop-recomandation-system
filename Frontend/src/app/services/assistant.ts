import aiData from "@/locales/Ai.json";

export interface ChatMessage {
  role: "user" | "model";
  text: string;
}

interface Translation {
  question: string;
  answer: string;
}

interface QnaEntry {
  translations: Record<string, Translation>;
}

const qnaData = aiData as Record<string, QnaEntry>;

interface IndexEntry {
  id: string;
  question: string;
  keywords: string[];
}

const STOP_WORDS = new Set([
  "the","is","are","was","were","a","an","in","on","at","to","for",
  "of","and","or","but","not","with","this","that","what","how",
  "why","when","where","which","who","can","does","do","did","has",
  "have","had","will","would","could","should","may","might","its",
  "my","your","their","our","i","me","we","you","it","be","been",
  "being","by","from","as","if","then","than","so","all","any",
  "there","here","about","into","use","used","using","get","give",
  "need","want","like","just","also","very","more","much","many",
]);

const questionIndex: IndexEntry[] = Object.entries(qnaData).map(([id, entry]) => {
  const question = entry.translations["en"]?.question ?? "";
  const keywords = question
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOP_WORDS.has(w));
  return { id, question, keywords };
});

function findBestMatch(userInput: string): QnaEntry | null {
  const inputWords = userInput
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOP_WORDS.has(w));

  if (inputWords.length === 0) return null;

  let bestScore = 0;
  let bestId: string | null = null;

  for (const entry of questionIndex) {
    let score = 0;
    for (const word of inputWords) {
      if (entry.keywords.includes(word)) {
        score += 2;
      } else if (entry.keywords.some((k) => k.includes(word) || word.includes(k))) {
        score += 1;
      }
    }
    const fullQ = entry.question.toLowerCase();
    for (const word of inputWords) {
      if (fullQ.includes(word)) score += 1;
    }
    if (score > bestScore) {
      bestScore = score;
      bestId = entry.id;
    }
  }

  if (bestScore < 2 || !bestId) return null;
  return qnaData[bestId];
}

const FALLBACK: Record<string, string> = {
  en: "Sorry, I could not find an answer to your question. Please try asking differently.",
  hi: "क्षमा करें, मुझे आपके प्रश्न का उत्तर नहीं मिला। कृपया अलग तरीके से पूछें।",
  gu: "માફ કરશો, મને તમારા પ્રશ્નનો જવાબ મળ્યો નહીં. કૃપા કરીને અલગ રીતે પૂછો.",
  mr: "माफ करा, मला तुमच्या प्रश्नाचे उत्तर सापडले नाही. कृपया वेगळ्या प्रकारे विचारा.",
  ta: "மன்னிக்கவும், உங்கள் கேள்விக்கு பதில் கிடைக்கவில்லை. வேறு விதமாக கேளுங்கள்.",
  te: "క్షమించండి, మీ ప్రశ్నకు సమాధానం దొరకలేదు. దయచేసి వేరే విధంగా అడగండి.",
  kn: "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರ ಸಿಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಬೇರೆ ರೀತಿಯಲ್ಲಿ ಕೇಳಿ.",
  bn: "দুঃখিত, আপনার প্রশ্নের উত্তর পাওয়া যায়নি। অনুগ্রহ করে অন্যভাবে জিজ্ঞাসা করুন।",
  pa: "ਮਾਫ਼ ਕਰਨਾ, ਤੁਹਾਡੇ ਸਵਾਲ ਦਾ ਜਵਾਬ ਨਹੀਂ ਮਿਲਿਆ। ਕਿਰਪਾ ਕਰਕੇ ਵੱਖਰੇ ਤਰੀਕੇ ਨਾਲ ਪੁੱਛੋ।",
  ml: "ക്ഷമിക്കണം, നിങ്ങളുടെ ചോദ്യത്തിന് ഉത്തരം കിട്ടിയില്ല. ദയവായി മറ്റൊരു രീതിയിൽ ചോദിക്കൂ.",
  or: "ଦୟାକରି ମାଫ କରନ୍ତୁ, ଆପଣଙ୍କ ପ୍ରଶ୍ନର ଉତ୍ତର ମିଳିଲାନି। ଅନ୍ୟ ଭାବରେ ପଚାରନ୍ତୁ।",
  ur: "معذرت، آپ کے سوال کا جواب نہیں ملا۔ براہ کرم مختلف طریقے سے پوچھیں۔",
  as: "দুঃখিত, আপোনাৰ প্ৰশ্নৰ উত্তৰ পোৱা নগ'ল। অনুগ্ৰহ কৰি বেলেগ ধৰণে সোধক।",
  ne: "माफ गर्नुहोस्, तपाईंको प्रश्नको उत्तर भेटिएन। कृपया अर्को तरिकाले सोध्नुहोस्।",
  sa: "क्षम्यताम्, भवतः प्रश्नस्य उत्तरं न लब्धम्। कृपया अन्यथा पृच्छतु।",
  mai: "माफ करू, अहाँक प्रश्नक उत्तर नहि भेटल। कृपया दोसर तरहें पूछू।",
  doi: "माफ़ करना, तुआड्डे सवाल दा जवाब नेई मिलेया। किरपा करियो होर तरीके कन्नै पुच्छो।",
  gom: "माफ करात, तुमच्या प्रश्नाचें उत्तर मेळ्ळें नाय। कृपया वेगळ्या प्रकाराने विचारात.",
  ks: "معاف کریو، آپ کے سوالۆ کا جواب نہیں ملِیا۔",
  mni: "সরি, নাংগী ꯃꯇꯦꯡꯃꯤ ꯄꯨꯛꯅꯤꯡ ꯄꯥꯝꯕꯤꯗꯦ। ꯑꯔꯣꯏꯕꯥ ꯑꯣꯏꯅꯥ ꯃꯥꯗꯒꯨ।",
  sat: "ᱦᱚᱲᱚ, ᱟᱢᱟᱜ ᱜᱟᱞ ᱨᱮ ᱡᱩᱣᱟᱹᱵ ᱵᱟᱹᱦᱤᱡ ᱠᱟᱱᱟ།",
  sd: "معاف ڪجو، توهان جي سوال جو جواب نه مليو. مهرباني ڪري ٻيءَ طرح پڇو.",
  brx: "माफ करनो, नोंनि सुंथिनि जोबाब नाथाय। जायेन फैगोन सुंथिनो।",
};

export async function askAssistant(
  userInput: string,
  _history: ChatMessage[],
  language: string
): Promise<string> {
  const lang = language || "en";
  const match = findBestMatch(userInput);
  if (!match) {
    return FALLBACK[lang] ?? FALLBACK["en"];
  }
  const translation = match.translations[lang] ?? match.translations["en"];
  return translation?.answer ?? FALLBACK["en"];
}