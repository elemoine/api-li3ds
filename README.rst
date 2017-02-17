LI3DS API
=========

Api for accessing metadata of a li3ds datastore.

1. Create your virtualenv
2. Install dependencies (dev)::

    pip install -e .[dev,doc]

3. Install dependencies (prod)::

    pip install .[prod]

4. (dev) Duplicate the conf/api_li3ds.sample.yml file to conf/api_li3ds.yml and adapt parameters

5. (dev) Launch the application using:

.. code-block::

    python api_li3ds/wsgi.py

6. (dev) Go to https://localhost:5000 and start to play with the API

.. image:: https://raw.githubusercontent.com/LI3DS/api-li3ds/master/screen-api.png
    :align: center
