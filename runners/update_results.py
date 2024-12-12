import os
import get_results
import get_isolation_results
import pandas as pd

def go():
    for root, dirs, files in os.walk("outputs/prev"):
        for dir in dirs:
            if not 'isolated' in dir:
                continue
            if not any((x in dir.lower() or x in root.lower()) for x in ['yuki', 'old', 'anthropic', 'bad', 'parsed', 'full']):
                out_pth = os.path.join(root,dir)
                res_pth = 'misc/results_cwe/'+dir
                print(dir)
                if 'isolated' in dir.lower():
                    get_isolation_results.getResults(out_pth=out_pth, res_pth=res_pth, updater=True)
                else:
                    get_results.getResults(out_pth=out_pth, res_pth=res_pth, updater=True)
                
                # df = getResults(out_pth=out_pth, res_pth=res_pth)
                # print(df[['run', 'predicted_confidence_normalized', 'predicted_pos_confidence_normalized', 'predicted_confidence_normalized2', 'predicted_pos_confidence_normalized2']])
                # return

            
if __name__ == '__main__':
    go()