# simple tests for DropBoxFs
import os
import sys


from fs.dropboxfs import DropBoxFS
    
 

    
dropBoxFsConfig = {
             'root':'dropbox'
            ,'path':'/testcase1'
            ,'consumer_key':'aaadffefz'
            ,'consumer_secret':'zefzgehrh'
            ,'user_name':'julien@revolunet.com'
            ,'user_password':'1234567890'
}

c = DropBoxFS(**dropBoxFsConfig)

print '[+]', 'list /'
print c.listdir('/')

print 'ISDIR /', c.isdir('/')
print 'ISFILE /', c.isfile('/')


print 'FILES ONLY', c.listdir('/', files_only=True)

print '[+]', 'list various'
print c.listdir('various')
print 'ISDIR Public', c.isdir('Public')
print 'ISFILE Public', c.isfile('Public')
print 'ISDIR /various', c.isdir('/various')
print 'ISFILE /various', c.isfile('/various')
print 'ISDIR various', c.isdir('various')
print 'ISFILE various', c.isfile('various')
 
print '[+]', 'makedir test3'
c.makedir('test3')
print c.listdir('/')

print '[+]', 'mv test3 to test4'
c.rename('test3', 'test4')
print c.listdir('/')


print '[+]', 'rm test4'
c.remove('test4')
print c.listdir('/')


def fileReadWriteRemoveTest( c, filePath ):
    print '[++] TEST fileReadWriteRemoveTest', filePath
    print '\t', '[+]', 'write to %s' % filePath
    f = c.open(filePath, 'w')
    f.write('My name is BatMan in %s' % filePath)
    f.close()

    print '\t', c.listdir(os.path.split(filePath)[0])

    print '\t', '[+]', 'read from %s' % filePath
    f = c.open(filePath, 'r')
    print '\t', f.read()
    f.close()

    print '\t', '[+]', 'rm %s' % filePath
    c.remove(filePath)
    
    print '\t', c.listdir(os.path.split(filePath)[0])



fileReadWriteRemoveTest(c, 'testfile1.txt')
fileReadWriteRemoveTest(c, 'testdir/testfile1.txt')
c.remove('testdir')
print '/ contains : ', c.listdir('/')