import vk_api
import json
import random
import time
import datetime
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import sqlalchemy
from sqlalchemy import Column, String, Integer
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

# достаем токен и id группы из файла
with open('./data_for_connect.json', 'r', encoding='utf-8') as file:
    # считываем данные, которые уже есть в файле
    token_and_group_id = json.load(file)
    file.close()
# токен и id группы
token = token_and_group_id['token']
group_id = token_and_group_id['group_id']
# авторизуемся в вк апи
vk_session = vk_api.VkApi(token=token)
# подключаем бота к longpoll серверу
longpoll = VkBotLongPoll(vk_session, group_id=group_id)

# строка с командами
commands_msg = '"кнопки" - чтобы получить кнопки.\n' \
               '"команды" - чтобы получить список команд, доступных боту.\n' \
               '"словарь" - чтобы добавить свои слова в словарь.\n' \
               '"слова" - чтобы посмотреть слова, которые уже есть в словаре.\n\n' \
               'p.s. команды нужно водить без ковычек.\n' \
               'p.p.s. для ввода команд можно использовать кнопки.'

# когда человек хочет найти слово в своем словаре, ему присылается это сообщение
string_for_slova = 'Если вы хотите получить список слов из вашего словаря, начинающихся на какую-то русскую букву, то вам нужно ввести rus - *буква*\n ' \
                   'Пример:\nrus - г\n Если вы хотите получить список слов, начинающихся на какую-то английскую букву, то вам нужно ввести eng - *буква*\n ' \
                   'Пример:\neng - q\n Если хотите закончить поиск слова, введите команду "закончить", или воспользуйтесь кнопкой.'

# когда человек хочет добавить слово в своем словаре, ему присылается это сообщение
string_for_slovar = 'Чтобы добавить слово в словарь, нужно сначала ввести слово на английском, затем поставить пробел тире пробел, и ввести слово на русском.\n'\
                                    'Пример:\nname - имя\n Вы можете остановить добавление новых слов, введя команду "закончить", или воспользовавшись кнопкой.'

# если юзер ввел некорректные данные когда добавлял слово в словарь
necorrect_dannie = 'Введенные вами данные некорректны! Чтобы добавить слово в словарь, вы должны сначала ввести слово на английском, затем слово на русском, ' \
                   'отграничив их друг от друга пробелом, тире и еще одним пробелом. Пример:\nname - имя\n Чтобы закончить добавлять слова, вы можете ввести команду закончить, или воспользоваться кнопкой.'

greeting_msg = 'Добро пожаловать! Если хочешь узнать, какими командами обучен бот, введи "команды" без ковычек, или воспользуйся кнопкой "команды".'

# счетчик для 'слова'
# counter = 0

# кнопка закончить
zak = {
'one_time': False,
    'inline': False,
    'buttons':[
        [
            {'action':{
            'type': 'text',
            'payload': [],
            'label': 'закончить'
        },
            'color': 'primary'

            }
                ]
                ]}
# кнопки, которые мы будем отправлять пользователю
Buttons = {
    'one_time': False,
    'inline': False,
    'buttons': [[{
        'action': {
            'type': 'text',
            'payload': [],
            'label': 'команды'
        }, 'color':'primary'
    },
{
        'action': {
            'type': 'text',
            'payload': [],
            'label': 'слова'
        }, 'color':'primary'
    }

        ],
[
    {
        'action': {
            'type': 'text',
            'payload': [],
            'label': 'словарь'
        }, 'color':'primary'
}]
    ]
}


# функция которая будет проверять, есть ли написавший пользователь в группе
def is_it_in_group(user_id):
    try:
        flag = False
        group_members = vk_session.method('groups.getMembers', {
            'group_id': group_id
        })
        if user_id in group_members['items']:
            flag = True
        return flag
    except:
        print('не работает функция is_it_in_group')


