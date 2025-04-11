import sys
import datetime
import math
import pytz
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QDateTimeEdit, 
                             QTextEdit, QTabWidget, QComboBox, QLineEdit, QHBoxLayout, QSpinBox)
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QIcon


DEFAULT_TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

def unix_timestamp_to_str(os_timestamp, timestamp_format, timezone=None):
    if timezone:
        tz = pytz.timezone(timezone)
        local_dt = datetime.datetime.fromtimestamp(os_timestamp, tz=tz)
    else:
        local_dt = datetime.datetime.fromtimestamp(os_timestamp)
    timestamp = local_dt.strftime(timestamp_format)
    return timestamp


def windows_timestamp_to_str(os_timestamp, timestamp_format, timezone=None):
    unix_time = (os_timestamp - 116444736000000000) / 10000000
    if timezone:
        tz = pytz.timezone(timezone)
        local_dt = datetime.datetime.fromtimestamp(unix_time, tz=tz)
    else:
        local_dt = datetime.datetime.fromtimestamp(unix_time)
    timestamp = local_dt.strftime(timestamp_format)
    return timestamp


class TimestampParser:
    def __init__(self):
        # 定义所有可能的解析函数
        self.POSSIBLE_TIMESTAMP_PARSER = [
            lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f"),
            lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S,%f"),
            lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S"),
            lambda s: datetime.datetime.strptime(s, "%Y-%m-%d_%H:%M:%S.%f"),
            lambda s: datetime.datetime.strptime(s, "%Y-%m-%d_%H:%M:%S,%f"),
            lambda s: datetime.datetime.strptime(s, "%Y-%m-%d_%H:%M:%S"),
            lambda s: datetime.datetime.strptime(s, "%H:%M:%S"),
            lambda s: datetime.datetime.strptime(s, "%H:%M:%S,%f"),
            lambda s: datetime.datetime.strptime(s, "%H:%M:%S.%f"),
            lambda s: datetime.timedelta(seconds=float(s))
        ]
        # 初始化上一次命中的解析函数为 None
        self.last_matched_timestamp_parser = None

    def parse_timestamp(self, timestamp_str):
        # 优先尝试使用上一次命中的解析函数
        if self.last_matched_timestamp_parser:
            try:
                # print(f'hit the cache for {timestamp_str}')
                return self.last_matched_timestamp_parser(timestamp_str)
            except (ValueError, TypeError):
                pass

        # 若上一次函数未命中，尝试所有可能的解析函数
        for func in self.POSSIBLE_TIMESTAMP_PARSER:
            try:
                # print(f'search format for {timestamp_str}')
                result = func(timestamp_str)
                # 记录本次命中的解析函数
                self.last_matched_timestamp_parser = func
                return result
            except (ValueError, TypeError):
                continue
        return None

    def calculate_time_difference(self, timestamp_str1, timestamp_str2):
        dt1 = self.parse_timestamp(timestamp_str1)
        dt2 = self.parse_timestamp(timestamp_str2)

        if dt1 and dt2:
            if isinstance(dt1, datetime.timedelta) and isinstance(dt2, datetime.timedelta):
                time_diff = (dt2 - dt1)
            elif isinstance(dt1, datetime.datetime) and isinstance(dt2, datetime.datetime):
                time_diff = (dt2 - dt1)
            else:
                return None
            return time_diff.total_seconds()
        return None
    

class MicrosecondTimeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()

        now = datetime.datetime.now()

        self.datetime_edit = QDateTimeEdit(self)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_edit.setDateTime(now)
        layout.addWidget(self.datetime_edit)

        self.microsecond_input = QSpinBox(self)
        self.microsecond_input.setPrefix('.')
        self.microsecond_input.setRange(0, 999999)
        self.microsecond_input.setValue(now.microsecond)
        layout.addWidget(self.microsecond_input)

        layout.addWidget(QLabel(' = '))

        self.display_time = QLineEdit(self)
        layout.addWidget(self.display_time)


        self.current_ts_btn = QPushButton('Now', self)
        self.current_ts_btn.clicked.connect(self.current_ts_clicked)
        self.current_ts_btn.setMaximumWidth(100)
        layout.addWidget(self.current_ts_btn)

        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(4)

        self.setLayout(layout)

        self.datetime_edit.dateChanged.connect(self.display_time_slot)
        self.datetime_edit.timeChanged.connect(self.display_time_slot)
        self.microsecond_input.valueChanged.connect(self.display_time_slot)
        # self.microsecond_input.editingFinished.connect(self.zfill_slot)

        # self.zfill_slot()

    # def zfill_slot(self):
    #     fill_str = '.'
    #     fill = 6 - len(str(self.microsecond_input.value()))
    #     if fill > 0:
    #         fill_str += '0' * fill
    #     self.microsecond_input.setPrefix(fill_str)

    def current_ts_clicked(self):
        now = datetime.datetime.now()
        self.datetime_edit.setDateTime(now)
        self.microsecond_input.setValue(now.microsecond)

    def display_time_slot(self):
        try:
            dt = self.datetime_edit.dateTime()
            dt_str = dt.toString("yyyy-MM-dd HH:mm:ss")
            # print(f'dt_str={dt_str}')
            
            microsecond = self.microsecond_input.value()
            # final_time_str = f"{dt_str}{str(microsecond).zfill(6)[3:]}"
            final_time_str = f"{dt_str}.{str(microsecond)}"

            self.display_time.setText(final_time_str)

        except ValueError:
            self.display_time.setText("无效的微秒输入，请输入整数")


class TimestampDifferenceCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.timestamp_parser = TimestampParser()

    def initUI(self):
        layout = QVBoxLayout()
        tab_widget = QTabWidget()

        # 第一个标签页：时间差计算
        diff_tab = QWidget()
        diff_layout = QVBoxLayout()

        # 选择第一个时间戳
        self.label1 = QLabel("第一个时间戳:")
        self.datetime_edit1 = MicrosecondTimeWidget()

        diff_layout.addWidget(self.label1)
        diff_layout.addWidget(self.datetime_edit1)


        # 选择第二个时间戳，默认显示前一天的时间
        self.label2 = QLabel("第二个时间戳:")
        self.datetime_edit2 = MicrosecondTimeWidget()

        diff_layout.addWidget(self.label2)
        diff_layout.addWidget(self.datetime_edit2)

        # 计算按钮
        self.calculate_button = QPushButton("计算差值")
        self.calculate_button.clicked.connect(self.calculate_difference)
        diff_layout.addWidget(self.calculate_button)

        # 用于显示计算结果的文本编辑框
        self.result_textedit = QTextEdit()
        self.result_textedit.setReadOnly(True)
        diff_layout.addWidget(self.result_textedit)

        diff_tab.setLayout(diff_layout)
        tab_widget.addTab(diff_tab, "时间差计算")


        # 第二个标签页：时间戳转换
        convert_tab = QWidget()
        convert_layout = QVBoxLayout()

        # 选择时间戳类型
        self.timestamp_type_combobox = QComboBox()
        self.timestamp_type_combobox.addItems(["Unix", "Windows"])


        config_widget = QWidget()
        config_widget.setLayout(QVBoxLayout())
        config_widget.layout().setContentsMargins(0,0,0,0)
        config_widget.layout().setSpacing(5)

        self.timestamp_type_label = QLabel("时间戳类型:")
        self.timestamp_type_label.setToolTip(
            """Windows系统的时间戳用64位整数来表示, 代表从1601年1月1日00:00:00 UTC开始经过的0.1微秒间隔数.\n"""
            """Unix系统的时间戳代表从1970年1月1日00:00:00 UTC起经过的秒数.""")

        config_widget.layout().addWidget(self.timestamp_type_label)
        config_widget.layout().addWidget(self.timestamp_type_combobox)


        # 选择时区
        self.timezone_combobox = QComboBox()
        self.timezone_combobox.addItem('None')
        self.timezone_combobox.addItems(pytz.all_timezones)
        self.timezone_combobox.setCurrentText("None")


        config_widget.layout().addWidget(QLabel("时区:"))
        config_widget.layout().addWidget(self.timezone_combobox)


        convert_layout.addWidget(config_widget)

        # 输入时间戳转换为日期时间
        self.timestamp_input = QLineEdit()
        self.timestamp_to_datetime_button = QPushButton("=>")
        self.timestamp_to_datetime_button.clicked.connect(self.timestamp_to_datetime_slot)

        self.timestamp_label = QLabel("时间戳:")

        # 输入日期时间转换为时间戳
        self.datetime_input = QLineEdit()
        self.datetime_to_timestamp_button = QPushButton("<=")
        self.datetime_to_timestamp_button.clicked.connect(self.datetime_to_timestamp_slot)

        self.left_and_right_widget = QWidget()
        self.left_and_right_widget.setLayout(QHBoxLayout())
        self.left_and_right_widget.layout().setContentsMargins(0,4,0,4)
        # self.left_and_right_widget.layout().setSpacing(4)

        self.left_widget = QWidget()
        self.left_widget.setLayout(QVBoxLayout())
        self.left_widget.layout().setContentsMargins(0,0,0,0)
        # self.left_widget.layout().setSpacing(4)
        self.left_widget.layout().addWidget(self.timestamp_label)
        self.left_widget.layout().addWidget(self.timestamp_input)

        btns_widget = QWidget()
        btns_widget.setLayout(QHBoxLayout())
        self.timestamp_now_btn = QPushButton('Now')
        btns_widget.layout().addWidget(self.timestamp_now_btn)
        btns_widget.layout().addWidget(self.timestamp_to_datetime_button)
        btns_widget.layout().setContentsMargins(0,0,0,0)
        # btns_widget.layout().setSpacing(4)
        self.left_widget.layout().addWidget(btns_widget)

        self.right_widget = QWidget()
        self.right_widget.setLayout(QVBoxLayout())
        self.right_widget.layout().setContentsMargins(0,0,0,0)
        # self.right_widget.layout().setSpacing(4)
        self.right_widget.layout().addWidget(QLabel("日期时间 (YYYY-MM-DD HH:MM:SS.ffffff):"))
        self.right_widget.layout().addWidget(self.datetime_input)

        btns_widget = QWidget()
        btns_widget.setLayout(QHBoxLayout())
        self.datetime_now_btn = QPushButton('Now')
        btns_widget.layout().addWidget(self.datetime_to_timestamp_button)
        btns_widget.layout().addWidget(self.datetime_now_btn)
        btns_widget.layout().setContentsMargins(0,0,0,0)
        # btns_widget.layout().setSpacing(4)
        self.right_widget.layout().addWidget(btns_widget)

        self.left_and_right_widget.layout().addWidget(self.left_widget)
        self.left_and_right_widget.layout().addWidget(self.right_widget)

        self.convert_result_textedit = QTextEdit()
        self.convert_result_textedit.setReadOnly(True)

        self.clear_btn = QPushButton('Clear')

        convert_layout.addWidget(self.left_and_right_widget)
        convert_layout.addWidget(self.convert_result_textedit)
        convert_layout.addWidget(self.clear_btn)

        convert_tab.setLayout(convert_layout)

        tab_widget.addTab(convert_tab, "时间戳转换")

        # time_calculator
        layout.addWidget(tab_widget)
        self.setLayout(layout)
        self.setWindowTitle('Time Calculator')
        self.setWindowIcon(QIcon('time.ico'))
        self.resize(600, 500)
        self.show()

        self.timestamp_now_btn.clicked.connect(self.timestamp_now_btn_slot)
        self.datetime_now_btn.clicked.connect(self.datetime_now_btn_slot)

        self.clear_btn.clicked.connect(self.clear_btn_slot)

        self.timestamp_type_combobox.currentTextChanged.connect(self.timestamp_type_combobox_changed_slot)
        self.timestamp_type_combobox.currentTextChanged.emit(self.timestamp_type_combobox.currentText())

        self.datetime_edit1.display_time_slot()
        self.datetime_edit2.display_time_slot()

    def clear_btn_slot(self):
        self.convert_result_textedit.clear()

    def convert_timestamp_to_print_format(self, timestamp):

        numeric_ts = 0
        try:
            if isinstance(timestamp, int):
                numeric_ts = timestamp
            elif isinstance(timestamp, float):
                numeric_ts = timestamp
            elif isinstance(timestamp, str):
                numeric_ts = float(timestamp)
        except ValueError:
            return 'neither int, float nor str'

        timestamp_type = self.timestamp_type_combobox.currentText()
        if timestamp_type == "Unix":
            return f'{numeric_ts:.6f}'

        return f'{numeric_ts:.0f}'

    def timestamp_now_btn_slot(self):
        ts = self.datetime_to_timestamp()
        self.timestamp_input.setText(self.convert_timestamp_to_print_format(ts))

    def datetime_now_btn_slot(self):
        now = datetime.datetime.now()
        timestamp = now.strftime(DEFAULT_TIMESTAMP_FORMAT)
        self.datetime_input.setText(timestamp)

    def timestamp_type_combobox_changed_slot(self, text):
        if text == 'unix':
            self.timestamp_label.setText(f'时间戳 (unit: second):')
        else:
            self.timestamp_label.setText(f'时间戳 (unit: 0.1 microsecond):')

    def calculate_difference(self):
        try:
            total_seconds = self.timestamp_parser.calculate_time_difference(self.datetime_edit1.display_time.text(), 
                                                                            self.datetime_edit2.display_time.text())
            total_days = total_seconds / 3600 / 24

            years = total_days // 365
            remaining_days = total_days % 365
            months = remaining_days // 30
            days = remaining_days % 30

            hours = int(total_seconds // 3600 % 24)
            minutes = int(total_seconds // 60 % 60)
            seconds = int(total_seconds % 60)

            # 显示结果
            result = ''
            result += f"相差年: {years:.0f}\n"
            result += f"相差月: {(months + years * 12):.0f}\n"
            result += f"相差天: {total_days:.2f}\n"
            result += f"相差时: {total_seconds / 3600:.2f}\n"
            result += f"相差分: {total_seconds / 60:.2f}\n"
            result += f"相差秒数: {total_seconds:.6f}\n"
            result += f"相差微秒: {total_seconds*1000000:.0f}\n"
            result += f"相差时间: {years:.0f} 年 {months:.0f} 月 {days:.2f} 天 {hours} 时 {minutes} 分 {seconds} 秒 （月按30天计算）"

            self.result_textedit.setPlainText(result)
        except Exception as e:
            QMessageBox.warning(self, "计算错误", str(e))

    def timestamp_to_datetime_slot(self):
        result = self.timestamp_to_datetime(float(self.timestamp_input.text()))
        self.datetime_input.setText(result)

        ts_str = self.convert_timestamp_to_print_format(self.timestamp_input.text())
        self.convert_result_textedit.append(f'timestamp={ts_str} => datetime={result}')

    def timestamp_to_datetime(self, timestamp):
        try:
            timezone = self.timezone_combobox.currentText()
            if timezone == "None":
                timezone = None

            timestamp_type = self.timestamp_type_combobox.currentText()
            if timestamp_type == "Unix":
                result = unix_timestamp_to_str(timestamp, DEFAULT_TIMESTAMP_FORMAT, timezone)
            else:
                result = windows_timestamp_to_str(timestamp, DEFAULT_TIMESTAMP_FORMAT, timezone)

            return result

        except Exception as e:
            QMessageBox.warning(self, "转换错误", str(e))

    def datetime_to_timestamp_slot(self):
        datetime_str = self.datetime_input.text()
        ts = self.datetime_to_timestamp(datetime_str)

        ts_str = self.convert_timestamp_to_print_format(ts)

        self.timestamp_input.setText(ts_str)
        self.convert_result_textedit.append(f'timestamp={ts_str} <= datetime={datetime_str}')

    def datetime_to_timestamp(self, datetime_str=None):
        try:
            dt = None
            if datetime_str is None:
                dt = datetime.datetime.now()
            else:
                dt = self.timestamp_parser.parse_timestamp(datetime_str)

            timezone = self.timezone_combobox.currentText()
            if timezone != "None":
                tz = pytz.timezone(timezone)
                dt = dt.replace(tzinfo=tz)

            timestamp_type = self.timestamp_type_combobox.currentText()
            if timestamp_type == "Unix":
                result = dt.timestamp()
            else:
                unix_time = dt.timestamp()
                result = round((unix_time * 10000000) + 116444736000000000)

            # print(f'result={result}')
            return result
        except Exception as e:
            QMessageBox.warning(self, "转换错误", str(e))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = TimestampDifferenceCalculator()
    sys.exit(app.exec_())
    
