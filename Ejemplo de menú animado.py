import sys, math
from PyQt5 import QtCore, QtGui, QtWidgets

class RadialMenu(QtWidgets.QWidget):
    """ Menú radial anclado en la esquina superior derecha; arco 90º hacia abajo-izquierda. """
    toggled = QtCore.pyqtSignal(bool)

    def __init__(self, actions, radius=85, start_angle_deg=90, arc_span_deg=90, edge_margin=16, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Parámetros del menú
        self.radius = radius
        self.start_angle = math.radians(start_angle_deg)   # 90º = abajo
        self.arc_span = math.radians(arc_span_deg)         # 90º de arco (90→180) hasta izquierda
        self.edge_margin = edge_margin
        self.opened = False
        self.anim_duration = 220


        # Botón central (llave inglesa)
        self.center_btn = QtWidgets.QToolButton(self)
        self.center_btn.setText("🔧")
        self.center_btn.setToolTip("Configuración")
        self.center_btn.setIconSize(QtCore.QSize(28, 28))
        self.center_btn.setAutoRaise(True)
        self.center_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.center_btn.clicked.connect(self.toggle)
        self.center_btn.setStyleSheet("""
            QToolButton { background: #ffffff; border: 1px solid #d0d0d0; border-radius: 14px; padding: 6px 10px; }
            QToolButton:hover { background: #f2f2f2; }
        """)
        effect = QtWidgets.QGraphicsDropShadowEffect(blurRadius=18, xOffset=0, yOffset=4)
        effect.setColor(QtGui.QColor(0, 0, 0, 80))
        self.center_btn.setGraphicsEffect(effect)

        # Botones de opciones
        self.option_buttons = []
        for text, callback in actions:
            b = QtWidgets.QToolButton(self)
            b.setText(text)
            b.setAutoRaise(True)
            b.setCursor(QtCore.Qt.PointingHandCursor)
            b.clicked.connect(callback)
            b.hide()
            b.setStyleSheet("""
                QToolButton { background: #ffffff; border: 1px solid #d0d0d0; border-radius: 12px; padding: 6px 10px; color: #222; }
                QToolButton:hover { background: #f6f6f6; }
            """)
            self.option_buttons.append(b)

        self.anim_group = QtCore.QParallelAnimationGroup(self)

    # --- Anclaje esquina superior derecha ---
    def _anchor_point(self):
        csz = self.center_btn.sizeHint()
        x = self.width() - self.edge_margin - csz.width() // 2
        y = self.edge_margin + csz.height() // 2
        return QtCore.QPoint(x, y)

    def resizeEvent(self, event):
        csz = self.center_btn.sizeHint()
        c = self._anchor_point() - QtCore.QPoint(csz.width() // 2, csz.height() // 2)
        self.center_btn.setGeometry(c.x(), c.y(), csz.width(), csz.height())
        # reposicionar botones según estado
        self._place_options(self.opened)
        super().resizeEvent(event)

    # --- Posiciones objetivo a lo largo de un arco (90→180: abajo→izquierda) ---
    def _target_positions(self):
        n = len(self.option_buttons)
        if n == 0:
            return []
        # Distribución uniforme en el arco. Si hay 1, al centro del arco.
        steps = [0.5] if n == 1 else [i / (n - 1) for i in range(n)]
        targets = []
        cx = self.center_btn.geometry().center().x()
        cy = self.center_btn.geometry().center().y()
        for t in steps:
            angle = self.start_angle + t * self.arc_span
            x = cx + self.radius * math.cos(angle)
            y = cy + self.radius * math.sin(angle)
            targets.append(QtCore.QPoint(int(x), int(y)))
        return targets

    def _place_options(self, expanded: bool):
        center = self.center_btn.geometry().center()
        targets = self._target_positions()
        for i, btn in enumerate(self.option_buttons):
            s = btn.sizeHint()
            if expanded:
                pos = targets[i] - QtCore.QPoint(s.width() // 2, s.height() // 2)
                btn.move(pos)
                btn.show()
            else:
                pos = center - QtCore.QPoint(s.width() // 2, s.height() // 2)
                btn.move(pos)
                if not self.opened:
                    btn.hide()

    # --- Animación abrir/cerrar ---
    def animate(self, expand: bool):
        self.anim_group.stop()
        self.anim_group = QtCore.QParallelAnimationGroup(self)

        center = self.center_btn.geometry().center()
        center_pos = lambda b: center - QtCore.QPoint(b.sizeHint().width() // 2, b.sizeHint().height() // 2)
        targets = self._target_positions()

        for i, btn in enumerate(self.option_buttons):
            btn.show()
            anim = QtCore.QPropertyAnimation(btn, b"pos", self)
            anim.setDuration(self.anim_duration)
            anim.setEasingCurve(QtCore.QEasingCurve.OutBack if expand else QtCore.QEasingCurve.InBack)
            if expand:
                anim.setStartValue(center_pos(btn))
                end_pos = targets[i] - QtCore.QPoint(btn.sizeHint().width() // 2, btn.sizeHint().height() // 2)
                anim.setEndValue(end_pos)
            else:
                anim.setStartValue(btn.pos())
                anim.setEndValue(center_pos(btn))
            self.anim_group.addAnimation(anim)

        def on_finished():
            if not expand:
                for b in self.option_buttons:
                    b.hide()
            self.opened = expand
            self.toggled.emit(self.opened)

        self.anim_group.finished.connect(on_finished)
        self.anim_group.start()

    def toggle(self):
        self.animate(not self.opened)

class Demo(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menú radial claro (abajo-izquierda desde la esquina superior derecha)")
        self.resize(900, 600)

        container = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)

        stack = QtWidgets.QStackedLayout()
        stack.setStackingMode(QtWidgets.QStackedLayout.StackAll)

        # Fondo claro
        fondo = QtWidgets.QWidget()
        fondo.setStyleSheet("background: #f5f5f7;")
        stack.addWidget(fondo)

        # Overlay para el radial
        overlay = QtWidgets.QWidget()
        overlay.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        ov_lay = QtWidgets.QVBoxLayout(overlay)
        ov_lay.setContentsMargins(0, 0, 0, 0)

        actions = [
            ("Preferencias", lambda: print("Preferencias")),
            ("Tema",         lambda: print("Cambiar tema")),
            ("Cuenta",       lambda: print("Cuenta")),
            ("Ayuda",        lambda: print("Ayuda")),
            ("Atajos",       lambda: print("Atajos")),
            ("Acerca de",    lambda: print("Acerca de")),
        ]

        radial = RadialMenu(
            actions=actions,
            radius=200,           # distancia de los botones
            start_angle_deg=90,  # empieza ABAJO
            arc_span_deg=90,     # hasta IZQUIERDA
            edge_margin=16
        )

        ov_lay.addWidget(radial)
        stack.addWidget(overlay)

        lay.addLayout(stack)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = Demo()
    w.show()
    sys.exit(app.exec_())
