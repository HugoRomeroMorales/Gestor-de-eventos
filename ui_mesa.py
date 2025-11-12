# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1026, 710)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStyleSheet("QWidget#centralwidget{background:#9cd3ff;}")

        self.rootV = QtWidgets.QVBoxLayout(self.centralwidget)
        self.rootV.setObjectName("rootV")

        # ========== Row Main ==========
        self.rowMain = QtWidgets.QHBoxLayout()
        self.rowMain.setObjectName("rowMain")
        self.rootV.addLayout(self.rowMain)

        # ----- Left Panel -----
        self.leftPanel = QtWidgets.QVBoxLayout()
        self.leftPanel.setObjectName("leftPanel")
        self.rowMain.addLayout(self.leftPanel)

        # Top bar
        self.leftTopBar = QtWidgets.QHBoxLayout()
        self.leftTopBar.setObjectName("leftTopBar")
        self.leftPanel.addLayout(self.leftTopBar)

        self.btnBack = QtWidgets.QToolButton(self.centralwidget)
        self.btnBack.setObjectName("btnBack")
        self.btnBack.setToolTip("Volver")
        self.btnBack.setStyleSheet("QToolButton{font:16pt;background:transparent;border:none;}")
        self.btnBack.setText("<-")
        self.leftTopBar.addWidget(self.btnBack)

        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText("PushButton")
        self.leftTopBar.addWidget(self.pushButton)

        # Group Mesas
        self.gbMesas = QtWidgets.QGroupBox(self.centralwidget)
        self.gbMesas.setObjectName("gbMesas")
        self.gbMesas.setTitle("Mesas")
        self.gbMesas.setStyleSheet(
            "QGroupBox{background:#f2f2f2;border:1px solid #ddd;border-radius:6px;margin-top:12px;padding-top:10px;}"
            "QGroupBox::title{subcontrol-origin: margin;left:8px;}"
        )
        self.gbMesasV = QtWidgets.QVBoxLayout(self.gbMesas)
        self.gbMesasV.setObjectName("gbMesasV")
        self.tblMesas = QtWidgets.QTableWidget(self.gbMesas)
        self.tblMesas.setObjectName("tblMesas")
        self.gbMesasV.addWidget(self.tblMesas)
        self.leftPanel.addWidget(self.gbMesas)

        # Group Invitados
        self.gbInvitados = QtWidgets.QGroupBox(self.centralwidget)
        self.gbInvitados.setObjectName("gbInvitados")
        self.gbInvitados.setTitle("Invitados")
        self.gbInvitados.setStyleSheet(
            "QGroupBox{background:#f2f2f2;border:1px solid #ddd;border-radius:6px;margin-top:12px;padding-top:10px;}"
            "QGroupBox::title{subcontrol-origin: margin;left:8px;}"
        )
        self.gbInvitadosV = QtWidgets.QVBoxLayout(self.gbInvitados)
        self.gbInvitadosV.setObjectName("gbInvitadosV")
        self.tblInvitados = QtWidgets.QTableWidget(self.gbInvitados)
        self.tblInvitados.setObjectName("tblInvitados")
        self.gbInvitadosV.addWidget(self.tblInvitados)
        self.leftPanel.addWidget(self.gbInvitados)

        # ----- Right Panel -----
        self.rightPanel = QtWidgets.QVBoxLayout()
        self.rightPanel.setObjectName("rightPanel")
        self.rowMain.addLayout(self.rightPanel)

        # Top buttons
        self.topButtons = QtWidgets.QHBoxLayout()
        self.topButtons.setObjectName("topButtons")
        self.rightPanel.addLayout(self.topButtons)

        self.spacerTop = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.topButtons.addItem(self.spacerTop)

        self.btnConfirmar = QtWidgets.QPushButton(self.centralwidget)
        self.btnConfirmar.setObjectName("btnConfirmar")
        self.btnConfirmar.setText("Confirmar")
        self.btnConfirmar.setStyleSheet(
            "QPushButton{background:#00d35a;color:#000;font-weight:700;border:none;border-radius:6px;padding:8px 14px;}"
            "QPushButton:hover{filter:brightness(0.95);}"
        )
        self.topButtons.addWidget(self.btnConfirmar)

        self.btnAnadir = QtWidgets.QPushButton(self.centralwidget)
        self.btnAnadir.setObjectName("btnAnadir")
        self.btnAnadir.setText("Añadir")
        self.btnAnadir.setStyleSheet(
            "QPushButton{background:#31e36a;color:#000;font-weight:700;border:none;border-radius:6px;padding:8px 14px;}"
            "QPushButton:hover{filter:brightness(0.95);}"
        )
        self.topButtons.addWidget(self.btnAnadir)

        self.btnEliminar = QtWidgets.QPushButton(self.centralwidget)
        self.btnEliminar.setObjectName("btnEliminar")
        self.btnEliminar.setText("Eliminar")
        self.btnEliminar.setStyleSheet(
            "QPushButton{background:#ff3b30;color:#fff;font-weight:700;border:none;border-radius:6px;padding:8px 14px;}"
            "QPushButton:hover{filter:brightness(0.95);}"
        )
        self.topButtons.addWidget(self.btnEliminar)

        # Card Preview
        self.cardPreview = QtWidgets.QFrame(self.centralwidget)
        self.cardPreview.setObjectName("cardPreview")
        self.cardPreview.setStyleSheet("QFrame#cardPreview{background:#ffffff;border-radius:6px;}")
        self.cardV = QtWidgets.QVBoxLayout(self.cardPreview)
        self.cardV.setObjectName("cardV")

        # Arena circular (donde pintamos los iconos)
        self.arena = QtWidgets.QFrame(self.cardPreview)
        self.arena.setObjectName("arena")
        self.arena.setMinimumSize(QtCore.QSize(480, 420))
        self.arena.setStyleSheet("QFrame#arena{background:qradialgradient(cx:0.5,cy:0.5,radius:0.9,stop:0 #d1ecff, stop:1 #a8d7ff);border-radius:200px;}")
        self.cardV.addWidget(self.arena)

        # Burbuja central con info
        self.centerBubble = QtWidgets.QFrame(self.cardPreview)
        self.centerBubble.setObjectName("centerBubble")
        self.centerBubble.setStyleSheet("QFrame#centerBubble{background:#ffffff;border-radius:100px;border:1px solid rgba(0,0,0,10%);}")
        self.bubbleV = QtWidgets.QVBoxLayout(self.centerBubble)
        self.bubbleV.setObjectName("bubbleV")
        self.lblTituloMesa = QtWidgets.QLabel(self.centerBubble)
        self.lblTituloMesa.setObjectName("lblTituloMesa")
        self.lblTituloMesa.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTituloMesa.setText("Mesa 12")
        self.bubbleV.addWidget(self.lblTituloMesa)
        self.lblAsientos = QtWidgets.QLabel(self.centerBubble)
        self.lblAsientos.setObjectName("lblAsientos")
        self.lblAsientos.setAlignment(QtCore.Qt.AlignCenter)
        self.lblAsientos.setText("Asientos: 0/0")
        self.bubbleV.addWidget(self.lblAsientos)
        self.lblCompat = QtWidgets.QLabel(self.centerBubble)
        self.lblCompat.setObjectName("lblCompat")
        self.lblCompat.setAlignment(QtCore.Qt.AlignCenter)
        self.lblCompat.setText("Compatibilidad: 92")
        self.bubbleV.addWidget(self.lblCompat)

        self.cardV.addWidget(self.centerBubble)
        self.rightPanel.addWidget(self.cardPreview)

        # ========== Search Row ==========
        self.searchRow = QtWidgets.QHBoxLayout()
        self.searchRow.setObjectName("searchRow")
        self.rootV.addLayout(self.searchRow)

        self.spacerSearchLeft = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.searchRow.addItem(self.spacerSearchLeft)

        self.txtBuscar = QtWidgets.QLineEdit(self.centralwidget)
        self.txtBuscar.setObjectName("txtBuscar")
        self.txtBuscar.setPlaceholderText("Escribe aquí el evento que quieras buscar")
        self.txtBuscar.setStyleSheet("QLineEdit{background:#ffffff;border:1px solid #cfcfcf;border-radius:6px;padding:6px 10px;font:600 12pt 'Segoe UI';}")
        self.searchRow.addWidget(self.txtBuscar)

        self.btnBuscar = QtWidgets.QToolButton(self.centralwidget)
        self.btnBuscar.setObjectName("btnBuscar")
        self.btnBuscar.setText("Buscar")
        self.searchRow.addWidget(self.btnBuscar)

        self.spacerSearchRight = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.searchRow.addItem(self.spacerSearchRight)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle("Gestor de Eventos")
