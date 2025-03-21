# CDAO-TAKE-HOME

Objective

Design a containerized microservice that:

• Accepts user ID, latitude, and longitude coordinates

• Retrieves weather data from the National Weather Service API

• Performs data enrichment and transformation

• Persists processed data to a database of your choice

    How to run locally ?
    
    1.clone the repo
    2.create virtual environment with command
        pythno3 -m venv venv
        source venv/bin/activate
    3.install the requirements.txt
        pip3 install -r requirements.txt
    4.Give proper env variables and command source .env
    5.Login into influxdb UI ( 127.0.0.1:8086 )and create organisation and buckets from UI, 
        update .env with those
    6.Run both the docker files on 2 seperate terminals
        docker-compose -f docker-compose-flask.yml up --build -d
        docker-compose -f docker-compose-influxdb.yml up --build -d
    7.you can access the API on 127.0.0.1:5000/apidocs

<<<<<<< Updated upstream
**setting up deployment env on AWS ec2:**
=======
1.clone the repo
2.create virtual environment with command
    pythno3 -m venv venv
    source venv/bin/activate
3.install the requirements.txt
    pip3 install -r requirements.txt
4.Give proper env variables and command source .env
5.Login into influxdb UI ( 127.0.0.1:8086 )and create organisation and buckets from UI, 
    update .env with those
6.Run both the docker files on 2 seperate terminals
    docker compose -f docker-compose-flask.yml up --build -d
    docker compose -f docker-compose-influxdb.yml up --build -d
7.you can access the API on 127.0.0.1:5000/apidocs
>>>>>>> Stashed changes

**git installation:**

    sudo yum update -y  
    sudo yum install git -y

**docker installation**

    sudo yum update -y  
    
    sudo yum install docker -y  
    
    sudo service docker start  
    
    sudo systemctl enable docker  
    

**docker-compose installtion:**

    sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
    
    sudo chmod +x /usr/local/bin/docker-compose
    
    docker-compose version
