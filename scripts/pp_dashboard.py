"""
This program is to validate the communication between
Media Player (MP) and User Interface(UI).

requirement:    MP send the temperature and UI will response as below.
                If temperature is above threshold value, then UI respond as HIGH.
                If temperature is equal or below threshold value, then UI respond as
                    Back to NORMAL.
                Once UI respond as Back to NORMAL, no response until the temperature
                greater than threshold.

input: Messages from MP and UI
output: PASS, if requirement satisfied else FAIL
"""

import sys
import time
import datetime
import threading
import json
import os
import os.path
import schedule
import paho.mqtt.client as mqttClient
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem
from PyQt5.QtCore import Qt
from pp_dashboard_ui import Ui_DashboardWindow as Ui_MainWindow
from settings import broker, port, locations
from summary import generate_summary

Client_ID = "PP_Tester"
MP_centers = {}
UI_centers = {}
Index = 0

class MyWindow(QtWidgets.QMainWindow):
    """
    This class is defined to test communication between MP and UI
    """

    def __init__(self):
        """
        This function makes to initialise table headers in GUI, start the connection to
        broker and create thread to open the summary report for each center
        """
        super(MyWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Thread creation for summary report
        t_summary = threading.Thread(target=self.report_schedule)
        t_summary.daemon = True
        t_summary.start()

        # Add headers
        self.add_table_header()
        self.add_table_header_ui()

        # Start the connection to broker
        self.start_broker()

    def table_add_rows(self, dataList):
        """
        This function creates the rows for each new MP center
        """

        # Colour mapping
        green_color = (92, 247, 108,)
        red_color = (255, 129, 120,)

        # Mapping the colour to PASS and FAIL
        if dataList[5] == 'PASS':
            color = green_color
        elif dataList[5] == 'FAIL':
            color = red_color
        else:
            color = (225, 230, 226,)

        # Identify the empty row
        rowPosition = self.ui.tableWidget.rowCount()

        # Create a row
        self.ui.tableWidget.insertRow(rowPosition)

        for column, data in enumerate(dataList):
            # create the item
            item = QTableWidgetItem("{}".format(data))
            # change the alignment
            item.setTextAlignment(Qt.AlignHCenter)
            # Add the item
            self.ui.tableWidget.setItem(rowPosition, column, QTableWidgetItem(item))
            self.ui.tableWidget.item(rowPosition, column). \
                setBackground(QtGui.QColor(color[0], color[1], color[2]))

        self.ui.tableWidget.scrollToBottom()

    def table_add_rows_ui(self, dataList):
        """
        This function creates the rows for each new UI center
        """

        # Green colour
        color = (92, 247, 108,)

        # Identify the empty row
        rowPosition = self.ui.tableWidget_ui.rowCount()

        # Create a row
        self.ui.tableWidget_ui.insertRow(rowPosition)

        for column, data in enumerate(dataList):
            # create the item
            item = QTableWidgetItem("{}".format(data))
            # change the alignment
            item.setTextAlignment(Qt.AlignHCenter)
            # Add the item
            self.ui.tableWidget_ui.setItem(rowPosition, column, QTableWidgetItem(item))

        self.ui.tableWidget_ui.item(rowPosition, 3). \
            setBackground(QtGui.QColor(color[0], color[1], color[2]))

        self.ui.tableWidget_ui.scrollToBottom()

    def add_table_header(self):
        """
        This function used to add the row header for MP center
        """

        # Disable maximize
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | \
        QtCore.Qt.WindowMinimizeButtonHint)

        # Setting Table font
        fnt = self.ui.tableWidget.font()
        fnt.setPointSize(10)
        fnt.setBold(True)
        self.ui.tableWidget.setFont(fnt)

        # Disable cell editing in GUI
        self.ui.tableWidget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Column count
        self.ui.tableWidget.setColumnCount(9)

        # Add table header
        columns = ["Location Name", "Location ID", "Last update",
                   "Present temperature", "UI Response", "Test result",
                   "Day Status", "Day Report", "Summary"]

        for Index, column in enumerate(columns):
            item1 = QtWidgets.QTableWidgetItem(column)
            item1.setBackground(QtGui.QColor(255, 0, 0))
            item1.setForeground(QtGui.QColor(0, 0, 0))

            self.ui.tableWidget.setHorizontalHeaderItem(Index, item1)

        # Table will fit the screen horizontally
        self.ui.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Mapping to open the report of MP center
        self.ui.tableWidget.cellClicked.connect(self.show_report)

    def add_table_header_ui(self):
        """
        This function used to add the row header for UI center
        """

        # Disable maximize
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | \
        QtCore.Qt.WindowMinimizeButtonHint)

        # Setting Table font
        fnt = self.ui.tableWidget_ui.font()
        fnt.setPointSize(10)
        fnt.setBold(True)
        self.ui.tableWidget_ui.setFont(fnt)

        # Disable cell editing in GUI
        self.ui.tableWidget_ui.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Column count
        self.ui.tableWidget_ui.setColumnCount(4)

        # Add table header
        columns = ["Name of the location", "Location ID", "Last update", "Connection Status"]
        for Index, column in enumerate(columns):
            item1 = QtWidgets.QTableWidgetItem(column)
            item1.setBackground(QtGui.QColor(255, 0, 0))
            item1.setForeground(QtGui.QColor(0, 0, 0))

            self.ui.tableWidget_ui.setHorizontalHeaderItem(Index, item1)

        # Table will fit the screen horizontally
        self.ui.tableWidget_ui.horizontalHeader().setStretchLastSection(True)
        self.ui.tableWidget_ui.update()
        self.ui.tableWidget_ui.setUpdatesEnabled(True)
        self.ui.tableWidget_ui.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


    def show_report(self, row, column):
        """
        This function is used to open the Day report and summary report of each center
        """

        # Select the location
        location_id = self.ui.tableWidget.item(row, 0).text()

        # Replace if any center has spaces in names
        report_file_name = location_id.replace(" ", "_")

        # Column 7 to open the Day report and Column 8 for summary report
        if column == 7:
            t_report = threading.Thread(target=lambda: \
                os.system("open_report.exe {}".format(report_file_name)))
            t_report.daemon = True
            t_report.start()
        elif column == 8:
            os.system("start {}/test_summary-{}.xlsx". \
                format(os.path.join(os.getcwd(), "reports", "summary"), report_file_name))

    def start_broker(self):
        """
        This function start the connection to broker
        """

        # create new instance
        self.client = mqttClient.Client(Client_ID)

        # Attach function to callback for connect, disconnect and message handle
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # connect to broker
        self.client.connect(broker, port=port)

        # Subscribe the topics
        self.client.subscribe("Temperature/#")
        self.client.subscribe("Temperature/status/#")
        self.client.subscribe("TelemetryInformationAck/#")
        self.client.subscribe("TelemetryInformationAck/status/#")

        # start the loop
        self.client.loop_start()

        # read the MP center specification
        with open('MP_Spec.json', 'r') as self.mp_specs:
            self.mpspec_json = json.load(self.mp_specs)

        self.devices = self.mpspec_json['locations']

        # store the UI previous response information
        with open('UI_Prev_data.json', 'r') as self.ui_prev:
            self.ui_prev_json = json.load(self.ui_prev)

        self.prev_ui_values = self.ui_prev_json['ui_prev_resp']

        # Wait for connection
        while not self.client.is_connected():
            time.sleep(0.1)

    def on_connect(self, client, userdata, flags, rc):
        """
        This function used to connect the broker
        """
        status = {0: "Connection successful",
                  1: "Connection refused – incorrect protocol version",
                  2: "Connection refused – invalid client identifier",
                  3: "Connection refused – server unavailable",
                  4: "Connection refused – bad username or password",
                  5: "Connection refused – not authorised",
                  6 - 255: "Currently unused"
                  }

    def close_event(self, event):
        """
        This function used to close event to disconnect from broker
        """
        self.client.disconnect()
        self.client.loop_stop()

    def on_disconnect(self, client, userdata, rc):
        """
        This function to used to initiate disconnection from broker
        """
        if self.client.is_connected() == False:
            print("Client disconnected------------------")

    def on_message(self, client, usrdata, msg):
        """
        This function receives the messages based on subscribed topic and handle.
        """

        # create thread to handle the messages
        if "status" not in msg.topic:
            t_msghandle = threading.Thread(target=self.process_messages, \
                                           args=(msg.topic, json.loads( \
                                               str(msg.payload, "UTF-8")),))
            t_msghandle.start()

        # Handle the status message from MP centers
        if "Temperature/status" in msg.topic:

            # Extract the location from topic and payload
            location_id = msg.topic.split("/")[-1]
            payload_dictionary = json.loads(str(msg.payload, "UTF-8"))

            # Check the location in MP center table, if not to add
            if MP_centers.get(location_id, None) == None:
                MP_centers[location_id] = payload_dictionary
                MP_centers[location_id].update({"rowId": self.ui.tableWidget.rowCount()})
                # Add this center to GUI table and get rowId
                self.table_add_rows([location_id, locations[location_id], \
                                     "", "", "", "", "", "Open", "Open"])

            # update the MP center table after disconnect
            elif MP_centers.get(location_id, None) != None and payload_dictionary["status"] == 0:
                MP_centers[location_id].update(payload_dictionary)
                # Update the GUI table row to empty for present temp column as PP is inactive
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.table_update_rows([location_id, timestamp, "", "", "", ""], )

            # update the MP center table after re-connect
            elif MP_centers.get(location_id, None) != None and payload_dictionary["status"] == 1:
                MP_centers[location_id].update(payload_dictionary)

            # Update the Lcd panel for MP center status
            self.update_lcd_panel()

        # Handle the status message from UI centers
        if "TelemetryInformationAck/status" in msg.topic:

            # Extract the location from topic and payload
            location_id = msg.topic.split("/")[-1]
            payload_dictionary = json.loads(str(msg.payload, "UTF-8"))

            # timestamp to show connect and disconnect update
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Check the location in UI center table, if not to add
            if UI_centers.get(location_id, None) == None:
                UI_centers[location_id] = payload_dictionary
                UI_centers[location_id].update({"rowId": self.ui.tableWidget_ui.rowCount()})
                self.table_add_rows_ui([location_id, locations[location_id], timestamp, "Active"])

            # update the UI center table after disconnect
            elif UI_centers.get(location_id, None) != None and payload_dictionary["status"] == 0:
                UI_centers[location_id].update(payload_dictionary)
                self.table_update_rows_ui([location_id, timestamp, "Inactive"], )

            # update the UI center table after re-connect
            elif UI_centers.get(location_id, None) != None and payload_dictionary["status"] == 1:
                UI_centers[location_id].update(payload_dictionary)
                self.table_update_rows_ui([location_id, timestamp, "Active"], )

            # Update the Lcd panel
            self.update_lcd_panel()

    def update_lcd_panel(self):
        """
        This function is used to display online and offline status of MP and UI
        """

        # create variables
        mp_on = 0
        mp_off = 0
        ui_on = 0

        # to get the no.of MP centers online and offline
        for value in MP_centers.values():
            if value["status"] == 1:
                mp_on += 1
            else:
                mp_off += 1

        # to get the UI status active or inactive
        for value in UI_centers.values():
            if value["status"] == 1:
                ui_on = 1

        # to display online, offline and total MP centers
        self.ui.lcdNumber_Online.display(mp_on)
        self.ui.lcdNumber_Offline.display(mp_off)
        self.ui.lcdNumber_Total.display(len(MP_centers))

        # to display active or inactive status of UI
        self.ui.lcdNumber_UI_status.display(ui_on)

    def process_messages(self, topic, kwargs):
        """
        Method to process the messages from Media player and User Interface (UI) and validate
        the exchange of messages
        """

        # create variables
        location_found = 'n'
        ui_status = ""
        status = ""

        # Create the reports paths if not available
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        report_path = os.path.join(os.getcwd(), "reports", today_date)
        if os.path.isdir(report_path) == False:
            os.makedirs(report_path)

        # extract the location
        location_id = topic.split("/")[-1]

        # Extract the Threshold values of loaction
        for getth in range(len(self.devices)):
            if self.devices[getth].get('location') == location_id:
                temp_upperth = float(self.devices[getth].get('thresholdtemp'))

        # Extract the previous responses from UI to the current location
        for getprevui in range(len(self.prev_ui_values)):
            if self.prev_ui_values[getprevui].get('location') == location_id:
                location_found = 'y'
                prev_timestamp = self.prev_ui_values[getprevui].get('timestamp')
                prev_uistatus = self.prev_ui_values[getprevui].get('uistatus')
                prev_tempvalue = float(self.prev_ui_values[getprevui].get('tempvalue'))
                prev_oa_status = self.prev_ui_values[getprevui].get('overall_status')
                prev_tc_id = int(self.prev_ui_values[getprevui].get('testcase_sno'))
                next_tc_id = prev_tc_id

        # Handle message from MP
        if "Temperature" in topic:
            try:
                # store previous UI info in temporary file
                if location_found == 'n':
                    # start the test case ID to 0
                    next_tc_id = 0
                    # store info starting of new device connect to broker
                    new_device = {"location": location_id, "timestamp": "null",
                                  "tempvalue": "0", "uistatus": "Temperature Back to normal",
                                  "overall_status": "PASS", "testcase_sno": "0"}
                    self.prev_ui_values.append(new_device)
                    with open('UI_Prev_data.json', 'w') as ui_prev:
                        json.dump(self.ui_prev_json, ui_prev, indent=4)
                    #store overall status of begining of test
                    prev_oa_status = 'PASS'

                # device is already connected
                if location_found == 'y':
                    # check for UI response for previous MP message
                    if prev_timestamp != 'null':
                        # check for threshold and UI response
                        if prev_tempvalue < temp_upperth and \
                                prev_uistatus == "Temperature Back to normal":
                            # UI response is not required
                            ui_status = "Not required"
                            status = 'PASS'
                        else:
                            # UI response is not received for previous message
                            ui_status = "Not received"
                            status = 'FAIL'
                            # update the UI response as null for previous MP message
                            for getprevui in range(len(self.prev_ui_values)):
                                if self.prev_ui_values[getprevui].get('location') == location_id:
                                    self.prev_ui_values[getprevui]['uistatus'] = 'null'
                                    with open('UI_Prev_data.json', 'w') as ui_prev:
                                        json.dump(self.ui_prev_json, ui_prev, indent=4)

                        # remove spaces in location name
                        report_file_name = location_id.replace(" ", "_")
                        # log file path
                        path = os.path.join(report_path, \
                                    "{}.log".format(datetime.datetime.now(). \
                                    strftime("%Y-%m-%d") + "-" + str(report_file_name)))
                        # open the log file to create for next day
                        with open(path, "a") as file:
                            if file.tell() == 0:
                                # reset the test case ID to 0 for the next day log file
                                prev_tc_id = 0
                                # write the header into next day log file
                                self.write_header(file, location_id, temp_upperth)

                                for getprevui in range(len(self.prev_ui_values)):
                                    if self.prev_ui_values[getprevui].get('location') \
                                            == location_id:
                                        # reset overall status to PASS for the coming day
                                        self.prev_ui_values[getprevui]['overall_status'] = 'PASS'
                                        # reset the test case ID for next day log
                                        self.prev_ui_values[getprevui]['testcase_sno'] = 1
                                        with open('UI_Prev_data.json', 'w') as ui_prev:
                                            json.dump(self.ui_prev_json, ui_prev, indent=4)
                                        prev_oa_status = 'PASS'
                            # increase test case ID
                            next_tc_id = prev_tc_id + 1
                            # format the test case to update in log
                            text = "{:^8}|{:^21}|{:^15}|{:^30}|{:^15}\n". \
                                format(next_tc_id, prev_timestamp, prev_tempvalue, \
                                       ui_status, status)
                            # enter the test info into log file
                            file.write("{}".format(text))

                        # set to overall status to FAIL, if any test failed for the day
                        if status == 'FAIL' and prev_oa_status == 'PASS':
                            prev_oa_status = 'FAIL'

                        # GUI Table data update
                        self.table_update_rows([location_id, prev_timestamp, \
                                                prev_tempvalue, ui_status, status, prev_oa_status])

                # update the previous response
                for getprevui in range(len(self.prev_ui_values)):
                    if self.prev_ui_values[getprevui].get('location') == location_id:
                        self.prev_ui_values[getprevui]['timestamp'] = kwargs['value']['timestamp']
                        self.prev_ui_values[getprevui]['tempvalue'] = kwargs['value']['value']
                        self.prev_ui_values[getprevui]['overall_status'] = prev_oa_status
                        self.prev_ui_values[getprevui]['testcase_sno'] = next_tc_id
                        with open('UI_Prev_data.json', 'w') as ui_prev:
                            json.dump(self.ui_prev_json, ui_prev, indent=4)
            except KeyError:
                status = "NA"
            except IndexError:
                status = "NA"

        # Handle the UI message handle
        elif "TelemetryInformationAck" in topic:
            try:
                # check for timestamp of message from MP
                if prev_timestamp == kwargs['timestamp']:
                    # check for Threshold condition and previous response
                    if prev_tempvalue > temp_upperth and kwargs['value'] \
                            == "Temperature too high":
                        # set the test status and store UI response
                        status = 'PASS'
                        store_ui = 'null'
                    # check for Threshold condition and previous response
                    elif prev_tempvalue <= temp_upperth and kwargs['value'] \
                            == "Temperature Back to normal":
                        # set the test status and store UI response
                        status = 'PASS'
                        store_ui = "Temperature Back to normal"
                    else:
                        status = 'FAIL'
                        store_ui = 'null'
                else:
                    status = 'FAIL'
                    store_ui = 'null'

            except KeyError:
                status = "NA"
            except IndexError:
                status = "NA"

            # remove spaces in location name
            report_file_name = location_id.replace(" ", "_")
            # log file path
            path = os.path.join(report_path,
                                "{}.log".format(datetime.datetime.now().strftime("%Y-%m-%d") \
                                + "-" + str(report_file_name)))

            # open the log file to create for next day
            with open(path, "a") as file:
                if file.tell() == 0:
                    # reset the test case ID to 0 for the next day log file
                    prev_tc_id = 0
                    # write the header into next day log file
                    self.write_header(file, location_id, temp_upperth)

                    for getprevui in range(len(self.prev_ui_values)):
                        if self.prev_ui_values[getprevui].get('location') == location_id:
                            # reset overall status to PASS for the coming day
                            prev_oa_status = 'PASS'
                            self.prev_ui_values[getprevui]['overall_status'] = 'PASS'
                            # reset the test case ID for next day log
                            self.prev_ui_values[getprevui]['testcase_sno'] = 1
                            with open('UI_Prev_data.json', 'w') as ui_prev:
                                json.dump(self.ui_prev_json, ui_prev, indent=4)

                # increase test case ID
                next_tc_id = prev_tc_id + 1
                # format the test case to update in log
                text = "{:^8}|{:^21}|{:^15}|{:^30}|{:^15}\n". \
                    format(next_tc_id, prev_timestamp, prev_tempvalue, kwargs['value'], status)
                # enter the test info into log file
                file.write("{}".format(text))

            # set to overall status to FAIL, if any test failed for the day
            if status == 'FAIL' and prev_oa_status == 'PASS':
                prev_oa_status = 'FAIL'

            # GUI Table data update
            self.table_update_rows([location_id, prev_timestamp, prev_tempvalue, \
                                    kwargs['value'], status, prev_oa_status])

            # update the previous response
            for getprevui in range(len(self.prev_ui_values)):
                if self.prev_ui_values[getprevui].get('location') == location_id:
                    self.prev_ui_values[getprevui]['timestamp'] = 'null'
                    self.prev_ui_values[getprevui]['tempvalue'] = '0'
                    self.prev_ui_values[getprevui]['uistatus'] = store_ui
                    self.prev_ui_values[getprevui]['overall_status'] = prev_oa_status
                    self.prev_ui_values[getprevui]['testcase_sno'] = next_tc_id
                    with open('UI_Prev_data.json', 'w') as ui_prev:
                        json.dump(self.ui_prev_json, ui_prev, indent=4)

    def table_update_rows_ui(self, dataList):
        """
        Method to update the status (Active or Inactive) of UI
        """

        # Colour information
        green_color = (92, 247, 108,)
        red_color = (255, 129, 120,)

        # Colour mapping for Active (green) and Inactive (red) status
        if dataList[2] == 'Active':
            color = green_color
        elif dataList[2] == 'Inactive':
            color = red_color
        else:
            color = (225, 230, 226,)

        # Time stamp column
        self.ui.tableWidget_ui.item(UI_centers[dataList[0]]["rowId"], 2). \
            setText("{}".format(dataList[1]))

        # UI status column
        self.ui.tableWidget_ui.item(UI_centers[dataList[0]]["rowId"], 3). \
            setText("{}".format(dataList[2]))
        self.ui.tableWidget_ui.item(UI_centers[dataList[0]]["rowId"], 3). \
            setBackground(QtGui.QColor(color[0], color[1], color[2]))

        self.ui.tableWidget_ui.viewport().update()

    def table_update_rows(self, dataList):
        """
        Method to update the details of MP center in the table
        """

        # Colour information
        green_color = (92, 247, 108,)
        red_color = (255, 129, 120,)

        # colour mapping for PASS and FAIL of Day status
        if dataList[4] == 'PASS':
            color = green_color
        elif dataList[4] == 'FAIL':
            color = red_color
        else:
            color = (225, 230, 226,)

        # colour mapping for PASS (green) and FAIL (red) of overall status
        if dataList[5] == 'PASS':
            oa_color = green_color
        elif dataList[5] == 'FAIL':
            oa_color = red_color
        else:
            oa_color = (225, 230, 226,)

        # Time stamp column
        self.ui.tableWidget.item(MP_centers[dataList[0]]["rowId"], 2). \
            setText("{}".format(dataList[1]))

        # # MP present temp
        self.ui.tableWidget.item(MP_centers[dataList[0]]["rowId"], 3). \
            setText("{}".format(dataList[2]))

        # # UI Response
        self.ui.tableWidget.item(MP_centers[dataList[0]]["rowId"], 4). \
            setText("{}".format(dataList[3]))

        # # test status
        self.ui.tableWidget.item(MP_centers[dataList[0]]["rowId"], 5). \
            setText("{}".format(dataList[4]))
        self.ui.tableWidget.item(MP_centers[dataList[0]]["rowId"], 5). \
            setBackground(QtGui.QColor(color[0], color[1], color[2]))

        # # overall status
        self.ui.tableWidget.item(MP_centers[dataList[0]]["rowId"], 6). \
            setText("{}".format(dataList[5]))
        self.ui.tableWidget.item(MP_centers[dataList[0]]["rowId"], 6). \
            setBackground(QtGui.QColor(oa_color[0], oa_color[1], oa_color[2]))

        self.ui.tableWidget.viewport().update()

    def write_header(self, file, location_id, temp_upperth):
        """
        Write header to test report file
        """

        file.write("-" * 60)
        text = "\n{:<27} : {}\n{:<27} : {}\n{:<27} : {}\n{:<27} : {}\n{:<27} : {}\n".format(
            "Client connected to broker", broker, "Client ID",
            Client_ID, "Location", MP_centers[location_id]["location"],
            "Client status", "Connection successful", "Threshold Temperature", temp_upperth)
        file.write(text)
        file.write("-" * 60)
        file.write("\n")

        header = "\n{:^8}|{:^21}|{:^15}|{:^30}|{:^15}\n". \
            format("  S.No  ", "Time stamp", "Temperature", "UI Response", "Test Status")
        file.write("-" * 93)
        file.write(header)
        file.write("-" * 93)
        file.write("\n")

    def report_schedule(self):
        """
        Schedule the summary generation for previous day
        """

        schedule.every().day.at("00:05:00").do(generate_summary, MP_centers=MP_centers.keys())
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    application = MyWindow()
    application.show()
    sys.exit(app.exec())
