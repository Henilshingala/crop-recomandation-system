import json
import os
import sys

# The new Q&A pairs provided by the user
new_qnas = [
{
"question": "What is a crop recommendation system?",
"answer": "A crop recommendation system is an AI-powered decision-support tool that analyses soil nutrient levels (N, P, K), soil pH, temperature, humidity, and rainfall to suggest the most suitable crop to grow in a specific location and season. It helps farmers maximise crop yield and optimise the use of natural resources."
},
{
"question": "How does the crop recommendation system work?",
"answer": "You enter soil and environmental parameters including Nitrogen (N), Phosphorus (P), Potassium (K), soil pH, temperature, humidity, and rainfall. The system processes these inputs using a trained machine learning model and predicts the crops that are most suitable for those conditions."
},
{
"question": "What inputs are required for crop prediction?",
"answer": "The system requires seven inputs: Nitrogen (N), Phosphorus (P), Potassium (K), soil pH value, temperature in degrees Celsius, humidity percentage, and rainfall measured in millimetres."
},
{
"question": "Why are Nitrogen, Phosphorus, and Potassium important for crops?",
"answer": "Nitrogen supports leaf growth, phosphorus helps root development and flowering, and potassium improves plant strength and disease resistance. These three nutrients are essential for healthy plant growth."
},
{
"question": "Why is soil pH important in agriculture?",
"answer": "Soil pH affects nutrient availability to plants. Most crops grow best in slightly acidic to neutral soil with a pH between 6.0 and 7.5. If soil pH is too high or too low, plants cannot absorb nutrients effectively."
},
{
"question": "How does rainfall affect crop growth?",
"answer": "Rainfall provides water necessary for plant growth. Different crops require different rainfall levels. Too little rainfall causes drought stress, while excessive rainfall can damage roots and reduce yield."
},
{
"question": "Why is temperature considered in crop prediction?",
"answer": "Temperature affects plant metabolism, germination, and growth cycles. Each crop has an optimal temperature range where it grows best."
},
{
"question": "Why is humidity used in the crop recommendation system?",
"answer": "Humidity affects plant transpiration, disease development, and moisture availability in the air. Certain crops grow better in humid environments while others prefer drier conditions."
},
{
"question": "What type of machine learning model is used in this system?",
"answer": "The system uses an ensemble machine learning model that combines Balanced Random Forest, XGBoost, and LightGBM with a Logistic Regression meta-model to generate accurate crop predictions."
},
{
"question": "How accurate is the crop recommendation system?",
"answer": "The accuracy depends on the quality of the dataset and the environmental conditions. Ensemble models typically achieve high predictive accuracy when trained on well-balanced agricultural datasets."
},
{
"question": "Can this system recommend multiple crops?",
"answer": "Yes. The system typically returns the top three most suitable crops ranked by confidence score."
},
{
"question": "What does the confidence score mean in crop prediction?",
"answer": "The confidence score represents how strongly the machine learning model believes that a particular crop is suitable for the provided environmental conditions."
},
{
"question": "What happens if no crop is suitable for the given conditions?",
"answer": "If the environmental conditions do not strongly match any crop in the dataset, the system may return low-confidence predictions or inform the user that no suitable crop recommendation is available."
},
{
"question": "Can farmers rely completely on this recommendation system?",
"answer": "The system provides data-driven guidance, but farmers should also consider local knowledge, weather forecasts, irrigation availability, and government agricultural advisories before making final decisions."
},
{
"question": "Does this system work for all countries?",
"answer": "The system works best for regions whose climate and crop types are represented in the training dataset. Predictions may be less accurate in regions with very different agricultural conditions."
},
{
"question": "Can this system help improve crop yield?",
"answer": "Yes. By recommending crops suited to soil and environmental conditions, the system can help farmers choose crops that have a higher probability of successful growth and better yield."
},
{
"question": "Is internet connection required to use this system?",
"answer": "Yes. The web application sends input data to the backend server where the machine learning model processes the request and returns the prediction results."
},
{
"question": "What technologies are used to build this system?",
"answer": "The system uses React and Next.js for the frontend interface, Django for the backend API, FastAPI for the machine learning inference service, and cloud hosting platforms like Render, Vercel, and HuggingFace Spaces."
},
{
"question": "What is the purpose of using AI in agriculture?",
"answer": "Artificial intelligence helps analyse large agricultural datasets and environmental factors to support better farming decisions, improve crop productivity, and reduce resource waste."
},
{
"question": "Can this system help beginner farmers?",
"answer": "Yes. The system simplifies complex agricultural data and provides recommendations that can help beginner farmers choose appropriate crops for their land."
}
]

