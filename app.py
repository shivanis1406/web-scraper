from bs4 import BeautifulSoup
import requests, re, os, pprint
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

google_search_api=os.getenv('GOOGLE_SEARCH_API')
search_engine_id=os.getenv('SEARCH_ENGINE_ID')


def googlesearch(user_query):
    # Build a service object for interacting with the API. Visit
    # the Google APIs Console <http://code.google.com/apis/console>
    # to get an API key for your own application.
    service = build(
        "customsearch", "v1", developerKey=google_search_api
    )

    res = (
        service.cse()
        .list(
            q=user_query,
            cx=search_engine_id,
            lr="lang_en"
        )
        .execute()
    )
    #pprint.pprint(res["items"])
    return res["items"]


def read_from_link(url):
    """Fetch HTML content from a given URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses
    return response.text

def check_for_doi(soup, text):
    """
    Look for DOI references in the page.
    First, search in meta tags, then in the text body.
    """
    doi_matches = []
    
    # Check for DOI in meta tags
    meta_doi = soup.find('meta', {'name': 'citation_doi'})
    if meta_doi:
        doi_matches.append(meta_doi['content'])

    # Check for DOI in text using regex
    #doi_pattern = r'\b(10\.\d{4,}/[-._;()/:A-Za-z0-9]+)\b'
    #text_doi_matches = re.findall(doi_pattern, text)
    #doi_matches.extend(text_doi_matches)
    
    return list(set(doi_matches))  # Remove duplicates

def clean_content(soup, min_len = 20):
    """
    Clean and print the body content of the journal after removing footers, ads, etc.
    """
    # Find all paragraph tags that do not have a class and extract text. 
    paragraphs = soup.find('body').find_all('p', class_=False)


    cleaned_paragraphs = []
    refs = []
    for para in paragraphs:
        if para.get_text(strip=True):
            cleaned_paragraphs.append(para.get_text(strip=True))
            
            # Find list of all <a href=> within above <p> elements?
            links = para.find_all('a')
            for link in links:
                #print("Link:", link['href'])
                refs.append(link['href'])

    # Further filter out irrelevant sections if needed
    # Example: Remove paragraphs that are too short or contain footer information
    #filtered_paragraphs = [para for para in cleaned_paragraphs if len(para) > min_len]  # Keep only meaningful paragraphs
    
    return cleaned_paragraphs, refs

# Main execution block
google_search_response = googlesearch("Are vegetable fats safe")
N = 2 #except heart.org
urls = []

for k in range(0, len(google_search_response)):
    if "www.heart.org" not in google_search_response[k]["link"] and len(urls) < N:
        urls.append(google_search_response[k]["link"])

#titles = [google_search_response[k]["htmlTitle"] for k in range(0, N)]

print("\n".join(urls))

for i in range(0, N):
    url1 = urls[i]
    html_content1 = read_from_link(url1)

    # Parse the HTML content
    soup1 = BeautifulSoup(html_content1, 'lxml')

    # Find DOI in the content or meta tags
    '''
    dois = check_for_doi(soup1, html_content1)

    if len(dois) > 0:
        # Fetch the document using the first DOI found
        doi_url = f"https://www.doi.org/{dois[0]}"
        print(f"Fetching content from DOI: {doi_url}")
        
        html_content2 = read_from_link(doi_url)
        soup2 = BeautifulSoup(html_content2, 'lxml')

        # Clean the content of the journal/article page
        cleaned_content = clean_content(soup2)
    else:
    '''
    print(f"\n\nFetching content {url1}")
    # Clean the content of the journal/article page
    cleaned_content, refs = clean_content(soup1)


    # Print cleaned content
    for paragraph in cleaned_content:
        print(paragraph)

    # Print refs
    for ref in refs:
        print(ref)
