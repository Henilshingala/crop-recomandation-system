import pickle

path = r'D:\downloads\CRS\Backend\app\Ai\trained_model.pkl'
with open(path, 'rb') as f:
    m = pickle.load(f)

print('Hindi greetings in the model:')
for meta in m['metadata']:
    if meta['lang'] == 'hi' and ('नमस्कार' in meta['original_question'].lower() or 'नमस्ते' in meta['original_question'].lower()):
        print(f'  {meta["original_question"]}')

print('\nAll Hindi questions:')
for meta in m['metadata']:
    if meta['lang'] == 'hi' and len(meta['original_question']) < 20:
        print(f'  {meta["original_question"]}')
