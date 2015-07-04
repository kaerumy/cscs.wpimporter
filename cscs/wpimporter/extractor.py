import BeautifulSoup, json, re
from dateutil.parser import parser as dateparser
import urllib, urllib2
import base64, sys, errno, os
import urlparse

def extract_data(stream):
    unknown_type = []
    soup = BeautifulSoup.BeautifulSoup(stream)
    for item in soup.findAll('item'):
        post_type = getattr(item, 'wp:post_type').text
        if post_type == 'attachment':
            data = extract_attachment(item)
        else:
            data = extract_metadata(item)
        yield (post_type, data)

def extract_attachment(item):
    data = extract_metadata(item)
    attachment_url = getattr(item, 'wp:attachment_url').text.encode('utf-8')

    urlpath = urlparse.urlparse(attachment_url).path
    data['id'] = os.path.basename(urlpath)
    data['path'] = urlpath[1:]
    data['attachment_url'] = attachment_url
    return data

def normalize_title(title):
    cleaned = re.sub('[^A-Za-z0-9 ]+', '', title.lower())
    return '-'.join(cleaned.split())


def unescape(text):
    return text.replace('&amp;', '&')

def extract_metadata(item):
    title = item.title.text
    effective_date = getattr(item, 'wp:post_date').text
    creator = getattr(item, 'dc:creator').text
    description = item.description.text
    bodyText = getattr(item, 'content:encoded').text
    excerpt = getattr(item, 'excerpt:encoded').text
    id_ = getattr(item, 'wp:post_name').text

    if not id_:
        id_ = normalize_title(title)

    review_state = getattr(item, 'wp:status').text
    tags = [unescape(c.text) for c in item.findAll('category')]

    edate = dateparser().parse(effective_date)

    path = '%s/%s/%s' % (edate.year, edate.month, id_)


    data = {
        'title':title,
        'effective_date':effective_date,
        'creator':creator,
        'description':description,
        'bodyText':bodyText,
        'excerpt':excerpt,
        'id':id_,
        'review_state':review_state,
        'tags':tags,
        'path':path
    }

    for meta in item.findAll('wp:postmeta'):
        key = getattr(meta, 'wp:meta_key').text
        value = getattr(meta, 'wp:meta_value').text
        if key == 'author':
            data['author'] = value
        if key == 'ref-url':
            data['remote_url'] = value

    return data

if __name__ == "__main__":
    main()
