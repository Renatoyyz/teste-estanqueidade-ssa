from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import Qt,QThread, QCoreApplication, QObject, pyqtSignal, QThread, QTimer, QEventLoop
import time

from View.tela_operacao_manual import Ui_OperacaoManual

class Operacao(QThread):
    sinal_atualizar = pyqtSignal(str, int, int)# Inicializa com a quantidade de variáveis que se deseja

    def __init__(self, instancia):
        super().__init__()
        self.instancia = instancia
        self._running = True
        self._ofset_temo = 0
        self._cnt_tempo_maximo = 0

    def run(self):
        while self._running == True:
            try:
                # Obtém o valor atualizado do dado (ou qualquer outra lógica necessária)

                variavel = ""

                if self.instancia._inicia_teste == True:
                    # Dá o start do ateq
                    self.instancia.io.wp_8025(self.instancia.dado.ADR_MOD2, 2, 1)
                    time.sleep(0.2)
                    self.instancia.io.wp_8025(self.instancia.dado.ADR_MOD2, 2, 0)

                    self.instancia.TEMPO_MAX = int(self.instancia.ui.spinTempoTeste.text())

                    while (self.instancia.io.io_rpi.passa_ateq == 1 and self.instancia.io.io_rpi.fail_ateq == 1) and self._cnt_tempo_maximo < self.instancia.TEMPO_MAX and self.instancia._inicia_teste == True:
                        self._cnt_tempo_maximo+=1
                        print(f"Tempo correndo: {self._cnt_tempo_maximo}")
                        time.sleep(1)
                    if (self.instancia.io.io_rpi.passa_ateq == 1 and self.instancia.io.io_rpi.fail_ateq == 1 and self.instancia._inicia_teste == True):
                        variavel = "Sem resposta do ATEQ."
                        # Emite o sinal para atualizar a interface do usuário
                        self.sinal_atualizar.emit(variavel,self.instancia.io.io_rpi.passa_ateq,self.instancia.io.io_rpi.fail_ateq)
                    elif self.instancia.io.io_rpi.passa_ateq == 0 and self.instancia._inicia_teste == True:
                        variavel = "PASSOU"
                        # Emite o sinal para atualizar a interface do usuário
                        self.sinal_atualizar.emit(variavel,self.instancia.io.io_rpi.passa_ateq,self.instancia.io.io_rpi.fail_ateq)
                    elif self.instancia.io.io_rpi.fail_ateq == 0 and self.instancia._inicia_teste == True:
                        variavel = "NÃO PASSOU"
                        # Emite o sinal para atualizar a interface do usuário
                        self.sinal_atualizar.emit(variavel,self.instancia.io.io_rpi.passa_ateq,self.instancia.io.io_rpi.fail_ateq)
                    
                    
                    self._cnt_tempo_maximo = 0
                    self.instancia._inicia_teste=False
                else:
                    pass

                

                # Aguarda 1 segundo antes de atualizar novamente
                # QApplication.processEvents()
            except Exception as e:
                print(f"Erro na Thread Operacao {e}")
            
            QThread.msleep(500)

    def iniciar(self):
        self._running = True
        self.start()

    def parar(self):
        self._running = False

