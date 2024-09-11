import time

class Dado:
    def __init__(self):
        self.TELA_INICIAL = 0
        self.TELA_OPERACAO_MANUAL = 1

        self.ADR_MOD1 = 1
        self.ADR_MOD2 = 2

        self.TEMPO_ESPERA_ATEQ = 65  

        self._telas = self.TELA_INICIAL

        self.full_scream = True

    @property
    def telas(self):
        return self._telas
    
    def set_tempo_espera_ateq(self, tempo):
        self.TEMPO_ESPERA_ATEQ = tempo
    
    def set_telas(self,tela):
        self.print_status_tela(tela)
        self._telas = tela

    def print_status_tela(self, tela):
        if tela == self.TELA_INICIAL:
            print(f"Está na tela: INICIAL")
        elif tela == self.TELA_OPERACAO_MANUAL:
            print(f"Está na tela: OPERACAO_MANUAL")