# The path to Ai.json
ai_json_path = r'd:\downloads\CRS\Frontend\src\locales\Ai.json'

print(f"Loading {ai_json_path}...")
with open(ai_json_path, 'r', encoding='utf-8') as f:
    ai_data = json.load(f)

# Find the highest QNA number to continue from there
max_qna_num = 0
for key in ai_data.keys():
    if key.startswith('QNA'):
        try:
            num = int(key[3:])
            if num > max_qna_num:
                max_qna_num = num
        except ValueError:
            pass

print(f"Current max QNA number: {max_qna_num}")

# Also get the list of languages needed from the first entry
sample_qna = ai_data.get('QNA1', {})
if not sample_qna:
   sample_qna = list(ai_data.values())[0]

languages = list(sample_qna.get('translations', {}).keys())
print(f"Languages to populate: {languages}")

# I noticed there were previous translation scripts in the codebase:
# d:\downloads\CRS\translate_qa.py and d:\downloads\CRS\translate_qna.py
# If they use googletrans or similar, we might need it. For now, we will add
# English to 'en' and just copy English for other languages to let the UI work,
# or we can try to use a translation library if available.
# Let's check if googletrans or deep_translator is installed.
try:
    from deep_translator import GoogleTranslator
    has_translator = True
    print("Using deep_translator.")
except ImportError:
    try:
        from googletrans import Translator
        translator = Translator()
        has_translator = True
        print("Using googletrans.")
    except ImportError:
        has_translator = False
        print("No translation library found. Falling back to English for all languages temporarily.")

def translate_text(text, target_lang):
    if not has_translator or target_lang == 'en':
        return text
    
    # Map some region/special codes to google translate codes if necessary
    # deep_translator supports things like 'as' (Assamese), 'bn' (Bengali), etc.
    lang_map = {
        'gom': 'gom', # Konkani might not be directly supported, fallback might happen
        'brx': 'brx', # Bodo
        'mai': 'mai', # Maithili
        'mni': 'mni-Mtei', # Meiteilon (Manipuri)
        'doi': 'doi', # Dogri
        'ks': 'ks', # Kashmiri
        'sat': 'sat', # Santali
        'sa': 'sa' # Sanskrit
    }
    
    gt_lang = target_lang
    if target_lang == 'gom': gt_lang = 'gom' # Google Translate supports Konkani
    
    try:
        if 'GoogleTranslator' in globals():
            return GoogleTranslator(source='en', target=gt_lang).translate(text)
        else:
            return translator.translate(text, dest=gt_lang).text
    except Exception as e:
        print(f"Error translating to {target_lang}: {e}")
        return text # fallback to english

# Process new QNAs
start_num = max_qna_num + 1
for i, qna in enumerate(new_qnas):
    qna_key = f"QNA{start_num + i}"
    print(f"Processing {qna_key}...")
    
    ai_data[qna_key] = {
        "translations": {}
    }
    
    for lang in languages:
        ai_data[qna_key]["translations"][lang] = {
            "question": translate_text(qna["question"], lang),
            "answer": translate_text(qna["answer"], lang)
        }

print(f"Saving updated {ai_json_path}...")
with open(ai_json_path, 'w', encoding='utf-8') as f:
    json.dump(ai_data, f, indent=2, ensure_ascii=False)

print("Done!")
