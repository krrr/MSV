from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class ProgressIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timerId = -1
        self.delay = 80
        self.displayedWhenStopped = False
        self.color = QColor(Qt.black)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFocusPolicy(Qt.NoFocus)

    def isAnimated(self):
        return self.timerId != -1

    def setDisplayedWhenStopped(self, state):
        self.displayedWhenStopped = state
        self.update()

    def isDisplayedWhenStopped(self):
        return self.displayedWhenStopped

    def startAnimation(self):
        self.angle = 0

        if self.timerId == -1:
            self.timerId = self.startTimer(self.delay)

    def stopAnimation(self):
        if self.timerId != -1:
            self.killTimer(self.timerId)

        self.timerId = -1

        self.update()

    def setAnimationDelay(self, delay):
        if self.timerId != -1:
            self.killTimer(self.timerId)

        self.delay = delay

        if self.timerId != -1:
            self.timerId = self.startTimer(self.delay)

    def setColor(self, color):
        self.color = color
        self.update()

    def sizeHint(self):
        return QSize(20, 20)

    def heightForWidth(self, w):
        return w

    def timerEvent(self, _):
        self.angle = (self.angle+30) % 360
        self.update()

    def paintEvent(self, _):
        if not self.displayedWhenStopped and not self.isAnimated():
            return

        width = min(self.width(), self.height())

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        outerRadius = (width-1)*0.5
        innerRadius = (width-1)*0.5*0.38

        capsuleHeight = outerRadius - innerRadius
        capsuleWidth = capsuleHeight * .23 if width > 32 else capsuleHeight * .35
        capsuleRadius = capsuleWidth / 2

        for i in range(12):
            color = self.color
            color.setAlphaF(1.0 - (i/12.0))
            p.setPen(Qt.NoPen)
            p.setBrush(color)
            p.save()
            p.translate(self.rect().center())
            p.rotate(self.angle - i*30.0)
            p.drawRoundedRect(-capsuleWidth*0.5, -(innerRadius+capsuleHeight), capsuleWidth, capsuleHeight, capsuleRadius, capsuleRadius)
            p.restore()
