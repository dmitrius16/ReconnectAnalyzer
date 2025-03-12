from typing import Optional
from typing import Tuple
from typing import List

import os

def get_filter_log_name(log_name: str) -> str:
    """
    Получить имя отфильтрованного лога из имени входного файла
    Parameters
    ----------
    log_name : str
        Полный путь до файла с логами
    Returns
    -------
    str
        Имя лога с фильтрованными значениями
    """
    log_name = os.path.basename(log_name).split(".")
    return log_name[0] + "_filter." + log_name[1]




def get_tm_label(log_msg: str) -> int:
    """
    Получить временную метку события в логе
    Parameters
    ----------
    log_msg : str
        Строка с временной меткой в логе
    Raises
    ------
    RuntimeError
        Если в строке лога, нет временней метки, выброситьб исключение RunTimeError
    Returns
    -------
    int
        Временная метка
    """

    if log_msg.rfind("tm") == -1:
        raise RuntimeError("Log string without tm label")
    return int(log_msg.split(" ")[-1])


def find_reconnect_event(log_strings: List[Tuple[int, str]],
                         st_ind: int) -> Optional[Tuple[int, int]]:
    """
    Найти событие отсутствия коннекта и зафиксировать время его начала и конца
    Parameters
    ----------
    log_strings : list
        Список, содержащий кортежи (номер строки, сама строка)
    st_ind : int
        Индекс в списке с которого начать поиск
    Returns
    -------
    Optional[Tuple[int, int]]
        Пара индексов строк (индекс строки с разрывом соединения, индекс строки с возобновлением соединения),
        если строка с разрывом соединения не найдена вернуть None
    """
    tm_lost_connect = None
    for num, msg in log_strings[st_ind:]:
        if msg.find("~~~~~~~~~~~~~   CONNECTION LOST") != -1:
            tm_lost_connect = num
            break

    tm_new_connect = None

    if tm_lost_connect is not None:
        for num, msg in log_strings[tm_lost_connect:]:
            if msg.find("F:Q:") != -1:
                tm_new_connect = num
                break
    else:
        return None

    # !!!! между этими событиями возможен параллельный поиск, когда связи нет, основной канал
    return (tm_lost_connect, tm_new_connect)


def get_list_records_before_disconnect(log_strings: List[Tuple[int, str]], disconn_ind: int, time_back: int) -> List[str]:
    """
    Получить список записей лога до события дисконнекта
    Parameters
    ----------
    log_strings : List[Tuple[int, str]]
        Пронумерованный лог с белтпака, список содержащий кортежи (номер строки, сама строка)
    disconn_ind : int
        индекс события разрыва связи
    time_back : int
        на сколько секунд отмотать назад от события разрыва для захвата строк с качеством

    Returns
    -------
    List[str]
        DESCRIPTION.

    """
    lost_conn_tm_label = get_tm_label(log_strings[disconn_ind][1])
    log_ind = disconn_ind
    time_back = time_back * 1000  # Convert 1 sec to millisec
    result = []
    while log_ind >= 0:
        log_ind -= 1
        result.insert(0, log_strings[log_ind][1])
        if log_strings[log_ind][1].find("tm:") != -1:
            tm_label = get_tm_label(log_strings[log_ind][1])
            if (lost_conn_tm_label - tm_label) >= time_back:
                break
            if "~~~~~~~~~~~~~   CONNECTION ESTABLISHED" in log_strings[log_ind][1]:
               break
            if "~~~~~~~~~~ SOUND CONNECT ESTABLISHED" in log_strings[log_ind][1]:
                break
    return result


def define_connected_RFPI(log_strings: List[Tuple[int, str]], conn_ind: int, time_back: int) -> str:
    """
    Определить к какой БС приконнектились
    Parameters
    ----------
    log_strings 
    """
    pass
