DropBoxFs for PyFileSystem
===

Use your DropBox account as a FileSystem with [pyfilesystem][1]

Author : [julien@revolunet.com][2]

**example**

    from fs.dropboxfs import DropBoxFS
        
    dropBoxFsConfig = {
        'path':'/'
        ,'consumer_key':'8px67m'
        ,'consumer_secret':'o61w3o9'
        ,'user_name':'julien@revolunet.com'
        ,'user_password':'aTrP5xAhxS7'
    }
    # open a connection
    mydropbox = DropBoxFS(**dropBoxFsConfig)
    # list a dir
    mydropbox.listdir('/')
    # read a file
    print mydropbox.open('README.txt','r').read()
    # write to a file
    mydropbox.open('writeTest.txt', 'w').write('hello, world')



**Links**

 * our [FileBrowser with PyFS backend][3] demo
 * the [PyFileSystem google group][4]

  [1]: http://code.google.com/p/pyfilesystem/
  [2]: mailto:julien@revolunet.com
  [3]: http://filebrowser.demo.revolunet.com
  [4]: http://groups.google.com/group/pyfilesystem-discussion/topics


