'''
Author: Yang Yang
LastEditors: Yang Yang
Date: 2024-08-16 14:22:47
LastEditTime: 2024-10-11 09:14:17
Description: 
'''
import pandas as pd
import json
import os
import warnings
warnings.filterwarnings('ignore')

def agg(jsonl_file_list):
    res_list = {"custom_id":[], "res":[]}
    for file_name in jsonl_file_list:
        with open(file_name, 'r', encoding='utf-8') as f:
            for item in f.readlines():
                item = json.loads(item)
                res_list["custom_id"].append(item['custom_id'])
                # print(item.keys())
                if "response" in item:
                    res_list["res"].append(item["response"]["body"]["choices"][0]["message"]["content"])
                else:
                    res_list["res"].append(item["choices"][0]["message"]["content"])
    return pd.DataFrame(res_list)

                

def align(pred_df, labeled_df):
    labeled_df["custom_id"] = labeled_df.apply(lambda x: str(x["id"]) +"_" + x["room_type"], axis=1)
    res_df = pd.merge(labeled_df, pred_df, on="custom_id")
    # res_df["ceil_true"] = (res_df["天花板"] == res_df["pred_ceiling"])
    # res_df["wall_true"] = (res_df["墙壁"] == res_df["pred_wall"])
    # res_df["floor_true"] = (res_df["地板"] == res_df["pred_floor"])
    # print(res_df['ceil_true'].mean(),res_df['wall_true'].mean(),res_df['floor_true'].mean())
    # print(res_df[res_df['ceil_true']==False].head())
    return res_df
    
def match_res_df(res_df):
    def _g_type(res_str, where):
        if where == "wall":
            label_dic = {"壁纸": "N2", "涂料": "N1", "水泥墙面":"N3", "装饰板":"N4", "其他":"N5", "X":None}
            target_name = "内墙面"
        if where == "ceiling":
            label_dic = {"涂料": "T1", "石膏板吊顶": "T2", "装饰板吊顶":"T3", "其他":"T4", "X":None}
            target_name = "天花板"
        if where == "floor":
            label_dic = {"地砖": "D1", "木地板": "D2", "水泥地板":"D3", "其他":"D4", "X":None}
            target_name = "地板"
        res_str = res_str.replace(" ", "")
        res_list = res_str.split("\n")
        for i in res_list:
            try:
                name, type_str = i.split("：")[0], i.split("：")[1]
                # if name =='内墙面':
                    # print(type_str)
            except:
                return None
            if name == target_name:
                if "/" in type_str:
                    res1 = label_dic[type_str.split("/")[0]] if type_str.split("/")[0] in label_dic else "其他"
                    res2 = label_dic[type_str.split("/")[1]] if type_str.split("/")[1] in label_dic else "其他"
                    return res1 + "/" + res2
                else:
                    if type_str in label_dic:
                        return label_dic[type_str]
                    else:
                        # print(name, type_str)
                        return "T4"
    
    def g_wall_type(res_str):
        return _g_type(res_str, 'wall')
        
    def g_ceiling_type(res_str):
        return _g_type(res_str, 'ceiling')
    
    def g_floor_type(res_str):
        return _g_type(res_str, 'floor')
        
    res_df["id"] = res_df["custom_id"].apply(lambda x: x.split("_")[0])
    res_df["room_type"] = res_df["custom_id"].apply(lambda x: x.split("_")[1])
    res_df["pred_wall"] = res_df["res"].apply(lambda x: g_wall_type(x))
    res_df["pred_ceiling"] = res_df["res"].apply(lambda x: g_ceiling_type(x))
    res_df["pred_floor"] = res_df["res"].apply(lambda x: g_floor_type(x))
    return res_df


def get_metrics(a):
    from sklearn.metrics import precision_score, recall_score, f1_score
    a.loc[a['天花板']=='T2/T4','天花板'] = 'T2'
    a.loc[a['pred_ceiling']=='T2/T4','pred_ceiling'] = 'T2'
    a.loc[a['墙壁']=='N1/N5', '墙壁'] = 'N1'
    a.loc[a['地板']=='D5', '地板'] = 'D4'
    print('------天花板------')
    print('Weighted precision', precision_score(a['天花板'], a['pred_ceiling'], average='weighted'))
    print('Weighted recall', recall_score(a['天花板'], a['pred_ceiling'], average='weighted'))
    print('Weighted f1-score', f1_score(a['天花板'], a['pred_ceiling'], average='weighted'))
    print('------墙壁------')
    print('Weighted precision', precision_score(a['墙壁'], a['pred_wall'], average='weighted'))
    print('Weighted recall', recall_score(a['墙壁'], a['pred_wall'], average='weighted'))
    print('Weighted f1-score', f1_score(a['墙壁'], a['pred_wall'], average='weighted'))
    print('------地板------')
    print('Weighted precision', precision_score(a['地板'], a['pred_floor'], average='weighted'))
    print('Weighted recall', recall_score(a['地板'], a['pred_floor'], average='weighted'))
    print('Weighted f1-score', f1_score(a['地板'], a['pred_floor'], average='weighted'))
   


def main():
    # res_list = ["batch_9BbqgqGLu0IpZxkDQyqkdSUR_output.jsonl", "batch_M2gUSQlYIpUnk6dOG2aAjvi1_output.jsonl", "batch_mSJV1Vb4CaDskNlNNUtQTnXm_output.jsonl"]
    res_list = ["revision/testing-res/doubao-pro-res.jsonl"]
    res_df = agg(res_list)
    labeled_df = pd.read_excel("raw_test.xlsx").head(1500)
    res_df = match_res_df(res_df)
    res_df = align(res_df, labeled_df)
    # print(res_df.head())
    res_df = res_df.fillna('unknown')
    res_df.to_excel("revision/formatted_res/20250503doubao-pro.xlsx", sheet_name='Sheet1')
    get_metrics(res_df)

if __name__ == "__main__":
    main()