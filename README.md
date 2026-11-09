# Anti-Theft Electricity Monitoring System

## Project Overview

The **Anti-Theft Electricity Monitoring System** is an IoT-based project designed to detect electricity theft and monitor power consumption in real time. The system uses an ESP32 microcontroller and two Current Transformer (CT) sensors to measure incoming and outgoing current.

By comparing the current values, the system identifies abnormal differences that may indicate electricity theft, such as illegal line tapping, meter bypassing, or unauthorized power usage.

The collected sensor data is processed through a Flask-based backend and stored in a PostgreSQL database. A web-based dashboard displays live readings, electricity theft alerts, consumer information, and monitoring results.

## Objectives

- Detect electricity theft in real time.
- Monitor incoming and outgoing current.
- Identify abnormal current differences.
- Generate alerts when suspicious activity is detected.
- Store electricity monitoring data for future analysis.
- Provide a user-friendly dashboard for monitoring.
- Reduce manual inspection and electricity losses.

## Problem Statement

Electricity theft through illegal connections, meter bypassing, and meter tampering causes financial losses to electricity distribution companies. Traditional inspection methods require manual monitoring and may not identify theft immediately.

This project addresses these problems by introducing an IoT-based monitoring system that continuously measures electricity flow and detects suspicious differences between incoming and outgoing current.

## Proposed System

The proposed system uses two CT sensors connected to an ESP32 microcontroller. One sensor measures the incoming current, while the other measures the outgoing current.

The ESP32 sends the collected readings to a Flask REST API. The backend processes the readings, stores the information in a PostgreSQL database, and identifies possible electricity theft.

The monitoring dashboard displays sensor readings, consumer details, charts, and alerts.

## Key Features

- Real-time electricity current monitoring.
- Incoming and outgoing current comparison.
- Automatic electricity theft detection.
- ESP32-based IoT integration.
- Flask REST API backend.
- PostgreSQL database integration.
- Web-based monitoring dashboard.
- Consumer management (CRUD operations).
- Theft alert management.
- Data visualization using Chart.js.
- CSV batch analysis.
- Machine learning-based prediction using Random Forest.
- Background sensor data simulation.

## Technologies Used

### Hardware
- ESP32 Microcontroller
- Current Transformer (CT) Sensors
- Buzzer
- LED
- Connecting Wires
- Power Supply

### Software
- Python
- Flask
- PostgreSQL
- HTML
- CSS
- JavaScript
- Chart.js
- Machine Learning (Random Forest)
- Arduino IDE

## System Architecture

1. **Current Measurement:** Two CT sensors measure incoming and outgoing current.
2. **Data Collection:** ESP32 collects the sensor readings.
3. **Data Transmission:** Sensor readings are transmitted to the Flask REST API.
4. **Data Processing:** The backend compares the current readings.
5. **Theft Detection:** Abnormal current differences are identified.
6. **Database Storage:** Readings and alerts are stored in PostgreSQL.
7. **Dashboard Monitoring:** The dashboard displays readings, charts, and alerts.

## Working Principle

The system continuously monitors the difference between incoming and outgoing current.

**Theft Detection Formula:**

`Current Difference = |Incoming Current - Outgoing Current|`

If the current difference exceeds the configured threshold, the system identifies the reading as suspicious and generates an alert.

**Default Threshold:** 2.0 A

The threshold can be adjusted according to the sensor calibration and project requirements.

## Hardware Pin Configuration

| Component | ESP32 GPIO Pin |
|---|---|
| CT Sensor 1 | GPIO 34 |
| CT Sensor 2 | GPIO 35 |
| Buzzer | GPIO 25 |
| Status LED | GPIO 2 |

## Machine Learning

The project includes a Random Forest machine learning model to support electricity theft prediction.

The model analyzes relevant electricity monitoring data and helps classify suspicious readings.

Model performance should be reported using results obtained from actual testing and evaluation.

## Dashboard Modules

- **Dashboard:** Displays overall monitoring information.
- **Live Monitoring:** Shows incoming and outgoing current readings.
- **Consumer Management:** Allows consumer information to be added, viewed, updated, and deleted.
- **Alert Center:** Displays detected suspicious activities.
- **Data Visualization:** Displays monitoring information through charts.
- **Batch Analysis:** Supports CSV-based data analysis.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/login` | User login |
| GET | `/api/dashboard/stats` | Dashboard statistics |
| GET | `/api/dashboard/chart-data` | Chart data |
| GET | `/api/consumers` | View consumers |
| POST | `/api/consumers` | Add a consumer |
| POST | `/api/sensor/data` | Receive sensor readings |
| GET | `/api/sensor/live` | Get live sensor data |
| POST | `/api/predict/single` | Predict a single reading |
| POST | `/api/predict/batch` | Perform batch prediction |
| GET | `/api/alerts` | View theft alerts |

## Installation and Setup

### Prerequisites

Install the following software:

- Python 3.x
- PostgreSQL
- Arduino IDE
- Git
- Visual Studio Code (recommended)

### Step 1: Download the Project

Download the project source code from this repository using GitHub's **Code → Download ZIP** option.

### Step 2: Open the Project

Extract the downloaded ZIP file and open the project folder in Visual Studio Code.

### Step 3: Install Dependencies

Open the terminal in the project directory and install the required Python packages:

```bash
pip install flask psycopg2-binary pandas scikit-learn
```

Install any additional packages listed in your project's `requirements.txt`, if available:

```bash
pip install -r requirements.txt
```

### Step 4: Configure the Database

Create a PostgreSQL database and configure the database connection details in your project.

Do not upload database passwords or secret credentials to GitHub.

### Step 5: Run the Application

Run the Flask application using the project's main Python file. For example:

```bash
python app.py
```

The dashboard can be accessed locally at:

`http://localhost:5000`

**Note:** The actual startup command may differ depending on your project files.

## ESP32 Setup

1. Open Arduino IDE.
2. Open `ESP32/anti_theft_monitor.ino`.
3. Select the appropriate ESP32 board.
4. Select the correct COM port.
5. Configure the Wi-Fi and API connection settings.
6. Upload the program to the ESP32.
7. Connect the CT sensors and output components according to the circuit configuration.

## Expected Results

- Continuous monitoring of incoming and outgoing current.
- Identification of abnormal current differences.
- Generation of electricity theft alerts.
- Visualization of sensor readings on the dashboard.
- Storage of monitoring information for further analysis.

## Advantages

- Real-time electricity monitoring.
- Automatic theft detection.
- Reduced manual inspection.
- Improved monitoring accuracy.
- Centralized consumer information.
- Historical data analysis.
- Expandable IoT-based architecture.

## Future Enhancements

- Mobile application integration.
- SMS and email notifications.
- GPS-based location tracking.
- Cloud-based monitoring.
- Improved machine learning models.
- Advanced electricity consumption analytics.

## Applications

- Residential electricity monitoring.
- Commercial electricity monitoring.
- Industrial power distribution.
- Electricity distribution companies.
- Smart grid monitoring systems.

## Conclusion

The Anti-Theft Electricity Monitoring System provides an IoT-based approach to identifying suspicious electricity usage. By combining ESP32, CT sensors, Flask, PostgreSQL, machine learning, and a web dashboard, the project supports continuous monitoring and faster detection of possible electricity theft.

---

**Project Title:** Anti-Theft Electricity Monitoring System

**Domain:** Internet of Things (IoT), Machine Learning, Web Development

**Microcontroller:** ESP32

**Backend:** Python Flask

**Database:** PostgreSQL