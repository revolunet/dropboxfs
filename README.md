DropBoxFs for PyFileSystem
===

Use your DropBox account as a FileSystem with [pyfilesystem][1]

Author : [julien@bouquillon.com][2] ( revolunet )

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
    # read to a file
    print mydropbox.open('README.txt','r').read()
    # write to a file
    mydropbox.open('writeTest.txt', 'w').write('hello, world')



**Links**

 * our [FileBrowser with PyFS backend][2] demo
 * the [PyFileSystem google group][3]

  [1]: http://code.google.com/p/pyfilesystem/
  [2]: mailto:julien@bouquillon.com
  [3]: filebrowser.demo.revolunet.com
  [4]: http://groups.google.com/group/pyfilesystem-discussion/topics


