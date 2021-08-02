import ast
import nltk
import spacy
import json
import csv
import sys
from Levenshtein import distance


def parse_levenshtein_distance(key_leve, array_leve):
    for point in array_leve:
        if 0 <= distance(key_leve, point) <= 1:
            return True
    return False


def parse_nlp_spacy(sentence):
    # convertir todos los caracteres en mayúscula de sentence en minúsculas
    sentence = sentence.lower()
    # llamar al pipeline NLP de SpaCy
    doc = nlp_spacy(sentence.lower())
    data = []

    # recorrer los tokens devueltos por el pipeline
    for token in doc:
        # analizar los tags de cada token y filtrar los que son necesarios para el análisis
        if token.pos_ not in ('ADJ', 'ADP', 'CONJ', 'DET',
                              'PUNCT', 'CCONJ', 'SCONJ', 'ADV'):
            # agregar el lema de la palabra
            data.append(token.lemma_)

    # retornar todos los tokens filtrados
    return data


def query_expansion(query):
    query_extracted = []
    for word in query:
        word_list = dict_tesauro.get(word)
        if word_list and word_list not in query_extracted:
            query_extracted = query_extracted + word_list

    return query_extracted


if __name__ == '__main__':
    search_type = sys.argv[len(sys.argv) - 3]
    search_engine = sys.argv[len(sys.argv) - 2]
    user_query = sys.argv[len(sys.argv) - 1]

    if user_query == 'help':
        print("First argument, search type:")
        print(" QE = Search with Query Expansion")
        print(" NQE = Search without Query Expansion")
        print("Second argument, search engine:")
        print(" A = Only title")
        print(" B = Only item description")
        print(" C = Only item classification level 4")
        print(" D = All (title + item + clasification level 4)")
        print("Last argument:")
        print(" User Query")
        sys.exit()

    from es_lemmatizer import lemmatize
    nlp_spacy = spacy.load("es_core_news_lg")

    nlp_spacy.add_pipe(lemmatize, after="tagger")
    lemmatizer = nlp_spacy.get_pipe("lemmatize")

    wn = nltk.corpus.reader.wordnet.WordNetCorpusReader('/home/andres/PycharmProjects/wn-mcr-transform/wordnet_spa',
                                                        None)

    data_source = 'covid_contracts_2021_05_06_with_keywords_test2.csv'
    output_file = 'results_found.csv'
    tesauro = 'evaluation_tesauro.json'
    search_engines = ["A", "B", "C", "D"]
    keys_selected = ["emergencia", "alimento", "insumo", "reactivo", "mascarilla", "equipo", "producto", "construcción",
                     "servicio", "hospital", "municipio", "terapia"]
    search_types = ["NQE", "QE"]
    contracts_found = []

    if search_type not in search_types:
        print("Search type not recognized")
        sys.exit()

    if search_engine not in search_engines:
        print("Search engine not recognized")
        sys.exit()

    with open(tesauro) as f:
        dict_tesauro = json.load(f)

    print("User Query: ", user_query)
    user_query = parse_nlp_spacy(user_query)
    print("NLP Query: ", user_query)
    if search_type == 'QE':
        user_query = query_expansion(user_query)
        print("Query Expansion: ", user_query)

    with open(data_source, newline='') as File:
        reader = csv.DictReader(File, delimiter=',')
        for row in reader:
            contract_id = row['Contract ID']
            title_keywords = ast.literal_eval(row['Title keywords'])
            item_keywords = ast.literal_eval(row['Item keywords'])
            item_classification_keywords = ast.literal_eval(row['Item Classification keywords'])
            title = row['Contract title'].lower()
            item = row['Item description'].lower()
            item_classification = row['Item Classification'].lower()

            if search_engine == 'A':
                keywords = title_keywords
                data_string = title
            elif search_engine == 'B':
                keywords = item_keywords
                data_string = item
            elif search_engine == 'C':
                keywords = item_classification_keywords
                data_string = item_classification
            elif search_engine == 'D':
                keywords = title_keywords + item_keywords + item_classification_keywords
                data_string = title + item + item_classification
            else:
                print("Search engine not recognized")
                sys.exit()

            for key in user_query:
                if (parse_levenshtein_distance(key, keywords) or key in data_string) \
                        and contract_id not in contracts_found:
                    contracts_found.append(contract_id)

    print("Contracts found: ", contracts_found)
    sys.exit()
