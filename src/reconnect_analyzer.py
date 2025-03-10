"""

"""
import toml
import pickle
from reconnect_stat import Reconnect_Stat
from reconnect_stat import find_reconnection
from render_results import plot_graphs
from log_utils import *


def process_logs() -> List[Reconnect_Stat]:
    config = toml.load("config.toml")
    filtered_log = config['files']['output_file']
    Reconnect_Stat.RoamingOptions = config['options']
    reconn_objs = find_reconnection(filtered_log)
    return reconn_objs


if __name__ == "__main__":
    reconn_objs = process_logs()
    '''
    out_objs = config['files']['recon_objs']
    with open(out_objs, 'wb') as obj_dump_file:
        pickle.dump(reconn_objs, obj_dump_file)
    '''
    for num, rec_obj in enumerate(reconn_objs, start=1):
        rec_obj.output_reconnect_info(num)
        figures = plot_graphs(rec_obj.qualities_before_disconn)
        for f in figures:
            f.show()
        pass
        # строим графики