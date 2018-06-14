# /templates Folder

This folder contains all of the Jinja2 templates to be served to the user. All templates should extend `base.hmtl` from the bootstrap module. This is achieved by including:

```
{% extends "bootstrap/base.html" %}
```

at the top of the file. The documentation for Jinja2 can be found [here](http://jinja.pocoo.org/docs/2.10/templates/). It is encouraged for developers to recycle templates in order to reduce the amount of redundant code. This can be achieved similarly to the above example with bootstrap.
