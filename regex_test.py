import re

regex = re.compile(r'^polls/(?P<buffr_id>.+)/{0,1}(?P<secondary>){0,1}$')

# (|/(?P<relative_url>.+))

possibles = [
'polls/world/optional',
'polls/hello/optional_world/',
'polls/dominic/',
'polls/']

for pos in possibles:
    print pos + ':',
    x = regex.search(pos)
    if x:
        print x.groupdict()
    print