class OperacaoManual(QDialog):
    def __init__(self, dado=None, io=None):
        super().__init__()

        self.io = io
        self.dado = dado
        self.TEMPO_MAX = self.dado.TEMPO_ESPERA_ATEQ

        self._inicia_teste = False
        self._translate = QCoreApplication.translate

        self.CINZA = "171, 171, 171"
        self.VERDE = "170, 255, 127"
        self.VERMELHO = "255, 0, 0"

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

        # Liga e desliga Lateral - operação manual
        self.ui.btVoltar.clicked.connect(self.voltar)
        self.ui.btLigaLateral_1.clicked.connect(self.liga_lateral_1)
        self.ui.btLigaLateral_2.clicked.connect(self.liga_lateral_2)
        self.ui.btLigaLateral_3.clicked.connect(self.liga_lateral_3)
        self.ui.btLigaLateral_4.clicked.connect(self.liga_lateral_4)
        self.ui.btDesligaLateral_1.clicked.connect(self.desliga_lateral_1)
        self.ui.btDesligaLateral_2.clicked.connect(self.desliga_lateral_2)
        self.ui.btDesligaLateral_3.clicked.connect(self.desliga_lateral_3)
        self.ui.btDesligaLateral_4.clicked.connect(self.desliga_lateral_4)

        # Liga e desliga Principal - operação manual
        self.ui.btLigaPrincipal_1.clicked.connect(self.liga_principal_1)
        self.ui.btLigaPrincipal_2.clicked.connect(self.liga_principal_2)
        self.ui.btLigaPrincipal_3.clicked.connect(self.liga_principal_3)
        self.ui.btLigaPrincipal_4.clicked.connect(self.liga_principal_4)
        self.ui.btDesligaPrincipal_1.clicked.connect(self.desliga_principal_1)
        self.ui.btDesligaPrincipal_2.clicked.connect(self.desliga_principal_2)
        self.ui.btDesligaPrincipal_3.clicked.connect(self.desliga_principal_3)
        self.ui.btDesligaPrincipal_4.clicked.connect(self.desliga_principal_4)

        # Liga e desliga Marcação - operação manual
        self.ui.btLigaMarca_1.clicked.connect(self.liga_marca_1)
        self.ui.btLigaMarca_2.clicked.connect(self.liga_marca_2)
        self.ui.btLigaMarca_3.clicked.connect(self.liga_marca_3)
        self.ui.btLigaMarca_4.clicked.connect(self.liga_marca_4)
        self.ui.btDesligaMarca_1.clicked.connect(self.desliga_marca_1)
        self.ui.btDesligaMarca_2.clicked.connect(self.desliga_marca_2)
        self.ui.btDesligaMarca_3.clicked.connect(self.desliga_marca_3)
        self.ui.btDesligaMarca_4.clicked.connect(self.desliga_marca_4)


        self.ui.btStartAteq.clicked.connect(self.start_ateq)
        self.ui.btResettAteq.clicked.connect(self.reset_ateq)

        # Inicializar o atualizador em uma nova thread
        # Atualizador Thread
        self.atualizador = Operacao(self)
        self.atualizador.sinal_atualizar.connect(self.thread_operacao)
        self.atualizador.iniciar()
        QApplication.processEvents()  # Mantém a UI responsiva após iniciar as threads

        self.ui.spinTempoTeste.setValue(self.TEMPO_MAX)

        # setText(str(self.TEMPO_MAX))

    def start_ateq(self):
        msg = "TESTANDO!"
        self.ui.lbPassouNaoPassou.setStyleSheet(f"background-color: rgb({self.CINZA});")
        self.ui.lbPassouNaoPassou.setText(self._translate("OperacaoManual", f"<html><head/><body><p align=\"center\">{msg}</p></body></html>"))

        self._inicia_teste = True


    def reset_ateq(self):
        if self._inicia_teste == True:
            msg = "CANCELADO"
            # Dá o Reset do ateq
            self.io.wp_8025(self.dado.ADR_MOD2, 1, 1)
            time.sleep(0.2)
            self.io.wp_8025(self.dado.ADR_MOD2, 1, 0)
            self.ui.lbPassouNaoPassou.setStyleSheet(f"background-color: rgb({self.CINZA});")
            self.ui.lbPassouNaoPassou.setText(self._translate("OperacaoManual", f"<html><head/><body><p align=\"center\">{msg}</p></body></html>"))
            self._inicia_teste = False
    
    def liga_lateral_1(self):
        self.io.wp_8025(self.dado.ADR_MOD1, 5, 1)
    def liga_lateral_2(self):
        self.io.wp_8025(self.dado.ADR_MOD1, 6, 1)
    def liga_lateral_3(self):
        self.io.wp_8025(self.dado.ADR_MOD1, 7, 1)
    def liga_lateral_4(self):
        self.io.wp_8025(self.dado.ADR_MOD1, 8, 1)

    def desliga_lateral_1(self):
        self.io.wp_8025(self.dado.ADR_MOD1, 5, 0)
    def desliga_lateral_2(self):
        self.io.wp_8025(self.dado.ADR_MOD1, 6, 0)
    def desliga_lateral_3(self):
        self.io.wp_8025(self.dado.ADR_MOD1, 7, 0)
    def desliga_lateral_4(self):
        self.io.wp_8025(self.dado.ADR_MOD1, 8, 0)
    
    def liga_principal_1(self):
        self.desliga_lateral_1()
        time.sleep(1)
        self.io.wp_8025(self.dado.ADR_MOD1, 1, 1)
    def liga_principal_2(self):
        self.desliga_lateral_2()
        time.sleep(1)
        self.io.wp_8025(self.dado.ADR_MOD1, 2, 1)
    def liga_principal_3(self):
        self.desliga_lateral_3()
        time.sleep(1)
        self.io.wp_8025(self.dado.ADR_MOD1, 3, 1)
    def liga_principal_4(self):
        self.desliga_lateral_4()
        time.sleep(1)
        self.io.wp_8025(self.dado.ADR_MOD1, 4, 1)

    def desliga_principal_1(self):
        self.desliga_lateral_1()
        time.sleep(1)
        self.io.wp_8025(self.dado.ADR_MOD1, 1, 0)
    def desliga_principal_2(self):
        self.desliga_lateral_2()
        time.sleep(1)
        self.io.wp_8025(self.dado.ADR_MOD1, 2, 0)
    def desliga_principal_3(self):
        self.desliga_lateral_3()
        time.sleep(1)
        self.io.wp_8025(self.dado.ADR_MOD1, 3, 0)
    def desliga_principal_4(self):
        self.desliga_lateral_4()
        time.sleep(1)
        self.io.wp_8025(self.dado.ADR_MOD1, 4, 0)

    def liga_marca_1(self):
        self.io.wp_8025(self.dado.ADR_MOD2, 8, 1)
    def liga_marca_2(self):
        self.io.wp_8025(self.dado.ADR_MOD2, 8, 1)
    def liga_marca_3(self):
        self.io.wp_8025(self.dado.ADR_MOD2, 8, 1)
    def liga_marca_4(self):
        self.io.wp_8025(self.dado.ADR_MOD2, 8, 1)

    def desliga_marca_1(self):
        self.io.wp_8025(self.dado.ADR_MOD2, 8, 0)
    def desliga_marca_2(self):
        self.io.wp_8025(self.dado.ADR_MOD2, 8, 0)
    def desliga_marca_3(self):
        self.io.wp_8025(self.dado.ADR_MOD2, 8, 0)
    def desliga_marca_4(self):
        self.io.wp_8025(self.dado.ADR_MOD2, 8, 0)

    def thread_operacao(self,msg, passou, fail):
        if passou == 0:
            self.ui.lbPassouNaoPassou.setStyleSheet(f"background-color: rgb({self.VERDE});")
            self.ui.lbPassouNaoPassou.setText(self._translate("OperacaoManual", f"<html><head/><body><p align=\"center\">{msg}</p></body></html>"))
        elif fail == 0:
            self.ui.lbPassouNaoPassou.setStyleSheet(f"background-color: rgb({self.VERMELHO});")
            self.ui.lbPassouNaoPassou.setText(self._translate("OperacaoManual", f"<html><head/><body><p align=\"center\">{msg}</p></body></html>"))
        elif passou == 1 and fail == 1:
            self.ui.lbPassouNaoPassou.setStyleSheet(f"background-color: rgb({self.VERMELHO});")
            self.ui.lbPassouNaoPassou.setText(self._translate("OperacaoManual", f"<html><head/><body><p align=\"center\">{msg}</p></body></html>"))
        QApplication.processEvents()

    def voltar(self):
        self.dado.set_telas(self.dado.TELA_INICIAL)
        self.close()

    def closeEvent(self, event):
        self.dado.set_tempo_espera_ateq(int(self.ui.spinTempoTeste.text()))
        self.atualizador.parar()  # Parar a thread do atualizador
        event.accept()