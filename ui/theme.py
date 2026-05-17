"""
QSS深色主题
"""
DARK_THEME = """
QMainWindow {
    background-color: #1a1a2e;
    color: #e0e0e0;
}
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
}
QMenuBar {
    background-color: #16213e;
    color: #e0e0e0;
    border-bottom: 1px solid #0f3460;
}
QMenuBar::item:selected {
    background-color: #0f3460;
}
QMenu {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
}
QMenu::item:selected {
    background-color: #e94560;
}
QToolBar {
    background-color: #16213e;
    border-bottom: 1px solid #0f3460;
    spacing: 4px;
    padding: 4px;
}
QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e0e0e0;
}
QToolButton:hover {
    background-color: #0f3460;
    border-color: #e94560;
}
QToolButton:pressed {
    background-color: #e94560;
}
QStatusBar {
    background-color: #16213e;
    color: #888;
    border-top: 1px solid #0f3460;
}
QPushButton {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #1a1a4e;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #e94560;
    border-color: #e94560;
}
QPushButton:pressed {
    background-color: #c73e54;
}
QPushButton#primaryBtn {
    background-color: #e94560;
    border-color: #e94560;
    font-size: 14px;
    padding: 10px 24px;
}
QPushButton#primaryBtn:hover {
    background-color: #ff6b81;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #1a1a4e;
    border-radius: 4px;
    padding: 6px 10px;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #e94560;
}
QListWidget, QTreeWidget, QTableWidget {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    alternate-background-color: #1a1a2e;
}
QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #e94560;
}
QListWidget::item:hover, QTreeWidget::item:hover {
    background-color: #0f3460;
}
QScrollBar:vertical {
    background: #16213e;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #0f3460;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #e94560;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QComboBox {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #1a1a4e;
    border-radius: 4px;
    padding: 6px 10px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    selection-background-color: #e94560;
}
QSlider::groove:horizontal {
    background: #0f3460;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #e94560;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -5px 0;
}
QProgressBar {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 4px;
    text-align: center;
    color: white;
}
QProgressBar::chunk {
    background-color: #e94560;
    border-radius: 3px;
}
QGroupBox {
    border: 1px solid #0f3460;
    border-radius: 8px;
    margin-top: 8px;
    padding-top: 16px;
    color: #e0e0e0;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}
QLabel#titleLabel {
    font-size: 16px;
    font-weight: bold;
    color: #e94560;
}
QSplitter::handle {
    background-color: #0f3460;
}
QTabWidget::pane {
    border: 1px solid #0f3460;
    background-color: #1a1a2e;
}
QTabBar::tab {
    background-color: #16213e;
    color: #e0e0e0;
    padding: 8px 16px;
    border: 1px solid #0f3460;
}
QTabBar::tab:selected {
    background-color: #e94560;
}
"""

def apply_theme(app):
    app.setStyleSheet(DARK_THEME)
