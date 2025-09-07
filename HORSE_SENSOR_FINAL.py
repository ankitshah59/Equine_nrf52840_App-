import sys
import asyncio
from bleak import BleakScanner, BleakClient
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from qasync import QEventLoop
import time
from datetime import datetime

# BLE device UUIDs
SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

class DeviceSection(QtWidgets.QWidget):
    def __init__(self, device_name, shared_window_length, main_window, sampling_rate_label, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_name = device_name
        self.client = None
        self.file_handle = None
        self.timer = QtCore.QTimer()
        self.timer.setInterval(0)
        self.timer.timeout.connect(self.update_plot)
        self.shared_window_length = shared_window_length
        self.main_window = main_window
        self.sampling_rate_label = sampling_rate_label
        self.first_data_received = False
        self.event_count = 1
        self.last_update_time = time.time()
        self.data_points_received = 0

        # Data dictionary for plotting
        self.data = {
            "time": [],
            "temperature": [],
            "audio": [],
            "x": [],
            "y": [],
            "z": []
        }

        # Plot Widgets
        plot_layout = QtWidgets.QVBoxLayout(self)
        self.plot_widgets = {}

        if self.device_name != "Device 3":  # Exclude full graph set for Device 3
            colors = {"Temperature": (255, 69, 0), "Audio Level": (65, 105, 225), "X": (50, 205, 50), "Y": (148, 0, 211), "Z": (255, 215, 0)}
            y_ranges = {"Temperature": (0, 60), "Audio Level": (-30, 30), "X": (-150, 150), "Y": (-150, 150), "Z": (-150, 150)}

            for label, color in colors.items():
                plot_widget = pg.PlotWidget()
                plot_widget.setBackground("w")
                plot_widget.setYRange(*y_ranges[label])
                plot_widget.setTitle(f"{label}: --")
                pen = pg.mkPen(color=color, width=2)
                self.plot_widgets[label] = plot_widget.plot(pen=pen)
                plot_widget.getAxis("bottom").tickStrings = self.format_time_ticks
                plot_layout.addWidget(plot_widget)

        # Flow Sensor plot (Device 1)
        if self.device_name == "Device 1":
            self.flow_plot = pg.PlotWidget()
            self.flow_plot.setBackground("w")
            self.flow_plot.setYRange(0, 100)
            self.flow_plot.setTitle("Flow Sensor")
            self.flow_line = self.flow_plot.plot(pen=pg.mkPen(color=(255, 140, 0), width=2))
            plot_layout.addWidget(self.flow_plot)

        # Audio plot for Device 2
        if self.device_name == "Device 2":
            self.audio_plot = pg.PlotWidget()
            self.audio_plot.setBackground("w")
            self.audio_plot.setYRange(-20, 20)
            self.audio_plot.setTitle("Audio")
            self.audio_line = self.audio_plot.plot(pen=pg.mkPen(color=(0, 191, 255), width=2))
            plot_layout.addWidget(self.audio_plot)

        # Connect and Disconnect Buttons
        self.connect_button = QtWidgets.QPushButton(f"Connect {device_name}")
        self.apply_button_styles(self.connect_button, background_color="#4CAF50", text_color="white")
        self.connect_button.setEnabled(False)
        self.connect_button.clicked.connect(lambda: asyncio.ensure_future(main_window.scan_and_connect_device(self)))

        self.disconnect_button = QtWidgets.QPushButton(f"Disconnect {device_name}")
        self.apply_button_styles(self.disconnect_button, background_color="#f44336", text_color="white")
        self.disconnect_button.clicked.connect(lambda: asyncio.ensure_future(self.disconnect()))
        self.disconnect_button.setEnabled(False)

        # Save Filename input and button
        self.filename_input = QtWidgets.QLineEdit(f"{device_name}_data_log.txt")
        self.save_filename_button = QtWidgets.QPushButton("Save Filename")
        self.apply_button_styles(self.save_filename_button, background_color="#4CAF50", text_color="white")
        self.save_filename_button.clicked.connect(self.save_filename)

    def apply_button_styles(self, button, background_color, text_color):
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {background_color};
                color: {text_color};
                font-weight: bold;
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:pressed {{
                background-color: dark{background_color};
            }}
            """
        )

    def format_time_ticks(self, values, scale, spacing):
        return [time.strftime("%M:%S", time.gmtime(value)) for value in values]

    def save_filename(self):
        self.filename = self.filename_input.text()
        self.filename_input.setDisabled(True)
        self.save_filename_button.hide()
        self.connect_button.setEnabled(True)
        print(f"Filename '{self.filename}' saved for {self.device_name}.")

    async def connect(self, address):
        self.client = BleakClient(address)
        try:
            await self.client.connect()
            await self.client.start_notify(CHARACTERISTIC_UUID, self.handle_notification)
            self.timer.start()
            print(f"{self.device_name} connected.")
            self.main_window.start_main_timer()
            self.file_handle = open(self.filename, "w")
            self.file_handle.write("Timestamp, Temperature, Audio, X, Y, Z, Event\n")
        except Exception as e:
            print(f"Failed to connect {self.device_name}: {e}")

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.stop_notify(CHARACTERISTIC_UUID)
            await self.client.disconnect()
            self.timer.stop()
            print(f"{self.device_name} disconnected.")
            if self.file_handle:
                self.file_handle.close()
                self.file_handle = None
            self.first_data_received = False
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)

    def handle_notification(self, sender, data):
        if not self.first_data_received:
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.first_data_received = True

        try:
            temperature, audio, x, y, z = map(int, data.decode('utf-8').split(','))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            event_label = "false"
            self.data["time"].append(time.time())
            self.data["temperature"].append(temperature)
            self.data["audio"].append(audio)
            self.data["x"].append(x)
            self.data["y"].append(y)
            self.data["z"].append(z)
            if self.file_handle:
                log_entry = f"{timestamp}, {temperature}, {audio}, {x}, {y}, {z}, {event_label}\n"
                self.file_handle.write(log_entry)
            if self.device_name != "Device 3":
                self.plot_widgets["Temperature"].getViewBox().parentItem().setTitle(f"Temperature: {temperature} °C")
                self.plot_widgets["Audio Level"].getViewBox().parentItem().setTitle(f"Audio Level: {audio}")
                self.plot_widgets["X"].getViewBox().parentItem().setTitle(f"X: {x}")
                self.plot_widgets["Y"].getViewBox().parentItem().setTitle(f"Y: {y}")
                self.plot_widgets["Z"].getViewBox().parentItem().setTitle(f"Z: {z}")
            self.data_points_received += 1
        except ValueError:
            print(f"Malformed data received on {self.device_name}")

    def update_plot(self):
        time_window = self.shared_window_length.value()
        current_time = time.time()
        filtered_indices = [i for i, t in enumerate(self.data["time"]) if current_time - t <= time_window]
        
        if filtered_indices:
            start_idx = filtered_indices[0]
            if self.device_name != "Device 3":
                self.plot_widgets["Temperature"].setData(
                    self.data["time"][start_idx:], self.data["temperature"][start_idx:])
                self.plot_widgets["Audio Level"].setData(
                    self.data["time"][start_idx:], self.data["audio"][start_idx:])
                self.plot_widgets["X"].setData(
                    self.data["time"][start_idx:], self.data["x"][start_idx:])
                self.plot_widgets["Y"].setData(
                    self.data["time"][start_idx:], self.data["y"][start_idx:])
                self.plot_widgets["Z"].setData(
                    self.data["time"][start_idx:], self.data["z"][start_idx:])

        # Update sampling rate display every second
        if current_time - self.last_update_time >= 1.0:
            sampling_rate = self.data_points_received / (current_time - self.last_update_time)
            self.sampling_rate_label.setText(f"{sampling_rate:.2f} Hz")
            self.last_update_time = current_time
            self.data_points_received = 0

    def log_event(self):
        """Log an event snapshot with the current data for this device."""
        if all(len(self.data[key]) > 0 for key in ["temperature", "audio", "x", "y", "z"]):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            event_label = f"event {self.event_count}"
            temperature = self.data["temperature"][-1]
            audio = self.data["audio"][-1]
            x = self.data["x"][-1]
            y = self.data["y"][-1]
            z = self.data["z"][-1]
            if self.file_handle:
                log_entry = f"{timestamp}, {temperature}, {audio}, {x}, {y}, {z}, {event_label}\n"
                self.file_handle.write(log_entry)
            self.event_count += 1
            print(f"{event_label} logged for {self.device_name}")
        else:
            print(f"Insufficient data to log event for {self.device_name}")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HORSE SENSOR DESKTOP APP 🐎")
        self.resize(1400, 800)

        main_layout = QtWidgets.QVBoxLayout()
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        central_widget.setLayout(main_layout)

        # Elapsed Time and Sampling Rate Labels
        self.elapsed_time_label = QtWidgets.QLabel("Elapsed Time: 00:00")
        self.sampling_rate_label1 = QtWidgets.QLabel("Sampling Rate 1: -- Hz")
        self.sampling_rate_label2 = QtWidgets.QLabel("Sampling Rate 2: -- Hz")
        self.sampling_rate_label3 = QtWidgets.QLabel("Sampling Rate 3: -- Hz")
        top_label_layout = QtWidgets.QHBoxLayout()
        top_label_layout.addWidget(self.elapsed_time_label)
        top_label_layout.addWidget(self.sampling_rate_label1)
        top_label_layout.addWidget(self.sampling_rate_label2)
        top_label_layout.addWidget(self.sampling_rate_label3)
        main_layout.addLayout(top_label_layout)

        self.elapsed_time_start = None
        self.elapsed_timer = QtCore.QTimer()
        self.elapsed_timer.timeout.connect(self.update_elapsed_time)

        # Initialize Device Sections
        self.shared_window_length = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.shared_window_length.setMinimum(10)
        self.shared_window_length.setMaximum(60)
        self.shared_window_length.setValue(30)
        self.shared_window_length.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.shared_window_length.setTickInterval(10)
        self.shared_window_length.valueChanged.connect(self.update_window_length_display)

        slider_layout = QtWidgets.QHBoxLayout()
        slider_label = QtWidgets.QLabel("Adjust Window Length (s):")
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.shared_window_length)
        self.window_length_display = QtWidgets.QLabel("30")
        slider_layout.addWidget(self.window_length_display)

        # Initialize Device Sections with individual sampling rate labels
        self.device1 = DeviceSection("Device 1", self.shared_window_length, self, self.sampling_rate_label1)
        self.device2 = DeviceSection("Device 2", self.shared_window_length, self, self.sampling_rate_label2)
        self.device3 = DeviceSection("Device 3", self.shared_window_length, self, self.sampling_rate_label3)

        # Layout for device sections
        top_device_layout = QtWidgets.QHBoxLayout()
        top_device_layout.addWidget(self.device1)
        top_device_layout.addWidget(self.device2)
        top_device_layout.addWidget(self.device3)

        main_layout.addLayout(top_device_layout)

        # Single Event Trigger button for all devices (placed below graphs and above slider)
        self.event_trigger_button = QtWidgets.QPushButton("Global Event Trigger")
        self.event_trigger_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                padding: 8px;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
        """)
        self.event_trigger_button.clicked.connect(self.log_event_for_all)
        main_layout.addWidget(self.event_trigger_button)
        main_layout.addLayout(slider_layout)

        # Arrange Connect and Disconnect buttons below Flow Sensor graph
        connect_disconnect_layout = QtWidgets.QHBoxLayout()
        connect_disconnect_layout.addWidget(self.device1.connect_button)
        connect_disconnect_layout.addWidget(self.device1.disconnect_button)
        connect_disconnect_layout.addWidget(self.device2.connect_button)
        connect_disconnect_layout.addWidget(self.device2.disconnect_button)
        connect_disconnect_layout.addWidget(self.device3.connect_button)
        connect_disconnect_layout.addWidget(self.device3.disconnect_button)
        main_layout.addLayout(connect_disconnect_layout)

        # Arrange Save Filename and input text boxes below Audio graph of Device 3
        save_filename_layout = QtWidgets.QHBoxLayout()
        save_filename_layout.addWidget(self.device1.filename_input)
        save_filename_layout.addWidget(self.device1.save_filename_button)
        save_filename_layout.addWidget(self.device2.filename_input)
        save_filename_layout.addWidget(self.device2.save_filename_button)
        save_filename_layout.addWidget(self.device3.filename_input)
        save_filename_layout.addWidget(self.device3.save_filename_button)
        main_layout.addLayout(save_filename_layout)

    def update_window_length_display(self):
        self.window_length_display.setText(str(self.shared_window_length.value()))

    def start_main_timer(self):
        if not self.elapsed_time_start:
            self.elapsed_time_start = time.time()
            self.elapsed_timer.start(1000)

    def update_elapsed_time(self):
        elapsed_time = int(time.time() - self.elapsed_time_start)
        minutes, seconds = divmod(elapsed_time, 60)
        self.elapsed_time_label.setText(f"Elapsed Time: {minutes:02}:{seconds:02}")

    async def scan_and_connect_device(self, device_section):
        devices = await BleakScanner.discover()
        items = [f"{d.name or 'Unknown'} ({d.address})" for d in devices]
        item, ok = QtWidgets.QInputDialog.getItem(self, f"Select {device_section.device_name}", "Devices:", items, 0, False)

        if ok and item:
            address = item.split("(")[-1].strip(")")
            await device_section.connect(address)

    def log_event_for_all(self):
        """Trigger event logging for all devices."""
        for device in [self.device1, self.device2, self.device3]:
            if device.first_data_received:  # Ensure the device has received data
                device.log_event()
            else:
                print(f"No data received for {device.device_name}; event not logged.")

app = QtWidgets.QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

main_window = MainWindow()
main_window.show()

with loop:
    loop.run_forever()
