import json
import os

locales_dir = r"d:\downloads\CRS\Frontend\src\locales"

en_data = {
    "tabs": {
        "cropRecommendation": "Crop Recommendation",
        "governmentSchemes": "Government Schemes"
    },
    "schemes": {
        "findTitle": "Find Government Schemes",
        "keywordLabel": "Search Keyword",
        "stateLabel": "State",
        "searchButton": "Find Agriculture Schemes",
        "noResults": "No schemes found",
        "noResultsHint": "Try adjusting your filters or search keywords.",
        "loadError": "Failed to load data. Please try again."
    }
}

translations = {
    "en": en_data,
    "hi": {
        "tabs": { "cropRecommendation": "फसल अनुशंसा", "governmentSchemes": "सरकारी योजनाएं" },
        "schemes": { "findTitle": "सरकारी योजनाएं खोजें", "keywordLabel": "कीवर्ड खोजें", "stateLabel": "राज्य", "searchButton": "कृषि योजनाएं खोजें", "noResults": "कोई योजना नहीं मिली", "noResultsHint": "अपने फ़िल्टर या खोज कीवर्ड को समायोजित करने का प्रयास करें।", "loadError": "डेटा लोड करने में विफल। कृपया पुन: प्रयास करें।" }
    },
    "gu": {
        "tabs": { "cropRecommendation": "પાક ભલામણ", "governmentSchemes": "સરકારી યોજનાઓ" },
        "schemes": { "findTitle": "સરકારી યોજનાઓ શોધો", "keywordLabel": "કીવર્ડ શોધો", "stateLabel": "રાજ્ય", "searchButton": "કૃષિ યોજનાઓ શોધો", "noResults": "કોઈ યોજનાઓ મળી નથી", "noResultsHint": "તમારા ફિલ્ટર્સ અથવા શોધ કીવર્ડને સમાયોજિત કરવાનો પ્રયાસ કરો.", "loadError": "ડેટા લોડ કરવામાં નિષ્ફળ. કૃપા કરીને ફરી પ્રયાસ કરો." }
    },
    "mr": {
        "tabs": { "cropRecommendation": "पीक शिफारस", "governmentSchemes": "सरकारी योजना" },
        "schemes": { "findTitle": "सरकारी योजना शोधा", "keywordLabel": "कीवर्ड शोधा", "stateLabel": "राज्य", "searchButton": "कृषी योजना शोधा", "noResults": "कोणत्याही योजना आढळल्या नाहीत", "noResultsHint": "आपले फिल्टर किंवा शोध कीवर्ड समायोजित करण्याचा प्रयत्न करा.", "loadError": "डेटा लोड करण्यात अयशस्वी. कृपया पुन्हा प्रयत्न करा." }
    },
    "ta": {
        "tabs": { "cropRecommendation": "பயிர் பரிந்துரை", "governmentSchemes": "அரசு திட்டங்கள்" },
        "schemes": { "findTitle": "அரசு திட்டங்களை தேடுக", "keywordLabel": "முக்கிய சொல்லை தேடுக", "stateLabel": "மாநிலம்", "searchButton": "வேளாண்மை திட்டங்களை தேடுக", "noResults": "எந்த திட்டங்களும் கிடைக்கவில்லை", "noResultsHint": "உங்கள் வடிப்பான்கள் அல்லது தேடல் முக்கிய சொற்களை சரிசெய்ய முயற்சிக்கவும்.", "loadError": "தரவை ஏற்ற முடியவில்லை. மீண்டும் முயற்சிக்கவும்." }
    },
    "te": {
        "tabs": { "cropRecommendation": "పంట సిఫార్సు", "governmentSchemes": "ప్రభుత్వ పథకాలు" },
        "schemes": { "findTitle": "ప్రభుత్వ పథకాలను శోధించండి", "keywordLabel": "కీవర్డ్ శోధన", "stateLabel": "రాష్ట్రం", "searchButton": "వ్యవసాయ పథకాలను శోధించండి", "noResults": "ఎటువంటి పథకాలు కనుగొనబడలేదు", "noResultsHint": "మీ ఫిల్టర్లు లేదా శోధన కీవర్డ్‌లను సర్దుబాటు చేయడానికి ప్రయత్నించండి.", "loadError": "డేటా లోడ్ చేయడంలో విఫలమైంది. దయచేసి మళ్లీ ప్రయత్నించండి." }
    },
    "kn": {
        "tabs": { "cropRecommendation": "ಬೆಳೆಯನ್ನು ಶಿಫಾರಸು", "governmentSchemes": "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು" },
        "schemes": { "findTitle": "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ", "keywordLabel": "ಕೀವರ್ಡ್ ಹುಡುಕಿ", "stateLabel": "ರಾಜ್ಯ", "searchButton": "ಕೃಷಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ", "noResults": "ಯಾವುದೇ ಯೋಜನೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ", "noResultsHint": "ನಿಮ್ಮ ಫಿಲ್ಟರ್‌ಗಳು ಅಥವಾ ಹುಡುಕಾಟ ಕೀವರ್ಡ್‌ಗಳನ್ನು ಹೊಂದಿಸಲು ಪ್ರಯತ್ನಿಸಿ.", "loadError": "ಡೇಟಾವನ್ನು ಲೋಡ್ ಮಾಡಲು ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ." }
    },
    "bn": {
        "tabs": { "cropRecommendation": "ফসল সুপারিশ", "governmentSchemes": "সরকারি স্কিম" },
        "schemes": { "findTitle": "সরকারি স্কিম খুঁজুন", "keywordLabel": "কীওয়ার্ড অনুসন্ধান", "stateLabel": "রাজ্য", "searchButton": "কৃষি স্কিম খুঁজুন", "noResults": "কোনো স্কিম পাওয়া যায়নি", "noResultsHint": "আপনার ফিল্টার বা অনুসন্ধান কীওয়ার্ড সামঞ্জস্য করার চেষ্টা করুন।", "loadError": "ডেটা লোড করতে ব্যর্থ৷ আবার চেষ্টা করুন।" }
    },
    "pa": {
        "tabs": { "cropRecommendation": "ਫ਼ਸਲ ਸਿਫ਼ਾਰਸ਼", "governmentSchemes": "ਸਰਕਾਰੀ ਸਕੀਮਾਂ" },
        "schemes": { "findTitle": "ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਲੱਭੋ", "keywordLabel": "ਕੀਵਰਡ ਖੋਜ", "stateLabel": "ਰਾਜ", "searchButton": "ਖੇਤੀਬਾੜੀ ਸਕੀਮਾਂ ਲੱਭੋ", "noResults": "ਕੋਈ ਸਕੀਮਾਂ ਨਹੀਂ ਮਿਲੀਆਂ", "noResultsHint": "ਆਪਣੇ ਫਿਲਟਰ ਜਾਂ ਖੋਜ ਕੀਵਰਡਾਂ ਨੂੰ ਵਿਵਸਥਿਤ ਕਰਨ ਦੀ ਕੋਸ਼ਿਸ਼ ਕਰੋ।", "loadError": "ਡਾਟਾ ਲੋਡ ਕਰਨ ਵਿੱਚ ਅਸਫਲ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।" }
    },
    "ml": {
        "tabs": { "cropRecommendation": "വിള ശുപാർശ", "governmentSchemes": "സർക്കാർ പദ്ധതികൾ" },
        "schemes": { "findTitle": "സർക്കാർ പദ്ധതികൾ കണ്ടെത്തുക", "keywordLabel": "കീവേഡ് തിരയുക", "stateLabel": "സംസ്ഥാനം", "searchButton": "കാർഷിക പദ്ധതികൾ കണ്ടെത്തുക", "noResults": "ഒരു പദ്ധതിയും കണ്ടെത്തിയില്ല", "noResultsHint": "നിങ്ങളുടെ ഫിൽട്ടറുകളോ തിരയൽ കീവേഡുകളോ ക്രമീകരിക്കാൻ ശ്രമിക്കുക.", "loadError": "ഡാറ്റ ലോഡുചെയ്യുന്നതിൽ പരാജയപ്പെട്ടു. ദയവായി വീണ്ടും ശ്രമിക്കുക." }
    },
    "or": {
        "tabs": { "cropRecommendation": "ଫସଲ ସୁପାରିଶ", "governmentSchemes": "ସରକାରୀ ଯୋଜନା" },
        "schemes": { "findTitle": "ସରକାରୀ ଯୋଜନା ଖୋଜନ୍ତୁ", "keywordLabel": "କୀୱାର୍ଡ ଖୋଜନ୍ତୁ", "stateLabel": "ରାଜ୍ୟ", "searchButton": "କୃଷି ଯୋଜନା ଖୋଜନ୍ତୁ", "noResults": "କୌଣସି ଯୋଜନା ମିଳିଲା ନାହିଁ", "noResultsHint": "ଆପଣଙ୍କର ଫିଲ୍ଟର୍ କିମ୍ବା ସନ୍ଧାନ କୀୱାର୍ଡଗୁଡ଼ିକୁ ସମନ୍ୱୟ କରିବାକୁ ଚେଷ୍ଟା କରନ୍ତୁ।", "loadError": "ଡାଟା ଲୋଡ୍ କରିବାରେ ବିଫଳ | ଦୟାକରି ପୁନର୍ବାର ଚେଷ୍ଟା କରନ୍ତୁ।" }
    },
    "ur": {
        "tabs": { "cropRecommendation": "فصل کی سفارش", "governmentSchemes": "سرکاری اسکیمیں" },
        "schemes": { "findTitle": "سرکاری اسکیمیں تلاش کریں", "keywordLabel": "مطلوبہ لفظ تلاش کریں", "stateLabel": "ریاست", "searchButton": "زرعی اسکیمیں تلاش کریں", "noResults": "کوئی اسکیمیں نہیں ملیں", "noResultsHint": "اپنے فلٹرز یا تلاش کے مطلوبہ الفاظ کو ایڈجسٹ کرنے کی کوشش کریں۔", "loadError": "ڈیٹا لوڈ کرنے میں ناکام۔ براہ کرم دوبارہ کوشش کریں۔" }
    },
    "ne": {
        "tabs": { "cropRecommendation": "बाली सिफारिस", "governmentSchemes": "सरकारी योजनाहरू" },
        "schemes": { "findTitle": "सरकारी योजनाहरू खोज्नुहोस्", "keywordLabel": "कुञ्जी शब्द खोज्नुहोस्", "stateLabel": "राज्य", "searchButton": "कृषि योजनाहरू खोज्नुहोस्", "noResults": "कुनै योजनाहरू फेला परेनन्", "noResultsHint": "तपाईंको फिल्टर वा खोज कुञ्जी शब्दहरू समायोजन गर्ने प्रयास गर्नुहोस्।", "loadError": "डेटा लोड गर्न असफल। कृपया फेरि प्रयास गर्नुहोस्।" }
    },
    "as": {
        "tabs": { "cropRecommendation": "শস্যৰ পৰামৰ্শ", "governmentSchemes": "চৰকাৰী আঁচনি" },
        "schemes": { "findTitle": "চৰকাৰী আঁচনি বিচাৰক", "keywordLabel": "কীৱৰ্ড বিচাৰক", "stateLabel": "ৰাজ্য", "searchButton": "কৃষি আঁচনি বিচাৰক", "noResults": "কোনো আঁচনি পোৱা নগ'ল", "noResultsHint": "আপোনাৰ ফিল্টাৰ বা অনুসন্ধান কীৱৰ্ডসমূহ সালসলনি কৰিবলৈ চেষ্টা কৰক।", "loadError": "তথ্য ল'ড কৰিবলৈ ব্যৰ্থ। অনুগ্ৰহ কৰি পুনৰ চেষ্টা কৰক।" }
    },
    "sa": {
        "tabs": { "cropRecommendation": "सस्य अनुशंसाम्", "governmentSchemes": "सर्वकारस्य योजनाः" },
        "schemes": { "findTitle": "सर्वकारस्य योजनाः अन्वेषयन्तु", "keywordLabel": "शब्दं अन्वेषयन्तु", "stateLabel": "राज्यम्", "searchButton": "कृषि योजनाः अन्वेषयन्तु", "noResults": "कापि योजना न प्राप्ता", "noResultsHint": "भवतः विकल्पान् वा शब्दान् परिवर्तयितुं प्रयतध्वम्।", "loadError": "दत्तांशं आनेतुं विफलम्। कृपया पुनः प्रयतध्वम्।" }
    }
}

for root, dirs, files in os.walk(locales_dir):
    for file in files:
        if file.endswith(".json"):
            filepath = os.path.join(root, file)
            lang_code = os.path.splitext(file)[0]
            
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Error decoding {file}")
                    continue
            
            lang_translations = translations.get(lang_code, en_data)
            
            changed = False
            
            if "tabs" not in data:
                data["tabs"] = lang_translations["tabs"]
                changed = True
            else:
                for k, v in lang_translations["tabs"].items():
                    if k not in data["tabs"]:
                        data["tabs"][k] = v
                        changed = True
            
            if "schemes" not in data:
                data["schemes"] = lang_translations["schemes"]
                changed = True
            else:
                for k, v in lang_translations["schemes"].items():
                    if k not in data["schemes"]:
                        data["schemes"][k] = v
                        changed = True
            
            if changed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"Updated {file}")
            else:
                print(f"No changes needed for {file}")
