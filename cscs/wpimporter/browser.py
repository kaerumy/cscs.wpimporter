from Products.Five import BrowserView
import json
from dateutil.parser import parser as dateparser
import OFS.ObjectManager
from cscs.wpimporter.extractor import extract_data
import urllib2
import transaction
from zope.component import getUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer

class BrokenItemException(Exception):
    def __init__(self, item):
        self.item = item

class ObjectExistException(Exception):
    def __init__(self, item):
        self.item = item

def create_folder(parent, child):
    if parent.has_key(child):
        return parent[child]
    print 'creating folder %s' % '/'.join((parent.getPhysicalPath() + (child,)))
    parent.invokeFactory("Folder", child)
    o = parent[child]
    o.setTitle(child)
    return o

def create_path(parent, paths):
    if not paths:
        return
    newparent = create_folder(parent, paths[0])
    create_path(newparent, paths[1:])

class ImportView(BrowserView):
    def __call__(self):
        path = self.request.get('path')
        broken = {}
        counter = 0
        failcount = 0

        for ptype, p in extract_data(open(path)):
            if p['review_state'] == 'draft':
                continue
            try:
                if ptype == 'page':
                    self.create_page(p)
                elif ptype == 'post':
                    self.create_post(p)
                elif ptype == 'attachment':
                    self.create_attachment(p)
                counter += 1
            except BrokenItemException, e:
                broken.setdefault(ptype, [])
                broken[ptype].append(e.item)
                failcount += 1
            except ObjectExistException, e:
                continue

            if counter % 20 == 0:
                transaction.savepoint(optimistic=True)

        out = json.dumps(broken, indent=4)
        transaction.commit()
        return '%s objects migrated\n%s objects failed\n\n\n%s' % (counter,
                failcount, out)


    def create_page(self, item):
        obj = self.create_obj(item, 'Document', tags=['WP:Page'])
        print 'created %s' % (obj.absolute_url())

    def create_post(self, item):
        obj = self.create_obj(item, 'Document', tags=['WP:Post'])
        print 'created %s' % (obj.absolute_url())

    def create_attachment(self, item):
        obj = self.create_obj(item, 'File', tags=['WP:Attachment'])
        print 'downloading %s' % item['attachment_url']
        try:
            f = urllib2.urlopen(item['attachment_url']).read()
        except urllib2.HTTPError, e:
            raise BrokenItemException(item)

        obj.Schema()['file'].set(obj, f)
        print 'created %s' % (obj.absolute_url())

    def create_obj(self, item, ftype, tags=[]):
        paths = item['path'].split('/')
        if '' in paths:
            paths.remove('')
        create_path(self.context, paths[:-1])
        container = self.context.restrictedTraverse(paths[:-1])
        pageid = paths[-1]

        if not pageid:
            raise BrokenItemException(item)

        if OFS.ObjectManager.bad_id(pageid) is not None:
            normalizer = getUtility(IIDNormalizer)
            pageid = normalizer.normalize(pageid)

        if container.has_key(pageid):
            raise ObjectExistException(item)
        
        container.invokeFactory(ftype, pageid)
        obj = container[pageid]
        self.set_metadata(obj, item, tags)
        return obj

    def set_metadata(self, obj, item, tags=[]):
        schema = obj.Schema()
        schema['title'].set(obj, item['title'])
        if schema.has_key('text'):
            schema['text'].set(obj, item['bodyText'])
        schema['creators'].set(obj, [item['creator']])
        effective_date = dateparser().parse(item['effective_date'])
        schema['effectiveDate'].set(obj, effective_date)
        schema['creation_date'].set(obj, effective_date)
        schema['modification_date'].set(obj, effective_date)
        schema['subject'].set(obj, item['tags'] + tags)
        if item.has_key('remote_url') and schema.has_key('remoteUrl'):
            schema['remoteUrl'].set(obj, item['remote_url'])
        if item.has_key('author'):
            schema['contributors'].set(obj, [item['author']])
        obj.reindexObject()

