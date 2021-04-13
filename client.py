from socket import *
from Pacote import *
from time import *
import random as rdm
import pickle


# ENVIO DE ARQUIVOS ----------------------------------------------------------------------------------------------------
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


# Função de controle que faz o envio dos arquivos para o cliente
def envia_arquivo(server_socket, endereco, nome):
    # Define time out em segundos
    server_socket.settimeout(time_out)
    # Arquivo de envio
    file = open("C:/Users/dougl/UFOP/+EE/9º Período - PLE/Redes II/Trabalho Prático/Trab v2 - Stop and Wait/client/"
                + nome, "rb")
    # Referência do seq_number
    i = 0
    fim = False
    resending = False
    data = 0
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
        # Enviando o pacote                     2 - Envia pacote
        server_socket.sendto(bytes(pack_dict), endereco)
        # Wait                                  3 - Recebe Pacote
        received_ack, endereco = server_socket.recvfrom(1024)
        # Converte para dict
        received_ack = pickle.loads(received_ack)
        # Decodifica Ack para objeto <Pacote>
        received_ack = decoder_dict(received_ack)
        # Verifica se ele é o ACK esperado      4 - Verifica pacote
        if verifica_ack(received_ack, i):
            print("ACK modified. Resending")
            resending = True
        else:
            i = i + 1
            resending = False
        # Se foi o último pacote e ele foi recebido corretamente, saí do laço
        if fim and not resending:
            print("Arquivo enviado!")
            break

    file.close()


# RECEBIMENTO DE ARQUIVOS ----------------------------------------------------------------------------------------------
# decoder_dict -> ambos
# Função que recebe um dicionário e transforma em um objeto tipo Pacote
def decoder_dict(dados_json):
    # dados_json = json.loads(dados_json)
    pack = Pacote()
    pack.set_num_seq(dados_json["num_seq"])
    pack.set_dados(dados_json["data"])    # Não retorna os dados, apenas os parâmetros
    pack.set_sender_adress(dados_json["sender_adress"])
    pack.set_receiver_adress(dados_json["receiver_adress"])
    pack.set_sended(dados_json["sended"])
    pack.set_sended_time(dados_json["sended_time"])
    pack.set_last(dados_json["last"])
    return pack


# Adiciona no Objeto <Pacote> as informações do ACK
def cria_ack_do_pacote(pack, received_time):
    # Salva o tempo de recebimento no cliente
    pack.set_received_time(received_time)
    # Informa que o pacote foi recebido
    pack.set_received(True)
    return pack


# Envia ao server um pedido do arquivo
def pede_server(conn_socket, adrr):
    conn_socket.sendto("SYN. Cliente 1".encode('utf-8'), adrr)


# Envia ACK confirmando o recebimento do pacote
def envia_ack(conn_socket, pack_ack, adrr):
    # Exclui dados no envio do ACK
    pack_ack.set_dados(None)
    # Converte para dicionário e serializa os dados
    pack_serial = pickle.dumps(pack_ack.__dict__)
    # Converte para um json
    # pack_json = json.dumps(pack_ack.__dict__)
    # Envia Json
    conn_socket.sendto(bytes(pack_serial), adrr)


# Função que recebe o pacote enviado pelo server
def recebe_server(conn_socket):
    datagrama, adrr = conn_socket.recvfrom(1024)
    received_time = time()
    # Passando para dict novamente
    datagrama = pickle.loads(datagrama)
    # print(datagrama)
    # datagrama = datagrama.decode('utf-8')
    # Decodificando o pacote recebido para Objeto <Pacote>
    pack = decoder_dict(datagrama)
    # Criando o ACK
    pack_ack = cria_ack_do_pacote(pack, received_time)
    return pack_ack, adrr


# Função que salva os dados recebidos
def salvando_dados(data, nome):
    file = open("C:/Users/dougl/UFOP/+EE/9º Período - PLE/Redes II/Trabalho Prático/Trab v2 - Stop and Wait/client/" +
                nome, "wb")
    for d in data:
        file.write(d)
    file.close()


# Função para simular uma perda de 10% dos ACKs
def simula_perda_de_ack(pack_ack):
    if rdm.random() > 0.9:
        # TESTE: DEIXANDO PACOTES SE PERDER
        pack_ack.set_num_seq(bin(-1))
    return pack_ack


# Função principal que controla a entrada dos pacotes e saída dos ACKs
def recebendo_arquivo(conn_socket, nome):
    i = 0
    data = []
    while True:
        # Recebe parte do arquivo. Se o envio do ack falhar ele retorna a esse mesmo ponto.
        pack_ack, adrr = recebe_server(conn_socket)

        # Função que simula perdas de pacotes
        pack_ack = simula_perda_de_ack(pack_ack)

        # Se o número de sequência for o que estamos esperando, salva os dados e passa para o próximo.
        if pack_ack.get_num_seq() == bin(i):
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
    print("Arquivo recebido com sucesso!")


# Função que recebe a lista de arquivos disponíveis
def recebendo_lista_e_opcoes(conn_socket):
    # Recebe a lista de arquivos e opções
    msg, adrr = conn_socket.recvfrom(1024)
    msg = msg.decode('utf-8')
    print(msg)
    return msg


# Função que indica ao server a opção escolhida
def seleciona_opcao(conn_socket, adrr):
    ops = ["1", "2"]
    while True:
        op = input("Opção: ")
        if op not in ops:
            print("Digite uma opção válida")
        else:
            break
    conn_socket.sendto(op.encode('utf-8'), adrr)
    return int(op)


# Envia nome do arquivo para download/envio
def seleciona_nome(conn_socket, adrr, opcoes):
    while True:
        nome = input("Arquivo: ")
        if nome not in opcoes:
            print("Erro no nome digitado")
        else:
            break
    conn_socket.sendto(nome.encode('utf-8'), adrr)
    return nome


# Envia a senha
def enviando_senha(conn_socket, adrr):
    passw = input("Digite a senha para envio: ")
    conn_socket.sendto(passw.encode('utf-8'), adrr)


def espera_confirmacao(conn_socket):
    # Recebe a confirmação 1-senha correta 0-senha incorreta
    accepted, adrr = conn_socket.recvfrom(1024)
    accepted = accepted.decode('utf-8')
    return int(accepted)


# Dados para conexão com servidor
host = "localhost"  # IP do Servidor
port = 1994
time_out = 5
buffer = 512

if __name__ == '__main__':
    # Configurações do socket. AF_INET = IP, SOCK_STREAM = TCP e SOCK_DGRAM = UDP
    conn_socket = socket(AF_INET, SOCK_DGRAM)  # Tipo UDP/IP

    # Envia pedido de lista das opções do server
    pede_server(conn_socket, (host, port))
    # Recebe arquivos disponíveis e opções
    opcoes = recebendo_lista_e_opcoes(conn_socket)
    # Seleciona opção para download/envio
    op = seleciona_opcao(conn_socket, (host, port))
    # Envia nome do arquivo para envio/download
    nome = seleciona_nome(conn_socket, (host, port), opcoes)
    if op == 1:
        # Recebendo arquivo
        recebendo_arquivo(conn_socket, nome)
    else:
        # Envia a senha digitada
        enviando_senha(conn_socket, (host, port))
        # Recebe a indicação de confirmação ou recusa
        accepted = espera_confirmacao(conn_socket)
        if accepted:
            print("Senha aceita")
            envia_arquivo(conn_socket, (host, port), nome)
        else:
            print("Senha incorreta. Programa finalizado.")

    # Fecha socket
    conn_socket.close()
