import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, QObject
from CanUtility import Ui_MainWindow  # Import the generated UI class
import can
import random
import threading
import time


class MainWindow(QMainWindow):
    # Define a signal to update the ODO count in the UI
    update_odo_signal = pyqtSignal(int)
    update_engine_signal = pyqtSignal(int)
    update_vehiclespeed_signal = pyqtSignal(int)

    def __init__(self, channel='PCAN_USBBUS1', bitrate=250000):
        super().__init__()
        try:
            self.bus = can.interface.Bus(channel=channel, interface='pcan', bitrate=bitrate)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize CAN bus: {e}")
            sys.exit(1)

        # Initialize variables
        self.current_odo_value = 0
        self.odo_increment_count = 0  
        self.enginespeed_count =0
        self.vehiclespeed_count =0

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setFixedSize(800, 600)

        self.running = False

        # Connect the signal to the slot
        self.update_odo_signal.connect(self.update_odo_display)
        self.update_engine_signal.connect(self.update_engine_display)
        self.update_vehiclespeed_signal.connect(self.update_vehiclespeed_display)

        self.ui.pushButton.clicked.connect(self.start_actions)
        self.ui.pushButton_2.clicked.connect(self.stop_actions)

    def update_odo_display(self, count):
        """Update the ODO increment count in the UI."""
        self.ui.plainTextEdit_3.setPlainText(f'{count}') 

    def update_engine_display(self,count1):
        self.ui.input2.setPlainText(f'{count1}')

    def update_vehiclespeed_display(self,count2):
        self.ui.input1.setPlainText(f'{count2}')


    def start_actions(self):
        """Start the execution of functions based on selected checkboxes."""
        self.running = True
        self.thread = threading.Thread(target=self.perform_actions)
        self.thread.start()

    def stop_actions(self):
        """Stop the execution of functions."""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()  # Wait for the thread to finish

    def perform_actions(self):
        """Run in a separate thread, checking the state of checkboxes and calling corresponding functions."""
        while self.running:
            if self.ui.checkBox.isChecked():
                self.vehicleSpeed_funn()

            if self.ui.checkBox_2.isChecked():
                self.EngineSpeed()

            if self.ui.checkBox_3.isChecked():
                self.odo_funn()

            time.sleep(0.1)  # Delay between checks

    def vehicleSpeed_funn(self):
        """Send vehicle speed CAN message."""
        can_id = 0x18FEF100
        message = can.Message(arbitration_id=can_id, data=[0] * 8, is_extended_id=True)

        VehicleSpeed_int = random.randint(0, 250)
        self.vehiclespeed_count +=1
        message.data[1] = VehicleSpeed_int & 0x00FF  # Set the second byte
        self.update_vehiclespeed_signal.emit(self.vehiclespeed_count)

        try:
            self.bus.send(message)
            print("vehicleSpeed:", VehicleSpeed_int)
        except can.CanError as e:
            print(f"Failed to send vehicle speed message: {e}")

    def EngineSpeed(self):
        """Send engine speed CAN message."""
        can_id = 0x0CF00400
        message = can.Message(arbitration_id=can_id, data=[0] * 8, is_extended_id=True)

        enginespeed = random.uniform(0, 8031.875)
        self.enginespeed_count += 1
        scaled_enginespeed = int(enginespeed * 16)

        self.update_engine_signal.emit(self.enginespeed_count)

        message.data[2] = scaled_enginespeed & 0x00FF  # Set the 3rd byte
        message.data[3] = (scaled_enginespeed >> 8) & 0x00FF  # Set the 4th byte

        try:
            self.bus.send(message)
            print("EngineSpeed:", enginespeed)
        except can.CanError as e:
            print(f"Failed to send engine speed message: {e}")

    def odo_funn(self):
        ODO_can_id = 0x361
        message = can.Message(arbitration_id=ODO_can_id, data=[0] * 8, is_extended_id=False)

        if self.current_odo_value > 1677721500:
            self.current_odo_value = 0
        self.current_odo_value += 5

        self.odo_increment_count += 1

        # Emit the signal to update the ODO count in the UI
        self.update_odo_signal.emit(self.odo_increment_count)

        print('ODO increment count:', self.odo_increment_count)

        message.data[2] = (self.current_odo_value >> 16) & 0xFF  # Byte 2
        message.data[3] = (self.current_odo_value >> 8) & 0xFF   # Byte 3
        message.data[4] = self.current_odo_value & 0xFF          # Byte 4

        try:
            self.bus.send(message)
            print("ODO:", self.current_odo_value)

        except can.CanError as e:
            print(f"Failed to send ODO message: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()  # Show the main window
    sys.exit(app.exec_())  # Start the application event loop
