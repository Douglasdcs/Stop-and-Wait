import socket
from time import *
from Pacote import *
import pickle
import os

# RECEBIMENTO ----------------------------------------------------------------------------------------------------------
# Envia ACK confirmando o recebimento do pacote
def envia_ack(conn_socket, pack_ack, adrr):
    # Exclui dados no envio do ACK
    pack_ack.set_dados(None)
    # Converte para dicionário e serializa os dados
    pack_serial = pickle.dumps(pack_ack.__dict__)
    conn_socket.sendto(bytes(pack_serial), adrr)


# Adiciona no Objeto <Pacote> as informações do ACK
def cria_ack_do_pacote(pack, received_time):
    # Salva o tempo de recebimento no cliente
    pack.set_received_time(received_time)
    # Informa que o pacote foi recebido
    pack.set_received(True)
    return pack


# Função que recebe o pacote enviado pelo server
def recebe_arq(conn_socket):
    datagrama, adrr = conn_socket.recvfrom(1024)
    received_time = time()
    # Passando para dict novamente
    datagrama = pickle.loads(datagrama)
    pack = decoder_dict(datagrama)
    # Criando o ACK
    pack_ack = cria_ack_do_pacote(pack, received_time)
    return pack_ack, adrr


# Função que salva os dados recebidos
def salvando_dados(data, nome):
    file = open("C:/Users/dougl/UFOP/+EE/9º Período - PLE/Redes II/Trabalho Prático/Trab v2 - Stop and Wait/server/"
                + nome, "wb")
    for d in data:
        file.write(d)
    file.close()


# Função principal que controla a entrada dos pacotes e saída dos ACKs
def recebendo_arquivo(conn_socket, nome):
    i = 0
    data = []
    try:
        while True:
            # Recebe parte do arquivo. Se o envio do ack falhar ele retorna a esse mesmo ponto.
            pack_ack, adrr = recebe_arq(conn_socket)
            # Se o número de sequência for o que estamos esperando, salva os dados e passa para o próximo.
            if pack_ack.get_num_seq() == bin(i):
                rtt_recebimento.append(time() - pack_ack.get_sended_time())
                # Salva dados recebidos em uma lista
                data.append(pack_ack.get_dados())
                # Proximo seq_number
                i = i + 1
            # Envia ACK. Remove dados antes do envio.
            envia_ack(conn_socket, pack_ack, adrr)
            # Se for o último pacote sai do laço        *** tratar caso do ultimo pacote
            if pack_ack.get_last():
                break
        # Salva o arquivo recebido
        salvando_dados(data, nome)
    except socket.timeout:
        pass


# ENVIO ----------------------------------------------------------------------------------------------------------------
# Função que recebe um dicionário e transforma em um objeto tipo Pacote
def decoder_dict(dados_json):
    # dados_json = json.loads(dados_json)
    pack = Pacote()
    pack.set_num_seq(dados_json["num_seq"])
    pack.set_dados(dados_json["data"])
    pack.set_sender_adress(dados_json["sender_adress"])
    pack.set_receiver_adress(dados_json["receiver_adress"])
    pack.set_sended(dados_json["sended"])
    pack.set_sended_time(dados_json["sended_time"])
    pack.set_last(dados_json["last"])
    return pack


# Função que recebe os dados lidos no arquivo para envio e cria o pacote para envio
def cria_pacote(data, i, endereco, fim):
    pack = Pacote()
    pack.set_num_seq(bin(i))
    pack.set_dados(data)
    pack.set_sender_adress((host, port))
    pack.set_receiver_adress(endereco)
    pack.set_sended(True)
    pack.set_sended_time(time())
    pack.set_last(fim)
    return pack


# Verifica se o Número de sequência é diferente. Retorna True caso seja.
def verifica_ack(received_pack, i):
    return received_pack.get_num_seq() != bin(i)


