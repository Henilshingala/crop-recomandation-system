import pickle

path = r'D:\downloads\CRS\Backend\app\Ai\trained_model.pkl'
with open(path, 'rb') as f:
    m = pickle.load(f)
    
# Check available languages for 'hi' greeting
print('Available languages for greeting (QNA1301):')
for meta in m['metadata']:
    if meta['qna_key'] == 'QNA1301':
        print(f'  {meta["lang"]}: {meta["original_question"]}')

print('\nAll available language codes:')
all_langs = sorted(set(meta['lang'] for meta in m['metadata']))
print(f'  {all_langs}')
