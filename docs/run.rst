
Running
-------

Deep-Framework starting is guided by a CLI procedure. You'll be prompted
to input some information about Deep Framework infrastructure settings
and video analyzing parameters. Deep Framework settings are related to
the cluster configuration (ip address, user, etc. of each of node in the
cluster). Video analyzing parameters are related to video source, max
delay you'll accept to get your results, stats interval generation and
the algorithms you'll want to execute with relative execution mode
(cpu/gpu). You can start this procedure with the following command:

::

    $ python3 main.py

If you want to run Deep-Framework with the last configuration used, type the following:

::

    $ python3 main.py -r

-  Stopping Deep-Framework: 

::

    $ python3 rm_services.py