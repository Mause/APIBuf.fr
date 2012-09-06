import re


api_path = 'api/v1'
buffr_id_regex = re.compile(
    r'^/%s/(?P<buffr_id>\w+)($|/(?P<relative_url>.+))' % (api_path))


possibles = [
'/api/v1/world_optional/',
'/api/v1/65771f565ed064f98636a0fef8757fde',
'/api/v1/65771f565ed064f98636a0fef8757fde/current',
'polls/']

for pos in possibles:
    print pos + ':',
    match = re.search(buffr_id_regex, pos)
    if match:
        print match.groupdict()
    print
