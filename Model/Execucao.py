from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, QThread
import time

from View.tela_execucao import Ui_TelaExecucao

class ExecucaoThread(QThread):
    sinal_atualizar = pyqtSignal(str, int, int)# Inicializa com a quantidade de variáveis que se deseja
    
    def __init__(self, instancia):
        super().__init__()
        self.instancia = instancia
        self._running = True
        self.invazao = False
        self.botao_emergencia = False

    def run(self):
        while self._running == True:
            try:
                if self.instancia.io.io_rpi.botao_esquerdo == 0 and self.instancia.io.io_rpi.botao_direito == 0:
                    self.executa_teste()
                self.sinal_atualizar.emit("mensagem",1,2)
                QThread.msleep(500)
            except Exception as e:
                print(f"Erro na Thread Operacao {e}")
    
    def executa_teste(self):
        self.instancia.io.desliga_lateral()
        if self.timer_com_erro(4) == True:
            self.instancia.io.liga_principal()
            if self.timer_com_erro(4) == True:
                 self.instancia.io.liga_lateral()
                 if self.timer_com_erro(4) == True:
                     self.instancia.io.start_ateq()
                     # Parei aqui...
                 


    def timer_com_erro(self, t):
        tempo = int(t*1000)

        for _ in range(tempo):
            if self.instancia.io.io_rpi.cortina_luz == 1:
                self.invazao = True
                return False
            time.sleep(0.001)
        return True

    def iniciar(self):
        self._running = True
        self.start()

    def parar(self):
        self._running = False

class Execucao(QDialog):
    def __init__(self, dado=None, io=None):
        super().__init__()

        self.io = io
        self.dado = dado

        # Configuração da interface do usuário gerada pelo Qt Designer
        self.ui = Ui_TelaExecucao()
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
        # Atualizador Thread
        self.atualizador = ExecucaoThread(self)
        self.atualizador.sinal_atualizar.connect(self.thread_execucao)
        self.atualizador.iniciar()
        QApplication.processEvents()  # Mantém a UI responsiva após iniciar as threads

        self.config()

    def thread_execucao(self,msg, passou, fail):
        print("Renato")

    def config(self):
        self.io.desliga_lateral()
        time.sleep(1)
        self.io.desliga_principal()
        time.sleep(1)
        self.io.desliga_marca()

    def voltar(self):
        self.close()

    def closeEvent(self, event):
        self.config()
        self.atualizador.parar()  # Parar a thread do atualizador
        event.accept()