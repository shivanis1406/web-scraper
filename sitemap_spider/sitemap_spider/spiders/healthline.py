import scrapy, os, re

os.system("rm -rf articles output.json")

class HealthlineSpider(scrapy.Spider):
    name = "healthline"
    allowed_domains = ["www.healthline.com"]
    start_urls = ["https://www.healthline.com/sitemap.xml"]

    def __init__(self, *args, **kwargs):
        super(HealthlineSpider, self).__init__(*args, **kwargs)
        self.article_count = 1  # Initialize counter for unique filenames

    def parse(self, response):
        self.logger.info(f"Visited: {response.url}")

        # Register the default namespace
        response.selector.register_namespace('ns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        # Extract URLs of nested sitemaps
        sitemap_urls = response.xpath('//ns:sitemap/ns:loc/text()').getall()

        if not sitemap_urls:
            self.logger.warning("No nested sitemap URLs found in the sitemap index.")
        
        # Follow each nested sitemap
        for url in sitemap_urls:
            yield scrapy.Request(url, callback=self.parse)

        # Extract URLs from the current sitemap if it contains page URLs
        page_urls = response.xpath('//ns:url/ns:loc/text()').getall()
        
        if page_urls:
            for url in page_urls:
                if "https://www.healthline.com/nutrition/" in url:
                    yield scrapy.Request(url, callback=self.parse_article)

    def parse_article_old(self, response):
        title = response.css('div:has(h1) > h1::text').get()

        # Extract only <p> and <li> tags within <article class="article-body">
        text_elements = response.css('article.article-body p::text, article.article-body li::text').getall()
        #text = ' '.join(text_elements)

        if title and text:
            yield {
                'url': response.url,
                'title': title,
                'text': text_elements
            }


    def parse_article(self, response):
        title = response.css('div:has(h1) > h1::text').get()

        # Extract <p> and <li> elements within <article class="article-body">
        #paragraphs = response.css('article.article-body p')
        #list_items = response.css('article.article-body li')
        text_elements = response.css('article.article-body p, article.article-body h2, article.article-body li')

        # Function to extract text and links from each element
        def extract_text_and_links(elements):
            #data = []
            text_data = []
            refs = []
            for element in elements:
                # Extract text content
                text_content = element.css('::text').getall()
                text = ' '.join(text_content).strip()
                

                # Check if element is <h2> and add extra newline
                if element.root.tag == 'h2':
                    text = f"\n{text}"  # Extra newline before <h2> text

                # Extract all <a> tags and their href attributes
                links = element.css('a::attr(href)').getall()
                
                # Append text and links to the data list
                #data.append({
                #    'text': text,
                #    'links': links
                #})

                text_data.append(text)
                link_str_list = []

                for link in links:
                    if link.strip() == "":
                        continue
                    if "www." not in link:
                        link_str_list.append("https://www.healthline.com" + link.strip())
                    else:
                        link_str_list.append(link.strip())

                refs.append("\n".join(link_str_list))
            
            text_data_str = "\n".join(text_data)
            ref_str = "\n".join(refs)
            # Replace multiple consecutive newlines with a single newline
            ref_str_cleaned = re.sub(r'\n+', '\n', ref_str)

            #self.logger.info(f"Text: {text_data_str}")

            #\\n allows json.loads to operate on this
            return text_data_str, ref_str_cleaned

        # Combine <p> and <li> elements text and links
        #text_data = extract_text_and_links(paragraphs) + extract_text_and_links(list_items)
        text_data, refs = extract_text_and_links(text_elements)

        if title and text_data:
            item =  {
                'url': response.url,
                'title': title,
                'content': text_data,
                'refs': refs
            }

            yield item

            # Write item to a file
            self.write_to_file(item)

    def write_to_file(self, item):
        # Format file content
        file_content = f"Title: {item['title']}\n\n{item['content']}\n\nReferences:\n{item['refs']}"

        # Use article count to ensure unique filename
        filename = f"article{self.article_count}.txt"

        # Define output directory
        output_dir = "articles"
        os.makedirs(output_dir, exist_ok=True)

        # Write to file
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as file:
            file.write(file_content)

        self.logger.info(f"Saved article to {filename}")

        # Increment counter for the next file
        self.article_count += 1


#Get score threshold : https://community.openai.com/t/setting-score-threshold-parameter-for-file-search-tool/1005231
