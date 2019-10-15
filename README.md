
# Broccoli: Brilliantly Recalcitrant Ordinary Computing Cluster for Obviating a Little Iciness

*Yes, I used github's name generator (which spat out potential-broccoli) and then really had to reach for the backronym.*
*Only now I've really leaned into it and the project has roots, stalks and florets...*

So I've built a heater for my living room by collecting some old desktop computers and having them run computationally intensive tasks to generate heat.
I figured I run a lot of optimisation engines to test their performance, and they can either be run in a data centre, which then needs to be cooled as a result, or they can be run in my living room, which needed a little heating anyway.

This repository contains services used to orchestrate the workers as a cluster and keep them configured/up to date with the required software.
Yes I know there are plenty of cluster computing frameworks and configuration managers which I could use ... but this is just for fun ;)

## Hardware Architecture

Each machine in the cluster is running Xen hypervisor.
The worker nodes (3 x old Core2 quad desktops) each have a single paravirtualised ubuntu guest OS using all their resources.
Xen is handy as a middle layer here so I can overwrite/update the guest OS remotely without having to go plug a screen into each machine.

The supervising node (old laptop) also runs Xen, hosting a few small services to control the other nodes and serve code repositories and archives to avoid too much back and forth to the internet (also serves the install script so that the setup command below works).

## Software Architecture

The core component is a worker node service which:
1. Maintains the configuration of the worker (i.e. required software versions installed and configured)
1. Keeps itself in a state requested by the supervisor (i.e. runs a specified service)
1. Reports its current state and usage metrics

## Service Setup

Just run this on the nodes...

    curl -fsSL http://192.168.1.101/source/install-broccoli.sh | bash
