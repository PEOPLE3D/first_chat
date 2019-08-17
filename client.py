#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Консольный клиент для подключения к серверу

from twisted.internet import reactor, stdio
from twisted.internet.protocol import Protocol, ClientFactory


class MessageHandler(Protocol):
    """Класс для работы параллельного ввода / вывода"""

    output = None  # путь для вывода сообщений из консоли

    def dataReceived(self, data: bytes):
        """Обработчик нового сообщения от сервера / ввода пользователя"""

        if self.output:
            self.output.write(data)  # перенаправялем сообщение на сервер


class User(MessageHandler):
    """Класс для отправки/обработки сообщений сервера"""

    factory: 'Connector'

    def wrap(self):
        """Обработка ввода / вывода в терминале"""

        handler = MessageHandler()  # создаем промежуточный объект для работы с вводом/выводом в консоли
        handler.output = self.transport  # назначем путь для вывода сообщений (на сервер)

        wrapper = stdio.StandardIO(handler)  # запускаем модуль Twisted для паралельного ввода и получения данных

        self.output = wrapper  # подставляем в текущий протокол (будет перехватывать по нажатию на Enter)

    def connectionMade(self):
        """
        Обработчик успешного соединения

        - посылаем логин на сервер
        - запускаем ввод/вывод
        """

        login_message = f"login:{self.factory.login}"  # формируем строку регистрации логина
        self.send_message(login_message)  # отправляем на сервер

        self.wrap()  # включаем режим ввода/вывода в консоли (чтобы отправлять сообщения нажатием Enter)

    def send_message(self, content: str):
        """Обработчик отправки сообщения на сервер"""

        data = f"{content}\n".encode()  # кодируем текст в двоичное представление
        self.transport.write(data)  # отправляем на сервер


class Connector(ClientFactory):
    """
    Класс для создания подключения к серверу
    """

    protocol = User
    login: str

    def __init__(self, login: str):
        """Создание менеджера подключений (сохраняем логин)"""

        self.login = login  # записываем логин для последующей регистрации

    def startedConnecting(self, connector):
        """Обработчик установки соединения (выводим сообщение)"""

        print("Connecting to the server...")  # уведомление в консоли клиента

    def clientConnectionFailed(self, connector, reason):
        """Обработчик неудачного соединения (отключаем reactor)"""

        print("Connection failed")  # уведомление в консоли клиента
        reactor.callFromThread(reactor.stop)  # остановка реактора

    def clientConnectionLost(self, connector, reason):
        """Обработчик отключения соединения (отключаем reactor)"""

        print("Disconnected from the server")  # уведомление в консоли клиента
        reactor.callFromThread(reactor.stop)  # остановка реактора


if __name__ == '__main__':
    # запрашиваем имя пользователя для подключения
    user_login = input("Your login: ")

    # параметры соединения
    reactor.connectTCP(
        "localhost",
        7410,
        Connector(user_login)
    )

    # запускаем реактор
    reactor.run()
