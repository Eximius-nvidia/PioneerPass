import os

books = [   '{',
                "\t\"ui_prev_resp\": [\n",
                "\t]\n",
                "}"
            ] 
    
uifile_del = os.path.join(os.getcwd(),"UIfile.ini")
if os.path.isfile(uifile_del):
    os.remove(uifile_del)

store_UI_data = os.path.join(os.getcwd(),"UI_Prev_data.json")
if os.path.isfile(store_UI_data):
    os.remove(store_UI_data)
    with open(store_UI_data, 'w') as fp: 
        pass

with open(store_UI_data, 'w') as filepp: 
    filepp.writelines("% s\n" % data for data in books) 

