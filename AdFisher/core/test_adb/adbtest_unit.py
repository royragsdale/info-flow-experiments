import logging
import datetime
import os
import urllib

# imports to use selenium
import selenium
from selenium import webdriver
from xvfbwrapper import Xvfb    # artificial display for headless experiments

# imports to parse easylist
from adblockparser import AdblockRules
from adblockparser import AdblockRule

# imports to save screen shots
from PIL import Image
import StringIO
import base64

class AdbTestUnit:

    def _load_easy_list(self):
        with open('easylist.txt') as f:
            lines = f.read().splitlines()
        logging.info("Loaded easy list: {} items".format(len(lines)))
        return lines


    def __init__(self,headless=False,easyList=True):
        if headless:
            self.vdisplay = Xvfb(width=1280, height=720)
            self.vdisplay.start()

        self.driver = webdriver.Firefox()
        self.session = self.driver.session_id
        print("Running session: {}".format(self.session))

        self.log_dir = os.path.join(os.getcwd(),"log_"+self.session)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        logging.basicConfig(filename=os.path.join(self.log_dir,'log.adbtest_unit.txt'),level=logging.INFO)
        if easyList:
            self.rules = AdblockRules(self._load_easy_list())
            self.all_options = {opt:True for opt in AdblockRule.BINARY_OPTIONS}
        else:
            logging.info("skipping easy list")

    def visit_url(self,url):
        driver = self.driver
        logging.info("Trying: {}".format(url))
        driver.get(url)
        logging.info("Visited: {}".format(url))
        self.screenshot = self.screenshot_page()
    
    def screenshot_page(self):
        # uses PIL library to open image in memory
        driver = self.driver
        b64_shot = driver.get_screenshot_as_base64()
        decode  = base64.decodestring(b64_shot)
        s = StringIO.StringIO(decode)
        img = Image.open(s)
        return img

    def log_element(self,element,source):
        url = element.get_attribute(source)
        html = element.get_attribute('outerHTML').encode('utf-8')
        tag = element.tag_name
        logging.info("Ad:{}:{}:{}".format(self.session, element.id,url))
        logging.info("Ad:Contents:{}:{}:{}".format(self.session, element.id, html))

        try:
            if tag == "img":
                urllib.urlretrieve(url, os.path.join(self.log_dir,"image_"+str(element.id)))
            elif tag == "a":
                a_img =  element.get_attribute("img")
                if a_img != None:
                    urllib.urlretrieve(url, os.path.join(self.log_dir,"a_image_"+str(element.id)))
            elif tag == "iframe":
                self.screen_shot_element(element)
        except:
            logging.error("Collecting enhanced contents:{}:{}:{}".format(self.session,element.id,tag))


    def check_elements(self, elements, source="href", options=None):
        count = 0
        for e in elements:
            try:
                url = e.get_attribute(source)
                logging.info("Checking:{}:{}".format(source, url))
                if self.rules.should_block(url, options):
                    self.log_element(e,source)

                    count+=1
            except selenium.common.exceptions.StaleElementReferenceException as e:
                logging.error(e)
        return count

    def find_href_ads(self):
        driver = self.driver
        elements = driver.find_elements_by_xpath("//*[@href]")
        count = self.check_elements(elements,"href", self.all_options)
        print "href search found: {}".format(count)
    

    def find_src_ads(self):
        driver = self.driver
        elements = driver.find_elements_by_xpath("//*[@src]")
        count = self.check_elements(elements, "src", self.all_options)
        print "src search found: {}".format(count)

    def screen_shot_element(self, element):

        location = element.location
        size = element.size
        
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']


        if left == 0 or top == 0 or right == 0 or bottom == 0  or size['width'] == 0 or size['height'] ==0:
            logging.error("screen_shot_element:{}:{}:({},{} by {},{})".format(self.session,element.id,left,top,right,bottom))
            return
        
        try:
            img = img.crop((left, top, right, bottom)) # defines crop points
            img.save(os.path.join(self.log_dir,'iframe_'+str(element.id)+'.png')) # saves new cropped image
        except:
            logging.error("clipping screenshot:{}:{}".format(self.session,element.id))


def treat_cmd(browser, cmd):
    if cmd[0] == "visit":
        if len(cmd) < 2:
            print "Incomplete command"
            return
        if cmd[1] == "cnn":
            url = "http://www.cnn.com/"
        elif cmd[1] == "bbc":
            url = "http://www.bbc.com/"
        elif cmd[1] == "fox":
            url = "http://www.foxnews.com/"
        elif cmd[1] == "href":
            if len(cmd) < 3:
                print "Please specify an address"
                return
            url = cmd[2]
        else:
            print "Unknown address shortcut - Type visit href url to specify another address"
            return
        print "Visiting {}".format(url)
        browser.visit_url(url)
    elif cmd[0] == "collect":
        if len(cmd) < 2:
            print "Incomplete command"
            return
        if cmd[1] == "href":
            print "Collecting href ads"
            browser.find_href_ads()
        elif cmd[1] == "src":
            print "Collecting src ads"
            browser.find_src_ads()
        else:
            print "Collecting {} ads".format(cmd[1])
            browser.check_tag(cmd[1])
    elif cmd[0] == "check":
        if len(cmd) < 2:
            print "Incomplete command"
            return
        source = "href"
        options = {}
        if len(cmd) > 2:
            source = cmd[2]
        if len(cmd) > 3:
            for opt in cmd[3].split(","):
                opt = opt.split(":")
                options[opt[0]] = len(opt) == 1 or opt[1] == "True"
        print "Checking {} from source {} with options {} for ads".format(cmd[1], source, str(options))
        print "\t -> {}".format(browser.check_block(url=cmd[1], source=source, options=options))
    elif cmd[0] == "read":
        if len(cmd) < 2:
            print "Incomplete command"
            return
        with open(cmd[1]) as f:
            lines = f.read().splitlines()
            for line in lines:
                treat_cmd(browser, line.split())
    else:
        print "Unknown command"
            

if __name__ == "__main__":
    browser = AdbTestUnit(headless=False)
    print "Browser ready - Enter commands"
    line = ""
    try:
        while line != "quit":
            cmd = line.split()
            if len(cmd) > 1:
                treat_cmd(browser, cmd)
            line = raw_input("adbtest: ")
        print "Received quit command. Exiting..."
    finally:
        browser.driver.quit()


