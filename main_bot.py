import sqlite3
from random import randrange
import json
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
conn=sqlite3.connect('cinemas.db')
cursor=conn.cursor()

def write_msg(user_id, message,keyboard=None):
    random_id=randrange(-pow(2,63),pow(2,63)-1,1)
    vk.method('messages.send', {'user_id': user_id, 'message': message,'random_id':random_id,'keyboard':keyboard})

def create_keyboard(list_buttons=[],brand=None,cinema_hall=None,date=None,cinema=None,next_=0):   
    keyboard={"one_time": True}
    list_buttons=list_buttons[32*next_:]
    if next_:
        payload={'b':brand,'h':cinema_hall,'d':date,'c':cinema,'n':next_-1}
        button_previous={"action": {"type": "text","payload": payload,"label": 'Назад'},
                        "color": "negative"}
    else:
        button_previous=None
    if len(list_buttons)>32:
        payload={'b':brand,'h':cinema_hall,'d':date,'c':cinema,'n':next_+1}
        button_next={"action": {"type": "text","payload": payload,"label": 'Далее'},
                     "color": "positive"}
    else:
        button_next=None
    list_buttons=list_buttons[:32]
    buttons=[]
    for i,button in enumerate(list_buttons):
        payload={'b':brand,'h':cinema_hall,'d':date,'c':cinema,'n':0}
        if not payload['b']:
            payload['b']=button
        elif not payload['h']:
            payload['h']=button
        elif not payload['d']:
            payload['d']=button
        else:
            payload['c']=button
        button={"action": {"type": "text","payload": payload,"label": next_*32+i+1},
                "color": "secondary"}
        buttons.append(button)
    list_buttons=[]
    for _ in range(len(buttons)//4):  
        list_buttons.append(buttons[:4])
        buttons=buttons[4:]
    if buttons:
        list_buttons.append(buttons)
    if button_next and button_previous:
        list_buttons.append([button_previous,button_next])
    elif button_next:
        list_buttons.append([button_next])
    elif button_previous:
        list_buttons.append([button_previous])
    else:
        pass
    button={"action": {"type": "text","payload": None,"label": 'В меню'},
                "color": "primary"}
    
    list_buttons.append([button])
    keyboard["buttons"]=list_buttons 
    keyboard=str(json.dumps(keyboard))
    return keyboard

def cinema_halls(brand):
    brand_id=cursor.execute(f"select id from brand where name='{brand}'").fetchall()[0][0]
    return [elem[0] for elem in cursor.execute(f"select name from cinema_halls where brand_id='{brand_id}'").fetchall()]

def dates(cinema_hall):
    cinema_hall_id=cursor.execute(f"select id from cinema_halls where name='{cinema_hall}'").fetchall()[0][0]
    date_list=[elem[0] for elem in cursor.execute(f"select date from sessions where hall_id='{cinema_hall_id}'").fetchall()]
    date_list=list(set(date_list))
    date_list.sort()
    return date_list

def cinemas(date,cinema_hall):
    cinema_hall_id=cursor.execute(f"select id from cinema_halls where name='{cinema_hall}'").fetchall()[0][0]
    cinema_list=cursor.execute(f"select cinema_id from sessions where (hall_id='{cinema_hall_id}'and date='{date}') ").fetchall()
    for i,cinema in enumerate(cinema_list):
        cinema_list[i]=cursor.execute(f"select name from cinemas where id='{cinema[0]}'").fetchall()[0][0]
    cinema_list=list(set(cinema_list))
    cinema_list.sort()
    return cinema_list

def information(brand,cinema_hall,date,cinema):
    info=cursor.execute(f"select address,metro,phone,id from cinema_halls where name='{cinema_hall}'").fetchall()[0]
    address=info[0]
    metro=info[1]
    phone=info[2]
    hall_id=info[3]
    info=cursor.execute(f"select duration,genres,id from cinemas where name='{cinema}'").fetchall()[0]
    duration=info[0]
    genres=info[1]
    cinema_id=info[2]
    info=cursor.execute(f"select time,price from sessions where (cinema_id='{cinema_id}' and hall_id='{hall_id}' and date='{date}')").fetchall()
    text=f'''Бренд: {brand}
Информация о кинозале:
Кинозал: {cinema_hall}
Адрес: {address}
Метро: {metro}
Телефон: {phone}
Информация о фильме:
Фильм: {cinema}
Продолжительность: {duration}
Жанр: {genres}
Сеансы и стоимость:'''
    for item in info:
        text=text+f'\nсеанс: {item[0]}, стоимость: {item[1]}'
    return text


brands=[elem[0] for elem in cursor.execute("select name from brand").fetchall()]
token = "be721235fa277f5115e38571dc4137fdd58b65364904a86dd46c2e328b7afbc64a7f5062117695d146103"
vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            request = event.text.lower()
            payload=json.loads(event.extra_values.get('payload','""'))
            if not(payload):
                write_msg(event.user_id, 'Выберите бренд\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(brands)]),create_keyboard(brands))
            elif payload['b']and not payload['h']:
                next_=payload['n']
                brand=payload['b']
                cinema_hall=cinema_halls(brand)
                write_msg(event.user_id,'Выберите кинотеатр\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(cinema_hall)]),create_keyboard(cinema_hall,brand,next_=next_))
            elif payload['b']and payload['h'] and not payload['d']:
                next_=payload['n']
                brand=payload['b']
                cinema_hall=payload['h']
                date=dates(cinema_hall)
                write_msg(event.user_id,'Выберите дату\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(date)]),create_keyboard(date,brand,cinema_hall,next_=next_))
            elif payload['b']and payload['h'] and payload['d'] and not payload['c']:
                next_=payload['n']
                brand=payload['b']
                cinema_hall=payload['h']
                date=payload['d']
                cinema=cinemas(date,cinema_hall)
                write_msg(event.user_id,'Выберите фильм\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(cinema)]),create_keyboard(cinema,brand,cinema_hall,date,next_=next_))
            else:
                brand=payload['b']
                cinema_hall=payload['h']
                date=payload['d']
                cinema=payload['c']
                text=information(brand,cinema_hall,date,cinema)
                write_msg(event.user_id,text,create_keyboard())