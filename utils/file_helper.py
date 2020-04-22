def write(filename,content):
    file = open(filename,'w+')
    file.write(content)
    file.close()

def read(filename):
    file = open(filename,'r')
    text = file.readlines()
    content = ''
    for line in text:
        content+=line
    file.close()
    return content
