from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, QThread
import time

from View.tela_operacao_manual import Ui_OperacaoManual

class Operacao(QObject):
    sinal_atualizar = pyqtSignal(str)# Inicializa com a quantidade de variáveis que se deseja

    def __init__(self, instancia):
        super().__init__()
        self.instancia = instancia
        self._running = True
        self._ofset_temo = 0

    def thread_atualizar_valor(self):
        while self._running == True:
            # Obtém o valor atualizado do dado (ou qualquer outra lógica necessária)

            variavel = ""
            # print(valor_atualizado)

            # Emite o sinal para atualizar a interface do usuário
            self.sinal_atualizar.emit(variavel)

            # Aguarda 1 segundo antes de atualizar novamente
            QApplication.processEvents()
            time.sleep(0.5)

    def parar(self):
        self._running = False


class OperacaoManual(QDialog):
    def __init__(self, dado=None, io=None):
        super().__init__()

        self.io = io
        self.dado = dado

        # Configuração da interface do usuário gerada pelo Qt Designer
        self.ui = Ui_OperacaoManual()
        self.ui.setupUi(self)

        # Remover a barra de título e ocultar os botões de maximizar e minimizar
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowState.WindowMaximized)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Maximizar a janela
        # self.showMaximized()
        if self.dado.full_scream == True:
            self.setWindowState(Qt.WindowState.WindowFullScreen)

        self.ui.btVoltar.clicked.connect(self.voltar)

        # Inicializar o atualizador em uma nova thread
        self.atualizador = Operacao(self)
        self.atualizador.sinal_atualizar.connect(self.thread_operacao)
        self.atualizador_thread = QThread()
        self.atualizador.moveToThread(self.atualizador_thread)
        self.atualizador_thread.started.connect(self.atualizador.thread_atualizar_valor)
        self.atualizador_thread.start()
    
    def thread_operacao(self):
        pass

    def voltar(self):
        self.dado.set_telas(self.dado.TELA_INICIAL)
        self.close()

    def closeEvent(self, event):
        event.accept()