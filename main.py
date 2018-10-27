import time
import re
import requests
import shutil
import argparse

from urllib.parse import urljoin

from selenium import webdriver


def get_parent(item):
    parent = item
    while parent.tag_name != 'a':
        parent = parent.find_element_by_xpath('parent::*')
    return parent


# Find all links to video pages in a list of modules.
# By video page, I mean a page dedicated to a video, not a direct
# link to the video itself.
def find_video_pages(webelems):
    urls = []
    for elem in webelems:
        module_type = elem.find_element_by_css_selector("strong")
        if module_type is not None:
            if module_type.text.lower().startswith('video'):
                a = elem.find_element_by_tag_name('a')
                url = a.get_attribute('href')
                urls.append(url)
                try:
                    title = elem.find_element_by_class_name('rc-WeekItemName')
                    title = title.text.split('\n')[-1]
                    print('Found {} @ {}'.format(title,url))
                except:
                    pass # title is optional
    return urls

def get_week(browser, week_no, args):
    week_url = urljoin(args.home, 'week/{}'.format(week_no))
    browser.get(week_url)
    time.sleep(2)

    # each module is a video, reading, lecture etc.
    modules = browser.find_elements_by_css_selector('.rc-ModuleLessons li')
    video_pages = find_video_pages(modules)
    for idx, href in enumerate(video_pages):
        browser.get(href)
        time.sleep(1.5)
        download_li   = browser.find_element_by_class_name('rc-LectureDownloadItem')
        download_a    = download_li.find_element_by_tag_name('a')
        download_href = download_a.get_attribute('href')
        print('Downloading {}'.format(download_href))
        r = requests.get(download_href, auth=(args.user, args.password), stream=True)
        if r.status_code == 200:
            with open('week{0:02d}_{1:02d}.mp4'.format(week_no, idx), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
                f.close()

if __name__ == '__main__':
    # login
    parser = argparse.ArgumentParser(description='Scrape a coursera course')
    parser.add_argument('--home', type=str, required=True, help='Home url of the course, e.g., https://www.coursera.org/learn/python-machine-learning/home/')
    parser.add_argument('--user', type=str, required=True, help='Coursera user name')
    parser.add_argument('--password', type=str, required=True, help='Coursera user password')
    parser.add_argument('--chromedriver', type=str, required=False, default='/usr/local/bin/chromedriver', help='Path to the chromedriver executable.')
    args = parser.parse_args()
    if args.home[-1] != '/':
        args.home += '/'

    profile  = webdriver.ChromeOptions()
    browser  = webdriver.Chrome(executable_path=args.chromedriver)
    browser.implicitly_wait(10)
    browser.get(args.home)

    browser.find_element_by_css_selector("input[id^='emailInput']").send_keys(args.user)
    browser.find_element_by_css_selector("input[id^='passwordInput']").send_keys(args.password)
    browser.find_elements_by_xpath('//button')[1].click()

    # course hoome
    time.sleep(3)
    anchors = browser.find_elements_by_tag_name('a')

    # find the final week
    week_links = browser.find_elements_by_css_selector('.rc-WeekCollectionNavigationItem a')
    final_week_url = week_links[-1].get_attribute('href')
    match = re.findall(r"/week/(\d+)", final_week_url)
    final_week = int(match[0])

    for i in range(1, final_week+1):
        get_week(browser, i, args)
        time.sleep(2)

    browser.close()
