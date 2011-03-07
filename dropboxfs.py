"""
fs.httpapifs
=========
pyfilesystem wrapper for DropBox API

julien@bouquillon.com

sample config :  {
             'path':'/samples'                      # all operations chrooted to this folder
            ,'consumer_key':'xxxxxx'                # grab theses from dropbox.com developer area
            ,'consumer_secret':'xxxx'
            ,'user_name':'xxxx@revolunet.com'
            ,'user_password':'azertyyy'
        }

dependencies :

dropbox-python-api : https://www.dropbox.com/developers/releases
python-poster
python-oauth

"""
import os
from fs.base import FS
from fs.path import normpath
from fs.errors import ResourceNotFoundError, UnsupportedError
import urlparse 
import urllib2
from urllib import urlencode

import simplejson

import httplib, mimetypes

import StringIO

import dropbox.auth, dropbox.client



import datetime

dropBoxConfig = {
    'root':'dropbox'
    ,'server':'api.dropbox.com'
    ,'content_server':'api-content.dropbox.com'
    ,'port':80
    ,'request_token_url':'https://api.dropbox.com/0/oauth/request_token'
    ,'access_token_url':'https://api.dropbox.com/0/oauth/access_token'
    ,'authorization_url':'https://www.dropbox.com/0/oauth/authorize'
    ,'trusted_access_token_url':'https://api.dropbox.com/0/token'

    }
    
class myStringIO(StringIO.StringIO, object):
    def __init__(self, name, data):
        self.data = data
        super(myStringIO, self).__init__(  self.data )
        self.name = name
        self.closed = False
    def tell(self):
        return len(self.data)
    def seek(self, *args):
        pass
        
        
class _DropBoxFSFile(object):

    """ A file-like that provides access to a file with FileBrowser API"""

    def __init__(self, dropboxfs, path, mode):
        self.dropboxfs = dropboxfs
        self.path = normpath(path)
        self.mode = mode
        self.closed = False
        self.file_size = 0
        #if 'r' in mode or 'a' in mode:
         #   self.file_size = dropboxfs.getsize(path)

    def read(self):
        # read dropboxfile
        resp = self.dropboxfs.dropBoxCommand('get_file', path = self.path)
        return resp.read()
        
    def write(self, data):
        # write dropboxfile
        cfile = myStringIO(self.path, data)
        resp = self.dropboxfs.dropBoxCommand('put_file', path = self.path, data = cfile)
        return (resp.status == 200)

    def close(self):
        self.closed = True        

 
