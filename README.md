 ## Developed to implement assignments for the course - Network Structures and Cloud Computing at Northeastern University

* Refer to the file Network Structures & Cloud Computing.pdf for the problem statement.
* Developed a no-UI web application using Flask and SQLAlchemy, to implement assignments.


# Steps to Run the Project

1. Unzip the project, and open the project in Visual Studio Code (You can download it from here: https://code.visualstudio.com/download)
2. Download the latest version of python from here: https://www.python.org/downloads/)
2. Open the terminal in Visual Studio Code and run the command "pip install -r requirements.txt". This will install all the required libraries and dependencies.
3. Make sure MySQL service is running and you have valid credentials for database.
3. In the file assignments.py, change the value of the database connection credentials to your own database credentials. Set value of db to "assignmentdb" and set the value of user and password to your own database credentials.
4. Run the command "python assignments.py" to start the Flask server.
5. You will need Postman to test and play around with the APIs. The API Suite is available to import to Postman from the "assignments_PostmanCollection.json" file.
