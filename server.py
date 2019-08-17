#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory, connectionDone


class Client(LineOnlyReceiver):
    """Класс для обработки соединения с клиентом сервера"""

    delimiter = "\n".encode()  # \n для терминала, \r\n для GUI

    # указание фабрики для обработки подключений
    factory: 'Server'

    # информация о клиенте
    ip: str
    login: str = None

    def connectionMade(self):
        """
        Обработчик нового клиента

        - записать IP
        - внести в список клиентов
        - отправить сообщение приветствия
        """

        self.ip = self.transport.getPeer().host  # записываем IP адрес клиента
        self.factory.clients.append(self)  # добавляем в список клиентов фабрики

        self.sendLine("Welcome to the chat!".encode())  # отправляем сообщение клиенту

        print(f"Client {self.ip} connected")  # отображаем сообщение в консоли сервера

    def connectionLost(self, reason=connectionDone):
        """
        Обработчик закрытия соединения

        - удалить из списка клиентов
        - вывести сообщение в чат об отключении
        """

        self.factory.clients.remove(self)  # удаляем клиента из списка в фабрике

        print(f"Client {self.ip} disconnected")  # выводим уведомление в консоли сервера

    def lineReceived(self, line: bytes):
        """
        Обработчик нового сообщения от клиента

        - зарегистрировать, если это первый вход, уведомить чат
        - переслать сообщение в чат, если уже зарегистрирован
        """

        message = line.decode()  # раскодируем полученное сообщение в строку

        # если логин еще не зарегистрирован
        if self.login is None:
            if message.startswith("login:"):  # проверяем, чтобы в начале шел login:
                tmp_login = message.replace("login:", "")  # вырезаем часть после :
                if any(tmp_login in str(reg.login) for reg in self.factory.clients):
                    self.sendLine(f"Логин {tmp_login} занят, попробуйте другой".encode())
                    reactor.callLater(0.5, self.transport.loseConnection)
                else:
                    self.login = tmp_login
                    notification = f"New user: {self.login}"  # формируем уведомление о новом клиенте
                    self.factory.notify_all_users(notification)  # отсылаем всем в чат
                    self.factory.send_history(self)  # последние сообщения
            else:
                self.sendLine("Invalid login".encode())  # шлем уведомление, если в сообщении ошибка
        else:  # если логин уже есть и это следующее сообщение
            format_message = f"{self.login}: {message}"  # форматируем сообщение от имени клиента

            # отсылаем всем в чат и в консоль сервера
            self.factory.notify_all_users(format_message)
            print(format_message)
            self.factory.messages.append(format_message)


class Server(ServerFactory):
    """Класс для управления сервером"""

    clients: list  # список клиентов
    messages: list  # сообщения
    protocol = Client  # протокол обработки клиента

    def __init__(self):
        """
        Старт сервера

        - инициализация списка клиентов
        - вывод уведомления в консоль
        """

        self.clients = []  # создаем пустой список клиентов
        self.messages = []
        print("Server started - OK")  # уведомление в консоль сервера

    def startFactory(self):
        """Запуск прослушивания клиентов (уведомление в консоль)"""

        print("Start listening ...")  # уведомление в консоль сервера

    def notify_all_users(self, message: str):
        """
        Отправка сообщения всем клиентам чата
        :param message: Текст сообщения
        """

        data = message.encode()  # закодируем текст в двоичное представление

        # отправим всем подключенным клиентам
        for user in self.clients:
            user.sendLine(data)

    def send_history(self, client: Client):
        cnt = 10
        if len(self.messages) - cnt > 0:
            begin = len(self.messages) - cnt
        else:
            begin = 0
        if len(self.messages) > 0:
            client.sendLine(f"Last {len(self.messages) - begin} messages:".encode())
            for mes in self.messages[begin:len(self.messages)]:
                client.sendLine(mes.encode())


if __name__ == '__main__':
    # параметры прослушивания
    reactor.listenTCP(
        7410,
        Server()
    )

    # запускаем реактор
    reactor.run()
