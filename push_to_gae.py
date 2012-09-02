import subprocess
import yaml


subprocess.Popen(
    [
        'C:\\Python27\\pythonw.exe',
        '-u', 'C:\\Program Files (x86)\\Google\\google_appengine\\appcfg.py',
        '--no_cookies',
        u'--email=jack.thatch@gmail.com',
        '--passin',
        'update', u'C:\\Users\\Mause\\Dropbox\\apibuffr'])

subprocess.Popen(['C:\Program Files (x86)\msysgit\msysgit\cmd\git.cmd', 'add', '*'])

with open('app.yaml', 'r') as fh:
    data = yaml.load(fh.read())

subprocess.Popen(['C:\Program Files (x86)\msysgit\msysgit\cmd\git.cmd', 'commit', '-m', '"%s"' % (data['version'])])
