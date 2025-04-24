# -*- coding: utf-8 -*-
"""
Created on Tue Mar  4 11:59:19 2025

@author: d.sysoev
"""
import pickle
import toml

from typing import List
from typing import Dict
from reconnect_stat import Reconnect_Stat

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from log_utils import *

def get_quality_values(qualities: Dict,
                       time_stmps: List[int],
                       name_quality: str) -> List[int]:
    result = [qualities[tm][name_quality] for tm in time_stmps]
    return result


def build_time_series(qualities_records: Dict):

    time_stmps = sorted(qualities_records.keys())

    result = {"time_stmps": time_stmps}

    for qual_item in Reconnect_Stat.QualityKeys:
        result.update({qual_item: get_quality_values(qualities_records, time_stmps, qual_item)})

    add_color_to_time_series(result)

    return result


def add_color_to_time_series(time_series_obj: Dict):
    '''
    Добавить цветовую кодировку в зависимости от соответствущего Options, для отображения на графике.
    '''
    time_series_colors = {}
    for qual_name in time_series_obj.keys():
        if qual_name in Reconnect_Stat.RoamingOptCmp: # если имя параметра в списке сравниваемых с Option
            new_qual_name = qual_name + "_color"
            qual_vals = time_series_obj[qual_name]
            time_series_colors[new_qual_name] = []

            option_thr = Reconnect_Stat.QKeysToOptParSearch[qual_name]
            option_thr_val = Reconnect_Stat.RoamingOptions[option_thr]

            for q in qual_vals:
                if Reconnect_Stat.RoamingOptCmp[qual_name](q, option_thr_val):
                    time_series_colors[new_qual_name].append('r')
                else:
                    time_series_colors[new_qual_name].append('g')

                # Проверяем не сработал ли порог по которому связь рвётся моментально
                if time_series_colors[new_qual_name][-1] == 'r':
                    if qual_name in Reconnect_Stat.QKeyToOptForceDisc:
                        force_option_thr = Reconnect_Stat.QKeyToOptForceDisc[qual_name]
                        force_option_thr_val = Reconnect_Stat.RoamingOptions[force_option_thr]
                        if Reconnect_Stat.RoamingOptCmp[qual_name](q, force_option_thr_val):
                            time_series_colors[new_qual_name][-1] = 'k'

    time_series_obj.update(time_series_colors)
    pass


def plot_rssi_info(time_series_obj: Dict) -> Figure:
    gridsize = (2, 3)
    fig = plt.figure(figsize=(12, 4))
    ax1 = plt.subplot2grid(gridsize, (0, 0), rowspan=2, colspan=2)
    ax2 = plt.subplot2grid(gridsize, (0, 2))
    ax3 = plt.subplot2grid(gridsize, (1, 2))
    width = 0.5

    x = np.arange(len(time_series_obj["time_stmps"]))
    time_axis = (np.array(time_series_obj["time_stmps"]) - time_series_obj["time_stmps"][0])
    roam_opt_for_rssi = "Option_3"
    roam_opt_for_rssi_val = Reconnect_Stat.RoamingOptions[roam_opt_for_rssi]
    opt_ = np.ones(len(x)) * roam_opt_for_rssi_val
    style = {'edgecolor': 'black', 'linewidth': 0.3}
    ax1.bar(x, time_series_obj["avr_rssi"], width, color=time_series_obj['avr_rssi_color'], label="avr_rssi", **style)
    ax1.plot(x, opt_, '--', color='r', label=f"{roam_opt_for_rssi}={roam_opt_for_rssi_val}")
    ax1.set_ylabel("rssi strength")
    ax1.legend()

    ax2.plot(time_axis, time_series_obj["avr_rssi"])
    ax2.set_ylabel("avr rssi strength")
    ax2.set_ylim([-2, max(time_series_obj["avr_rssi"]) + 2])
    ax2.yaxis.tick_right()

    ax1.bar(x + width, time_series_obj["min_rssi"], width, label="min_rssi", **style)  # ax1
    ax3.plot(time_axis, time_series_obj["min_rssi"])
    ax3.set_ylabel("min rssi strength")
    ax3.set_ylim([-2, max(time_series_obj["min_rssi"]) + 2])
    ax3.set_xlabel("time, sec")
    ax3.yaxis.tick_right()

    return fig


