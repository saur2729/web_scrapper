import os
import sys
import re
import requests
import argparse
from bs4 import BeautifulSoup
from pywebcopy import save_webpage
from urllib.parse import urljoin

_cwd = os.getcwd()


def parse_args():
    parser = argparse.ArgumentParser()
    # Adding Arguments
    parser.add_argument('--urls', nargs="*", required=True,
                        help="List of URL's for which we wish to download the html")
    parser.add_argument("--metadata", action="store_true", required=False,
                        help='Also prints the metadata for each URL passed.')
    parser.add_argument("--fetch_all", action="store_true", required=False,
                        help='Also downloads the relevant asset class for the url passed so that we can access webpage locally.')
    parser.add_argument("--output_dir", required=False,
                        default=_cwd, help='Output dir to store the output file. By default it is current dir - [{}]'.format(_cwd))

    args = parser.parse_args()
    return args


def print_metadata(r):
    # Using beautiful soup to find the total number of links and images in the webpage
    soup = BeautifulSoup(r.text, "html.parser")
    total_links = len([link.get('href') for link in soup.find_all('a')])
    total_img = len(soup.find_all('img'))

    print("""
    site: {}
    num_links: {}
    images: {}
    last_fetch: {}
    """.format(r.url, total_links, total_img, r.headers['Date']))


def download_site(args, url):
    if not url.startswith("http"):
        url = "http://" + url

    try:
        r = requests.get(url, timeout=5)  # timeout post 5 seconds
    except Exception as e:
        print("Failed to parse the url {} with below exception - \n {}".format(url, e))

    # continue only if status code is OK -
    if r.status_code != requests.codes.ok:
        print(
            "Got below error while fetching url [{}] - \n{}".format(r.url, r.raise_for_status))
        print("Continue...")
        return

    main_url = url.split("://")[-1]
    html_file_nm = main_url + ".html"
    html_file_path = os.path.join(args.output_dir, html_file_nm)

    # Dumping the html page to the file at Local path
    with open(html_file_path, "wb+") as fp:
        fp.write(r.content)
        print(
            "Successfully dumped the html file at - [{}]".format(html_file_path))

    # print metadata
    if args.metadata:
        print_metadata(r)

    if args.fetch_all:
        fetchall(url)
        return
        # to get the complete webpage -
        download_folder = "/Users/saurabh/curl/web_scrapper/{}".format(
            main_url)
        # kwargs = {'bypass_robots': True, 'project_name': 'sm_nm'}
        save_webpage(url, download_folder)  # , **kwargs)


def savenRename(soup, pagefolder, session, url, tag, inner):
    if not os.path.exists(pagefolder):  # create only once
        print("Creating dir - ", pagefolder)
        os.mkdir(pagefolder)

    for res in soup.findAll(tag):   # images, css, etc..
        if res.has_attr(inner):  # check inner tag (file object) MUST exists
            try:
                filename, ext = os.path.splitext(
                    os.path.basename(res[inner]))  # get name and extension
                # clean special chars from name
                filename = re.sub('\W+', '', filename) + ext
                fileurl = urljoin(url, res.get(inner))
                filepath = os.path.join(pagefolder, filename)
                # rename html ref so can move html and folder of files anywhere
                res[inner] = os.path.join(
                    os.path.basename(pagefolder), filename)
                if not os.path.isfile(filepath):  # was not downloaded
                    with open(filepath, 'wb') as file:
                        filebin = session.get(fileurl)
                        file.write(filebin.content)
            except Exception as exc:
                print(exc, file=sys.stderr)


def fetchall(url, pagepath='/Users/saurabh/curl/web_scrapper/'):
    session = requests.Session()
    # ... whatever other requests config you need here
    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    path, _ = os.path.splitext(pagepath)
    print("Got path - ", path)
    pagefolder = path+'_files'  # page contents folder
    tags_inner = {'img': 'src', 'link': 'href',
                  'script': 'src'}  # tag&inner tags to grab
    for tag, inner in tags_inner.items():  # saves resource files and rename refs
        savenRename(soup, pagefolder, session, url, tag, inner)
    with open(path+'.html', 'wb') as file:  # saves modified html doc
        file.write(soup.prettify('utf-8'))


def main():
    args = parse_args()
    print("The html files will be dumped at - [{}]".format(args.output_dir))
    for url in args.urls:
        print("\nParsing URL - [{}]".format(url))
        download_site(args, url)


if __name__ == '__main__':
    main()
