# Sanitizing headers

The [`sanitize_headers` plugin](sanitize_headers.py) should be used for processing scenarios that were generated 
in the Chrome browser, but is advised to be used whenever cookies handling is important.
 
The plugin removes Chrome-specific, RFC non-compliant headers starting with ":". 

Example of such headers:
```
:authority: chrome.google.com
:method: POST
:path: /reviews/json/search
:scheme: https
```

Additionally the plugin:
- maps header keys to lowercase, which makes further overriding of headers deterministic,
- ignores the `cookie` header, as cookies are handled by [Locust's `HttpSession`][http-session].

[http-session]: https://docs.locust.io/en/stable/api.html#httpsession-class