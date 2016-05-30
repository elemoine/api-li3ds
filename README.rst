LI3DS API
=========

Api for accessing metadata of a li3ds datastore.

1. create your virtualenv
2. Install what you need :

  - dev environnement :

    .. code-block::

        pip install .[dev,doc]

  - prod environnement:

    .. code-block::

        pip install .[prod]


3. (dev) Duplicate the conf/lids_api.sample.yml file to conf/lids_api.yml and adapt parameters

4. (dev) Launch the application using:

  .. code-block::

      python lids_api/wsgi.py

5. (dev) Go to https://localhost:5000 and start to play with the API


