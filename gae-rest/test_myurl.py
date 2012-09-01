""" Unit tests for the urlxutil module
"""
import cgi
import unittest
import myurl

class TestUrlx(unittest.TestCase):

  def _p(ys, ns):
    sq = []
    for y in ys: sq.append((y, y, True))
    for n in ns: sq.append((n, '', False))
    return sq
  # model identifiers to try (must-succeed, then must-fail)
  _models = _p(('Zip', '$Zop'), ('!', '$', ''))
  # ids to try (must-succeed, then must-fail)
  _ids = _p(('12', '34', ''), ('za', 'zi'))
  # method identifiers to try (must-succeed, then must-fail)
  _methods = _p(('foo', 'bar', ''), ('$',))
  # query strings to try (must-succeed, then must-fail)
  _queries = _p(('', '?x=y', '?x=y&x=t'), (',x=y', '?zap'))
  for _i, (_q, _yn, _tf) in enumerate(_queries):
    if _q and _yn and _tf: _queries[_i] = _q, cgi.parse_qsl(_q[1:]), _tf
    else: _queries[_i] = _q, [], _tf
  del _p, _i, _q, _yn, _tf

  def _testalot(self, path_prefix, ignored_prefix):
    if ignored_prefix: urlxutil.set_prefix_ignored(ignored_prefix)
    errors = []
    oks = 0
    for m, em, sm in self._models:
      for i, ei, si in self._ids:
        for e, ee, se in self._methods:
          for q, eq, sq in self._queries:
            if not se: eq=[]
            path = '%s/%s/%s/%s%s' % (path_prefix, m, i, e, q)
            am, ai, ae, aq = myurl.resolve(path)
            if (am, ai, ae, aq) != (em, ei, ee, eq):
              errors.append((path, (em, ei, ee, eq), (am, ai, ae, aq)))
            else:
              oks +=1
    self.assertEquals(errors, [])
    self.assertEquals(oks, 5*5*4*5)

  # RE-pattern prefixes-to-ignore
  _re_prefixes = '/zapp', '/za*pp'
  # URL prefixes to try (must all succeed except last one must fail)
  _url_prefixes = ('/zapp', '/zopp'), ('/zpp', '/zapp', '/zaapp', '/zopp')

  def test_parse_path(self):
    self._testalot('', '')
    for ip, pps in zip(self._re_prefixes, self._url_prefixes):
      for pp in pps:
        self._testalot(pp, ip)


if __name__ == '__main__':
    unittest.main()

