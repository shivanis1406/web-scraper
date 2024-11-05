from bs4 import BeautifulSoup
import requests, re, os, pprint
from dotenv import load_dotenv
from googleapiclient.discovery import build
import time

load_dotenv()

google_search_api=os.getenv('GOOGLE_SEARCH_API')
search_engine_id=os.getenv('SEARCH_ENGINE_ID')


def googlesearch(user_query, google_search_api, search_engine_id):
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

def extract_text_from_element(soup, ele, class_name = None, id = None, min_len = 0):
    article = None
    content = []
    refs_per_para = []
    refs = []

    if class_name:
        article = soup.find(ele, class_=class_name)
    elif id:
        article = soup.find(ele, id=id)

    # If the article body is found
    if article:
        # Extract all <p>, <li> tags within the article
        content_elements = article.find_all(["p", "li"])

        # Collect text from each element
        for element in content_elements:
            text = element.get_text()
            if len(text) >= min_len:  # Check if text meets minimum length requirement
                content.append(text)
                print(f"Para is - {text}")
                
                # Find list of all <a href=> within above elements?
                refs_per_para = []
                links = element.find_all('a')
                for link in links:
                    print("Links are -", link['href'])
                    refs_per_para.append(link['href'])
                    
                refs.append(refs_per_para)

    return content, refs

def clean_content(soup, url, min_len = 0):
    """
    Clean and print the body content of the journal after removing footers, ads, etc.
    """
    #Find all <article tags with class article-body for url contains "www.healthline.com"
    if "www.healthline.com" in url or "www.medicalnewstoday.com" in url:
        content, refs = extract_text_from_element(soup, "article", class_name = "article-body")

    elif "www.webmd.com" in url:
        content, refs = extract_text_from_element(soup, "div", class_name = "article__body")
    
    elif "www.mayoclinic.org" in url:
        content, refs = extract_text_from_element(soup, "div", id = "main-content")

    elif "www.eatright.org" in url:
        content, refs = extract_text_from_element(soup, "main", id = "main")     

    elif "www.nutritionsource.hsph.harvard.edu" in url:
        content, refs = extract_text_from_element(soup, "div", class_name = "site-main")

    else:
        print("Find all paragraph tags that do not have a class and extract text.")
        '''
        content = []
        refs_per_para = []
        refs = []

        paragraphs = soup.find('body').find_all('p', class_=False)

        for para in paragraphs:
            if para.get_text() and len(para.get_text()) > min_len:
                content.append(para.get_text())
                print(f"Para is - {para.get_text()}")
                
                # Find list of all <a href=> within above <p> elements?
                refs_per_para = []
                links = para.find_all('a')
                for link in links:
                    print("Links are -", link['href'])
                    refs_per_para.append(link['href'])
                
                refs.append(refs_per_para)
        '''
    
    return content, refs

def scrape_data(query, google_search_api, search_engine_id, N=2):
    # Main execution block
    #google_search_response = googlesearch(query, google_search_api, search_engine_id)
    
    urls = ["https://www.healthline.com/nutrition/too-much-sugar",
    "https://www.eatright.org/health/wellness/healthful-habits/forget-low-fat-and-low-sugar-concentrate-on-a-healthy-eating-pattern",
    "https://www.medicalnewstoday.com/articles/141442#what-are-fats",
    "https://nutritionsource.hsph.harvard.edu/what-should-you-eat/fats-and-cholesterol/types-of-fat/omega-3-fats/",
    "https://www.webmd.com/food-recipes/protein",
    "https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/expert-answers/high-protein-diets/faq-20058207"]

    #for k in range(0, len(google_search_response)):
    #    if "www.heart.org" not in google_search_response[k]["link"] and len(urls) < N:
    #        urls.append(google_search_response[k]["link"])

    #titles = [google_search_response[k]["htmlTitle"] for k in range(0, N)]

    #print("\n".join(urls))

    cleaned_content_list = []
    refs_list = []

    for i in range(0, N):
        url1 = urls[i]
        print(f"\n\nFetching content {url1}\n")
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
        # Clean the content of the journal/article page
        cleaned_content, refs = clean_content(soup1, url1)


        # Print cleaned content
        for i in range(len(cleaned_content)):
            print(f"\nPara - {cleaned_content[i]}")
            print(f"Refs - {refs[i]}")


        cleaned_content_list.append(cleaned_content)
        refs_list.append(refs)

        time.sleep(5) #Delay to prevent 403 error

    return cleaned_content_list, refs_list


para_list, refs_list = scrape_data("Are emulsifiers safe", google_search_api, search_engine_id, N=4)
