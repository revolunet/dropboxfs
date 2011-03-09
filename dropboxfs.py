"""
fs.dropboxfs
=========
PyFilesystem wrapper for DropBox API

julien@bouquillon.com - http://github.com/revolunet/dropboxfs

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
    # simple wrapper due to DropBox that need a 'physical' file
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

    def __init__(self, dropboxfs, path, mode = 'r'):
        if not path.startswith('/'):
            path = u'/%s' % path
        self.dropboxfs = dropboxfs
        self.path = path
        self.mode = mode
        self.closed = False
        self.file_size = 0
        #if 'r' in mode or 'a' in mode:
         #   self.file_size = dropboxfs.getsize(path)
         
    def getCacheDir(self, dir = False):
        if dir:
            return self.path
        root = os.path.split(self.path)[0]
        if root == '':
            root = '/'
        return root
        
    def getFullPath(self):
        return self.dropboxfs.getDropBoxFullPath( self.path )

    def read(self):
        # read dropboxfile
        if self.dropboxfs.isfile(self.path):
            resp = self.dropboxfs.dropBoxCommand('get_file', path = self.path)
            return resp.read()
        else:
            return False
        
    def write(self, data):
        # write to dropbox
        cfile = myStringIO(self.path, data)
        resp = self.dropboxfs.dropBoxCommand('put_file', path = self.path, data = cfile)
        self.dropboxfs.refreshDirCache( os.path.split(self.path)[0] )
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
        self.config = dropBoxConfig
        self.client = None
        
        # cache folder infos
        self.cache_paths = {}
        
        # update with settings
        self.config.update(  **kwargs )

 
    def getsize(self, path):
        item = self.__getNodeInfo( path )
        if item:
            return item.get('size',0)
        return 0

    def _check_path(self, path):
        path = (path)
        base, fname = pathsplit(abspath(path))
        
        dirlist = self._readdir(base)
        if fname and fname not in dirlist:
            raise ResourceNotFoundError(path)
        return dirlist, fname

    def getinfo(self, path, overrideCache = False):
        node = self.__getNodeInfo(path, overrideCache = overrideCache)
        return node

        
    def open(self, path, mode="r"):

        path = (path)
        mode = mode.lower()        
        if self.isdir(path):
            raise ResourceInvalidError(path)        
        if 'a' in mode or '+' in mode:
            raise UnsupportedError('write')
            
        #if 'r' in mode:
            # if not self.isfile(path):
                # raise ResourceNotFoundError(path)
      
        f = _DropBoxFSFile(self, (path), mode) 
      
        return f 
 
    
    def exists(self, path):
        return self.isfile(path) or self.isdir(path)
    
    def isdir(self, path):
        if path in ['', '/']:
            return True
        item = self.__getNodeInfo( path )
        if item:
            # attribute may not be present in the JSON for dirs
            return (item.get('is_dir') == True)
        else:
            return False

    
    def isfile(self, path):
        if path in ['', '/']:
            return False
        item = self.__getNodeInfo( path )
        if item:
            return (item.get('is_dir') == False)
        else:
            return False

    def makedir(self, path, recursive=False, allow_recreate=False):
        if path in ('', '/'):
            return
        resp = self.dropBoxCommand('file_create_folder', path=path)
        self.refreshDirCache( os.path.split(path)[0] )
        return (resp.status==200)
        
        
    def rename(self, src, dst, overwrite=False, chunk_size=16384):
        # if not overwrite and self.exists(dst):
            # raise DestinationExistsError(dst)
        resp = self.dropBoxCommand('file_move', from_path=src, to_path=dst)
        self.refreshDirCache( os.path.split(src)[0] )
        self.refreshDirCache( os.path.split(dst)[0] )
         
        return (resp.status==200)

    def refreshDirCache(self, path):
        # reload cache for dir
        self.listdir(path, overrideCache=True)

    def removedir(self, path):        
        if not self.isdir(path):
            raise ResourceInvalidError(path)
        return self.remove( path, False )
        
    def remove(self, path, checkFile = True):        
        # DROPBOX DELETE 
        resp = self.dropBoxCommand('file_delete', path=path)
        self.refreshDirCache( os.path.split(path)[0] )
        return (resp.status==200)
 
    def __getNodeInfo(self, path, overrideCache = False):
        # check if file exists in cached data or fecth target dir
        f = _DropBoxFSFile(self, path)
        cachedir = f.getCacheDir()
        fpath = f.getFullPath()
        # check if in cache
        cache = self.cache_paths.get( cachedir )
        item = None
        if cache and not overrideCache:
            item = [item for item in cache if item['path']==fpath] or None
            if item: 
                item = item[0]
        else:
            # fetch listdir in cache then restart
            res = self.listdir( cachedir )
            if res:
                item = self.__getNodeInfo( path )
                pass
        return item
            
 
        
    def listdir(self, path="/",
                      wildcard=None,
                      full=False,
                      absolute=False,
                      dirs_only=False,
                      files_only=False,
                      overrideCache=False
                      ):
        if not path.startswith('/'):
            path=u'/%s' % path
             
        f = _DropBoxFSFile(self, path)
        cachedir = f.getCacheDir(dir=True)
 
        root = self.config.get('path', '/')
   
        fdir = self.getDropBoxFullPath(path)

        cache = self.cache_paths.get( cachedir )
        if cache and not overrideCache:
            flist = [f['path'][f['path'].rfind('/')+1:] for f in cache]
        else:
            json = self.dropBoxCommand('metadata', path=path )
            flist = []
            if json and json.has_key('contents'):
                d = json['contents']
                self.cache_paths[cachedir] = d
                flist = [f['path'][f['path'].rfind('/')+1:] for f in d]

        alist = self._listdir_helper('/', flist, wildcard, full, absolute, dirs_only, files_only)
        return alist
    
    def getDropBoxClient(self):
        auth = dropbox.auth.Authenticator( self.config )
        token = auth.obtain_trusted_access_token(self.config['user_name'], self.config['user_password'])
        c = dropbox.client.DropboxClient(self.config['server'], self.config['content_server'], self.config['port'], auth, token)
        return c
 
        
    def getDropBoxFullPath(self, inPath):
        path = self.config['path']

        if inPath not in ['/','']:
            if path == '/':
                path=''
            p = inPath
            if not p.startswith('/'):
                p = '/%s' % p
            path += p
        return path
        
    def dropBoxCommand(self, cmd, **kwargs):
        path = self.getDropBoxFullPath( kwargs.get('path','') ) 
 
        if not self.client:
            self.client = self.getDropBoxClient()
        if cmd == 'metadata':
            #print 'metadata', path
            resp = self.client.metadata(self.config['root'], path, list=True, status_in_response=False, callback=None)
            if resp.status==200:
                return simplejson.loads(resp.body)
        elif cmd == 'file_create_folder':
            #print 'file_create_folder', path
            resp = self.client.file_create_folder(self.config['root'], path)
            return resp
        elif cmd == 'file_delete':
            #print 'file_delete', path
            resp = self.client.file_delete(self.config['root'], path)
            return resp
        elif cmd == 'file_move':
            from_path = self.getDropBoxFullPath( kwargs.get('from_path','') ) 
            to_path = self.getDropBoxFullPath( kwargs.get('to_path','') ) 
            #print 'file_move', from_path, to_path
            resp = self.client.file_move(self.config['root'], from_path, to_path)
            return resp
        elif cmd == 'get_file':
            #print 'get_file', path
            resp = self.client.get_file(self.config['root'], path)
            return resp
        elif cmd == 'put_file':
            #print 'put_file', os.path.split(path)[0]
            resp = self.client.put_file(self.config['root'], os.path.split(path)[0], kwargs.get('data'))
            return resp
            
        return None
         