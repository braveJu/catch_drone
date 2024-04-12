import pickle


def save_file(file_name:str, data):
    with open(file_name, 'wb') as f:
        pickle.dump(data, f)
        
        
def load_file(name:str):
    with open(f'{name}', 'rb') as f:
        data = pickle.load(f)
    return data