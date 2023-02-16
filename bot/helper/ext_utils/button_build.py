
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton



class ButtonMaker:
    def __init__(self):
        self.first_button = []
        self.__header_button = []
        self.__footer_button = []
        self.__footer_second_button = []
        self.__footer_third_button = []

    def url_buildbutton(self, key, link):
        self.first_button.append(InlineKeyboardButton(text = key, url = link))

    def cb_buildbutton(self, key, data, position= None):
        if not position:
            self.first_button.append(InlineKeyboardButton(text = key, callback_data = data))
        elif position == 'header':
            self.__header_button.append(InlineKeyboardButton(text = key, callback_data = data))
        elif position == 'footer':
            self.__footer_button.append(InlineKeyboardButton(text = key, callback_data = data))
        elif position == 'footer_second':
            self.__footer_second_button.append(InlineKeyboardButton(text = key, callback_data = data))  
        elif position == 'footer_third':
            self.__footer_third_button.append(InlineKeyboardButton(text = key, callback_data = data))  

    def build_menu(self, n_cols):
        menu = [self.first_button[i: i + n_cols] for i in range(0, len(self.first_button), n_cols)]
        if self.__header_button:
            menu.insert(0, self.__header_button)
        if self.__footer_button:
            if len(self.__footer_button) > 8:
                [menu.append(self.__footer_button[i:i + 8]) for i in range(0, len(self.__footer_button), 8)]
            else:
                menu.append(self.__footer_button)
        if self.__footer_second_button:
            menu.append(self.__footer_second_button)
        if self.__footer_third_button:
            menu.append(self.__footer_third_button)
        return InlineKeyboardMarkup(menu)


