# Store Service

## Introduction

This is a store service that uses DynamoDB to store its content, and using Redis to cache those contents. You need to download DynamoDB version for it to work, https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html. Just follow the instructions below to start the DynamoDB (Make sure you write "-sharedDb" beside the startup command). After downloading the DynamoDB, remember to populate the database with the node JS application that I send to you (I will be preparing a bash script when I have the time), remember to ask from me if you have not receive it.

You will also have to install Redis using WSL (Using Ubuntu terminal should be fine, do not use windows powershell or command terminal). Again follow the instructions below on starting up the Redis locally.https://redis.io/

## Instructions

### Installing dynamodb

- Install local version of dynamodb from this link https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html and place it in a directory that is convenient for you.

- Extract the zip folder. Once it is done, you should be able to see "DynamoDBLocal_lib" folder and DynamoDBLocal.jar file

- Open up your terminal, and cd to the place where you found the DynamoDBLocal.jar file.

- Run this command to start the DynamoDB: **java -D"java.library.path=./DynamoDBLocal_lib" -jar DynamoDBLocal.jar -sharedDb**


## Creating tables and populating items in DynamoDB
Go to https://gitlab.com/is458-t5/dynamodb_start, read the instructions there to create tables and inserting items for the store service

### Installing Redis

- Make sure you have WSL2 install if you are using Windows. This instruction assume you are running Ubuntu terminal 

- Run each of the commands below:
    - **curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg**
    - **echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list**
    - **sudo apt-get update**
    - **sudo apt-get install redis**
- Lastly, start the Redis server using either **sudo service redis-server start** or **redis-server**

### Running this application 
Before running this service, please remember to setup the python virtual environment. And install the required modules listed on **"requirements.txt"** with this command: **"pip install -r requirements.txt"**. Visit "http://localhost:5000/view/book or stationery or file" to look at items. Visit "http://localhost:5000/home" to view the home page, the cart page can be click to view cart items.