# функция для отправки сообщения пользователю
def send_to_user(user_id, msg=None, att=None):
    try:
        vk_session.method('messages.send', {
            'random_id': random.randrange(-1000000, 1000000),
            'user_id': user_id,
            'message': msg,
            'attachment': att})
    except:
        print('не работает функция send_to_user')


# функция для отправки кнопок
def send_keyboard(user_id, msg, buttons):
    try:
        vk_session.method('messages.send', {'user_id': user_id, 'message': msg, 'keyboard': buttons, 'random_id': random.randrange(-1000000, 100000)})
    except:
        print('не работает функция send_keyboard')


# функция для изменения и создания состояния пользователя для добавления нового пользователя в словарь
def user_state_change_for_add_new_word(user_id, add_new_word_now, play_in_game, time_msg, get_words):
    try:
        with open('./user_states/'+str(user_id)+'.json', 'r', encoding='utf-8') as file:
            file_contents = json.load(file)
            file.close()
        file_contents["add_new_word_now"] = add_new_word_now
        file_contents["play_in_game"] = play_in_game
        file_contents["time"] = time_msg
        file_contents["get_words"] = get_words
        with open('./user_states/'+str(user_id)+'.json', 'w', encoding='utf-8') as file:
            json.dump(obj=file_contents, fp=file)
            file.close()
    except FileNotFoundError:
        # если файла данного пользователя нет, то создает новый файд и засовывает туда заготовку
        with open('./user_states/'+str(user_id)+'.json', 'w', encoding='utf-8') as file:
            for_dump = {"user_id": user_id, "add_new_word_now": add_new_word_now, "play_in_game": play_in_game, "time":time_msg, "get_words":get_words}
            json.dump(obj=for_dump, fp=file)
            file.close()
    except:
        print('ошибка в функции user_state_change_for_add_new_word')


# функция для проверки состояния пользователя
def checking_user_state(user_id):
    try:
        with open('./user_states/' + str(user_id) + '.json', 'r', encoding='utf-8') as file:
            file_contents = json.load(file)
            file.close()
        return file_contents
    # если файла данного пользователя нет, то создает новый файд и засовывает туда заготовку
    except FileNotFoundError:
        # если файла данного пользователя нет, то создает новый файд и засовывает туда заготовку
        with open('./user_states/' + str(user_id) + '.json', 'w', encoding='utf-8') as file:
            for_dump = {"user_id": user_id, "add_new_word_now": False, "play_in_game": False,
                        "time": time.time(), "get_words": False}
            json.dump(obj=for_dump, fp=file)
            file.close()
            file_contents = for_dump
        return file_contents
    except:
        print('ошибка в функции user_state_change_for_add_new_word')


# функция для добавление слов в словарь в БД
def add_word_in_dict(user_id, date, eng_word, rus_word):
    engine = create_engine('sqlite:///user_dicts/' + str(user_id) + '.db', echo=True)
    base = declarative_base()

    class User_words(base):
        __tablename__ = 'user_dict'
        id = Column(Integer, primary_key=True)
        user_id = Column(String)
        date = Column(String)
        eng_word = Column(String)
        rus_word = Column(String)

    base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    new_word = User_words(user_id=user_id, date=date, eng_word=eng_word, rus_word=rus_word)
    session.add(new_word)
    session.commit()


# возвращает список списков всех слов, начинающихся с указанной английской буквы
def search_eng_words(user_id, b):
    try:
        engine = create_engine('sqlite:///user_dicts/' + str(user_id) + '.db', echo=False)
        base = declarative_base()

        class User_words(base):
            __tablename__ = 'user_dict'
            id = Column(Integer, primary_key=True)
            user_id = Column(String)
            date = Column(String)
            eng_word = Column(String)
            rus_word = Column(String)

        session = sessionmaker(bind=engine)()
        sp = []
        for q in session.query(User_words).order_by(User_words.id):
            if q.eng_word[0].lower() == b:
                sp.append([q.eng_word, q.rus_word])
    except:
        sp = []
    return(sp)


