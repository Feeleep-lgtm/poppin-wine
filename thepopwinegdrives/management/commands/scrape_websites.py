import asyncio
import logging
import nest_asyncio
from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from langchain_community.document_transformers import BeautifulSoupTransformer
import os
CHROMIUM_PATH = os.getenv("CHROMIUM_PATH", "chromium_path")

# Apply the patch to allow nested asyncio event loops
nest_asyncio.apply()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape websites and process the content'

    def handle(self, *args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.run_until_complete(self.scrape_websites())  # Now we can safely use this
            else:
                loop.run_until_complete(self.scrape_websites())
        except Exception as e:
            logger.error("An error occurred during web scraping", exc_info=True)
            self.stdout.write(self.style.ERROR(f"Failed to scrape websites: {e}"))

    async def scrape_websites(self):
        websites = [
            "https://www.fessparker.com/",
            "https://www.thevalleyprojectwines.com/",
            "https://lalieffwines.com/",
            "https://www.blairfoxcellars.com/",
            "https://paliwineco.com/",
            "https://riverbench.com/",
            "https://www.paradisespringsofsantabarbara.com/",
            "https://melvillewinery.com/",
            "https://www.jwilkes.com/",
            "https://www.margerumwines.com/",
            "https://skyenna.com/",
            "https://www.foleyfoodandwinesociety.com/",
            "https://www.corksandcrowns.com/",
            "https://municipalwinemakers.com/",
            "https://www.sbwinery.com/",
            "https://www.santabarbarawinecollective.com/",
            "https://www.conwayfamilywines.com/",
            "https://www.grassinifamilyvineyards.com/",
            "https://www.happycanyonvineyard.com/",
            "https://aubonclimat.com/",
            "https://jamieslonewines.com/",
            "https://barbieriwines.com/",
            "https://longoriawines.com/",
            "https://frequencywines.com/",
            "https://carrwinery.com/",
            "https://www.kuninwines.com/",
            "https://municipalwinemakers.com/collections/potek-wines",
            "https://foldedhills.com/",
            "https://satellitesb.com/",
            "https://www.aperitivosb.com/",
            "https://www.villawinebar.com/",
            "https://www.silverwines.com/",
            "https://whitcraftwinery.com/",
            "https://www.sanguiswine.com/",
            "https://www.jaffurswine.com/",
            "https://goodlandwineshop.com/",
            "https://www.samsarawine.com/",
            "https://www.brander.com/",
            "https://braveandmaiden.com/",
            "https://www.buttonwoodwinery.com/",
            "https://roblarwinery.com/",
            "https://www.rusack.com/",
            "https://sunstonewinery.com/",
            "https://dovecotewine.com/",
            "https://rideauvineyard.com/",
            "https://www.stolpmanvineyards.com/",
            "https://saarloosandsons.com/",
            "https://www.waylanwine.com/",
            "https://www.carharttfamilywines.com/",
            "https://dragonettecellars.com/",
            "https://www.liquidfarm.com/",
            "https://www.margerumwines.com/",
            "https://www.stormwines.com/",
            "https://refugioranch.com/",
            "https://futureperfectwine.com/",
            "https://www.bygregbrewer.com/",
            "https://www.blairfoxcellars.com/",
            "https://www.fessparker.com/epiphany-tasting-room",
            "https://www.coquelicotwines.com/",
            "https://www.arthurearl.com/",
            "https://www.grimmsbluff.com/",
            "https://holusboluswine.com/",
            "https://www.larnerwine.com/",
            "https://www.babcockwinery.com/",
            "https://lofi-wines.com/",
            "https://www.lumenwines.com/",
            "https://riverbench.com/",
            "https://presquilewine.com/",
            "https://www.crawfordfamilywines.com/",
            "https://www.almarosawinery.com/"
        ]

        print('...scraping websites...')
        try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(executable_path=CHROMIUM_PATH, args=["--no-sandbox"])
                # Continue with your scraping tasks

                # Loop through each website and process it
                html_docs = []
                for url in websites:
                    page = await browser.new_page()
                    await page.goto(url)
                    content = await page.content()
                    html_docs.append(content)
                    await page.close()

                await browser.close()

                # Transform the documents with BeautifulSoupTransformer
                bs_transformer = BeautifulSoupTransformer()
                docs_transformed = bs_transformer.transform_documents(html_docs, tags_to_extract=["p", "li", "div", "a", "span"])

                scraped_documents = []
                for doc in docs_transformed:
                    scraped_documents.append({
                        "page_content": doc.page_content,
                        "metadata": {"source": doc.metadata.get('source', 'unknown website')}
                    })

                print('...finished scraping websites...')
                # Save or process the scraped documents as needed
                logger.info(f"Scraped and processed content from {len(websites)} websites.")
        except Exception as e:
            print('...error scraping websites...')
            logger.error("An error occurred during web scraping", exc_info=True)
            raise
