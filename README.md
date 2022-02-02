# mse_auto_checking_slides_vaganov
#### Running this project:  
```console
$ git clone https://github.com/futurewarning/mse_auto_checking_slides_vaganov.git
$ cd mse_auto_checking_slides_vaganov/
$ docker-compose up --build
```  
After the init build, one can run the dev docker-compose[won't hot reload for the absence of flask debug mode in this app] with
```console
$ docker-compose -f docker-compose-dev.yml up
```
Front-end has be rebuild[on every change made in js] with
```console
$ docker ps
[look up the container_id of mse_auto_checking_slides_vaganov_web_1]
$ docker exec -it <container_id> /bin/sh
$ ./act.sh -b
```
