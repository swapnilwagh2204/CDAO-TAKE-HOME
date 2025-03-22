# CDAO-TAKE-HOME

Objective
    
    Design a containerized microservice that:
    
    • Accepts user ID, latitude, and longitude coordinates
    
    • Retrieves weather data from the National Weather Service API
    
    • Performs data enrichment and transformation
    
    • Persists processed data to a database of your choice

**Local Deployment ?**
    
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

**Deployment on AWS ec2:**

**1.Spin up the instance**

    Spin up the EC2 instance and save the key-pair at safe place.

    Open following port numbers for the instance to allow traffic
        
        port 22 - SSH
        port 80 - HTTP
        port 5000 - flask endpoint
        port 8086 - influxdb endpoint

    Create .env and add following variables in it.

        # Change these configs:
        
        INFLUXDB_INIT_USERNAME=<username>
        INFLUXDB_INIT_PASSWORD=<password>
        INFLUXDB_INIT_ADMIN_TOKEN=<token>
        INFLUXDB_INIT_ORG=<org>
        INFLUXDB_INIT_BUCKET=<bucket>
            
        # Dont change these configs:
        INFLUXDB_HOST_URL=http://influxdb:8086
        NWS_BASE_URL =https://api.weather.gov
        APP_BASE_URL=http://flask_app:5000

**2.First time environment creation**

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
3.Fork the repo and add following secrets into your own repository.We need to add these 

    #EC2 instance configs:
    
    EC2_HOST
    EC2_SSH_KEY
    EC2_USER
    
    # Change these configs:
    INFLUXDB_INIT_USERNAME=<username>
    INFLUXDB_INIT_PASSWORD=<password>
    INFLUXDB_INIT_ADMIN_TOKEN=<token>
    INFLUXDB_INIT_ORG=<org>
    INFLUXDB_INIT_BUCKET=<bucket>

    # Dont change these configs:
    INFLUXDB_HOST_URL=http://influxdb:8086
    NWS_BASE_URL =https://api.weather.gov
    APP_BASE_URL=http://flask_app:5000

4.Trigger the workflow and the code will be deployed on EC2. 

    Access flask Apis documentation 
        http://<EC2-PUBLIC-IP>:5000/apidocs
        
    Access influx db 
        http://<EC2-PUBLIC-IP>:8086

        Login into influxdb UI with username and password given in .env file.



    
