"""
Orange Canvas Welcome Dialog
"""
from typing import Optional, Union, Iterable

from xml.sax.saxutils import escape

from AnyQt.QtWidgets import (
    QDialog, QWidget, QToolButton, QCheckBox, QAction, QLineEdit, QFrame,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QLabel, QApplication
)
from AnyQt.QtGui import (
    QFont, QIcon, QPixmap, QPainter, QColor, QBrush, QActionEvent, QIconEngine,
)

from AnyQt.QtCore import Qt, QRect, QSize, QPoint
from AnyQt.QtCore import pyqtSignal as Signal

from ..canvas.items.utils import radial_gradient
from ..registry import NAMED_COLORS
from ..gui.svgiconengine import StyledSvgIconEngine
from .. import styles


class DecoratedIconEngine(QIconEngine):
    def __init__(self, base: QIcon, background: QColor):
        super().__init__()
        self.__base = base
        self.__background = background
        self.__gradient = radial_gradient(background)

    def paint(
            self, painter: 'QPainter', rect: QRect, mode: QIcon.Mode,
            state: QIcon.State
    ) -> None:
        size = rect.size()
        dpr = painter.device().devicePixelRatioF()
        size = size * dpr
        pm = self.pixmap(size, mode, state)
        painter.drawPixmap(rect, pm)
        return

    def pixmap(
            self, size: QSize, mode: QIcon.Mode, state: QIcon.State
    ) -> QPixmap:
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setBrush(QBrush(self.__gradient))
        p.setPen(Qt.NoPen)
        icon_size = QSize(5 * size.width() // 8, 5 * size.height() // 8)
        icon_rect = QRect(QPoint(0, 0), icon_size)
        ellipse_rect = QRect(QPoint(0, 0), size)
        p.drawEllipse(ellipse_rect)
        icon_rect.moveCenter(ellipse_rect.center())
        palette = styles.breeze_light()
        # Special case for StyledSvgIconEngine. This is drawn on a
        # light-ish color background and should not render with a dark palette
        # (this is bad, and I feel bad).
        with StyledSvgIconEngine.setOverridePalette(palette):
            self.__base.paint(p, icon_rect, Qt.AlignCenter)
        p.end()
        return pixmap

    def clone(self) -> 'QIconEngine':
        return DecoratedIconEngine(
            self.__base, self.__background
        )


def decorate_welcome_icon(icon, background_color):
    # type: (QIcon, Union[QColor, str]) -> QIcon
    """Return a `QIcon` with a circle shaped background.
    """
    background_color = NAMED_COLORS.get(background_color, background_color)
    return QIcon(DecoratedIconEngine(icon, QColor(background_color)))


WELCOME_WIDGET_BUTTON_STYLE = """
    QToolButton {
        padding: 10px 15px;
        border-radius: 5px;
        background: transparent;
        font-size: 13px;
        color: black;
        font-weight: 200;
    }
    QToolButton:hover {
        background-color: #E9ECEF;
    }
    QToolButton[selected=true] {
        background-color: #4CC9FE;
    }
"""

SIDEBAR_STYLE = """
    QFrame {
        background-color: #F5F5F5;
    }
"""

BUTTON_BASE = """
    QToolButton {{
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 200;
        background-color: {bg_color};
    }}
    QToolButton:hover {{
        background-color: {hover_color};
    }}
"""
    
NEW_PROJECT_BUTTON = BUTTON_BASE.format(
    bg_color="#4B9BFF",
    hover_color="#3D8BFF"
)
    
OPEN_BUTTON = BUTTON_BASE.format(
    bg_color="#6C757D",
    hover_color="#5A6268"
)
    
SEARCH_BOX = """
    QLineEdit {
        padding: 8px;
        border: 1px solid #DDE1E6;
        border-radius: 4px;
        background-color: white;
        font-size: 13px;
        color: black;
        font-weight: 200;
    }
"""

SUB_TITLE_STYLE = """
    QLabel {
        color: #6C757D; 
        font-size: 10px; 
        font-weight: 200;
    }
"""

class WelcomeActionButton(QToolButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFont(QApplication.font("QAbstractButton"))
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)

    def actionEvent(self, event):
        # type: (QActionEvent) -> None
        super().actionEvent(event)
        if event.type() == QActionEvent.ActionChanged \
                and event.action() is self.defaultAction():
            # The base does not update self visibility for defaultAction.
            self.setVisible(event.action().isVisible())


class WelcomeDialog(QDialog):
    """
    A welcome widget shown at startup presenting a series
    of buttons (actions) for a beginner to choose from.
    """
    triggered = Signal(QAction)

    new_project_clicked = Signal()
    open_scheme_clicked = Signal()

    def __init__(self, *args, **kwargs):
        showAtStartup = kwargs.pop("showAtStartup", True)
        feedbackUrl = kwargs.pop("feedbackUrl", "")
        super().__init__(*args, **kwargs)

        self.__triggeredAction = None  # type: Optional[QAction]
        self.__sidebarLayout = None
        self.__contectLayout = None
        self.__showAtStartupCheck = None
        self.__feedbackUrl = None
        self.__feedbackLabel = None

        self.setupUi()

        # self.setFeedbackUrl(feedbackUrl)
        self.setShowAtStartup(showAtStartup)

    def setupUi(self):
        # Main layout
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setStyleSheet(SIDEBAR_STYLE)

        self.__sidebarLayout = QVBoxLayout()
        self.__sidebarLayout.setContentsMargins(20, 20, 20, 20)
        self.__sidebarLayout.setSpacing(0)
        sidebar.setLayout(self.__sidebarLayout)

        # Logo and subtitle
        logo = QLabel("RadyaAI")
        logo.setFont(QFont("Arial", 25, QFont.Bold))
        logo.setStyleSheet("color: #4B0082;")

        subtitle = QLabel("Powered by Orange Data Mining")
        subtitle.setStyleSheet(SUB_TITLE_STYLE)

        # Add widgets to sidebar
        self.__sidebarLayout.addWidget(logo)
        self.__sidebarLayout.addWidget(subtitle)
        self.__sidebarLayout.addSpacing(30)

        # Main content area
        self.__contectLayout = QVBoxLayout()
        self.__contectLayout.setContentsMargins(20, 20, 20, 20)
        self.__contectLayout.setSpacing(0)
        
        content = QWidget()
        content.setLayout(self.__contectLayout)

        # Top bar with search and buttons
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        # Action buttons
        new_project_btn = QToolButton()
        new_project_btn.setText("New Project")
        new_project_btn.setStyleSheet(NEW_PROJECT_BUTTON)
        new_project_btn.setMinimumWidth(100)
        new_project_btn.clicked.connect(lambda: self.new_project_clicked.emit())

        open_btn = QToolButton()
        open_btn.setText("Open")
        open_btn.setStyleSheet(OPEN_BUTTON)
        open_btn.setMinimumWidth(80)
        open_btn.clicked.connect(lambda : self.open_scheme_clicked.emit())

        # Search box
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search Projects")
        search_box.setStyleSheet(SEARCH_BOX)

        # Add widgets to top bar
        top_bar_layout.addWidget(search_box, stretch=1)
        top_bar_layout.addWidget(new_project_btn)
        top_bar_layout.addWidget(open_btn)

        top_bar = QWidget()
        top_bar.setLayout(top_bar_layout)

        # Add top bar to content layout        
        self.__contectLayout.addWidget(top_bar)
        self.__contectLayout.addStretch()

        # # Add sidebar and content to main layout
        self.layout().addWidget(sidebar)
        self.layout().addWidget(content)

        self.setSizeGripEnabled(False)
        self.setMinimumSize(1000, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Set window background to white
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

    def setShowAtStartup(self, show):
        # type: (bool) -> None
        """
        Set the 'Show at startup' check box state.
        """
        # if self.__showAtStartupCheck.isChecked() != show:
        #     self.__showAtStartupCheck.setChecked(show)
        pass

    def showAtStartup(self):
        # type: () -> bool
        """
        Return the 'Show at startup' check box state.
        """
        # return self.__showAtStartupCheck.isChecked()
        pass

    def setFeedbackUrl(self, url):
        # type: (str) -> None
        """
        Set an 'feedback' url. When set a link is displayed in the bottom row.
        """
        # self.__feedbackUrl = url
        # if url:
        #     text = self.tr("Help us improve!")
        #     self.__feedbackLabel.setText(
        #         '<a href="{url}">{text}</a>'.format(url=url, text=escape(text))
        #     )
        # else:
        #     self.__feedbackLabel.setText("")
        # self.__feedbackLabel.setVisible(bool(url))
        pass
    
    def addColumn(self, actions, background="light-orange"):
        """Add a column with `actions`.
        """
        count = self.__contectLayout.count()
        self.insertColumn(count, actions, background)
    
    def insertColumn(self, index, actions, background="light-orange"):
        """Insert a column with `actions` at `index`.
        """
        widget = QWidget(objectName="icon-column")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        widget.setLayout(layout)

        self.__contectLayout.insertWidget(0, widget, stretch=10, alignment=Qt.AlignTop)

        for i, action in enumerate(actions):
            self.insertAction(index, i, action, background)

    def addRow(self, actions, background="light-orange"):
        """Add a row with `actions`.
        """
        count = self.__sidebarLayout.count()
        self.insertRow(count, actions, background)

    def insertRow(self, index, actions, background="light-orange"):
        # type: (int, Iterable[QAction], Union[QColor, str]) -> None
        """Insert a row with `actions` at `index`.
        """
        widget = QWidget(objectName="icon-row")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        widget.setLayout(layout)

        self.__sidebarLayout.insertWidget(index, widget, stretch=10, alignment=Qt.AlignTop)

        for i, action in enumerate(actions):
            self.insertAction(index, i, action, background)

    def insertAction(self, row, index, action, background="light-orange"):
        """Insert `action` in `row` in position `index`.
        """
        button = self.createButton(action, background)
        self.insertButton(row, index, button)

    def insertButton(self, row, index, button):
        # type: (int, int, QToolButton) -> None
        """Insert `button` in `row` in position `index`.
        """
        item = self.__sidebarLayout.itemAt(row)
        layout = item.widget().layout()
        layout.insertWidget(index, button)
        button.triggered.connect(self.__on_actionTriggered)

    def createButton(self, action, background="light-orange"):
        # type: (QAction, Union[QColor, str]) -> QToolButton
        """Create a tool button for action.
        """
        button = WelcomeActionButton(self)
        button.setDefaultAction(action)
        button.setStyleSheet(WELCOME_WIDGET_BUTTON_STYLE)
        button.setMinimumWidth(200)
       
        return button

    def buttonAt(self, i, j):
        # type: (int, int) -> QToolButton
        """Return the button at i-t row and j-th column.
        """
        item = self.__sidebarLayout.itemAt(i)
        row = item.widget()
        item = row.layout().itemAt(j)
        return item.widget()

    def triggeredAction(self):
        # type: () -> Optional[QAction]
        """Return the action that was triggered by the user.
        """
        return self.__triggeredAction

    def showEvent(self, event):
        # Clear the triggered action before show.
        self.__triggeredAction = None
        super().showEvent(event)

    def __on_actionTriggered(self, action):
        # type: (QAction) -> None
        """Called when the button action is triggered.
        """
        self.triggered.emit(action)
        self.__triggeredAction = action
