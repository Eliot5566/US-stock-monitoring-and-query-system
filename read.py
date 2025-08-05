import pickle


with open('./cache_pickle/CLS.pkl', 'rb') as f:
    data = pickle.load(f)


print(data)