class DropBoxFS(FS):
    
    """Uses the DropBox API to read and write to dropbox via HTTP"""
    
    _meta = { 'network' : True,
              'virtual': False,
              'read_only' : False,
              'unicode_paths' : True,
              'case_insensitive_paths' : False,
              'atomic.move' : True,
              'atomic.copy' : True,              
              'atomic.makedir' : True,
              'atomic.rename' : True,
              'atomic.setcontents' : True,
              'file.read_and_write' : False,
              }
              
    def __init__(self, **kwargs): 
                    
        # base settings
        self.dropBoxConfig = dropBoxConfig
       
        # update with settings
        self.dropBoxConfig.update(  **kwargs )

        self.cache_paths = {}
       
    # def urlopen( self, data, get = {}, headers = {}):
        # if self.username and self.username!='' and self.password and self.password!='':
            # passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            # passman.add_password(None, self.root_url, self.username, self.password)
            # authhandler = urllib2.HTTPBasicAuthHandler(passman)
            # opener = urllib2.build_opener(authhandler)
            # urllib2.install_opener(opener)
        
        # get = get and ('?'+urlencode(get)) or ""
        # r = urllib2.urlopen( urllib2.Request(self.root_url + get, urlencode(data), headers ) )
        # return r
        
    def cacheReset(self):
        self.cache_paths = {}
        
 
    def getsize(self, path):
        item = self.__getNodeInfo( path )
        if item:
            return item.get('size',0)
        return 0

    def _check_path(self, path):
        path = normpath(path)
        base, fname = pathsplit(abspath(path))
        
        dirlist = self._readdir(base)
        if fname and fname not in dirlist:
            raise ResourceNotFoundError(path)
        return dirlist, fname

    def getinfo(self, path, overrideCache = False):
        node = self.__getNodeInfo(path, overrideCache = overrideCache)
        #node['modified_time'] = datetime.datetime.fromtimestamp(node['modified_time'])
        #node['created_time'] = node['modified_time']
        return node

        
    def open(self, path, mode="r"):

        path = normpath(path)
        mode = mode.lower()        
        if self.isdir(path):
            raise ResourceInvalidError(path)        
        if 'a' in mode or '+' in mode:
            raise UnsupportedError('write')
            
        #if 'r' in mode:
            # if not self.isfile(path):
                # raise ResourceNotFoundError(path)
      
        f = _DropBoxFSFile(self, normpath(path), mode) 
      
        return f 
 
    
    def exists(self, path):
        return self.isfile(path) or self.isdir(path)
    
    def isdir(self, path):
        if path==self.dropBoxConfig.get('path', '/'):
            return True
        item = self.__getNodeInfo( path )
        #print item
        if item:
            # attribute may not be present in the JSON for dirs
            return (item.get('is_dir') == True)
        else:
            return False

    
    def isfile(self, path):
        if path==self.dropBoxConfig.get('path', '/'):
            return False
        item = self.__getNodeInfo( path )
        if item:
            return (item.get('is_dir') == False)
        else:
            return False

    def makedir(self, path, recursive=False, allow_recreate=False):
        path = normpath(path)
        if path in ('', '/'):
            return
        # DROPBOX MAKEDIR
        resp = self.dropBoxCommand('file_create_folder', path=path)
        self.refreshDirCache( path )
        return (resp.status==200)
        
        
    def rename(self, src, dst, overwrite=False, chunk_size=16384):
        # if not overwrite and self.exists(dst):
            # raise DestinationExistsError(dst)
        # DROPBOX RENAME
        
        resp = self.dropBoxCommand('file_move', from_path=src, to_path=dst)
        self.refreshDirCache( src )
        self.refreshDirCache( dst )
         
        return (resp.status==200)

    def refreshDirCache(self, path):
        (root1, file) = self.__getBasePath( path )
        # reload cache for dir
        self.listdir(root1, overrideCache=True)

    def removedir(self, path):        
        if not self.isdir(path):
            raise ResourceInvalidError(path)
        return self.remove( path, False )
        
    def remove(self, path, checkFile = True):        
        # DROPBOX DELETE 
        resp = self.dropBoxCommand('file_delete', path=path)
        self.refreshDirCache( path )
        return (resp.status==200)
        
    def __getBasePath(self, path):
        parts = path.split('/')
        root = self.dropBoxConfig.get('path', '/')
        file = path
        if len(parts)>1:
            root += '/'+('/'.join(parts[:-1]))
            file = parts[-1]
        if file == '/': file=''
        if root == '//': root='/'
        return root, file
        
        
    def __getNodeInfo(self, path, overrideCache = False):
        # check if file exists in cached data or fecth target dir
        
        (root, file) = self.__getBasePath( path )
        
        cache = self.cache_paths.get( root )
        # check if in cache
        item = None
        if cache and not overrideCache:
            item = [item for item in cache if item['path']==(root+file)] or None
            if item: 
                item = item[0]
        else:
            # fetch listdir in cache then restart
            res = self.listdir( root )
            if res:
                item = self.__getNodeInfo( path )
        return item
            
    def close(self):
        # for cacheFS   
        pass
        
    def listdir(self, path="/",
                      wildcard=None,
                      full=False,
                      absolute=False,
                      dirs_only=False,
                      files_only=False,
                      overrideCache=False
                      ):
        # if not path.startswith('/'):
            # path=u'/%s' % path
        if not path.startswith('/'):
            path = '/'+path
        if path!=self.dropBoxConfig.get('path') and path.rstrip('/')!=self.dropBoxConfig.get('path'):
            path=self.dropBoxConfig.get('path') + path
        cache = self.cache_paths.get(path)
        if cache and not overrideCache:
            flist = [f['path'][f['path'].rfind('/')+1:] for f in cache]
        else:
            json = self.dropBoxCommand('metadata', path=path)
            flist = []
            if json and json.has_key('contents'):
                d = json['contents']
                if d:
                    self.cache_paths[path] = d
                    flist = [f['path'][f['path'].rfind('/')+1:] for f in d]
                
        alist = self._listdir_helper('/', flist, wildcard, full, absolute, dirs_only, files_only)
        return alist
    
    def getDropBoxClient(self):
        auth = dropbox.auth.Authenticator( self.dropBoxConfig )
        token = auth.obtain_trusted_access_token(self.dropBoxConfig['user_name'], self.dropBoxConfig['user_password'])
        c = dropbox.client.DropboxClient(self.dropBoxConfig['server'], self.dropBoxConfig['content_server'], self.dropBoxConfig['port'], auth, token)
        return c

    def dropBoxPath(self, path):
        root = self.dropBoxConfig['path']
        if path and not path.startswith(root):
            if not root.endswith('/') and not path.startswith('/'):
                root += '/'
            root += path
        return root
        
    def dropBoxCommand(self, cmd, **kwargs):
        if not self.client:
            self.client = self.getDropBoxClient()
        if cmd == 'metadata':
            path =  kwargs.get('path','')         
            resp = self.client.metadata(self.dropBoxConfig['root'], path, list=True, status_in_response=False, callback=None)
            if resp.status==200:
                return simplejson.loads(resp.body)
        elif cmd == 'file_create_folder':
            path = self.dropBoxPath(kwargs.get('path',''))
            #print 'file_create_folder', path
            resp = self.client.file_create_folder(self.dropBoxConfig['root'], path)
            return resp
        elif cmd == 'file_delete':
            path = self.dropBoxPath(kwargs.get('path',''))
            #print 'file_delete', path
            resp = self.client.file_delete(self.dropBoxConfig['root'], path)
            return resp
        elif cmd == 'file_move':
            from_path = self.dropBoxPath(kwargs.get('from_path',''))
            to_path = self.dropBoxPath(kwargs.get('to_path',''))
            #print 'file_move', from_path, to_path
            resp = self.client.file_move(self.dropBoxConfig['root'], from_path, to_path)
            return resp
        elif cmd == 'get_file':
            path = self.dropBoxPath(kwargs.get('path',''))
            #print 'get_file', path
            resp = self.client.get_file(self.dropBoxConfig['root'], path.strip())
            return resp
        elif cmd == 'put_file':
            path = self.dropBoxPath(kwargs.get('path',''))
            #print 'put_file',  os.path.split(path)[0]
            resp = self.client.put_file(self.dropBoxConfig['root'], os.path.split(path)[0], kwargs.get('data'))
            return resp
            
        return None
         