from typing import Optional
from typing import Tuple
from typing import List
from typing import Dict
from typing import Any
import os


connection_establish_str = "~~~~~~~~~~~~~   CONNECTION ESTABLISHED"
sound_connect_establish_str = "~~~~~~~~~~ SOUND CONNECT ESTABLISHED"
connection_lost_str = "~~~~~~~~~~~~~   CONNECTION LOST"
output_every_5_sec_str = "~~~~~~~~~~~ Output every 5 sec"
selected_rfpi_str = "> F:FP selected: RFPI"
s_cc_setup_str = "> S:-> {CC-SETUP}"

bs_name_to_rfpi = {}
rfpi_to_bs_name = {}


def parse_bs_config(config: Dict[str, Any]) -> None:
    for bs in config["BaseStation"]:
        bs_name = bs["name"]
        bs_rfpis = bs["RFPI"]
        bs_name_to_rfpi[bs_name] = bs_rfpis
        for rfpi in bs_rfpis:
            rfpi_to_bs_name[rfpi] = bs_name


def get_name_bs_from_rfpi(rfpi_bs: str):
    if rfpi_bs in rfpi_to_bs_name:
        return rfpi_to_bs_name[rfpi_bs]
    return "undefined"


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
        if msg.find(connection_lost_str) != -1:
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
            if connection_establish_str in log_strings[log_ind][1]:
                break
            if sound_connect_establish_str in log_strings[log_ind][1]:
                break
    return result


def get_rfpi_from_selected_rfpi_str(rfpi_str: str) -> str:
    rfpi_text = "RFPI = "
    ind_rfpi = rfpi_str.find(rfpi_text)
    if ind_rfpi != -1:
        ind_rfpi += len(rfpi_text)
        rfpi_str = rfpi_str[ind_rfpi:].split(";")[0]
        rfpi_str = rfpi_str.lower().replace(" ", "")
        return rfpi_str
    return ""


def get_rfpi_from_s_cc_setup_str(cc_setup: str) -> str:
    rfpi_str = cc_setup.split("(")[1]
    rfpi_str = rfpi_str.split(" ")
    rfpi_str = "".join(rfpi_str[15:20]).lower()
    return rfpi_str


def define_connected_RFPI(log_strings: List[Tuple[int, str]], conn_ind: int) -> str:
    """
    Получить rfpi станции к которой удалось приконнектится
    Parameters
    ----------
    log_strings : List[Tuple[int, str]]
        Пронумерованный лог с белтпака, список содержащий кортежи (номер строки, сама строка)
    conn_ind : int
        индекс события установления связи
    time_back : int
        на сколько секунд отмотать назад от события разрыва для захвата строк с качеством

    Returns
    -------
    List[str]
        DESCRIPTION.
    """
    result = "undefined"
    log_ind = conn_ind
    while log_ind > 0:
        log_ind -= 1
        if log_strings[log_ind][1].find(selected_rfpi_str) != -1:
            result = get_rfpi_from_selected_rfpi_str(log_strings[log_ind][1])
            return result
        elif log_strings[log_ind][1].find(s_cc_setup_str) != -1:
            result = get_rfpi_from_s_cc_setup_str(log_strings[log_ind][1])
            return result
        if log_strings[log_ind][1].find(connection_lost_str) != -1:
            break
    return result

