# grace_shutdown

An example of using signal handling to gracefully shut down pods when they terminate.

Two modules work: the _sender_ queues messages on _RabbitMQ_, the _receiver_ selects messages from the queue.

When deleting a _receiver_, the pod exits gracefully: when the replica set restarts _receiver_, no messages are lost.

_Humio Community Edition_ is used for storing logs.

Usage:
------

Create _Humio_ parser named _clearway_ (_humio/clearway.txt_)

Replace _Humio_ ingest token value in _helm/values.yaml_

    $ minikube start -p grace
    $ kubectl create ns grace
    $ cd docker
    $ ./build_minikube
    $ cd ../helm
    $ helm dependencies build grace
    $ helm install grace grace --namespace grace

To run locally:

    $ cd docker
    $ ./build_local
    $ docker-compose up
