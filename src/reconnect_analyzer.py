"""

"""
import toml
import pickle
import pandas as pd

from reconnect_stat import Reconnect_Stat
from reconnect_stat import find_reconnection
from render_results import plot_graphs
from render_results import create_reconnect_report
from render_results import create_bs_search_report
from render_results import create_no_snd_pivot_table

from log_filter import input_config_file
from log_utils import *


def process_logs(toml_conf: Dict[str, Any]) -> List[Reconnect_Stat]:
    # config = toml.load(input_config_file)
    input_file = toml_conf['files']['input_file']
    filtered_dir = toml_conf['files']['output_dir']
    parse_bs_config(toml_conf)
    filtered_log_file_name = filtered_dir + "\\" + get_filter_log_name(input_file)
    Reconnect_Stat.RoamingOptions = toml_conf['options']
    reconn_objs = find_reconnection(filtered_log_file_name)

    return reconn_objs


if __name__ == "__main__":
    config = toml.load(input_config_file)
    reconn_objs = process_logs(config)
    '''
    out_objs = config['files']['recon_objs']
    with open(out_objs, 'wb') as obj_dump_file:
        pickle.dump(reconn_objs, obj_dump_file)
    '''
    report_obj = create_reconnect_report(reconn_objs)
    df = pd.DataFrame(report_obj)
    print(df)

    no_snd_time_durations = create_no_snd_pivot_table(reconn_objs, config)
    df = pd.DataFrame([no_snd_time_durations,])
    print(df)

    for num, recon_obj in enumerate(reconn_objs, start=1):
        bs_search_report = create_bs_search_report(recon_obj)
        df = pd.DataFrame(bs_search_report)
        print(f"Disconnect #{num}")
        print(df)

    for num, rec_obj in enumerate(reconn_objs, start=1):
        rec_obj.output_reconnect_info(num)
        '''
        figures = plot_graphs(rec_obj.qualities_before_disconn)
        for f in figures:
            f.show()
        '''
        pass