# возвращает список списков всех слов, начинающихся с указанной английской буквы
def search_rus_words(user_id, b):
    try:
        engine = create_engine('sqlite:///user_dicts/' + str(user_id) + '.db', echo=False)
        base = declarative_base()

        class User_words(base):
            __tablename__ = 'user_dict'
            id = Column(Integer, primary_key=True)
            user_id = Column(String)
            date = Column(String)
            eng_word = Column(String)
            rus_word = Column(String)

        session = sessionmaker(bind=engine)()
        sp = []
        for q in session.query(User_words).order_by(User_words.id):
            if q.rus_word[0].lower() == b:
                sp.append([q.eng_word, q.rus_word])
    except:
        sp = []
    return(sp)


# добавляет юзера, вступившего в группу, в файл с id всех юзеров
"""
def add_new_user_id_in_file(user_id):
    try:
        with open('all_users'+'.json', 'r', encoding='utf-8') as file:
            file_contents = json.load(file)
            file.close()
        if user_id not in file_contents:
            file_contents.append(user_id)
        with open('all_users' + '.json', 'w', encoding='utf-8') as file:
            json.dump(obj=file_contents, fp=file)
            file.close()
    # если файла данного пользователя нет, то создает новый файд и засовывает туда id пользователя
    except FileNotFoundError:
        with open('all_users' + '.json', 'w', encoding='utf-8') as file:
            for_dump = [user_id]
            json.dump(obj=for_dump, fp=file)
            file.close()
    except:
        print('ошибка в функции user_state_change_for_add_new_word')
"""


