# simple tests for DropBoxFs

import sys

from fs.dropboxfs import DropBoxFS
    
dropBoxFsConfig = {
    'root':'dropbox'
    ,'path':'/'
    ,'consumer_key':'8px67m'
    ,'consumer_secret':'o61w3o9'
    ,'user_name':'julien@revolunet.com'
    ,'user_password':'aTrP5xAhxS7'
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
print 'ISDIR /various/', c.isdir('/various/')
print 'ISFILE /various/', c.isfile('/various/')

print '[+]', 'makedir test3'
c.makedir('test3')
print c.listdir('/')

print '[+]', 'mv test3 to test4'
c.rename('test3', 'test4')
print c.listdir('/')


print '[+]', 'rm test4'
c.remove('test4')
print c.listdir('/')

print '[+]', 'write to sample222.txt'
f = c.open('sample222.txt', 'w')
f.write('My name is BatMan')
f.close()

print c.listdir('/')

print '[+]', 'read from sample222.txt'
f = c.open('sample222.txt', 'r')
print f.read()
f.close()

print '[+]', 'rm sample222.txt'
c.remove('sample222.txt')
print c.listdir('/')



