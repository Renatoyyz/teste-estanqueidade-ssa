from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt

from View.tela_inicial import Ui_TelaInicial

from Model.OperacaoManual import OperacaoManual
from Model.Execucao import Execucao

class TelaInicial(QMainWindow):
    def __init__(self, dado=None, io=None):
        super().__init__()

        self.io = io
        self.dado = dado
        self.dado.set_telas(self.dado.TELA_INICIAL)

        # Configuração da interface do usuário gerada pelo Qt Designer
        self.ui = Ui_TelaInicial()
        self.ui.setupUi(self)

        # Remover a barra de título e ocultar os botões de maximizar e minimizar
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowState.WindowMaximized)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Maximizar a janela
        # self.showMaximized()
        if self.dado.full_scream == True:
            self.setWindowState(Qt.WindowState.WindowFullScreen)

        self.mouseReleaseEvent = self.setfoccus
        self.ui.btConfigurar.clicked.connect(self.tela_configurar)
        self.ui.btIniciar.clicked.connect(self.tela_execucao)

        self.config()

    def config(self):
        self.io.habilita_cortina_luz()

    def tela_configurar(self):
        self.dado.set_telas(self.dado.TELA_OPERACAO_MANUAL)
        oper_manual = OperacaoManual(dado=self.dado, io=self.io)
        oper_manual.exec_()


    def tela_execucao(self):
        execucao = Execucao(dado=self.dado, io=self.io)
        execucao.exec_()

    def closeEvent(self, event):
        event.accept()

    def setfoccus(self, event):
        if self.io.io_rpi.botao_esquerdo == 0:
            self.close()