def plot_error_info(time_series_obj: Dict, name_err: str) -> Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    soft_opt_name = None
    strict_opt_name = None
    if name_err in Reconnect_Stat.QKeysToOptParSearch:
        soft_opt_name = Reconnect_Stat.QKeysToOptParSearch[name_err]

    if name_err in Reconnect_Stat.QKeyToOptForceDisc:
        strict_opt_name = Reconnect_Stat.QKeyToOptForceDisc[name_err]

    x = np.arange(len(time_series_obj["time_stmps"]))
    color_name = name_err + "_color"
    style = {'edgecolor': 'black', 'linewidth': 0.3}
    ax.bar(x, time_series_obj[name_err], color=time_series_obj[color_name], **style)
    ax.set_ylabel(name_err)
    if soft_opt_name is not None:
        soft_opt_val = Reconnect_Stat.RoamingOptions[soft_opt_name]
        soft_opt_y_level = np.ones(len(x)) * soft_opt_val
        ax.plot(x, soft_opt_y_level, '--', color='r', label=f"{soft_opt_name}={soft_opt_val}")

    if strict_opt_name is not None:
        strict_opt_val = Reconnect_Stat.RoamingOptions[strict_opt_name]
        strict_opt_y_level = np.ones(len(x)) * strict_opt_val
        ax.plot(x, strict_opt_y_level, '--', color='k', label=f"{strict_opt_name}={strict_opt_val}")
    ax.set_ylim([-0.1, max(time_series_obj[name_err]) + 1])
    ax.legend()
    return fig


def plot_graphs(qualities_record: Dict) -> List[Figure]:
    data_to_plot = build_time_series(qualities_record)
    rssi_fig = plot_rssi_info(data_to_plot)
    figures = [plot_error_info(data_to_plot, err_name) for err_name in Reconnect_Stat.QualityErr]
    figures.insert(0, rssi_fig)
    return figures


def create_reconnect_report(reconn_objs: List[Reconnect_Stat]) -> Dict:
    result = []
    for num, obj in enumerate(reconn_objs, start=1):
        obj_dict = {}
        obj_dict["Disconnect #"] = num
        obj_dict["Time conn Lost"] = obj.start_tm
        obj_dict["Time conn Estbl"] = obj.end_tm
        obj_dict["Time no sound"] = obj.end_tm - obj.start_tm
        obj_dict["Disconnect reason"] = obj.disconn_reason
        obj_dict["Par search reason"] = obj.secondary_search_reason or "-----"
        obj_dict["Force search reason"] = obj.force_disc_reason or "-----"
        obj_dict["BS name"] = get_name_bs_from_rfpi(obj.connect_rfpi)
        obj_dict["RFPI"] = obj.connect_rfpi
        result.append(obj_dict)
    return result


def get_fun_from_range(interval: str):
    bounds  = interval.split("-")
    if bounds[1] == "inf":
        return lambda x : int(bounds[0]) <= x
    else:
        return lambda x: int(bounds[0]) <= x < int(bounds[1])


def create_no_snd_pivot_table(reconn_objs: List[Reconnect_Stat], toml_cfg: Dict) -> Dict:
    no_snd_stat_ranges = toml_cfg["No_sound_Stat"]
    intervals = no_snd_stat_ranges["intervals"]
    check_func = {}
    for interval in intervals:
        check_func[interval] = get_fun_from_range(interval)

    res = dict.fromkeys(intervals, 0)
    for recon_obj in reconn_objs:
        for k in check_func:
            no_snd_tm = recon_obj.end_tm - recon_obj.start_tm
            if check_func[k](no_snd_tm):
                res[k] += 1
    return res

def create_bs_search_report(reconn_obj: Reconnect_Stat) -> Dict:
    result = []
    for num, obj in enumerate(reconn_obj.bs_search_info):
        bs_search_dict = {}
        bs_search_dict["Name"] = obj.bs_info.name_bs
        bs_search_dict["RFPI"] = obj.bs_info.rfpi
        bs_search_dict["RSSI"] = obj.bs_info.level_rssi
        bs_search_dict["State"] = obj.conn_result
        bs_search_dict["tm st"] = obj.tm_label_sel_rfpi
        bs_search_dict["tm end"] = obj.tm_label_end
        bs_search_dict["Tm delta, ms"] = obj.tm_label_end - obj.tm_label_sel_rfpi
        result.append(bs_search_dict)
    return result


def main():
    config = toml.load("config.toml")
    ser_conn_objs = config['files']['recon_objs']
    Reconnect_Stat.RoamingOptions = config['options']
    with open(ser_conn_objs, 'rb') as f:
        reconnect_objs = pickle.load(f)  # deserialize using load()
    build_time_series(reconnect_objs[0].qualities_before_disconn)


if __name__ == "__main__":
    main()