# * Função de controle que faz o envio dos arquivos para o cliente
def envia_arquivo(server_socket, endereco, nome):
    # Define time out em segundos
    server_socket.settimeout(time_out)
    # Arquivo de envio - Se não existir sai da conexão
    try:
        file = open("C:/Users/dougl/UFOP/+EE/9º Período - PLE/Redes II/Trabalho Prático/Trab v2 - Stop and Wait/server/"
                    + nome, "rb")
    except FileNotFoundError:
        return
    # Referência do seq_number
    i = 0
    fim = False
    resending = False
    data = 0
    cont_loss_pack = 0
    cont_pack = 0
    try:
        while True:
            if not resending:
                data = file.read(buffer)
            size = len(data)
            # Indica que é o último arquivo
            if size < buffer:
                fim = True
            # Função que cria o pacote              1 - Cria pacote
            pack = cria_pacote(data, i, endereco, fim)
            # Enviando um dicionário
            pack_dict = pack.__dict__
            pack_dict = pickle.dumps(pack_dict)   # Serial
            # print(pack_dict)
            # # Salva um json para ver
            # if i == 0:
            #     file2 = open("pack.json", "w")
            #     file2.writelines(pack_json)
            #     file2.close()
            # Enviando o pacote                     2 - Envia pacote
            server_socket.sendto(bytes(pack_dict), endereco)

            # Wait                                  3 - Recebe Pacote
            received_ack, endereco = server_socket.recvfrom(1024)
            # print(received_ack)
            # Converte para dict
            received_ack = pickle.loads(received_ack)
            # Decodifica Ack para objeto <Pacote>
            received_ack = decoder_dict(received_ack)
            # Verifica se ele é o ACK esperado      4 - Verifica pacote
            if verifica_ack(received_ack, i):
                print("ACK modified. Resending")
                resending = True
                cont_loss_pack = cont_loss_pack + 1
            else:
                rtt_envio.append(time() - received_ack.get_sended_time())
                i = i + 1
                resending = False
            # Se foi o último pacote e ele foi recebido corretamente, saí do laço
            if fim and not resending:
                print("Concluído!")
                cont_pack = i
                break
        print("Pacotes: ", cont_pack)
        print("Pacotes perdidos: ", cont_loss_pack)
        file.close()
    except socket.timeout:
        pass


# Função que envia os arquivos presentes no sistema e opção de baixar ou enviar
def envia_opcao(server_socket, endereco):
    texto = "-----------------------"
    arquivos = os.listdir("C:/Users/dougl/UFOP/+EE/9º Período - PLE/Redes II/Trabalho Prático/Trab v2 - Stop and Wait/"
                          "server/")
    texto = texto + "\nOpção 1 - Baixar\nOpção 2 - Enviar\n---Lista de arquivos---\n"
    # Concatena
    for arq in arquivos:
        texto = texto + arq + '\n'
    texto = texto + "-----------------------"
    # Enviando as opções para o cliente
    server_socket.sendto(bytes(texto, encoding='utf-8'), endereco)


# Recebe a opção escolhida pelo cliente
def recebe_opcao(server_socket):
    op, endereco = server_socket.recvfrom(1024)
    op = int(op.decode('utf-8'))
    return op


# Função que recebe nome do arquivo de envio/recebimento para o cliente
def recebe_nome_do_arquivo(server_socket):
    nome, endereco = server_socket.recvfrom(1024)
    nome = nome.decode('utf-8')
    return nome


# Verifica senha recebida do cliente
def verifica_senha(server_socket):
    passw, endereco = server_socket.recvfrom(1024)
    passw = passw.decode('utf-8')
    if passw == senha:
        return 1
    else:
        return 0


# Indica ao cliente se a senha foi aceita ou não
def envia_confirmacao(server_socket, endereco, accepted):
    server_socket.sendto(bytes(str(accepted), encoding='utf-8'), endereco)


# Loop que espera por conexão com algum cliente
def espera_conexao(server_socket):
    # Laço infinito
    while True:
        # Define time out em segundos           ***
        server_socket.settimeout(time_out*1000)
        # Recebe o pedido do cliente - (UDP troca o accept pelo recvfrom)
        msg, endereco = server_socket.recvfrom(1024)
        print("Server conectado por: ", endereco)
        print("Mensagem: ", msg)
        # Função que envia os arquivos presentes no sistema e opção de baixar ou enviar
        envia_opcao(server_socket, endereco)
        # Função que recebe a opção escolhida
        op = recebe_opcao(server_socket)
        nome = recebe_nome_do_arquivo(server_socket)
        if op == 1:
            # Função que envia ao cliente o arquivo
            envia_arquivo(server_socket, endereco, nome)
        elif op == 2:
            # Recebe senha e verifica. 1-aceito e 0-Recusado
            accepted = verifica_senha(server_socket)
            # Envia ao cliente a confirmação. 1-aceito e 0-Recusado
            envia_confirmacao(server_socket, endereco, accepted)
            if accepted:
                # print("Recebendo arquivo..")
                recebendo_arquivo(server_socket, nome)
            # Fazer função que verifica senha e recebe
        else:
            pass
        print(rtt_envio)
        print(rtt_recebimento)


# Configurações do server
host = "localhost"
port = 1994
# Tamanho dos dados para envio
buffer = 512  # 512 bytes
time_out = 5  # 5s
senha = "12345"
rtt_envio = []
rtt_recebimento = []


if __name__ == '__main__':
    # Configurações do socket. AF_INET = IP, SOCK_STREAM = TCP e SOCK_DGRAM = UDP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Tipo UDP/IP
    # garante que o socket será destruído (pode ser reusado) após uma interrupção da execução
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Vínculo com o server criado. Como o cliente fará a conexão.
    server_socket.bind((host, port))
    print("Server em funcionamento!")
    # Inicia loop
    espera_conexao(server_socket)
