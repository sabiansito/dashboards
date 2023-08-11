# Custom CSE Dashboard for Data Analysis and Visualization

Welcome to the Custom CSE Dashboard repository! This repository hosts a Python-based dashboard built using the Dash framework, designed specifically for data analysis and visualization of Aqueon fits and datasets. 

## Overview
The Custom CSE Dashboard provides a user-friendly interface for exploring and analyzing Aqueon fits and datasets.

## Features
- **Data Analysis**: Perform in-depth analysis on Aqueon fits and datasets using various statistical and visual techniques.
- **Visualization**: Generate insightful visualizations such as charts, graphs, and plots to gain a comprehensive understanding of the data.
- **Interactive Interface**: Interact with the dashboard through a dynamic and responsive user interface, enabling easy exploration and manipulation of data.
- **Customization**: Tailor the dashboard to your specific needs by modifying the code and incorporating additional functionalities.

## Requirements
To run the Custom CSE Dashboard locally, ensure you have the following prerequisites installed:
- Python (version 3.6 or above)
- Dash (version 2.0 or above)
- Additional Python libraries as specified in the `requirements.txt` file.

## Getting Started
To get started with the Custom CSE Dashboard, follow these steps:

1. Clone this repository to your local machine using the following command:

Using HTTPS
```bash
git clone https://github.com/Tachyus/dashboards.git
```

or using SSH

```bash
git clone git@github.com:Tachyus/dashboards.git
```


2. Navigate to the project directory:

```bash
cd dashboards
```

3. Install the required dependencies using the following command:

```bash
pip install -r requirements.txt
```

4. Launch the dashboard application by executing the following command:

- In mac / linux
```bash
python ./app/index.py
```

- In Windows

```powershell
python .\app\index.py
```


5. Open a web browser and visit `http://localhost:8080` or `http://0.0.0.0:8080/` to access the dashboard.

## Running the Docker Image

1. Make sure you have Docker installed on your machine. You can download Docker from the official website: https://www.docker.com/products/docker-desktop

2. Open a terminal or command prompt and navigate to the directory where the `Dockerfile` is located.

Example `Dockerfile`

```dockerfile
FROM python:3.11
WORKDIR /code 
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/
EXPOSE 8080
CMD ["gunicorn","-b","0.0.0.0:8080","index:server"]
```

3. Build the Docker image using the following command:

`docker build -t my-image .`

This will create a Docker image with the tag `my-image`.

This will create a Docker image with the tag `my-image`.

4. Set the required environment variables using the following command:

```bash
export API_ORIGINATOR=${API_ORIGINATOR}
export API_CUSTOMER=${API_CUSTOMER}
export API_URL=${API_URL}
export API_KEY=${API_KEY}
```

5. Run the Docker image using the following command:

```bash
docker run -p 8080:8080 -e API_ORIGINATOR=API_ORIGINAOR -e API_CUSTOMER=API_CUSTOMER -e API_URL=API_URL -e API_KEY=API_KEY

```


This will start a Docker container and map port 8080 in the container to port 8080 on your machine. The `-e` option is used to pass the environment variable to the container.

1. Open a web browser and visit `http://localhost:8080` or `http://0.0.0.0:8080/` to access the dashboard.

2. To stop the Docker container, press `Ctrl+C` in the terminal or command prompt where the container is running.

## Using Docker Compose

If you prefer to use Docker Compose to manage your containers, you can use the included `docker-compose.yml` file.

1. Make sure you have Docker and Docker Compose installed on your machine. You can download Docker from the official website: https://www.docker.com/products/docker-desktop and Docker Compose from the official website: https://docs.docker.com/compose/install/

2. Open a terminal or command prompt and navigate to the directory where the `docker-compose.yml` file is located.

3. Set the required environment variables by creating a `.env` file in the same directory as the `docker-compose.yml` file. The `.env` file should contain one environment variable per line in the format `VAR=value`.

4. Start the containers using the following command:

`docker-compose up`


This will start the containers defined in the `docker-compose.yml` file.

5. Open a web browser and visit `http://localhost:8080` or `http://0.0.0.0:8080/` to access the dashboard.

6. To stop the containers, press `Ctrl+C` in the terminal or command prompt where the containers are running. You can also use the following command:

`docker-compose down`


This will stop and remove the containers defined in the `docker-compose.yml` file.

Example of Docker-compose file:

```dockerfile
version: "3.9"
services:
  dashboard:
    image: dashboard:v0.0.1
    env_file:
      - .env
    environment:
      - API_ORIGINATOR=${API_ORIGINATOR}
      - API_CUSTOMER=${API_CUSTOMER}
      - API_URL=${API_URL}
      - API_KEY=${API_KEY}
    ports:
      - 2751:8080

```


## Contributing
We welcome contributions from the Tachyus team. If you encounter any issues or have suggestions for improvements, please submit them via GitHub issues. Moreover, feel free to fork this repository and submit pull requests for any new features or bug fixes you'd like to contribute.

### Dashboard Pages
The Custom CSE Dashboard is based on individual pages contained in the ./app/pages folder. Each file in this folder represents a separate dashboard page and will be displayed as a new URL path.

To add a new page to the dashboard, follow these steps:

1. Create a new Python file in the ./app/pages folder.
2. Define the layout and functionality of the page using Dash components and callbacks.
3. Save the file with an appropriate name representing the page's content.
   
For example, if you create a file named custom_page.py in the ./app/pages folder, the corresponding URL path to access that page would be 0.0.0.0:8080/custom-page (assuming the dashboard is running locally on port 8080).

You can customize the pages and their URLs as per your requirements, enabling you to create a tailored and comprehensive dashboard experience.

We look forward to your contributions in expanding the functionality and content of the Custom CSE Dashboard!

Feel free to modify this section or add more details based on your specific requirements.