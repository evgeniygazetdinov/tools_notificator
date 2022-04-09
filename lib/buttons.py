import json.decoder
from lib.base import build_keyboard

raw_menu_keyboard = {
    "one_time_keyboard": True,
    "keyboard": [["регистрация"], ["войти"], ["помощь"]],
}
login_items = [
    "мои загрузки",
    "загрузить фото",
    "сменить пароль",
    "сменить время чистки",
    "завершить сессию",
]
menu_items = ["регистрация", "войти", "помощь"]
yes_no_items = {"one_time_keyboard": True, "keyboard": [["да"], ["нет"]]}
kick_out = {"resize_keyboard": True, "keyboard": [["назад"]]}
under_upload_menu = build_keyboard(
    ["новый список", "веcь список", "удалить просмотренные", "назад"]
)


def draw_lists_buttons(response):
    # create keyboard based on uploads
    lists = response["upload_list"]
    buttons = []
    keyboard = {"resize_keyboard": True, "keyboard": []}
    k = []
    for lis in lists:
        buttons.append(lis["date_upload"])
    for button in buttons:

        k.append("загрузки " + button)
    if len(response["photos_without_upload_list"]) != 0:
        k.append("фото без списка")
    k.append("назад")
    return k