while True:
    try:
        # слушаем longpoll
        for event in longpoll.listen():
            print(event)
            # если кто-то выходит из группы
            if event.type == VkBotEventType.GROUP_LEAVE:
                send_to_user(user_id=event.obj['user_id'], msg='Прощай...((')
            # если кто-то захолит в группу
            elif event.type == VkBotEventType.GROUP_JOIN:
                # добавляем юзера в файл со списком id всех юзеров
                # add_new_user_id_in_file(user_id=event.obj['user_id'])
                # Отправляем приветственные сообщения
                send_to_user(user_id=event.obj['user_id'], msg=greeting_msg)
                # отправляем кнопки
                send_keyboard(user_id=event.obj['user_id'], buttons=str(json.dumps(Buttons)),
                              msg='Ты можешь быстро использовать команды бота, благодаря кнопкам!')
                # создаем файл с состоянием пользователя
                user_state_change_for_add_new_word(user_id=event.obj['user_id'], add_new_word_now=False, play_in_game=False, time_msg=time.time(), get_words=False)
            # если кто-то отправляет боту сообщение
            elif event.type == VkBotEventType.MESSAGE_NEW:
                # если отправивший сообщение есть в группе
                if is_it_in_group(user_id=event.obj.message['from_id']):
                    # вызываем функцию для создания файла состояния пользователя
                    checking_user_state(event.obj.message['from_id'])
                    # если юзер добавляет слова в словарь
                    if checking_user_state(event.obj.message['from_id'])['add_new_word_now']:
                        # если юзер решил закончить добавлять слова в словарь
                        if event.obj.message['text'].lower().strip() == 'закончить':
                            # меняем состояние пользователя
                            user_state_change_for_add_new_word(user_id=event.obj.message['from_id'], add_new_word_now=False, play_in_game=False, time_msg=time.time(), get_words=False)
                            # отправляем основные кнопки
                            send_keyboard(user_id=event.obj.message['from_id'], msg='Все слова успешно добавлены в словарь!', buttons=json.dumps(Buttons))
                        # если пользователь не заканчивает
                        else:
                            # пытаемся:
                            try:
                                # разделяем строку на русское слово и англ. слово
                                eng_word = event.obj.message['text'].strip().split(' - ')[0].strip()
                                rus_word = event.obj.message['text'].strip().split(' - ')[1].strip()
                                # дата добавления нового слова в БД
                                date = str(datetime.datetime.fromtimestamp(time.time()).strftime('%d-%m-%Y')).replace('-', '.')
                                # добавляем новое слово в БД
                                add_word_in_dict(user_id=event.obj.message['from_id'], eng_word=eng_word, rus_word=rus_word, date=date)
                                # отправляем юзеру сообщение о том что слово добавлено с БД
                                send_to_user(user_id=event.obj.message['from_id'], msg='Слово успешно добавлено в словарь!')
                            # если не получается, то значит юзер некорректно ввел данные
                            except:
                                send_to_user(user_id=event.obj.message['from_id'], msg=necorrect_dannie)
                    # если юзер хочет получить список слов из словаря, которые начинаются на указанную им букву
                    elif checking_user_state(event.obj.message['from_id'])['get_words']:
                        if event.obj.message['text'].lower().strip() == 'закончить':
                            user_state_change_for_add_new_word(user_id=event.obj.message['from_id'], add_new_word_now=False,
                                                           play_in_game=False, time_msg=int(time.time()),
                                                           get_words=False)
                            send_keyboard(user_id=event.obj.message['from_id'],
                                      msg='Поиск слова был остановлен.', buttons=str(json.dumps(Buttons)))
                            # если юзер 5 раз вводит некорректные данные, то останавливается посиск слова
                            """
                        elif counter == 5:
                            counter = 0
                            send_to_user(user_id=event.obj.message['from_id'], msg='Вы ввели некорректные данные 5 раз подряд, поэтому поиск слова был остановлен.')
                            user_state_change_for_add_new_word(user_id=event.obj.message['from_id'], add_new_word_now=False,
                                                               play_in_game=False, time_msg=int(time.time()),
                                                               get_words=False)
                            """
                        else:
                            # если вводится буква на англе
                            if event.obj.message['text'].lower().strip().split(' - ')[0] == 'eng':
                                string = ''
                                # если список с словами на введенную букву не пустой
                                if search_eng_words(user_id=event.obj.message['from_id'], b=event.obj.message['text'].lower().strip().split(' - ')[1]) != []:
                                    # отправляется основная клава и слова, изменяется состояние пользователя
                                    send_keyboard(user_id=event.obj.message['from_id'], msg=(
                                            'Все слова, которые вы добавляли в словарь на букву ' + str(
                                        event.obj.message['text'].lower().strip().split(' - ')[1]) + ':'),
                                                  buttons=str(json.dumps(Buttons)))
                                    for eng_and_rus in search_eng_words(user_id=event.obj.message['from_id'], b=
                                    event.obj.message['text'].lower().strip().split(' - ')[1]):
                                        string = eng_and_rus[0] + ' - ' + eng_and_rus[1]
                                        send_to_user(user_id=event.obj.message['from_id'], msg=string)
                                        user_state_change_for_add_new_word(user_id=event.obj.message['from_id'],
                                                                           add_new_word_now=False,
                                                                           play_in_game=False, time_msg=int(time.time()),
                                                                           get_words=False)
                                # отправляется клава и изменяется состояние пользователя
                                else:
                                    send_keyboard(user_id=event.obj.message['from_id'], msg='На такую букву слов в вашем словаре не обнаружено. Поиск слов остановлен.', buttons=str(json.dumps(Buttons)))
                                    user_state_change_for_add_new_word(user_id=event.obj.message['from_id'],
                                                                       add_new_word_now=False,
                                                                       play_in_game=False, time_msg=int(time.time()),
                                                                       get_words=False)
                            # если вводится буква на русском
                            elif event.obj.message['text'].lower().strip().split(' - ')[0] == 'rus':
                                string = ''
                                # если список с словами на введенную букву не пустой
                                if search_rus_words(user_id=event.obj.message['from_id'], b=event.obj.message['text'].lower().strip().split(' - ')[1]) != []:
                                    # отправляется основная клава и слова, изменяется состояние пользователя
                                    send_keyboard(user_id=event.obj.message['from_id'], msg=(
                                                'Все слова, которые вы добавляли в словарь на букву ' + str(
                                            event.obj.message['text'].lower().strip().split(' - ')[1]) + ':'),
                                                  buttons=str(json.dumps(Buttons)))
                                    for eng_and_rus in search_rus_words(user_id=event.obj.message['from_id'], b=event.obj.message['text'].lower().strip().split(' - ')[1]):
                                        string = eng_and_rus[0] + ' - ' + eng_and_rus[1]
                                        send_to_user(user_id=event.obj.message['from_id'], msg=string)
                                        user_state_change_for_add_new_word(user_id=event.obj.message['from_id'], add_new_word_now=False,
                                                                           play_in_game=False, time_msg=int(time.time()),
                                                                           get_words=False)
                                # отправляется клава и изменяется состояние пользователя
                                else:
                                    send_keyboard(user_id=event.obj.message['from_id'], msg='На такую букву слов в вашем словаре не обнаружено. Поиск слов остановлен.', buttons=str(json.dumps(Buttons)))
                                    user_state_change_for_add_new_word(user_id=event.obj.message['from_id'],
                                                                       add_new_word_now=False,
                                                                       play_in_game=False, time_msg=int(time.time()),
                                                                       get_words=False)
                            else:
                                # счетчик попыток
                                # counter += 1
                                # отправляется сообщение о том как правильно нужно вводить
                                send_to_user(user_id=event.obj.message['from_id'],
                                             msg=string_for_slova)
                    else:
                        # если просят отправить команды бота
                        if event.obj.message['text'].lower().strip() == 'команды':
                            send_to_user(user_id=event.obj.message['from_id'], msg=commands_msg)
                        # если просят бота отправить кнопки
                        elif event.obj.message['text'].lower().strip() == 'кнопки':
                            send_keyboard(user_id=event.obj.message['from_id'], msg='с кнопками проще)',
                                          buttons=str(json.dumps(Buttons)))
                        # если пользователь хочет найти какое-нибудь слово
                        elif event.obj.message['text'].lower().strip() == 'слова':
                            # отправляем кнопку закончить и сообщение
                            send_keyboard(user_id=event.obj.message['from_id'],
                                         msg=string_for_slova, buttons=str(json.dumps(zak)))
                            # меняем состояние пользователя
                            user_state_change_for_add_new_word(user_id=event.obj.message['from_id'], add_new_word_now=False,
                                                               play_in_game=False, time_msg=int(time.time()), get_words=True)
                        # если пользователь хочет добавить какое-нибудь слово в словарь
                        elif event.obj.message['text'].lower().strip() == 'словарь':
                            # меняем состояние пользователя
                            user_state_change_for_add_new_word(user_id=event.obj.message['from_id'], add_new_word_now=True,
                                                               play_in_game=False, time_msg=int(time.time()), get_words=False)
                            # отправляем кнопку закончить и сообщение
                            send_keyboard(user_id=event.obj.message['from_id'], msg=string_for_slovar, buttons=str(json.dumps(zak)))
                            # если хочет запустить игру
                            """
                        elif event.obj.message['text'].lower().strip() == 'игра':
                            user_state_change_for_add_new_word(user_id=event.obj.message['from_id'], add_new_word_now=False,
                                                               play_in_game=True, time_msg=int(time.time()), get_words=False)
                            """
                        else:
                            send_to_user(user_id=event.obj.message['from_id'], msg='Прости, но я не понимаю тебя. Если хочешь '
                                                                                   'получить список команд, которым я обучена, '
                                                                                   'набери "команды" без ковычек.')
                # если отправившего сообщение нет в группе
                else:
                    send_to_user(user_id=event.obj.message['from_id'],
                             msg='Чтобы пользоваться чат-ботом, тебе нужно вступить в группу!')
    except requests.exceptions.ConnectionError:
        print('нет подключения к интернету')
    except:
        print('ошибка в цикле лонгпула')

















