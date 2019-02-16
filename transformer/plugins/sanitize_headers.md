# Sanitizing headers

The [`sanitize_headers` plugin](sanitize_headers.py) should be used for
processing scenarios generated in the Chrome browser, but is also advised to
use it whenever cookies handling is important.

The plugin removes Chrome-specific, RFC-non-compliant headers starting with `:`.

Examples of such headers:
```
:authority: chrome.google.com
:method: POST
:path: /reviews/json/search
:scheme: https
```

Additionally, the plugin:
  - converts header names to lowercase, which simplifies further header overriding,
  - ignores the `cookie` header, as cookies are handled by
  [Locust's _HttpSession_][http-session].

[http-session]: https://docs.locust.io/en/stable/api.html#httpsession-class
