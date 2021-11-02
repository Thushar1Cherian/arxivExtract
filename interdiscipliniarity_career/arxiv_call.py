import urllib
import urllib.request
import xmltodict
import pandas as pd
import datetime
from collections import Counter
import networkx as nx
import os


category_list = ['q-bio.PE', 'math.DS', 'math-ph', 'cond-mat.soft', 'cond-mat.mtrl-sci',
                 'cond-mat.stat-mech', 'nlin.AO','cs.AI','cs.NE']
cwd = os.getcwd()
#data_path = "A:\\Aston\\Project\\Code\\arxiv\\arxivExtract\\interdiscipliniarity_career\\data\\"
category_author_frame = pd.read_excel(cwd + "\\data\\" + "category_author.xlsx")


def url_maker(author=None, category=None, max_results=10):
    """Generates the query to be sent to the arxiv API recieving user inputs.
    Currently only author, category and max_results are accepted. More to follow.

    Args:
        author ([String], optional): [Name of the author]. Defaults to None.
        category ([String], optional): [Category of the journals needed]. Defaults to None.
        max_results (int, optional): [maximum results required]. Defaults to 10.

    Returns:
        [type]: [description]
    """
    print(category)
    parameters = 0
    url_base = 'http://export.arxiv.org/api/query?search_query='
    if author != None:
        au = str(author)
        url_base = url_base+"au:\'"+au+'\''
        parameters += 1
    if category != None:
        cat = str(category)
        if parameters > 0:
            url_base = url_base+"+AND+cat:"+cat
        else:
            url_base = url_base+"+AND+cat:"+ cat
            parameters += 1
    '''
    if max_results != 10:
        max_results = str(max_results)
        if parameters > 0:
            url_base = url_base+"&"+"max_results="+max_results
        else:
            url_base = url_base+"&max_results="+max_results
            parameters += 1
    '''
    print(url_base)
    return url_base


def xmltoframe(data):
    """Converts the XML reponse to python pandas dataframe

    Args:
        data ([XML]): [response of the query send to Arxiv API]

    Returns:
        [pd.Dataframe]: [response as a frame]
    """
    dict_data = xmltodict.parse(data)
    try:
        if type(dict_data['feed']['entry'])==list:
            frame = pd.DataFrame.from_dict(dict_data['feed']['entry'])
        else:
            frame = pd.DataFrame.from_dict(dict_data['feed']['entry'], orient='index')
            frame = frame.T
    except KeyError as error:
        frame = pd.DataFrame()
        print("No such articles present in arxiV"+ str(error))
    return frame


def api_call(query):
    """Calls the arxiv API

    Args:
        query ([String]): [The query to be sent to the API]

    Returns:
        [pd.Dataframe]: [Resposne of the query as a frame]
    """
    temp = urllib.request.urlopen(query)
    data = temp.read().decode('utf-8')
    data_dict = dict(xmltodict.parse(data))
    frame = xmltoframe(data)
    return frame , data_dict


def write_file(data,name):
    """ Write extracted data to csv file
    """
    now = datetime.datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    time = now.strftime("%H%M%S")
    time_stamp = year+month+day+time
    file_path = name + str(time_stamp) + ".csv"
    data.to_csv(file_path)

def loop_category(author_dict):
    '''Looping through each category and corresponding authors
    scrapping data from arxiv
    '''
    category_list = list()
    dictionary_list = list()
    for category in author_dict:
        author_list = author_dict[category]
        author_list = [ str(author).replace(' ', '%20') for author in author_list
                       if str(author) != 'nan']
        for author in author_list:
            frame, dictionary = data_extract(author, category)
            category_list.append(frame) 
            try:
                dictionary_list.append(dictionary['feed']['entry'])
            except KeyError as error:
                print('error: '+ category + author)
                print(str(error))
    category_frame = pd.concat(category_list)    
    raw_dict_list = [item for sublist in dictionary_list  if type(sublist)==list for item in sublist]
    return category_frame,raw_dict_list
            
def data_extract(author, category):
    query = url_maker(author, category, max_results=11)
    arxiv_data_frame, arxiv_data_dict = api_call(query)
    return arxiv_data_frame, arxiv_data_dict
 
def cleaned_data_extract(dictionary):
    #creates clean dataframe with only required columns
    cleaned_list = list()
    for publication in dictionary:
        try:
            author_list =  [str(author['name']) for author in publication['author']]
        except Exception:
            author_list = [publication['author']['name']]
            pass        
        try:
            category_list = [str(category['@term']) for category in publication['category']]
        except Exception:
            category_list = [publication['category']['@term']]
            pass
        try:
            summary=publication['summary']
        except Exception:
            summary = ''
            pass
        cleaned_dict = {'id':publication['id'],'author':author_list,
                        'title': publication['title'], 'summary':summary,
                        'category': category_list}
        cleaned_list.append(cleaned_dict)
    return cleaned_list 

def network_dict_creation(dictionary):
    ''' creates dictionary required for network graph creation
    Parameters
    ----------
    dictionary : TYPE List

    Returns
    -------
    author_dict : TYPE dictionary
        DESCRIPTION.

    '''
    authors_complete_list = [element['author'] for element in dictionary]
    authors_complete_list = sum(authors_complete_list, [])
    authors_complete_list = list(set(authors_complete_list))
    author_dict = dict()
    for author in authors_complete_list:
        temp_count_list = list()
        for element in dictionary:
            if author in element['author']:
                temp_count_list.append(element['author'])
        temp_count_list = sum(temp_count_list, [])
        temp_count_dict = dict(Counter(temp_count_list))
        #removing author name from co-author list
        del temp_count_dict[author]
        author_dict[author] = temp_count_dict
    return author_dict
                
def network_graph_creation(co_author_dict):
    '''directed graph creation
    
    '''
    g = nx.DiGraph()
    g.add_nodes_from(co_author_dict.keys())
    for k, v in co_author_dict.items():
        g.add_edges_from(([(k, t) for t,weight in v.items()]))
        
    for k, v in co_author_dict.items():
        for t,weight in v.items():
            g[k][t]['weight'] = weight
    return g
       
     
if __name__ == '__main__':
    """Starting point of arxiv Api Call
    %20 is used to represent space in the query parameters
    Please use named query parameters.
    """
    #category author dict stores the list of required authors with their co-authors in a category
    category_author_dict = category_author_frame.to_dict('list')
    frame,dictionary = loop_category(category_author_dict)
    
    clean_list = cleaned_data_extract(dictionary)
    clean_df = pd.DataFrame(clean_list)
    write_file(clean_df,'cleaned dataframe ')
    #category_author_frame = pd.read_csv(data_path + "cleaned_dataframe_20211024231227.csv")
    #dictionary = category_author_frame.to_dict('index')
    
    co_author_dict = network_dict_creation(clean_list)
    
    graph = network_graph_creation(co_author_dict)
    nx.write_gexf(graph, "test2.gexf")         