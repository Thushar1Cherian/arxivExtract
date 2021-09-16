import urllib
import urllib.request
import xmltodict
import pandas as pd
import datetime


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
            url_base = url_base+"+AND+"+"cat:"+cat
        else:
            url_base = url_base+"cat:"+cat
            parameters += 1
    if max_results != 10:
        max_results = str(max_results)
        if parameters > 0:
            url_base = url_base+"&"+"max_results="+max_results
        else:
            url_base = url_base+"max_results="+max_results
            parameters += 1
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
        frame = pd.DataFrame.from_dict(dict_data['feed']['entry'])
    except KeyError as error:
        frame = pd.DataFrame()
        print("No such articles present in arxiV")
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
    frame = xmltoframe(data)
    return frame


def write_file(author_name, category_name, data):
    now = datetime.datetime.now()
    if category_name is None:
        category_name = ""
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    time = now.strftime("%H%M%S")
    time_stamp = year+month+day+time
    file_path = str(author_name) + str(category_name) + \
        str(time_stamp) + ".csv"
    data.to_csv(file_path)
    return 1


if __name__ == '__main__':
    """Strating point of arxiv Api Call
    use %20 to represent space in the query parameters
    Please use named query parameters.
    """
    author_name = 'Christian%20Claussen'
    category_name = None
    query = url_maker(author='Christian',
                      max_results=100)
    arxiv_data = api_call(query)
    writing_status = write_file(author_name, category_name, arxiv_data)
    print(writing_status)
