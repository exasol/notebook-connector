#!/usr/bin/env python
# coding: utf-8

# <div style="text-align: right;">
#   <img src="https://raw.githubusercontent.com/exasol/ai-lab/refs/heads/main/assets/Exasol_Logo_2025_Dark.svg" style="width:200px; margin: 10px;" />
# </div>
# 
# # Popup message implementation
# 
# <b>This notebook is not supposed to be used on its own.<b>

# In[ ]:


import ipywidgets as widgets
from IPython.display import Javascript, display, clear_output

# Prepare to display a popup message
notify_output = widgets.Output()
display(notify_output)

@notify_output.capture()
def popup_message(message):
    clear_output()
    message = message.replace("'", '"')
    display(Javascript(f"alert('{message}')"))

