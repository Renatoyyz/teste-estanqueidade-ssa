# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'View/tela_inicial.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_TelaInicial(object):
    def setupUi(self, TelaInicial):
        TelaInicial.setObjectName("TelaInicial")
        TelaInicial.resize(1024, 768)
        self.btIniciar = QtWidgets.QPushButton(TelaInicial)
        self.btIniciar.setGeometry(QtCore.QRect(120, 390, 212, 102))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.btIniciar.setFont(font)
        self.btIniciar.setObjectName("btIniciar")
        self.btConfigurar = QtWidgets.QPushButton(TelaInicial)
        self.btConfigurar.setGeometry(QtCore.QRect(690, 390, 212, 102))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.btConfigurar.setFont(font)
        self.btConfigurar.setObjectName("btConfigurar")
        self.lbLogo = QtWidgets.QLabel(TelaInicial)
        self.lbLogo.setGeometry(QtCore.QRect(23, 40, 981, 210))
        self.lbLogo.setStyleSheet("border-image: url(:/logo/logo.png);")
        self.lbLogo.setText("")
        self.lbLogo.setObjectName("lbLogo")

        self.retranslateUi(TelaInicial)
        QtCore.QMetaObject.connectSlotsByName(TelaInicial)

    def retranslateUi(self, TelaInicial):
        _translate = QtCore.QCoreApplication.translate
        TelaInicial.setWindowTitle(_translate("TelaInicial", "Form"))
        self.btIniciar.setText(_translate("TelaInicial", "INICIAR"))
        self.btConfigurar.setText(_translate("TelaInicial", "MENU"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    TelaInicial = QtWidgets.QWidget()
    ui = Ui_TelaInicial()
    ui.setupUi(TelaInicial)
    TelaInicial.show()
    sys.exit(app.exec_())
