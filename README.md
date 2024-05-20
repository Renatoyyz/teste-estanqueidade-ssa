# Projeto Bancada de testes de estanqueidade

Um  projeto para controlar uma bancada que testa quatro peças automotivas quanto a sua estanqueidade

## Pré-requisitos para o sistema

Para montar um ambiente de desenvolvimento python:

```text
Python 3.8 ou superior
pip 20.0 ou superior
virtualenv 20.4 ou superior
```

Criando o ambiente virtual:

```text
python -m venv <nome-ambiente>
```

Ativar o embiente:

```text
source nome_ambiente/bin/activate
```

Com o ambiente ativado instalamos as dependências:

```text
pip install --upgrade pip
pip install -r requirements.txt
```

Para atualizar o arquivo requirements.txt cada vez que for atualizando pacotes:

```text
pip freeze > requirements.txt
```

## Para instalar o PyQt5

O PyQt tem que ser instalado via pacote

```text
sudo apt-get update
sudo apt-get install qt5-default
sudo apt-get install qtcreator
```

## Para instalar o QT Designer

```text
sudo apt install qttools5-dev-tools
depois execute em linha de comando:
>designer
```

Depois de instalado globalmente:

```text
ln -s /usr/lib/python3/dist-packages/PyQt5/ .env/lib/python3.11/site-packages/PyQt5
```

Onde '.env' é o ambiente que foi criado e pode ser qualquer nome.
Isso garante que o ambiente virtual acesse o pacote instalado globalmente.

## Com o pacote PyQt5 instalado e o Qt Designer instalado

Com o Qt Designer desenvolva a tela com extensão .ui e em seguida, no direório salvo execute o comando:

```text
pyuic5 -x arquivo.ui -o arquivo.py
```

Para gerar recursos de imagens no PyQt5:

```text
pyrcc5 nome_do_recurso.qrc -o nome_do_arquivo.py
```

Esse arquivo .qrc é gerado no QT Designer e com o comando pyrcc5 faz-se a conversão para a extensão .py

Fazer comando para que inicie o Raspberry rodando a aplicação:

a) Primeiro, abra o terminal e digite o seguinte comando para criar um arquivo .desktop no diretório autostart:

```text
sudo mousepad /etc/xdg/autostart/display.desktop .
```

Usamos display.desktop como nome de arquivo, mas você pode nomear o arquivo da área de trabalho como quiser.

b) No arquivo .desktop, adicione as seguintes linhas de código:

```text
[Desktop Entry]
Name=choque-termico
Exec=/usr/bin/python /home/maeda/choque-termico/main.py
```

O diretório /usr/bin/pythyon é onde está instalado o python,normalmente no raspberry esse é o local padrão.
