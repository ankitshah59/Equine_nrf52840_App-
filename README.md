# Equine_nrf52840_App-
Python App to get multi sensor data from multiples devices and real time customizable graphs. The app is intended for collecting real time sensor data from farm horses while being monitored for regular health screening and exercise. The custom made device sends the data for additional ML based approaches.

![alt text](https://github.com/ankitshah59/Equine_nrf52840_App-/blob/a607668a86c7dafb2f1e8e8cfcff7ad525953345/Application%20GUI%20Interface.png)

# 🐎 HORSE SENSOR DESKTOP APP

## Overview
This repository provides a **desktop application** for real-time monitoring of equine physiological signals using **Bluetooth Low Energy (BLE) sensors**. The system was developed as part of the research project:

📄 *"Wearable Smart Textile Band for Continuous Equine Health Monitoring"* 
The application supports:
- Continuous data acquisition from multiple BLE-enabled sensors  
- Real-time visualization of physiological parameters (respiration, cardiac activity, movement)  
- Event logging with timestamped snapshots  
- Adjustable time windowing for signal inspection  
- Data export to `.txt` logs for further analysis  

This work bridges veterinary medicine and biomedical engineering, enabling **wireless, non-invasive, and continuous equine health monitoring** in both clinical and field environments.
<img width="820" height="643" alt="image" src="https://github.com/user-attachments/assets/7b04e53d-198a-4b04-9122-05af213082c5" />

Fig. 1. Overall system design for equine physiological monitoring with enhanced
wearability. (A) Schematic illustration of the smart textile band applied to a horse (scale bar,
20 cm). Insets show close-up images of the sensor-embedded textile band and secure
attachment mechanism on the horse’s chest and abdomen (top right; scale bar, 2 cm), along
with example data visualization of physiological signals transmitted wirelessly (bottom right).
(B) Exploded view and layout of the flexible electronic device. (C) Image of the unfolded
layout of the flexible electronic circuit (scale bar, 2 cm). 
---

## Features
- 📡 **Multi-device BLE connectivity** (up to 3 devices simultaneously)  
- 📊 **Real-time plots** for temperature, audio, and 3-axis accelerometry  
- 🌬️ **Flow sensor integration** for respiratory monitoring (Device 1)  
- 🎤 **Microphone/audio integration** for respiratory acoustics (Device 2)  
- 📝 **Event logging** with customizable triggers  
- 💾 **Data saving** into structured `.txt` logs with timestamps  
- 🖥️ **Cross-platform GUI** built with PyQt5 + PyQtGraph  

---

## Installation

### Prerequisites
- Python 3.8+
- Bluetooth adapter supporting BLE
- OS: Windows, Linux, or macOS

### Required Dependencies
Install using `pip`:
```bash
pip install bleak pyqt5 pyqtgraph qasync
