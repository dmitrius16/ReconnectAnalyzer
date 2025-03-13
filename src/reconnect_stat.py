# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 11:13:12 2025

@author: d.sysoev
"""
from typing import List
from log_utils import *

'''
try:
    from log_utils import *
except ImportError:
    from src.log_utils import *
'''

class Reconnect_Stat():
    """
    reconnect_stat - class that contains statistics about recconection
    """
    DisconnReason_ConnRejByBS = "Connection rejected by BS"
    DisconnReason_ConnRejByBeltpack = "Connection rejected by Beltpack"
    DisconnReason_FindBSWith2Ch = "Sync completed with 2'nd ch"
    DisconnReason_Undefined = "Undefined disconnect reason"

    '''
    Quality keys
    '''
    PreambleQuality = "qual_pr"
    NumberOf_BeltpackNoSync = "num_nosync"
    NumberOf_ZError = "z_err"
    NumberOf_XCRCError = "xcrc_err"
    NumberOf_ACRCError = "acrc_err"
    NumberOf_BSNoSync = "num_nack_BS"
    NumberOf_TxHiPwrPackets = "hi_pwr_packets"
    NumberOf_PacketsOnSecAnt = "second_ant"
    Average_RSSI = "avr_rssi"
    Min_RSSI = "min_rssi"


    QualityKeys = [PreambleQuality, NumberOf_BeltpackNoSync, NumberOf_ZError, NumberOf_XCRCError, NumberOf_ACRCError,
                   NumberOf_BSNoSync, NumberOf_TxHiPwrPackets, NumberOf_PacketsOnSecAnt, Average_RSSI, Min_RSSI]

    QualityErr = [NumberOf_BeltpackNoSync, NumberOf_ZError, NumberOf_XCRCError, NumberOf_ACRCError, NumberOf_BSNoSync]

    QKeysToOptParSearch = {Average_RSSI : "Option_3", NumberOf_BeltpackNoSync : "Option_4",
                           NumberOf_ACRCError : "Option_5", NumberOf_XCRCError: "Option_6",
                           NumberOf_ZError: "Option_7", NumberOf_BSNoSync: "Option_16"}  # отображение ошибок на опции которые задают пороги

    QKeyToOptForceDisc = {NumberOf_BeltpackNoSync : "Option_8", NumberOf_ACRCError : "Option_9",
                          NumberOf_XCRCError : "Option_10", NumberOf_BSNoSync : "Option_17"}

    OptLessOrEq = lambda x, y: x <= y
    OptMoreOrEq = lambda x, y: x >= y

    RoamingOptCmp = {Average_RSSI : OptLessOrEq, NumberOf_BeltpackNoSync: OptMoreOrEq, NumberOf_ACRCError: OptMoreOrEq,
                     NumberOf_XCRCError: OptMoreOrEq, NumberOf_ZError: OptMoreOrEq, NumberOf_BSNoSync: OptMoreOrEq}


    RoamingOptions = {}

    def __init__(self):
        self.start_tm = 0  # зафиксированное время потери связи с БС
        self.end_tm = 0    # зафиксированное время возобновления связи с БС
        self.disconn_reason = ""
        self.connect_rfpi = ""
        self.secondary_search_reason = []
        self.force_disc_reason = []
        self.qualities_before_disconn = {}
        # self.connected_RFPI возможно зафиксированть RFPI и rssi станции к которой получили коннект коннект
        # РЭО за десять секунд до реконнекта

    def parse_quality_logs(self, log_before_disconn):
        for log_str in log_before_disconn:
            if log_str.find("> F:Q:") != -1:
                parts = log_str.split()
                timestamp = int(parts[-1])
                # Extract the values (numbers between "F:Q:" and "sys")
                values = parts[2:12]  # Adjust indices based on the structure
                # Create a dictionary for the values
                value_dict = {key: int(value) for key, value in zip(Reconnect_Stat.QualityKeys, values)}
                # Create the final dictionary with the timestamp as the key
                self.qualities_before_disconn.update({timestamp: value_dict})
        self.define_reason_for_disconnect(log_before_disconn)

    def define_reason_for_disconnect(self, log_before_disconn):
        for log_str in log_before_disconn[::-1]:
            if log_str.find("> F:No FP found") != -1:
                self.disconn_reason = Reconnect_Stat.DisconnReason_ConnRejByBS
                return
            elif log_str.find("> F:Conn. close by thr.") != -1:
                self.disconn_reason = Reconnect_Stat.DisconnReason_ConnRejByBeltpack
                return
            elif log_str.find("> F:FP find secondary") != -1:
                self.disconn_reason = Reconnect_Stat.DisconnReason_FindBSWith2Ch
                return
        self.disconn_reason = Reconnect_Stat.DisconnReason_ConnRejByBS

    def calc_errors_before_trig_thr(self, tm_stmp_trig, cnt_trig_thr, option_dict, num_err_in_a_row):
        tm_stmps = sorted(self.qualities_before_disconn.keys())
        for tm_st in tm_stmps:
            if tm_st <= tm_stmp_trig:
                for key in cnt_trig_thr.keys():
                    q_val = self.qualities_before_disconn[tm_st][key]
                    trig_threshold_key = option_dict[key]

                    if Reconnect_Stat.RoamingOptCmp[key](q_val, Reconnect_Stat.RoamingOptions[trig_threshold_key]):
                        cnt_trig_thr[key] += 1
                    else:
                        cnt_trig_thr[key] = 0

        # ищем ключ у которого максимальное значение ошибок, на случай если не получится определить по срабатыванию порогов
        max_err_key_name = ""
        max_err_val = 0
        thr_keys = []
        for key, val in cnt_trig_thr.items():
            if val > max_err_val:
                max_err_val = val
                max_err_key_name = key
            if val >= num_err_in_a_row:
                thr_keys.append(key)
        if not thr_keys:
            thr_keys.append(max_err_key_name)
        return thr_keys

    def define_reason_for_search_or_broke_link(self, log_before_disconn):
        num_err_trig_par_search = (Reconnect_Stat.RoamingOptions["Option_13"] & 0xF) + 1
        num_err_trig_force_discon = ((Reconnect_Stat.RoamingOptions["Option_13"] & 0xF0) >> 4) + 1
        find_text_in_log = ""
        cnt_thr = {}
        force_disc = False
        if self.disconn_reason == Reconnect_Stat.DisconnReason_FindBSWith2Ch:
            find_text_in_log = "> F:BS search init by thr"
            cnt_thr = {Reconnect_Stat.Average_RSSI: 0, Reconnect_Stat.NumberOf_BeltpackNoSync: 0, Reconnect_Stat.NumberOf_ACRCError: 0,
                       Reconnect_Stat.NumberOf_XCRCError: 0, Reconnect_Stat.NumberOf_ZError: 0, Reconnect_Stat.NumberOf_BeltpackNoSync: 0}
        elif self.disconn_reason == Reconnect_Stat.DisconnReason_ConnRejByBeltpack:
            cnt_thr = {Reconnect_Stat.NumberOf_BeltpackNoSync: 0, Reconnect_Stat.NumberOf_ACRCError: 0,
                       Reconnect_Stat.NumberOf_XCRCError: 0, Reconnect_Stat.NumberOf_BSNoSync: 0}

            find_text_in_log = "> F:Conn. close by thr."
            force_disc = True

        analyze_fq_str = False

        # Ищем признак срабатывания порога
        time_pnt_thr_event = 0
        if find_text_in_log:
            for log_entry in log_before_disconn[::-1]:
                if find_text_in_log in log_entry:
                    analyze_fq_str = True
                    time_pnt_thr_event = get_tm_label(log_entry)
                    break
            if analyze_fq_str:
                res = self.calc_errors_before_trig_thr(time_pnt_thr_event, cnt_thr,
                                                Reconnect_Stat.QKeyToOptForceDisc if force_disc else Reconnect_Stat.QKeysToOptParSearch,
                                                num_err_trig_force_discon if force_disc else num_err_trig_par_search)
                if force_disc:
                    self.force_disc_reason = res
                else:
                    self.secondary_search_reason = res


    def output_reconnect_info(self, disconn_num: int):
        print(f"Disconnect number {disconn_num}")
        print(f"Lost conn: {self.start_tm}\nreconn {self.end_tm}\ndelta = {self.end_tm - self.start_tm}")
        print(f"Disconnect reason: {self.disconn_reason}")
        if self.secondary_search_reason:
            print(f"Parallel search reason {self.secondary_search_reason}")
        elif self.force_disc_reason:
            print(f"Force disconnect reason {self.force_disc_reason}")
        print(f"Connected to BS: {get_name_bs_from_rfpi(self.connect_rfpi)} rfpi: {self.connect_rfpi}")
        print("------------------------------")


def find_reconnection(file_name: str) -> List[Reconnect_Stat]:
    """
    Найти информацию о реконнектах и сформировать объекты со статистикой
    Parameters
    ----------
    file_name : str
        Имя файла с предварительно отфильтрованными логами
    Returns
        Список объектов reconnect_stat
    -------
    """
    with open(file_name, "r") as f:
        filter_logs = f.readlines()

    log_strings = list(enumerate(filter_logs))

    # Поискать строки Options и если они есть перезаписать Options

    st_ind = 0
    result = []
    while True:
        tm_labels = find_reconnect_event(log_strings, st_ind)
        if tm_labels is not None:
            reccon_stat = Reconnect_Stat()
            result.append(reccon_stat)
            reccon_stat.start_tm = get_tm_label(log_strings[tm_labels[0]][1])
            log_before_disconn = get_list_records_before_disconnect(log_strings, tm_labels[0], 10)  # берём 10 секунд от потери связи
            reccon_stat.parse_quality_logs(log_before_disconn)
            reccon_stat.define_reason_for_search_or_broke_link(log_before_disconn)
            # Здесь надо добавить причины по которым случился рекконект
            # Также надо добавить причины по которым есть параллельный запуск
            if tm_labels[1] is not None:
                reccon_stat.end_tm = get_tm_label(log_strings[tm_labels[1]][1])

                # Здесь пытаемся определить к какой RFPI мы соединились
                reccon_stat.connect_rfpi = define_connected_RFPI(log_strings, tm_labels[1])

                st_ind = tm_labels[1]
            else:
                break
        else:
            break
    return result

